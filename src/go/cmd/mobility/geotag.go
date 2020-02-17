package main

import (
	"log"
	"time"

	"github.com/bradfitz/latlong"
	"github.com/ericwenn/mscthesis/src/go/internal/repository"
	"github.com/urfave/cli/v2"
	"gopkg.in/ugjka/go-tz.v2/tz"
)

func (a *mobility) geotag() *cli.Command {
	return &cli.Command{
		Name: "geotag",
		Flags: []cli.Flag{
			&cli.BoolFlag{
				Name: "create",
			},
		},
		Action: func(context *cli.Context) error {
			tr := repository.TweetRepo{DB: a.db}
			gtr := repository.GeoTweetRepo{DB: a.db}
			if context.Bool("create") {
				if err := gtr.CreateTable(); err != nil {
					return err
				}
			}
			tweets, err := tr.List("latitude != 0 and longitude != 0")
			if err != nil {
				return err
			}
			gTweets, err := toGeoTweet(tweets)
			if err != nil {
				return err
			}
			if err := gtr.InsertMany(gTweets); err != nil {
				return err
			}
			return nil
		},
	}
}

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

func toGeoTweet(tweets []*repository.Tweet) ([]*repository.GeoTweet, error) {
	geoTweets := make([]*repository.GeoTweet, len(tweets))
	for i, tweet := range tweets {
		tzo := timeZone(tweet.Latitude, tweet.Longitude)
		tweetLocation, err := time.LoadLocation(tzo)
		if err != nil {
			return nil, err
		}
		createdLocal := tweet.CreatedAt.In(tweetLocation)
		hour, _, _ := createdLocal.Clock()
		geoTweets[i] = &repository.GeoTweet{
			TweetID:   tweet.ID,
			UserID:    tweet.UserID,
			CreatedAt: tweet.CreatedAt,
			Latitude:  tweet.Latitude,
			Longitude: tweet.Longitude,
			Month:     createdLocal.Month(),
			Weekday:   createdLocal.Weekday(),
			HourOfDay: hour,
			TimeZone:  tzo,
		}
	}
	return geoTweets, nil
}
