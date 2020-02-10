package twitterddl

import (
	"database/sql"
	"time"
)

type SpatioTemporal struct {
	UserID  int
	TweetID int
	// spatial
	Geohash string // 12 precision
	// temporal
	Month     time.Month   // Jan = 1, ..., Dec = 12
	Weekday   time.Weekday // Sun = 0, Mon = 1, ... Sat = 6s
	HourOfDay int          // 0...23
}

func (s *SpatioTemporal) InsertExec() []interface{} {
	return []interface{}{s.TweetID, s.UserID, s.Geohash, s.Month, s.Weekday, s.HourOfDay}
}

func (s *SpatioTemporal) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(&s.TweetID, &s.UserID, &s.Geohash, &s.Month, &s.Weekday, &s.HourOfDay)
}

const SpatioTemporalDDL = `
CREATE TABLE spatiotemporal (
	tweet_id INTEGER NOT NULL PRIMARY KEY,
	user_id INTEGER NOT NULL,
	geohash STRING NOT NULL,
	month INTEGER NOT NULL,
	weekday INTEGER NOT NULL,
	hourofday INTEGER NOT NULL
);
`
const SpatioTemporalInsertStm = "INSERT INTO spatiotemporal(tweet_id, user_id, geohash, month, weekday, hourofday) VALUES (?, ?, ?, ?, ?, ?)"
