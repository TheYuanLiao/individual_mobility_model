package main

import (
	"database/sql"
	"flag"
	"fmt"
	"log"

	"github.com/ericwenn/mscthesis/src/go/internal/ingest"
	_ "github.com/mattn/go-sqlite3"
)

func main() {
	sqlitePath := flag.String("sqlite", "", "The path to sqlite database for storing converted files")
	jsonFile := flag.String("jsonFile", "", "The input json file to parse")
	jsonDirectory := flag.String("jsonDir", "", "The directory containing json files, possibly nested")
	flag.Parse()
	if sqlitePath == nil || *sqlitePath == "" {
		log.Fatal("sqlite path not set")
	}
	db, err := sql.Open("sqlite3", fmt.Sprintf("%s?_busy_timeout=50000&_journal_mode=MEMORY&_sync=OFF", *sqlitePath))
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(createTablesSQL); err != nil {
		log.Fatal(err)
	}
	switch {
	case jsonFile != nil && *jsonFile != "":
		if err := ingest.JSONFile(db, *jsonFile); err != nil {
			log.Fatal(err)
		}
	case jsonDirectory != nil && *jsonDirectory != "":
		if err := ingest.JSONDirectory(db, *jsonDirectory); err != nil {
			log.Fatal(err)
		}
	}
}

const createTablesSQL = `
CREATE TABLE tweets (
	id INTEGER NOT NULL PRIMARY KEY,
	user_id INTEGER NOT NULL,
	created_at TIMESTAMP NOT NULL,
	language STRING,
	longitude FLOAT,
	latitude FLOAT
);

CREATE TABLE profiles (
	id INTEGER NOT NULL PRIMARY KEY,
	user_id INTEGER NOT NULL,
	created_at TIMESTAMP NOT NULL,
	language STRING,
	utc_offset int,
	timezone STRING
);

CREATE INDEX profile_user_id ON profiles(user_id);
`
