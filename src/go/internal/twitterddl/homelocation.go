package twitterddl

import "database/sql"

type HomeLocation struct {
	UserID      int
	Latitude    float64
	Longitude   float64
	Geohash     string
	Percentage  float64
	TotalTweets int
}

func (s *HomeLocation) InsertExec() []interface{} {
	return []interface{}{s.UserID, s.Latitude, s.Longitude, s.Geohash, s.Percentage, s.TotalTweets}
}

func (s *HomeLocation) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(&s.UserID, &s.Latitude, &s.Longitude, &s.Geohash, &s.Percentage, &s.TotalTweets)
}

const HomeLocationDDL = `
CREATE TABLE homelocations (
	user_id INTEGER NOT NULL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    geohash STRING NOT NULL,
    percentage FLOAT NOT NULL,
	total_tweets INT NOT NULL
);
`
const HomeLocationInsertStm = "INSERT INTO homelocations(user_id, latitude, longitude, geohash, percentage, total_tweets) VALUES (?, ?, ?, ?, ?, ?)"
