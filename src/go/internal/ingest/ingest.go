package ingest

import (
	"archive/zip"
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/ericwenn/mscthesis/src/go/internal/repository"
)

type JSONTweet struct {
	CreatedAtTime time.Time
	CreatedAt     string `json:"created_at"`
	ID            int    `json:"id"`
	Language      string `json:"lang"`
	Coordinates   struct {
		Coordinates []float64 `json:"coordinates"`
	} `json:"coordinates"`
	Text string `json:"text"`
	User struct {
		ID        int    `json:"id"`
		Language  string `json:"lang"`
		Location  string `json:"location"`
		UTCOffset int    `json:"utc_offset"`
		Timezone  string `json:"time_zone"`
	} `json:"user"`
}

type User struct {
	ID       int
	Profiles []*repository.Profile
	Timeline []*repository.GeoTweet
}

func parseJSON(r io.Reader) (*User, *Summary, error) {
	sc := bufio.NewScanner(r)
	var tweets []*JSONTweet
	for sc.Scan() {
		var t JSONTweet
		if err := json.Unmarshal(sc.Bytes(), &t); err != nil {
			return nil, nil, err
		}
		ts, err := time.Parse(time.RubyDate, t.CreatedAt)
		if err != nil {
			return nil, nil, err
		}
		t.CreatedAtTime = ts
		tweets = append(tweets, &t)
	}
	if len(tweets) == 0 {
		return nil, nil, fmt.Errorf("no tweets found for user")
	}
	u, sum, err := jsonAsUser(tweets)
	if err != nil {
		return nil, nil, err
	}
	return u, sum, nil
}

type Summary struct {
	Duplicates int
	Tweets     int
	GeoTweets  int
}

func (s *Summary) Add(other *Summary) {
	s.Duplicates += other.Duplicates
	s.Tweets += other.Tweets
	s.GeoTweets += other.GeoTweets
}

func jsonAsUser(tweets []*JSONTweet) (*User, *Summary, error) {
	sort.Slice(tweets, func(i, j int) bool {
		return tweets[i].CreatedAtTime.Before(tweets[j].CreatedAtTime)
	})
	var u User
	seenTweets := make(map[int]struct{})
	var summary Summary
	for _, tw := range tweets {
		if u.ID != 0 && tw.User.ID != u.ID {
			return nil, nil, fmt.Errorf("found tweets with different user id: %d, %d", u.ID, tw.User.ID)
		}
		u.ID = tw.User.ID
		if _, ok := seenTweets[tw.ID]; ok {
			summary.Duplicates++
			continue
		}
		summary.Tweets++
		// not a geotagged tweet
		if len(tw.Coordinates.Coordinates) != 2 {
			continue
		}
		summary.GeoTweets++
		seenTweets[tw.ID] = struct{}{}
		t, err := toGeoTweet(&repository.Tweet{
			ID:        tw.ID,
			UserID:    tw.User.ID,
			CreatedAt: tw.CreatedAtTime,
			Language:  tw.Language,
			Latitude:  tw.Coordinates.Coordinates[1],
			Longitude: tw.Coordinates.Coordinates[0],
		})
		if err != nil {
			return nil, nil, fmt.Errorf("to geotweet: %w", err)
		}
		u.Timeline = append(u.Timeline, t)
		p := &repository.Profile{
			ID:        tw.ID,
			UserID:    tw.User.ID,
			CreatedAt: tw.CreatedAtTime,
			Language:  tw.User.Language,
			UTCOffset: tw.User.UTCOffset,
			Timezone:  tw.User.Timezone,
		}
		if len(u.Profiles) == 0 || !equalProfile(u.Profiles[len(u.Profiles)-1], p) {
			u.Profiles = append(u.Profiles, p)
		}
	}
	return &u, &summary, nil
}

func equalProfile(a, b *repository.Profile) bool {
	return a.Timezone == b.Timezone && a.UTCOffset == b.UTCOffset && a.Language == b.Language
}

type Ingester struct {
	TweetRepo   *repository.GeoTweetRepo
	ProfileRepo *repository.ProfileRepo
}

func (i *Ingester) Directory(path string) error {
	filePaths, err := filepath.Glob(filepath.Join(path, "User*.json"))
	if err != nil {
		return err
	}
	sources := make([]Source, len(filePaths))
	for i, fp := range filePaths {
		sources[i] = &FileSource{
			absolutePath: fp,
		}
	}
	return i.process(sources)
}

func (i *Ingester) Zip(path string) error {
	r, err := zip.OpenReader(path)
	if err != nil {
		return err
	}
	defer r.Close()
	sources := make([]Source, len(r.File))
	for i, f := range r.File {
		sources[i] = &ZipSource{
			f: f,
		}
	}
	return i.process(sources)
}

func (i *Ingester) process(sources []Source) error {
	const maxFilesInMem = 50
	const insertBatchSize = 1000
	fmt.Printf("Processing %d files\n", len(sources))
	fsGrouped := groupByUser(sources)
	fmt.Printf("Found unique %d users\n", len(fsGrouped))
	bytesChan := make(chan []byte, maxFilesInMem)
	userChan := make(chan *User, insertBatchSize)
	summaryChan := make(chan *Summary, maxFilesInMem)
	var parseGroup sync.WaitGroup
	// Read and parse json files concurrently
	for i := 0; i < 10; i++ {
		parseGroup.Add(1)
		go func() {
			for {
				b, more := <-bytesChan
				if !more {
					parseGroup.Done()
					return
				}
				u, sum, err := parseJSON(bytes.NewBuffer(b))
				if err != nil {
					log.Println("parse file", err)
					continue
				}
				// release file from memory
				b = nil
				userChan <- u
				summaryChan <- sum
			}
		}()
	}
	// Store users to DB in batches
	var storeGroup sync.WaitGroup
	storeGroup.Add(1)
	go func() {
		nUsers := 0
		var tweets []*repository.GeoTweet
		var profiles []*repository.Profile
		flush := func() {
			log.Printf("flushing %d ...", nUsers)
			if err := i.TweetRepo.InsertMany(tweets); err != nil {
				fmt.Println(err)
			}
			if err := i.ProfileRepo.InsertMany(profiles); err != nil {
				fmt.Println(err)
			}
			tweets = nil
			profiles = nil
			nUsers = 0
		}
		for {
			u, more := <-userChan
			if !more {
				flush()
				storeGroup.Done()
				return
			}
			tweets = append(tweets, u.Timeline...)
			profiles = append(profiles, u.Profiles...)
			nUsers++
			if nUsers >= insertBatchSize {
				flush()
			}
		}
	}()
	var summaryGroup sync.WaitGroup
	summaryGroup.Add(1)
	go func() {
		var summary Summary
		got := 0
		for {
			s, more := <-summaryChan
			if !more {
				fmt.Printf("%+v\n", summary)
				summaryGroup.Done()
				return
			}
			summary.Add(s)
			got++
			if got%1000 == 0 {
				fmt.Printf("%+v\n", summary)
			}
		}
	}()
	// Start processing all files
	for _, srcs := range fsGrouped {
		var bs []byte
		for _, src := range srcs {
			b, err := src.ReadAll()
			if err != nil {
				return err
			}
			bs = append(bs, b...)
		}
		if len(bs) == 0 {
			continue
		}
		bytesChan <- bs
	}
	// let parsers finish
	close(bytesChan)
	log.Printf("waiting for parsers to finish")
	parseGroup.Wait()
	// let storer finish
	close(userChan)
	close(summaryChan)
	storeGroup.Wait()
	return nil
}

func groupByUser(sources []Source) [][]Source {
	// from userId to filepaths for this user
	groups := make(map[string][]Source)
	for _, src := range sources {
		// Filenames are on the form "UserID_[user-id]_[time-period].json
		// Ex: UserID_6913_20171122-233133.json
		parts := strings.Split(src.Name(), "_")
		userID := parts[1]
		groups[userID] = append(groups[userID], src)
	}
	var grouped [][]Source
	for _, src := range groups {
		grouped = append(grouped, src)
	}
	return grouped
}
