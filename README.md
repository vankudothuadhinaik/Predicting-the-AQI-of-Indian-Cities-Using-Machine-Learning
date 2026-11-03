# Indian City AQI Prediction

[![Artifact validation](https://github.com/vankudothuadhinaik/Predicting-the-AQI-of-Indian-Cities-Using-Machine-Learning/actions/workflows/validate-artifacts.yml/badge.svg)](https://github.com/vankudothuadhinaik/Predicting-the-AQI-of-Indian-Cities-Using-Machine-Learning/actions/workflows/validate-artifacts.yml)

A time-series forecasting and evaluation project exploring air-quality trends across Indian city/station series. The repository combines exploratory notebooks with reproducible chronological baselines to establish a transparent reference for future model comparisons.

> **Research/demo only.** This repository is not a live AQI service. Predictions are not a substitute for official measurements, alerts, or public-health guidance.

## At a glance

| Area | Current state |
|---|---|
| Problem | Explore historical AQI forecasting across multiple city/station series |
| Data | Repository training CSV and sample-submission template |
| Methods explored | ARIMA, SARIMAX, Prophet |
| Reproducible baselines | Previous-observation persistence and training-partition mean |
| Evaluation | Chronological, per-series holdout; aggregate and per-series metrics |
| Automation | GitHub Actions runs tests, evaluates baselines, validates notebooks/data, and publishes JSON artifacts |
| Deployment | No production service is provided |

## Results: reproducible persistence baseline

The standard-library evaluator parses each `ID_Date` series, sorts observations chronologically, and predicts each held-out AQI value using the immediately preceding observed value from the same series.

| Metric | Current baseline result |
|---|---:|
| Held-out rows | 5,088 |
| Series | 40 |
| Test date range | 2022-06-16 to 2022-12-03 |
| MAE | 28.54 |
| RMSE | 43.42 |

The evaluator also writes per-series held-out row counts, MAE, RMSE, and test date coverage to `baseline_metrics.json`. These results are a **persistence baseline**, not a model leaderboard or evidence of production forecasting quality.

## Baseline comparison

`compare_baselines.py` evaluates two simple methods on the same chronological holdout:

- **Previous observation:** predicts the next value using the immediately preceding observation in that series.
- **Training mean:** predicts each held-out value using the mean AQI from that series' training partition only.

It reports MAE and RMSE for both methods, the winning baseline by each metric, and the shared evaluation coverage in `baseline_comparison.json`. The held-out targets are not used to fit either baseline.

## Historical notebook metrics (not independently validated)

| Model | Historical MAE noted in the project |
|---|---:|
| Prophet | 528.99 |
| SARIMAX | 36.89 |
| ARIMA with Box–Cox transformation | 32 |

The older values are retained as historical notes only. Their original evaluation protocol does not fully specify the split, target scale, forecast horizon, or leakage checks. Do not compare them directly with the baselines above until all models are rerun on the same chronological holdout and target scale.

## Repository guide

| Path | Purpose |
|---|---|
| `dataset/train.csv` | Training data used by the baseline evaluators |
| `dataset/sample_submission.csv` | Submission-format example |
| `Notebooks/Data Analysis-EDA.ipynb` | Exploratory data analysis |
| `Notebooks/ARIMA .ipynb` | ARIMA-family forecasting experiments |
| `H2o_models/` | Supporting model artifacts |
| `output_file/` | Existing output artifacts |
| `evaluate_baseline.py` | Per-series chronological persistence evaluator |
| `compare_baselines.py` | Same-holdout comparison of persistence and training-mean baselines |
| `test_evaluate_baseline.py` | Evaluator unit tests |
| `test_compare_baselines.py` | Baseline-comparison unit tests |
| `.github/workflows/validate-artifacts.yml` | CI for tests, evaluation, notebooks, data, and result artifacts |

## Tools and technologies

| Area | Tools |
|---|---|
| Language | Python |
| Analysis | Jupyter Notebook, pandas, NumPy, Matplotlib (notebook dependencies) |
| Forecasting experiments | ARIMA, SARIMAX, Prophet |
| Reproducible baselines | Python standard library |
| Evaluation | MAE, RMSE, chronological per-series holdout |
| Testing and automation | Python `unittest`, GitHub Actions |
| Artifacts | JSON metrics and workflow artifacts |

The baseline evaluator and its tests intentionally use only the Python standard library. Notebook experiments may require additional packages; install the dependencies imported by the notebook you plan to run rather than assuming one environment covers every historical experiment.

## Quick start

**Requirements:** Python 3.10 or newer. The baseline evaluators and tests use only the Python standard library.

From the repository root:

```bash
python -m unittest -v test_evaluate_baseline.py test_compare_baselines.py
python evaluate_baseline.py --data dataset/train.csv --output baseline_metrics.json
python compare_baselines.py --data dataset/train.csv --output baseline_comparison.json
```

The JSON files contain aggregate metrics and evaluation coverage; the persistence evaluator additionally includes per-series metrics. GitHub Actions uploads both files as a commit-specific artifact retained for 30 days. See the [CI run history](https://github.com/vankudothuadhinaik/Predicting-the-AQI-of-Indian-Cities-Using-Machine-Learning/actions) to inspect a run and download its results.

To explore the notebooks, open them in Jupyter Notebook or JupyterLab and install the packages imported by the notebook you intend to run.

## Evaluation protocol

The current baseline evaluation:

1. Parses the stable series identifier and ISO date from `ID_Date`.
2. Sorts observations chronologically within each series.
3. Holds out the latest 20% of rows in each series by default (configurable from 5% to 50%).
4. Evaluates each series independently; observations from another series are never used as the previous value.
5. Reports aggregate MAE/RMSE and date coverage; the persistence evaluator also reports per-series MAE/RMSE, row counts, and date coverage.

The comparison script uses the same split for persistence and training-mean baselines. The training mean is calculated only from each series' training partition.

Before treating any model comparison as valid, use the same time-based split, target units, forecast horizon, and metric definitions across all models. Fit preprocessing on training data only, check missing values and duplicate timestamps, and verify that no future information enters features or transformations.

## Models explored

- **ARIMA** — univariate autoregressive integrated moving-average forecasting.
- **SARIMAX** — seasonal and/or exogenous-variable time-series modeling.
- **Prophet** — decomposable trend and seasonality modeling.

The notebooks are exploratory artifacts; they are not yet a single, fully reproducible benchmark pipeline.

## Roadmap

- [ ] Document the dataset source, license, target units, and series semantics.
- [ ] Pin notebook dependencies and add a repeatable training/evaluation entry point.
- [ ] Re-run ARIMA, SARIMAX, and Prophet on the same chronological holdout.
- [ ] Add a clear multi-step forecast horizon and compare it separately from one-step-ahead baselines.
- [ ] Review all feature engineering and transformations for temporal leakage.
- [ ] Record environment and configuration alongside each result.

## Limitations

- Historical model metrics have not been independently reproduced.
- Dataset provenance and licensing need to be documented clearly.
- The baselines are reference points, not complete forecasting solutions.
- The current one-step-ahead persistence evaluation uses the previous observed value for each held-out point; it should not be interpreted as a fixed-origin multi-step forecast.
- No live data ingestion, deployment, monitoring, or public-health alerting is included.

## Contributing

Keep evaluation changes reproducible: add or update tests, preserve chronological separation, avoid leakage, and document any change to the holdout protocol before comparing metrics.
