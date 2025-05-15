# /home/ubuntu/load_forecasting_agents/run_pipeline.py
import pandas as pd
import numpy as np
import logging
import os
import time
import requests
import json

# Import Agents
from agents.data_processing_agent import DataProcessingAgent
from agents.modeling_agent import ModelingAgent
from agents.monitoring_agent import MonitoringAgent
# ModelDeploymentAgent is run separately to start the server

logging.basicConfig(level=logging.INFO, format=\"%(asctime)s - %(levelname)s - %(message)s\")

def run_end_to_end_validation():
    logging.info("--- Starting End-to-End Pipeline Validation ---")
    overall_success = True
    final_metrics = None

    # --- Configuration ---
    raw_data_source = "/home/ubuntu/load_forecasting_agents/data/raw/dummy_load_data_v2.csv" # Use the dummy data
    datetime_col = "timestamp"
    value_col = "load_kw"
    processed_data_output = "/home/ubuntu/load_forecasting_agents/data/processed/processed_dummy_validation.csv"
    registered_model_name = "ValidationLoadForecaster"
    prediction_service_url = "http://127.0.0.1:5001" # Default port used in deployment agent
    optuna_trials = 5 # Keep low for validation speed

    # --- 1. Data Processing ---
    logging.info("--- Stage 1: Data Processing ---")
    data_processor = DataProcessingAgent()
    processed_df = data_processor.process_data(
        source_path=raw_data_source, 
        datetime_col=datetime_col, 
        value_col=value_col,
        output_filename=os.path.basename(processed_data_output)
    )
    if processed_df is None:
        logging.error("Data processing failed. Aborting validation.")
        return False, None
    logging.info(f"Data processing successful. Processed data saved to {processed_data_output}")

    # --- 2. Modeling ---
    logging.info("--- Stage 2: Modeling & Registration ---")
    modeler = ModelingAgent(
        processed_data_path=processed_data_output,
        value_col=value_col,
        registered_model_name=registered_model_name
    )
    if modeler.df is None:
        logging.error("Modeling agent initialization failed. Aborting validation.")
        return False, None
    
    modeling_results, best_model_name, registered_version = modeler.run_modeling_pipeline(optuna_trials=optuna_trials)
    
    if not modeling_results or not best_model_name or not registered_version:
        logging.error("Modeling pipeline failed or did not register a model. Aborting validation.")
        overall_success = False
    else:
        logging.info(f"Modeling successful. Best model: {best_model_name}. Registered as: {registered_version.name} v{registered_version.version}")
        final_metrics = modeling_results.get(best_model_name)
        logging.info(f"Test Metrics for {best_model_name}: {final_metrics}")
        # Check if metrics meet basic criteria (e.g., R2 > 0)
        if final_metrics and final_metrics.get("R2_Score", -1) < 0:
             logging.warning(f"Best model {best_model_name} has poor R2 score: {final_metrics.get(\"R2_Score\")}")
             # Decide if this constitutes failure
             # overall_success = False 

    # --- 3. Deployment (Run as separate process) ---
    logging.info("--- Stage 3: Deployment (Assumed Running) ---")
    logging.info(f"Please ensure the ModelDeploymentAgent server is running for model \'{registered_model_name}\' on {prediction_service_url}")
    logging.info("Waiting 10 seconds for server to potentially start...")
    time.sleep(10) # Give time for manual start or background process

    # --- 4. Monitoring ---
    logging.info("--- Stage 4: Monitoring Checks ---")
    monitor = MonitoringAgent(
        training_data_path=processed_data_output, # Use the data just processed as reference
        value_col=value_col,
        prediction_service_url=prediction_service_url
    )
    if monitor.reference_data is None:
        logging.warning("Monitoring agent could not load reference data. Checks will be limited.")
    
    # Perform checks (simulate recent data using last few points of processed data)
    if processed_df is not None:
        recent_data = processed_df.tail(10).copy()
        monitor.run_monitoring_checks(current_data=recent_data)
    else:
        monitor.check_system_health() # At least check health if data failed
    logging.info("Monitoring checks executed.")

    # --- 5. Prediction Request ---
    logging.info("--- Stage 5: Prediction Request ---")
    prediction_successful = False
    try:
        info_response = requests.get(f"{prediction_service_url}/info", timeout=10)
        info_response.raise_for_status() 
        model_info = info_response.json()
        model_type = model_info.get("model_type")
        logging.info(f"Prediction service reports model type: {model_type}")

        prediction_payload = None
        if processed_df is not None:
            if model_type == "prophet":
                last_date = processed_df.index.max()
                freq = pd.infer_freq(processed_df.index) or \'H\' # Default to Hourly if inference fails
                future_dates = pd.date_range(start=last_date + pd.Timedelta(hours=1), periods=5, freq=freq)
                prediction_payload = {"ds": [d.isoformat() for d in future_dates]}
            elif model_type == "lightgbm":
                last_features = processed_df.drop(columns=[value_col]).tail(1).to_dict(orient="records")[0]
                prediction_payload = [last_features] 
            elif model_type == "statsmodels": 
                prediction_payload = {"steps": 5}
            else: 
                 last_features = processed_df.drop(columns=[value_col]).tail(1).to_dict(orient="records")[0]
                 prediction_payload = [last_features]
        else:
             logging.warning("Processed data not available, attempting simple prediction request (e.g., ARIMA steps).")
             if model_type == "statsmodels":
                 prediction_payload = {"steps": 5}

        if prediction_payload:
            logging.info(f"Sending prediction request with payload: {json.dumps(prediction_payload)}")
            predict_response = requests.post(f"{prediction_service_url}/predict", json=prediction_payload, timeout=20)
            predict_response.raise_for_status()
            prediction_result = predict_response.json()
            logging.info(f"Prediction successful. Result snippet: {str(prediction_result)[:200]}...")
            prediction_successful = True
        else:
            logging.warning("Could not determine appropriate payload for prediction request based on model type and data availability.")
            overall_success = False # Consider prediction failure as overall failure

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to connect to or get prediction from service at {prediction_service_url}: {e}")
        overall_success = False
    except Exception as e:
        logging.error(f"An error occurred during prediction request: {e}")
        overall_success = False

    logging.info("--- End-to-End Pipeline Validation Finished ---")
    return overall_success, final_metrics

if __name__ == "__main__":
    # Ensure the dummy data exists
    dummy_data_path = "/home/ubuntu/load_forecasting_agents/data/raw/dummy_load_data_v2.csv"
    if not os.path.exists(dummy_data_path):
         logging.info(f"Creating dummy data at {dummy_data_path} for validation...")
         # Make slightly more data for better validation
         num_records = 96 # 4 days of hourly data
         base_data = {
            \"load_kw\": [100 + 20 * np.sin(i / (24/ (2*np.pi))) + np.random.normal(0,5) for i in range(num_records)],
            \"other_col\": [\"val\"] * num_records
         }
         dummy_df = pd.DataFrame(base_data)
         dummy_df[\"timestamp\"] = pd.date_range(start=\"2023-01-01\", periods=len(dummy_df), freq=\"H\")
         # Introduce some NaNs and duplicates
         nan_indices = np.random.choice(dummy_df.index, size=5, replace=False)
         dummy_df.loc[nan_indices, \"load_kw\"] = np.nan
         dup_indices = np.random.choice(dummy_df.index[:num_records//2], size=2, replace=False)
         dummy_df = pd.concat([dummy_df, dummy_df.loc[dup_indices]])
         dummy_df = dummy_df.sort_values(by=\"timestamp\").reset_index(drop=True)

         os.makedirs(os.path.dirname(dummy_data_path), exist_ok=True)
         dummy_df.to_csv(dummy_data_path, index=False)
         logging.info("Dummy data created.")

    # Run the validation
    print("*********************************************************************")
    print("** IMPORTANT: Start the deployment server in a separate terminal: **")
    print(f"** python3 /home/ubuntu/load_forecasting_agents/agents/model_deployment_agent.py **")
    print("** (Using registered model name: ValidationLoadForecaster)         **")
    print("*********************************************************************")
    input("Press Enter to continue after starting the server...")

    success, metrics = run_end_to_end_validation()

    print("\n--- Validation Summary ---")
    if success:
        print("[SUCCESS] End-to-end validation script completed without critical errors.")
    else:
        print("[FAILURE] End-to-end validation script encountered errors.")
    
    if metrics:
        print("\nBest Model Metrics (on Test Set):")
        print(f"  MAPE: {metrics.get(\"MAPE\", \"N/A\"):.4f}")
        print(f"  MAE:  {metrics.get(\"MAE\", \"N/A\"):.4f}")
        print(f"  R2:   {metrics.get(\"R2_Score\", \"N/A\"):.4f}")
    else:
        print("\nMetrics for the best model are not available (modeling may have failed).")

    print("\n*********************************************************************")
    print("** IMPORTANT: Remember to stop the deployment server manually.    **")
    print("*********************************************************************")

