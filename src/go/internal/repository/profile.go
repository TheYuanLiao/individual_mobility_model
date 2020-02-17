package repository

import "time"

type Profile struct {
	ID        int
	UserID    int
	CreatedAt time.Time
	Language  string
	UTCOffset int
	Timezone  string
}
