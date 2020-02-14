package twitterddl

import "database/sql"

type HomeLocation struct {
	UserID int
	// Center of location
	Latitude  float64
	Longitude float64
	// Number of tweets at this location
	Count int
	// Percentage of total amount of tweets at this location
	Percentage       float64
	RadiusKilometers float64
}

func (s *HomeLocation) InsertExec() []interface{} {
	return []interface{}{
		s.UserID,
		s.Latitude,
		s.Longitude,
		s.Count,
		s.Percentage,
		s.RadiusKilometers,
	}
}

func (s *HomeLocation) UnmarshalRow(row *sql.Rows) error {
	return row.Scan(
		&s.UserID,
		&s.Latitude,
		&s.Longitude,
		&s.Count,
		&s.Percentage,
		&s.RadiusKilometers,
	)
}

const HomeLocationDDL = `
CREATE TABLE homelocations (
	user_id INTEGER NOT NULL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    count INTEGER NOT NULL,
    percentage FLOAT NOT NULL,
    radius_kilometers FLOAT NOT NULL
);
`

const HomeLocationInsertStm = `INSERT INTO homelocations(
    user_id, 
    latitude, 
    longitude, 
    count, 
    percentage, 
    radius_kilometers
) VALUES (?, ?, ?, ?, ?, ?)`
