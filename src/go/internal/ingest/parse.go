package ingest

import (
	"bufio"
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
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

func parseJSON(r io.Reader) (*User, error) {
	sc := bufio.NewScanner(r)
	var tweets []*JSONTweet
	for sc.Scan() {
		var t JSONTweet
		if err := json.Unmarshal(sc.Bytes(), &t); err != nil {
			return nil, err
		}
		ts, err := time.Parse(time.RubyDate, t.CreatedAt)
		if err != nil {
			return nil, err
		}
		t.CreatedAtTime = ts
		tweets = append(tweets, &t)
	}
	u, err := jsonAsUser(tweets)
	if err != nil {
		return nil, err
	}
	return u, nil
}

func parseJSONFile(path string) (*User, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	user, err := parseJSON(f)
	if err != nil {
		return nil, err
	}
	return user, nil
}

func jsonAsUser(tweets []*JSONTweet) (*User, error) {
	sort.Slice(tweets, func(i, j int) bool {
		return tweets[i].CreatedAtTime.Before(tweets[j].CreatedAtTime)
	})
	var u User
	for _, tw := range tweets {
		t := &Tweet{
			ID:        tw.ID,
			UserID:    tw.User.ID,
			CreatedAt: tw.CreatedAtTime,
			Language:  tw.Language,
		}
		if len(tw.Coordinates.Coordinates) == 2 {
			t.Latitude = tw.Coordinates.Coordinates[1]
			t.Longitude = tw.Coordinates.Coordinates[0]
		}
		u.Timeline = append(u.Timeline, t)

		p := &ProfileSnapshot{
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
	return &u, nil
}

func equalProfile(a, b *ProfileSnapshot) bool {
	return a.Timezone == b.Timezone && a.UTCOffset == b.UTCOffset && a.Language == b.Language
}

func JSONFile(db *sql.DB, path string) error {
	p := parser{
		s: storage{
			db: db,
		},
	}
	return p.jsonFile(path)
}

func JSONDirectory(db *sql.DB, path string) error {
	p := parser{
		s: storage{
			db: db,
		},
	}
	return p.jsonDirectory(path)
}

type parser struct {
	s storage
}

func (p *parser) jsonFile(path string) error {
	user, err := parseJSONFile(path)
	if err != nil {
		return err
	}
	if err := p.s.insertAll([]*User{user}); err != nil {
		return err
	}
	return nil
}

func (p *parser) jsonDirectory(path string) error {
	const maxFilesInMem = 200
	const insertBatchSize = 1000
	fs, err := filepath.Glob(filepath.Join(path, "User*.json"))
	if err != nil {
		return err
	}
	fmt.Printf("Found %d files\n", len(fs))
	bytesChan := make(chan []byte, maxFilesInMem)
	userChan := make(chan *User, insertBatchSize)
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
				u, err := parseJSON(bytes.NewBuffer(b))
				if err != nil {
					log.Println("parse file", err)
				}
				// release file from memory
				b = nil
				userChan <- u
			}
		}()
	}
	// Store users to DB in batches
	var storeGroup sync.WaitGroup
	storeGroup.Add(1)
	go func() {
		var users []*User
		flush := func() {
			log.Printf("flushing %d users...", len(users))
			if err := p.s.insertAll(users); err != nil {
				fmt.Println(err)
			}
			log.Printf("flushed %d users", len(users))
			users = nil
		}
		for {
			u, more := <-userChan
			if !more {
				flush()
				storeGroup.Done()
				return
			}
			users = append(users, u)
			if len(users) >= insertBatchSize {
				flush()
			}
		}
	}()
	// Start processing all files
	for _, p := range fs {
		b, err := ioutil.ReadFile(p)
		if err != nil {
			return err
		}
		bytesChan <- b
	}
	// let parsers finish
	close(bytesChan)
	log.Printf("waiting for parsers to finish")
	parseGroup.Wait()
	// let storaer finish
	close(userChan)
	storeGroup.Wait()
	return nil
}
