package ingest

import (
	"log"
	"time"

	"github.com/bradfitz/latlong"
	"github.com/TheYuanLiao/individual-mobility-model/src/go/internal/repository"
	"gopkg.in/ugjka/go-tz.v2/tz"
)

func timeZone(lat, lng float64) string {
	tzo := latlong.LookupZoneName(lat, lng)
	if tzo != "" {
		return tzo
	}
	tzos, err := tz.GetZone(tz.Point{
		Lon: lng,
		Lat: lat,
	})
	if err != nil || len(tzos) == 0 {
		log.Printf("failed to get tz %f %f", lat, lng)
		return ""
	}
	return tzos[0]
}

func toGeoTweet(tweet *repository.Tweet) (*repository.GeoTweet, error) {
	tzo := timeZone(tweet.Latitude, tweet.Longitude)
	tweetLocation, err := time.LoadLocation(tzo)
	if err != nil {
		return nil, err
	}
	createdLocal := tweet.CreatedAt.In(tweetLocation)
	hour, _, _ := createdLocal.Clock()
	return &repository.GeoTweet{
		TweetID:   tweet.ID,
		UserID:    tweet.UserID,
		CreatedAt: tweet.CreatedAt,
		Latitude:  tweet.Latitude,
		Longitude: tweet.Longitude,
		Month:     createdLocal.Month(),
		Weekday:   createdLocal.Weekday(),
		HourOfDay: hour,
		TimeZone:  tzo,
	}, nil
}
