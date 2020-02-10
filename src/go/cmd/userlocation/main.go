package main

import (
	"database/sql"
	"flag"
	"fmt"
	_ "github.com/mattn/go-sqlite3"
	"github.com/mmcloughlin/geohash"
)

type UserTopLocation struct {
	UserID  int
	Geohash string // 6 precision
	TweetsInGeo int
}

type UserLoc struct {
	UserID  int
	Lat float64 // 6 precision
	Long float64
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
	topGeohash, err := listUsersTopGeohash(db)
	check(err)
	var userLocs []*UserLoc
	for _, row := range topGeohash {
		var u UserLoc
		u.UserID = row.UserID
		lat, long := geohash.DecodeCenter(row.Geohash)
		u.Lat = lat
		u.Long = long
		userLocs = append(userLocs, &u)

	}
	for _, u := range userLocs[0:100] {
		fmt.Println(u)
	}
}


func listUsersTopGeohash(db *sql.DB) ([]*UserTopLocation, error) {
	stm, err := db.Prepare("SELECT user_id, geohash, max(c) FROM (     SELECT         user_id, substr(geohash, 0, 7) as geohash, count(*) as c     FROM spatiotemporal     WHERE             hourofday < 10       and hourofday > 0       and weekday < 5       and weekday > 0     GROUP BY substr(geohash, 0, 7), user_id     ORDER BY c desc) GROUP BY user_id, geohash order by max(c) desc")
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