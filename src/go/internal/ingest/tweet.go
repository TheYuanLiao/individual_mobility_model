package ingest

import (
	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
)

type User struct {
	ID       int
	Profiles []*twitterddl.ProfileSnapshot
	Timeline []*twitterddl.Tweet
}
