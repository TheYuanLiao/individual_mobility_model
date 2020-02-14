package twitterddl

import (
	"database/sql"
	"time"
)

type GeoTweet struct {
	TweetID   int
	UserID    int
	CreatedAt time.Time
	Latitude  float64
	Longitude float64
	Month     time.Month   // Jan = 1, ..., Dec = 12
	Weekday   time.Weekday // Sun = 0, Mon = 1, ... Sat = 6s
	HourOfDay int          // 0...23
	TimeZone  string       // IANA Database format. Ex: Europe/Stockholm
}

func (gt *GeoTweet) InsertExec() []interface{} {
	return []interface{}{
		gt.TweetID,
		gt.UserID,
		gt.CreatedAt,
		gt.Latitude,
		gt.Longitude,
		gt.Month,
		gt.Weekday,
		gt.HourOfDay,
		gt.TimeZone,
	}
}

func (gt *GeoTweet) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(
		&gt.TweetID,
		&gt.UserID,
		&gt.CreatedAt,
		&gt.Latitude,
		&gt.Longitude,
		&gt.Month,
		&gt.Weekday,
		&gt.HourOfDay,
		&gt.TimeZone,
	)
}

const GeoTweetDDL = `
CREATE TABLE geotweets (
	tweet_id INTEGER NOT NULL PRIMARY KEY,
	user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
	month INTEGER NOT NULL,
	weekday INTEGER NOT NULL,
	hourofday INTEGER NOT NULL,
	time_zone STRING
);
`

const GeoTweetInsertStm = `
INSERT INTO geotweets(
    tweet_id, 
    user_id, 
    created_at, 
    latitude, 
    longitude,
    month,
    weekday,
    hourofday,
	time_zone
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
