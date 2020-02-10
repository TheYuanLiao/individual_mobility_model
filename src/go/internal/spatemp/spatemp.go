package spatemp

import (
	"log"
	"sync"
	"time"

	"github.com/bradfitz/latlong"
	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
	"github.com/mmcloughlin/geohash"
)

func ConvertTweets(tweets []*twitterddl.Tweet) []*twitterddl.SpatioTemporal {
	var convertGroup sync.WaitGroup
	tweetChan := make(chan *twitterddl.Tweet)
	stChan := make(chan *twitterddl.SpatioTemporal)
	go func() {
		for _, t := range tweets {
			tweetChan <- t
		}
		close(tweetChan)
	}()
	for i := 0; i < 10; i++ {
		convertGroup.Add(1)
		go func() {
			for {
				t, more := <-tweetChan
				if !more {
					convertGroup.Done()
					return
				}
				st, err := convert(t)
				if err != nil {
					log.Printf("convert tweet: %w", err)
					continue
				}
				stChan <- st
			}
		}()
	}
	go func() {
		convertGroup.Wait()
		close(stChan)
	}()
	sts := make([]*twitterddl.SpatioTemporal, 0, len(tweets))
	for {
		st, more := <-stChan
		if !more {
			break
		}
		sts = append(sts, st)
	}
	return sts
}

func convert(tweet *twitterddl.Tweet) (*twitterddl.SpatioTemporal, error) {
	tweetLocation, err := time.LoadLocation(latlong.LookupZoneName(tweet.Latitude, tweet.Longitude))
	if err != nil {
		return nil, err
	}
	createdLocal := tweet.CreatedAt.In(tweetLocation)
	st := twitterddl.SpatioTemporal{
		UserID:  tweet.UserID,
		TweetID: tweet.ID,
		Geohash: geohash.Encode(tweet.Latitude, tweet.Longitude),
		Month:   createdLocal.Month(),
		Weekday: createdLocal.Weekday(),
	}
	st.HourOfDay, _, _ = createdLocal.Clock()
	return &st, nil
}
