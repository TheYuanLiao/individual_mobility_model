package twitterddl

import (
	"database/sql"
	"time"
)

type Tweet struct {
	ID        int
	UserID    int
	CreatedAt time.Time
	Language  string
	Latitude  float64
	Longitude float64
}

func (t *Tweet) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(&t.ID, &t.UserID, &t.CreatedAt, &t.Language, &t.Longitude, &t.Latitude)
}
