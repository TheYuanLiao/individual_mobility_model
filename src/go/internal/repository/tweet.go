package repository

import (
	"time"
)

type Tweet struct {
	ID        int       `pk:"" notnull:""`
	UserID    int       `idx:"user" notnull:""`
	CreatedAt time.Time `notnull:""`
	Language  string
	Longitude float64
	Latitude  float64
}
