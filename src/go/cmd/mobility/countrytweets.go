package main

import (
	"fmt"
	"github.com/ericwenn/mscthesis/src/go/internal/bounds"
	"github.com/ericwenn/mscthesis/src/go/internal/repository"
	"github.com/urfave/cli/v2"
	"strings"
	"os"
	"encoding/csv"
	"time"
)

func (a *mobility) countrytweets() *cli.Command {
	return &cli.Command{
		Name: "countrytweets",
		Flags: []cli.Flag{
			&cli.PathFlag{
				Name: "shapeDir",
				Required: true,
			},
			&cli.PathFlag{
				Name: "outputDir",
				Value: "./../../dbs/",
			},
			&cli.StringFlag{
				Name:  "region",
				Value: "Sweden",
			},
			&cli.StringFlag{
				Name:  "filter",
				Value: "calc_name = 'weekday_8pm_10am_and_weekend'",
			},
		},
		Action: func(context *cli.Context) error {
			tr := repository.GeoTweetRepo{DB: a.db}
			lr := repository.LocationRepo{DB: a.db}
			shapeDir := context.Path("shapeDir")
			outputDir := context.Path("outputDir")
			region := context.String("region")
			filter := context.String("filter")
			users, err := lr.List(filter)
			if err != nil {
				return err
			}
			bds, err := bounds.New(shapeDir)
			if err != nil {
				return err
			}
			var usersInCountry []string
			for _, u := range users {
				if bds.Contains(region, u.Latitude, u.Longitude) {
					usersInCountry = append(usersInCountry, fmt.Sprintf("%d", u.UserID))
				}
			}
			fmt.Println(fmt.Sprintf("Detected %d users in %s", len(usersInCountry), region))
			userIds := strings.Join(usersInCountry, ",")
			tweets, err := tr.List("user_id IN (" + userIds + ")" )
			if err != nil {
				return err
			}
			outFile := outputDir + region + ".csv"
			fmt.Println(fmt.Sprintf("Storing %d tweets in %s", len(tweets), outFile))
			file, err := os.Create(outputDir + region + ".csv")
			if err != nil {
				return err
			}
			writer := csv.NewWriter(file)
			err = writer.Write([]string{"userid", "tweetid", "createdat", "latitude", "longitude", "month", "weekday", "hourofday", "timezone"})
			if err != nil {
				return err
			}
			for _, t := range tweets {
				loc, err := time.LoadLocation(t.TimeZone)
				if err != nil {
					return err
				}
				ti := t.CreatedAt.In(loc)
				err = writer.Write([]string{
					fmt.Sprintf("%d", t.UserID),
					fmt.Sprintf("%d", t.TweetID),
					ti.Format(time.RFC3339),
					fmt.Sprintf("%f", t.Latitude),
					fmt.Sprintf("%f", t.Longitude),
					fmt.Sprintf("%d", t.Month),
					fmt.Sprintf("%d", t.Weekday),
					fmt.Sprintf("%d", t.HourOfDay),
					t.TimeZone,
				})
				if err != nil {
					return err
				}
			}
			return nil
		},
	}
}
