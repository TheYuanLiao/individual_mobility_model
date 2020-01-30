package ingest

import (
	"database/sql"
	"sync"
)

type storage struct {
	db      *sql.DB
	mu      sync.Mutex
	batched []*User
}

func (s *storage) insertAll(users []*User) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	stm, err := tx.Prepare("INSERT INTO tweets(id, user_id, created_at, language, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?)")
	if err != nil {
		return err
	}
	defer stm.Close()
	for _, u := range users {
		for _, t := range u.Timeline {
			if _, err := stm.Exec(t.ID, t.UserID, t.CreatedAt, t.Language, t.Longitude, t.Latitude); err != nil {
				return err
			}
		}
	}
	pStm, err := tx.Prepare("INSERT INTO profiles(id, user_id, created_at, language, utc_offset, timezone) VALUES (?, ?, ?, ?, ?, ?)")
	defer pStm.Close()
	for _, u := range users {
		for _, p := range u.Profiles {
			if _, err := pStm.Exec(p.ID, p.UserID, p.CreatedAt, p.Language, p.UTCOffset, p.Timezone); err != nil {
				return err
			}
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	return nil
}
