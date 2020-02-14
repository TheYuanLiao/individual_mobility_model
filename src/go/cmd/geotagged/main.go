package main

import (
	"database/sql"
	"flag"
	"log"
	"time"

	"github.com/bradfitz/latlong"
	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
	_ "github.com/mattn/go-sqlite3"
	"gopkg.in/ugjka/go-tz.v2/tz"
)

func main() {
	sqlitePath := flag.String("sqlite", "", "The path to sqlite database for storing converted files")
	flag.Parse()
	db, err := sql.Open("sqlite3", *sqlitePath)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(twitterddl.GeoTweetDDL); err != nil {
		log.Fatal(err)
	}
	log.Println("Listing tweets")
	tweets, err := listTweets(db)
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Listed tweets")
	gtweets, err := toGeoTweet(tweets)
	if err != nil {
		log.Fatal(err)
	}
	tx, err := db.Begin()
	if err != nil {
		log.Fatal(err)
	}
	stm, err := tx.Prepare(twitterddl.GeoTweetInsertStm)
	if err != nil {
		log.Fatal(err)
	}
	defer stm.Close()
	for _, gt := range gtweets {
		if _, err := stm.Exec(gt.InsertExec()...); err != nil {
			log.Fatal(err)
		}
	}
	if err := tx.Commit(); err != nil {
		log.Fatal(err)
	}
}

func timeZone(lat, lng float64) string {
	tzo := latlong.LookupZoneName(lat, lng)
	if tzo != "" {
		return tzo
	}
	tzos, err := tz.GetZone(tz.Point{
		Lon: lng,
		Lat: lat,
	})
	if err != nil || len(tzos) == 0 {
		log.Printf("failed to get tz %f %f", lat, lng)
		return ""
	}
	return tzos[0]
}

func toGeoTweet(tweets []*twitterddl.Tweet) ([]*twitterddl.GeoTweet, error) {
	geoTweets := make([]*twitterddl.GeoTweet, len(tweets))
	for i, tweet := range tweets {
		tzo := timeZone(tweet.Latitude, tweet.Longitude)
		tweetLocation, err := time.LoadLocation(tzo)
		if err != nil {
			return nil, err
		}
		createdLocal := tweet.CreatedAt.In(tweetLocation)
		hour, _, _ := createdLocal.Clock()
		geoTweets[i] = &twitterddl.GeoTweet{
			TweetID:   tweet.ID,
			UserID:    tweet.UserID,
			CreatedAt: tweet.CreatedAt,
			Latitude:  tweet.Latitude,
			Longitude: tweet.Longitude,
			Month:     createdLocal.Month(),
			Weekday:   createdLocal.Weekday(),
			HourOfDay: hour,
			TimeZone:  tzo,
		}
	}
	return geoTweets, nil
}

func listTweets(db *sql.DB) ([]*twitterddl.Tweet, error) {
	stm, err := db.Prepare("SELECT * FROM tweets WHERE latitude != 0 and longitude != 0")
	if err != nil {
		return nil, err
	}
	rows, err := stm.Query()
	if err != nil {
		return nil, err
	}
	var tweets []*twitterddl.Tweet
	for rows.Next() {
		var t twitterddl.Tweet
		if err := t.UnmarshalRow(rows); err != nil {
			return nil, err
		}
		tweets = append(tweets, &t)
	}
	return tweets, nil
}
