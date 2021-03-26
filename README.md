# Synthetic Travel Demand from Sparse Individual Traces
Yuan Liao, Kristoffer Ek, Eric Wennerberg, Sonia Yeh, Jorge Gil

## 1. Bootstrap environment
Make sure you have Conda installed
```bash
sh ./src/py/conda-install.sh
```
This will install all required dependencies to a miniconda workspace.

## 2. Data pre-processing
In this part, the sparse mobility traces from the geolocations of Twitter data are extracted and preprocessed.

### 1) Extract sparse data from their raw databases
This is done in the script `src/py/sqlite3-converter.py`.

### 2) Preprocess the sparse geolocations of Twitter data
This corresponds to Section 3.1. Sparse traces: geotagged tweets. 
This is done in the script `src/py/tweets-filter.py`.

## 3. Model
The code for the proposed individual mobility model can be found in `lib/models.py`.
See `lib/gs_model.py` for how it's configured.

There are other scripts under `lib/` defined to be called by `lib/models.py`, `lib/gs_model.py`,
and the below scripts and notebooks.

## 4. Search for model parameters
This corresponds to Section 3.2. Experiment: model validation.

### 1) Split the processed Twitter data into validation and calibration sets
This is done in the notebook `src/py/1-split-input-for-validation.ipynb`.

### 2) Bayesian optimisation
This is done in the script `src/py/parasearch-bayesian.py`.

### 3) Summarise the optimal parameters and model performance
This is done in the notebook `src/py/2-parasearch-summary.ipynb` containing the instruction of 
using the script `src/py/parameters-validation.py`.

## 5. Apply the calibrated model to multiple regions
This corresponds to Section 3.3. Application: characterising trip distance.

### 1) Generate visits using the calibrated model
This is done in the script `src/py/multi-region-visits-generation.py`.

### 2) Create statistics and trips from the generated visits
This is done in the script `src/py/multi-region-visits-describe.py`.

### 3) Preprocess the model-generated trips
This is done in the script `src/py/multi-region-visits-trips-filtering.py`.

### 4) Characterising trip distance
This is done in the notebook `src/py/4-characterising-trip-distance.ipynb` and the R script
`src/r/correlation-multi-region-agg.R`.

## 6. Descriptive analysis and illustration
Description of the applied datasets and regional properties is 
found in the notebook `src/py/5-descriptive-analysis.ipynb`. The data used for 
an illustration example of model input and output
can be found in the notebook `src/py/6-model-input-output-illustration.ipynb`.

The summary of figures is shown below.

| Script                                    | Objectives                                                                                                       | Output                                      | No. in the manuscript |
|-------------------------------------------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------|-----------------------|
| `src/r/plot-regions.R`                    | Visualise the regions for the experiment                                                                         | `figures/gt-zones.png`                      | 3                     |
| `src/r/plot-para-search.R`                | The results of parameters search                                                                                 | `figures/para-search.png`                   | 4                     |
| `src/r/plot-input-output-illustration.R`  | Visualise the sparse traces and model output                                                                     | `figures/input_output.png`                  | 5                     |
| `src/r/plot-odm.R`                        | Comparison of trip frequency rate in all origin-destination pairs between the ground truth data and model output | `figures/od_pairs.png`                      | 6                     |
| `src/r/plot-distance.R`                   | Comparison of trip distance distribution between the ground truth data and the model output                      | `figures/distance.png`                      | 7                     |
| `src/r/plot-multi-region-pdf.R`           | Distance distributions of model-synthesised domestic trips (PDF)                                                 | `figures/trip_distance.png`                 | 8                     |
| `src/r/plot-individuals.rmd`              | Individual example of model input and output                                                                     | -                                           | -                     |
| `src/r/plot-multi-region-cdf.R`           | CDF of the model-synthesised domestic trips' distance distribution                                               | `figures/trip_distance_CDF.png`             | -                     |
| `src/r/extra-plot-typical-pdf-distance.R` | Illustration of a few theoretical distributions of trip distance                                                 | `figures/trip_distance_pdf_theoretical.png` | -                     |
