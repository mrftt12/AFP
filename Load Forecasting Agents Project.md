# Load Forecasting Agents Project

## Overview

This project implements an end-to-end load forecasting system using multiple AI agents coordinated to perform tasks ranging from data ingestion and processing to model training, deployment, and monitoring, following MLOps principles.

## Project Structure

```
/home/ubuntu/load_forecasting_agents/
├── agents/                 # Python code for each specialized agent
│   ├── __init__.py
│   ├── coordinating_agent.py   # (Conceptual - logic embedded in run_pipeline.py for now)
│   ├── data_processing_agent.py
│   ├── eda_agent.py            # (Placeholder)
│   ├── forecasting_agent.py    # (Placeholder - prediction logic in deployment_agent)
│   ├── model_deployment_agent.py # Includes Flask API server
│   ├── model_verification_agent.py # (Placeholder - logic in modeling_agent)
│   ├── modeling_agent.py         # Includes training, tuning, evaluation, registration
│   └── monitoring_agent.py       # Includes health, drift, performance checks & alerting
├── data/
│   ├── raw/                # Raw data (e.g., uploaded CSVs)
│   └── processed/          # Processed data ready for modeling
├── mlruns/                 # MLflow tracking data and artifacts (generated)
├── notebooks/              # Jupyter notebooks for exploration (optional)
├── scripts/                # Utility scripts (none currently)
├── tests/                  # Unit and integration tests (placeholders)
│   └── __init__.py
├── architecture_design.md  # System architecture details
├── cicd_pipeline.md        # Conceptual CI/CD pipeline description
├── config.yaml             # Configuration file (placeholder)
├── requirements.txt        # Python dependencies
├── run_pipeline.py         # Script to run end-to-end validation pipeline
├── todo.md                 # Project task checklist
└── README.md               # This file
```

## Architecture

The system uses a modular, agent-based architecture. Please refer to `architecture_design.md` for a detailed diagram and description of agent roles and interactions.

## Key Components & Agents

*   **Data Processing Agent (`data_processing_agent.py`):** Handles loading data from CSV (local/URL), cleaning (duplicates, NaNs), type conversion, and basic time-based feature engineering.
*   **Modeling Agent (`modeling_agent.py`):** Orchestrates model training. Splits data, trains multiple models (Prophet, LightGBM with Optuna tuning, ARIMA, AutoTS), evaluates them using MAPE/MAE/R2, logs experiments to MLflow, and registers the best-performing model in the MLflow Model Registry.
*   **Model Deployment Agent (`model_deployment_agent.py`):** Loads a registered model from MLflow (specified by name/stage) and serves predictions via a Flask API endpoint (`/predict`). Also provides an `/info` endpoint.
*   **Monitoring Agent (`monitoring_agent.py`):** Performs checks for system health (API endpoint status), data drift (using KS test on specified columns), and model performance degradation (comparing recent MAPE against a threshold). Includes placeholder alerting.
*   **End-to-End Pipeline (`run_pipeline.py`):** Orchestrates the agents (Data Processing, Modeling) for a validation run. It assumes the Deployment Agent server is running separately and interacts with it for prediction testing. It also invokes the Monitoring Agent for checks.
*   **MLflow:** Used for experiment tracking, artifact storage (models, summaries), and model registry.
*   **Flask:** Used within the Model Deployment Agent to create a simple REST API for serving predictions.

## Setup and Installation

1.  **Prerequisites:** Python 3.10+, pip.
2.  **Clone/Extract:** Get the project code.
3.  **Navigate:** `cd /path/to/load_forecasting_agents`
4.  **Install Dependencies:** `pip3 install -r requirements.txt`

## Usage

### 1. Running the End-to-End Validation Pipeline

This script simulates the core workflow: data processing -> modeling -> registration -> monitoring -> prediction.

*   **Start Deployment Server:** Open a **separate terminal** and run:
    ```bash
    python3 /home/ubuntu/load_forecasting_agents/agents/model_deployment_agent.py
    ```
    This will start the Flask server (usually on port 5001) using the model named `ValidationLoadForecaster` (created by the validation script).

*   **Run Validation Script:** In the **original terminal**, run:
    ```bash
    python3 /home/ubuntu/load_forecasting_agents/run_pipeline.py
    ```
    Follow the prompt (press Enter after starting the server). The script will:
    *   Create/use dummy data in `data/raw/`.
    *   Process the data and save it to `data/processed/`.
    *   Train models, tune LightGBM, log to MLflow (in `mlruns/`), and register the best model as `ValidationLoadForecaster`.
    *   Perform monitoring checks against the running server.
    *   Send a sample prediction request to the server.
    *   Print a summary of the validation run and final model metrics.

*   **Stop Deployment Server:** After the validation script finishes, manually stop the deployment server in the separate terminal (usually with `Ctrl+C`).

### 2. Exploring MLflow Results

*   Navigate to the project directory: `cd /home/ubuntu/load_forecasting_agents`
*   Run the MLflow UI: `mlflow ui`
*   Open your browser to `http://127.0.0.1:5000` (or the address shown) to view experiments, runs, parameters, metrics, and registered models.

### 3. Making Predictions (Manual)

While the deployment server is running (see step 1 above), you can send POST requests to `http://127.0.0.1:5001/predict`. The required JSON payload depends on the deployed model type (check the `/info` endpoint or `run_pipeline.py` for examples):

*   **Prophet:** `{"ds": ["YYYY-MM-DDTHH:MM:SS", ...]}`
*   **LightGBM/PyFunc:** `[{"feature1": value1, "feature2": value2, ...}]` (List of feature dictionaries)
*   **ARIMA (Steps):** `{"steps": N}`

Example using `curl` for ARIMA (5 steps):
```bash
curl -X POST -H "Content-Type: application/json" -d '{"steps": 5}' http://127.0.0.1:5001/predict
```

## Validation Results (Example from last run)

*(This section would be populated by the results from `run_pipeline.py`)*

Based on the last validation run using dummy data:
*   **Overall Status:** [SUCCESS/FAILURE]
*   **Best Model Found:** [e.g., LightGBM_Tuned]
*   **Test Metrics:**
    *   MAPE: [Value]
    *   MAE: [Value]
    *   R2 Score: [Value]

## Future Enhancements

*   Implement EDA Agent.
*   Implement Forecasting Agent (separate from deployment).
*   Implement Model Verification Agent (separate from modeling).
*   Implement Coordinating Agent for more complex workflows.
*   Add more sophisticated feature engineering.
*   Implement LSTM model training.
*   Add robust backtesting framework.
*   Integrate actual alerting mechanisms (Slack, Email, etc.).
*   Fully implement CI/CD pipeline using tools like GitHub Actions or Jenkins.
*   Add data versioning with DVC.
*   Improve error handling and robustness.
*   Develop a proper user interface (e.g., using Streamlit or a web framework).
*   Containerize the application using Docker.

