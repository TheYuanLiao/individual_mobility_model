package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	_ "github.com/mattn/go-sqlite3"
	"github.com/urfave/cli/v2"
)

func main() {
	m := &mobility{}
	app := m.App()
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

type mobility struct {
	db *sql.DB
}

func (a *mobility) App() *cli.App {
	return &cli.App{
		Name:  "Mobility",
		Usage: ".",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "ctx",
				Usage: "sqlite ctx, will be created if not exists",
			},
			&cli.PathFlag{
				Name: "sqlite",
			},
		},
		Before: func(context *cli.Context) error {
			dataSource := ""
			if context.String("ctx") != "" {
				dataSource = fmt.Sprintf("./../../dbs/%s.sqlite3", context.String("ctx"))
			} else if context.Path("sqlite") != "" {
				dataSource = context.Path("sqlite")
			}
			db, err := sql.Open("sqlite3", fmt.Sprintf("%s?_journal_mode=MEMORY", dataSource))
			if err != nil {
				return err
			}
			a.db = db
			return nil
		},
		Commands: []*cli.Command{
			a.ingest(),
			a.geotag(),
			a.homelocation(),
		},
	}
}
