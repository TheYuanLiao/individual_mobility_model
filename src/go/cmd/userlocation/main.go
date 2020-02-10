package main

import (
	"database/sql"
	"flag"
	"fmt"
	"log"
	"sort"

	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"

	"github.com/mmcloughlin/geohash"

	_ "github.com/mattn/go-sqlite3"
)

type UserTopLocation struct {
	UserID      int
	Geohash     string // 6 precision
	TweetsInGeo int
}

type UserLoc struct {
	UserID int
	Lat    float64 // 6 precision
	Long   float64
}

func (s *UserTopLocation) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(&s.UserID, &s.Geohash, &s.TweetsInGeo)
}

func main() {
	sqlitePath := flag.String("sqlite", "", "The path to sqlite database for storing converted files")
	flag.Parse()
	db, err := sql.Open("sqlite3", *sqlitePath)
	defer db.Close()
	check(err)
	if _, err := db.Exec(twitterddl.HomeLocationDDL); err != nil {
		log.Fatal(err)
	}
	topGeohash, err := listUsersTopGeohash(db)
	check(err)
	usersGeohashes := groupByUser(topGeohash)
	var hls []*twitterddl.HomeLocation
	for _, tls := range usersGeohashes {
		if len(tls) < 2 {
			continue
		}
		hl := homeLocation(tls)
		hls = append(hls, hl)
	}
	check(insertHomeLocations(db, hls))
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

func groupByUser(tls []*UserTopLocation) map[int][]*UserTopLocation {
	users := make(map[int][]*UserTopLocation)
	for _, tl := range tls {
		users[tl.UserID] = append(users[tl.UserID], tl)
	}
	return users
}

const usersToGeohashStm = `
SELECT
   user_id, 
   geohash as geohash, 
   count(*) as c
FROM spatiotemporal
WHERE             
	  hourofday < 10      
  and hourofday > 0    
  and weekday < 5    
  and weekday > 0   
GROUP BY geohash, user_id   
ORDER BY c desc
`

func homeLocation(tls []*UserTopLocation) *twitterddl.HomeLocation {
	totalTweets := 0
	for _, bin := range tls {
		totalTweets += bin.TweetsInGeo
	}
	perc := float64(0)
	for perc < 0.1 {
		perc = float64(tls[0].TweetsInGeo) / float64(totalTweets)
		// fmt.Println(len(tls), tls[0].TweetsInGeo, perc)
		tls = unsharpen(tls)
	}
	lat, lng := geohash.Decode(tls[0].Geohash)
	return &twitterddl.HomeLocation{
		UserID:      tls[0].UserID,
		Latitude:    lat,
		Longitude:   lng,
		Geohash:     tls[0].Geohash,
		Percentage:  perc,
		TotalTweets: totalTweets,
	}
}

func unsharpen(tls []*UserTopLocation) []*UserTopLocation {
	groups := make(map[string][]*UserTopLocation)
	for _, tl := range tls {
		if len(tl.Geohash) == 0 {
			fmt.Println("Skipping nil geohash")
			continue
		}
		unsharp := tl.Geohash[:len(tl.Geohash)-1]
		groups[unsharp] = append(groups[unsharp], tl)
	}
	var newTls []*UserTopLocation
	for hash, tls := range groups {
		newCount := 0
		for _, tl := range tls {
			newCount += tl.TweetsInGeo
		}
		newTls = append(newTls, &UserTopLocation{
			UserID:      tls[0].UserID,
			Geohash:     hash,
			TweetsInGeo: newCount,
		})
	}
	sort.Slice(newTls, func(i, j int) bool {
		return newTls[i].TweetsInGeo > newTls[j].TweetsInGeo
	})
	return newTls
}

func listUsersTopGeohash(db *sql.DB) ([]*UserTopLocation, error) {
	stm, err := db.Prepare(usersToGeohashStm)
	if err != nil {
		return nil, err
	}
	rows, err := stm.Query()
	if err != nil {
		return nil, err
	}
	var loc []*UserTopLocation
	for rows.Next() {
		var t UserTopLocation
		if err := t.UnmarshalRow(rows); err != nil {
			return nil, err
		}
		loc = append(loc, &t)
	}
	return loc, nil
}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
