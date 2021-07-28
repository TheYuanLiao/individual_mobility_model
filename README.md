# A Mobility Model for Synthetic Travel Demand from Sparse Individual Traces
Yuan Liao, Kristoffer Ek, Eric Wennerberg, Sonia Yeh, Jorge Gil

## 1. Model (Section 2)
The code for the proposed individual mobility model can be found in `lib/models.py`.
See `lib/gs_model.py` for how it's configured.

There are other scripts under `lib/` defined to be called by `lib/models.py`, `lib/gs_model.py`,
and the below scripts and notebooks.

## 2. Data pre-processing (Section 3.1)
In this part, the sparse mobility traces from the geolocations of Twitter data are extracted and preprocessed.

### 1) Extract sparse data from their raw databases
This is done in the script `src/py/sqlite3-converter.py`.

### 2) Preprocess the sparse geolocations of Twitter data
This corresponds to Section 3.1. Sparse traces: geotagged tweets. 
This is done in the script `src/py/tweets-filter.py`.

## 3. Experiment: model validation (Section 3.2)

### 1) Split the processed Twitter data into validation and calibration sets
This is done in the notebook `src/py/1-split-input-for-validation.ipynb`.

### 2) Bayesian optimisation
This is done in the script `src/py/parasearch-bayesian.py`.

### 3) Model output on validation and calibration datasets
This is done in the script `src/py/parameters-validation.py`.

### 4) A test of model parameter transferability (Section 4.3)
This is done in the script `src/py/parameters-sensitivity-test.py`.

### 5) Summarise the optimal parameters and model performance
This is done in the notebook `src/py/2-parasearch-summary.ipynb`.

## 4. Application: characterising trip distance (Section 3.3)

### 1) Generate visits using the calibrated model
This is done in the script `src/py/multi-region-visits-generation.py`.

### 2) Create statistics and trips from the generated visits
This is done in the script `src/py/multi-region-visits-describe.py`.

### 3) Summarise the statistics of the generated visits of multiple regions
This is done in the script `src/py/3-multi-region-summary.ipynb`.

### 4) Preprocess the model-generated trips into domestic trips
This is done in the script `src/py/multi-region-visits-trips-filtering.py`.

### 5) Characterising trip distance
This is done in the notebook `src/py/4-characterising-trip-distance.ipynb` and the R script
`src/r/correlation-multi-region-agg.R`.

## 5. Value difference between Euclidean trip distance and travel distance (Appendix B.2)
This is to quantify to what extent we underestimate the travel distance
by using Haversine distance. This is done by comparing 
Haversine distance with the reported & the simulated travel distance.

### 1) Prepare survey data 
This is done in the notebook `src/py/7-distance-error-data-based.ipynb`.

### 2) Prepare simulation data
#### 2-1) Download drive road networks
This is done in the script `src/py/multi-region-drive-network-downloader.py`.

#### 2-2) Calculate network distances
This is done in the script `src/py/multi-region-distance-error-computation.py`.

#### 2-3) Summarise simulated network distances
This is done in the notebook `src/py/8-distance-error-simulation-based.ipynb`.

## 6. Descriptive analysis and results illustration
Description of the applied datasets and regional properties is 
found in the notebook `src/py/5-descriptive-analysis.ipynb`. The data used for 
an illustration example of model input and output
can be found in the notebook `src/py/6-model-input-output-illustration.ipynb`.

The below shows a summary of figures.

| Script                                    | Objective                                                                                                        | Output                                      | No. in the manuscript |
|-------------------------------------------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------|-----------------------|
| `src/r/plot-regions.R`                    | Visualise the regions for the experiment                                                                         | `figures/gt-zones.png`                      | 3                     |
| `src/r/plot-para-search.R`                | The results of parameters search                                                                                 | `figures/para-search.png`                   | 4                     |
| `src/r/plot-input-output-chord.R`         | Individual mobility ODMs based on the benchmark model and the proposed model                                     | `figures/chord_input_output.png`            | 5                     |
| `src/r/plot-odm-r1-calibration.R`         | Comparison of trip frequency rate between the ground truth data and model output - calibration data              | `figures/od_pairs_calibration.png`          | 6                     |
| `src/r/plot-odm-r1-validation.R`          | Comparison of trip frequency rate between the ground truth data and model output - validation data               | `figures/od_pairs_validation.png`           | B.1                   |
| `src/r/plot-distance.R`                   | Comparison of trip distance distribution between the ground truth data and the model output                      | `figures/distance.png`                      | 7                     |
| `src/r/plot-sensitivity.R`                | Performance gain of each region using the model parameters calibrated from the other regions                     | `figures/sensitivity.png`                   | 8                     |
| `src/r/plot-multi-region-pdf.R`           | Distance distributions of model-synthesised domestic trips (PDF)                                                 | `figures/trip_distance.png`                 | 9                     |
| `src/r/plot-empirical-M-distri.R`         | Empirical distribution of the number of visits per day derived from the Swedish National Travel Survey           | `figures/M_day_empirical.png`               | A.1                   |
| `src/r/plot-distance-error-data.R`        | Trip distance, Euclidean vs. reported travel distance (survey data)                                              | `figures/distance_error_data.png`           | B.2                   |
| `src/r/plot-distance-error-simulation.R`  | Distance ratio of selected urban areas (simulated)                                                               | `figures/distance_error_simulation.png`     | B.3                   |