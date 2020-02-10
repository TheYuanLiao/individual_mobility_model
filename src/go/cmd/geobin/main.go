package main

import (
	"database/sql"
	"flag"
	"fmt"
	"log"

	"github.com/ericwenn/mscthesis/src/go/internal/spatemp"
	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
	_ "github.com/mattn/go-sqlite3"
)

func main() {
	sqlitePath := flag.String("sqlite", "", "The path to sqlite database for storing converted files")
	flag.Parse()
	db, err := sql.Open("sqlite3", *sqlitePath)
	defer db.Close()
	check(err)
	if _, err := db.Exec(twitterddl.SpatioTemporalDDL); err != nil {
		log.Fatal(err)
	}
	tweets, err := listTweets(db)
	check(err)
	fmt.Println(len(tweets))
	spatioTemporals := spatemp.ConvertTweets(tweets)
	fmt.Println(len(spatioTemporals))
	err = insertSpatioTemporals(db, spatioTemporals)
	check(err)
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

func insertSpatioTemporals(db *sql.DB, sts []*twitterddl.SpatioTemporal) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	stm, err := tx.Prepare(twitterddl.SpatioTemporalInsertStm)
	if err != nil {
		return err
	}
	defer stm.Close()
	for _, st := range sts {
		if _, err := stm.Exec(st.InsertExec()...); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	return nil
}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
