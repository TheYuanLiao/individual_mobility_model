# Synthetic Travel Demand from Sparse Individual Traces
Yuan Liao, Kristoffer Ek, Eric Wennerberg, Sonia Yeh, and Jorge Gil

## Bootstrap environment
Make sure you have Conda installed
```bash
sh ./src/py/conda-install.sh
```
This will install all required dependencies to a miniconda workspace.

## Pre-processing
This is done in the notebook `src/py/1-filter-tweets.ipynb`.

## Model
The code for individual mobility model can be found in `src/py/models.py`.
See grid search for how it's configured.

### Grid search
Due to the differences between Sweden and Netherlands/Sao Paulo in terms of structure there are two gridsearch scripts.
`src/py/gridsearch.py` performs grid search in National/East/West area in Sweden.
`src/py/generic-gridsearch.py` performs grid search in Netherlands/Sao Paulo.
