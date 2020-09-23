package main

import (
	"fmt"

	"github.com/TheYuanLiao/individual-mobility-model/src/go/internal/locations"
	"github.com/TheYuanLiao/individual-mobility-model/src/go/internal/repository"
	"github.com/urfave/cli/v2"
)

func (a *mobility) homelocation() *cli.Command {
	return &cli.Command{
		Name: "homelocation",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:     "name",
				Required: true,
			},
			&cli.BoolFlag{
				Name: "create",
			},
			&cli.StringFlag{
				Name:  "filter",
				Value: "(hour_of_day < 10 or hour_of_day > 20) and weekday < 6 and weekday > 0",
			},
		},
		Action: func(context *cli.Context) error {
			tr := repository.GeoTweetRepo{DB: a.db}
			lcr := repository.LocationCalcRepo{DB: a.db}
			lr := repository.LocationRepo{DB: a.db}
			if context.Bool("create") {
				if err := lcr.CreateTable(); err != nil {
					return err
				}
				if err := lr.CreateTable(); err != nil {
					return err
				}
			}
			name := context.String("name")
			filter := context.String("filter")
			locationCalc := &repository.LocationCalc{
				Name:          name,
				MinPoints:     2,
				ClusterRadius: 0.1,
				TweetFilter:   filter,
			}
			tweets, err := tr.List(filter)
			if err != nil {
				return err
			}
			if err := lcr.InsertMany([]*repository.LocationCalc{locationCalc}); err != nil {
				return err
			}
			users := make(map[int][]*repository.GeoTweet)
			for _, t := range tweets {
				users[t.UserID] = append(users[t.UserID], t)
			}
			var locs []*repository.Location
			for uid, tws := range users {
				loc := locations.Visits(tws, locations.Options{
					ClusterRadius: locationCalc.ClusterRadius,
					MinPoints:     locationCalc.MinPoints,
				})
				if loc == nil {
					fmt.Printf("Did not find home location for user %d %d\n", uid, len(tws))
					continue
				}
				loc.CalcName = locationCalc.Name
				loc.Type = "home"
				loc.UserID = uid
				locs = append(locs, loc)
			}
			if err := lr.InsertMany(locs); err != nil {
				return err
			}
			return nil
		},
	}
}
