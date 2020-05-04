package ingest

import (
	"archive/zip"
	"io/ioutil"
	"path"
)

type Source interface {
	Name() string
	ReadAll() ([]byte, error)
}

type FileSource struct {
	absolutePath string
}

func (f *FileSource) Name() string {
	return path.Base(f.absolutePath)
}

func (f *FileSource) ReadAll() ([]byte, error) {
	return ioutil.ReadFile(f.absolutePath)
}

type ZipSource struct {
	f *zip.File
}

func (z *ZipSource) Name() string {
	return path.Base(z.f.Name)
}

func (z *ZipSource) ReadAll() ([]byte, error) {
	reader, err := z.f.Open()
	if err != nil {
		return nil, err
	}
	defer reader.Close()
	return ioutil.ReadAll(reader)
}
