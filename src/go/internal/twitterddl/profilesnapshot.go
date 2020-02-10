package twitterddl

import "time"

type ProfileSnapshot struct {
	ID        int
	UserID    int
	CreatedAt time.Time
	Language  string
	UTCOffset int
	Timezone  string
}
