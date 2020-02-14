package main

import (
	"database/sql"
	"flag"
	"fmt"
	"log"

	"github.com/ericwenn/mscthesis/src/go/internal/locations"

	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
	_ "github.com/mattn/go-sqlite3"
)

func main() {
	sqlitePath := flag.String("sqlite", "", "The path to sqlite database for storing converted files")
	flag.Parse()
	db, err := sql.Open("sqlite3", *sqlitePath)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(twitterddl.HomeLocationDDL); err != nil {
		log.Fatal(err)
	}
	log.Println("Listing tweets")
	tweets, err := listTweets(db)
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Listed tweets")
	userTweets := groupByUser(tweets)
	log.Println("Grouped tweets")
	var hls []*twitterddl.HomeLocation
	for uid, ts := range userTweets {
		loc := locations.Visits(ts)
		if loc == nil {
			fmt.Printf("Did not find home location for user %d %d\n", uid, len(ts))
			continue
		}
		hls = append(hls, loc)
	}
	if err := insertHomeLocations(db, hls); err != nil {
		log.Fatal(err)
	}
}

func insertHomeLocations(db *sql.DB, hls []*twitterddl.HomeLocation) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	stm, err := tx.Prepare(twitterddl.HomeLocationInsertStm)
	if err != nil {
		return err
	}
	defer stm.Close()
	for _, hl := range hls {
		if _, err := stm.Exec(hl.InsertExec()...); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	return nil
}

func groupByUser(tweets []*twitterddl.GeoTweet) map[int][]*twitterddl.GeoTweet {
	users := make(map[int][]*twitterddl.GeoTweet)
	for _, t := range tweets {
		users[t.UserID] = append(users[t.UserID], t)
	}
	return users
}

func listTweets(db *sql.DB) ([]*twitterddl.GeoTweet, error) {
	stm, err := db.Prepare(`
	SELECT 
	       * 
	FROM geotweets
	WHERE             
		(hourofday < 10 or hourofday > 20)     
	  and weekday < 6    
	  and weekday > 0`)
	if err != nil {
		return nil, err
	}
	rows, err := stm.Query()
	if err != nil {
		return nil, err
	}
	var tweets []*twitterddl.GeoTweet
	for rows.Next() {
		var t twitterddl.GeoTweet
		if err := t.UnmarshalRow(rows); err != nil {
			return nil, err
		}
		tweets = append(tweets, &t)
	}
	return tweets, nil
}
