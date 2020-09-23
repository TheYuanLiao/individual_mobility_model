package main

import (
	"github.com/TheYuanLiao/individual-mobility-model/src/go/internal/ingest"
	"github.com/TheYuanLiao/individual-mobility-model/src/go/internal/repository"
	"github.com/urfave/cli/v2"
)

func (a *mobility) ingest() *cli.Command {
	return &cli.Command{
		Name: "ingest",
		Flags: []cli.Flag{
			&cli.PathFlag{
				Name: "directory",
			},
			&cli.PathFlag{
				Name: "zip",
			},
			&cli.BoolFlag{
				Name: "create",
			},
		},
		Action: func(context *cli.Context) error {
			directory := context.Path("directory")
			zip := context.Path("zip")
			ing := ingest.Ingester{
				TweetRepo:   &repository.GeoTweetRepo{DB: a.db},
				ProfileRepo: &repository.ProfileRepo{DB: a.db},
			}
			if context.Bool("create") {
				if err := ing.TweetRepo.CreateTable(); err != nil {
					return err
				}
				if err := ing.ProfileRepo.CreateTable(); err != nil {
					return err
				}
			}
			switch {
			case directory != "":
				return ing.Directory(directory)
			case zip != "":
				return ing.Zip(zip)
			}
			return nil
		},
	}
}
