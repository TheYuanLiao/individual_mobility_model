package main

import (
	"flag"
	"fmt"
	"go/format"
	"log"
	"os"
	"path/filepath"

	"github.com/ericwenn/mscthesis/src/go/internal/repogen"
)

func main() {
	p := flag.String("path", "", "Directory to generate repositories from")
	pkgName := flag.String("pkg", "", "The package to generate from")
	flag.Parse()

	tbls, err := repogen.Parse(*p, *pkgName)
	if err != nil {
		log.Fatal(err)
	}
	for _, t := range tbls {
		b := repogen.Generate(t)
		bf, err := format.Source(b.Bytes())
		if err != nil {
			fmt.Println(b.String())
			log.Fatal(err)
		}
		filename := fmt.Sprintf("%s_gen.go", t.FilePrefix)
		f, err := os.Create(filepath.Join(*p, filename))
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()
		if _, err := f.Write(bf); err != nil {
			log.Fatal(err)
		}
	}
}
