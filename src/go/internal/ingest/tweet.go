package ingest

import "time"

type User struct {
	ID       string
	Profiles []*ProfileSnapshot
	Timeline []*Tweet
}

type ProfileSnapshot struct {
	ID        int
	UserID    int
	CreatedAt time.Time
	Language  string
	UTCOffset int
	Timezone  string
}

type Tweet struct {
	ID        int
	UserID    int
	CreatedAt time.Time
	Language  string
	Latitude  float64
	Longitude float64
}
