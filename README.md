# Master thesis: Individual Mobility Model
Kristoffer Ek & Eric Wennerberg

## Bootstrap environment
Make sure you have Conda installed
```bash
sh ./src/py/conda-install.sh
```
This will install all required dependencies to a miniconda workspace.

## Converting from JSON dump to sqlite
This is done in Go `src/go`. Can "ingest" regular directories filled with JSON files and zipped directories with JSON files.
```bash
cd src/go

# Regular directories
go run ./cmd/mobility --ctx saopaulo ingest --create --directory /path/to/HDD/07_Timelines_Sao\ Paulo

# Zipped directory
go run ./cmd/mobility --ctx netherlands ingest --create --zip /path/to/HDD/02_Netherlands.zip
```

This will, after some time, create a .sqlite3 file in CWD filled with geotagged tweets.

## Pre-processing
This is done in the notebook `src/py/1-filter-tweets.ipynb`.

## Model
The code for individual mobility model can be found in `src/py/models.py`.
See grid search for how it's configured.

### Grid search
Due to the differences between Sweden and Netherlands/Sao Paulo in terms of structure there are two gridsearch scripts.
`src/py/gridsearch.py` performs grid search in National/East/West area in Sweden.
`src/py/generic-gridsearch.py` performs grid search in Netherlands/Sao Paulo.
