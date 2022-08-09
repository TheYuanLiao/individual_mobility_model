# A Mobility Model for Synthetic Travel Demand from Sparse Traces
Yuan Liao, Kristoffer Ek, Eric Wennerberg, Sonia Yeh, Jorge Gil

## 1. Model (Section II)
The code for the proposed individual mobility model can be found in `lib/models.py`.
See `lib/gs_model.py` for how it's configured.

There are other scripts under `lib/` defined to be called by `lib/models.py`, `lib/gs_model.py`,
and the below scripts and notebooks.

## 2. Data pre-processing (Appendix B)
In this part, the sparse mobility traces from the geolocations of Twitter data are extracted and preprocessed.

### 1) Extract sparse data from their raw databases
This is done in the script `src/py/sqlite3-converter.py`.

### 2) Preprocess the sparse geolocations from Twitter data
This is done in the script `src/py/tweets-filter.py`.

## 3. Model experiment (Section III)

### 1) Split the processed sparse traces into validation and calibration sets
This is done in the notebook `src/py/1-split-input-for-validation.ipynb`.

### 2) Bayesian optimisation against calibration data
This is done in the script `src/py/parasearch-bayesian.py`.

### 3) Model output against validation and calibration datasets
This is done in the script `src/py/parameters-validation.py`. The selection of parameter ![](https://latex.codecogs.com/svg.latex?D) 
is tested in the script `src/py/parameter-D-KL-relationship.py`.

### 4) Impact of trip distance and data length (Section IV.C)
This is done in the script `src/py/N-KL-relationship.py`.

### 5) A test of model parameter transferability (Section IV.D)
This is done in the script `src/py/parameters-transferability-test.py`.

### 6) Summarise the optimal parameters, parameter transferability, and model performance
This is done in the notebook `src/py/2-parasearch-summary.ipynb`.


## 4. Descriptive analysis and results illustration (Section IV)
Description of the applied datasets and regional properties is 
found in the notebook `src/py/3-descriptive-analysis.ipynb`. The data used for 
an illustration example of model input and output
can be found in the notebook `src/py/4-model-input-output-illustration.ipynb`.

The below shows a summary of figures produced by the scripts under `src/visualisation/`.

| Script                                     | Objective                                                                                                                                 | Output                             | No. in the manuscript |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|-----------------------|
| `fig3-regions.R`                           | Visualise the regions for the model experiment                                                                                            | `figures/gt-zones.png`             | 3                     |
| `fig4-para-search.R`                       | The results of parameters search                                                                                                          | `figures/para-search.png`          | 4                     |
| `fig5-input-output-chord.R`                | Individual mobility ODMs based on the benchmark model and the proposed model                                                              | `figures/chord_input_output.png`   | 5                     |
| `fig6-odm-calibration.R`                   | Comparison of trip frequency rate between the ground truth data and model output - calibration data                                       | `figures/od_pairs_calibration.png` | 6                     |
| `fig7-distance.R`                          | Comparison of trip distance distribution between the ground truth data and the model output                                               | `figures/distance.png`             | 7                     |
| `fig8-model-performance-by-distance.R`     | Impact of trip distance on model performance                                                                                              | `figures/model_perf_distance.png`  | 8                     |
| `fig9-model-performance-by-data-lengths.R` | Impact of data length on model performance                                                                                                | `figures/data_length_impact.png`   | 9                     |
| `fig10-transferability.R`                  | Relative performance of each region using the model parameters calibrated from the other regions                                          | `figures/transferability.png`      | 10                    |
| `figC1-parameters-M-D.R`                    | Value settings of the model parameters ![](https://latex.codecogs.com/svg.latex?M_{day}) and ![](https://latex.codecogs.com/svg.latex?D). | `figures/M_day_D.png`              | C.1                   |
| `figD1-odm-validation.R`                 | Comparison of trip frequency rate between the ground truth data and model output - validation data                                        | `figures/od_pairs_validation.png`  | D.1                   |
