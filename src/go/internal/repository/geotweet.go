package repository

import "time"

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
