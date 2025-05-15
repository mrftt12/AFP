# /home/ubuntu/load_forecasting_agents/agents/model_deployment_agent.py
import mlflow
import pandas as pd
import logging
import os
from flask import Flask, request, jsonify
import threading
import time
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
class ModelDeploymentAgent:
    def __init__(self, registered_model_name: str, stage: str = "None",
                 mlflow_tracking_uri: str = "file:/home/ubuntu/load_forecasting_agents/mlruns"):
        """
        Initializes the Model Deployment Agent.

        Args:
            registered_model_name: Name of the model in the MLflow Model Registry.
            stage: Stage of the model to load (e.g., "Staging", "Production", "None" for latest).
            mlflow_tracking_uri: URI for MLflow tracking server.
        """
        self.registered_model_name = registered_model_name
        self.stage = stage
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        self.model = None
        self.model_version = None
        self.model_type = None # To store the type (e.g., prophet, lightgbm) for prediction logic
        self.features = None # Store features needed for prediction (for tree models)
        self._load_model()

    def _get_model_uri(self):
        """Gets the URI for the specified model name and stage."""
        try:
            client = mlflow.tracking.MlflowClient()
            if self.stage and self.stage != "None":
                latest_versions = client.get_latest_versions(self.registered_model_name, stages=[self.stage])
                if not latest_versions:
                    logging.warning(f"No model version found for name 	{self.registered_model_name}	 and stage 	{self.stage}	. Trying latest overall.")
                    # Fallback to latest version if stage yields no results
                    latest_versions = client.get_latest_versions(self.registered_model_name)
            else:
                latest_versions = client.get_latest_versions(self.registered_model_name)

            if not latest_versions:
                logging.error(f"No versions found for model 	{self.registered_model_name}	.")
                return None, None

            model_version = latest_versions[0] # Get the latest version object
            logging.info(f"Found model version: {model_version.version}, stage: {model_version.current_stage}, run_id: {model_version.run_id}")
            return model_version.source, model_version # Return URI and version object
        except Exception as e:
            logging.error(f"Error retrieving model URI for 	{self.registered_model_name}	 stage 	{self.stage}	: {e}")
            return None, None

    def _load_model(self):
        """Loads the model from the MLflow Model Registry."""
        model_uri, model_version_obj = self._get_model_uri()
        if not model_uri:
            logging.error("Failed to get model URI. Model not loaded.")
            return

        self.model_version = model_version_obj
        logging.info(f"Loading model from URI: {model_uri}")
        try:
            # Determine model type based on run tags or conventions if possible
            client = mlflow.tracking.MlflowClient()
            run_info = client.get_run(self.model_version.run_id)
            self.model_type = run_info.data.tags.get("mlflow.log-model.history")
            if self.model_type: # Often a JSON string list
                 import json
                 try:
                     # Extract the flavor name (e.g., mlflow.prophet, mlflow.lightgbm)
                     flavors = json.loads(self.model_type)
                     # Prioritize specific flavors over generic python_function
                     if any("mlflow.lightgbm" in f["flavor"] for f in flavors):
                         self.model_type = "lightgbm"
                     elif any("mlflow.prophet" in f["flavor"] for f in flavors):
                         self.model_type = "prophet"
                     elif any("mlflow.statsmodels" in f["flavor"] for f in flavors):
                         self.model_type = "statsmodels"
                     # Add other types as needed (e.g., autots, lstm)
                     else:
                         self.model_type = "python_function" # Default fallback
                 except json.JSONDecodeError:
                     logging.warning(f"Could not parse model type tag: {self.model_type}. Defaulting to python_function.")
                     self.model_type = "python_function"
            else:
                 # Fallback: Try inferring from artifact path if tag is missing
                 if "lightgbm" in model_uri:
                     self.model_type = "lightgbm"
                 elif "prophet" in model_uri:
                     self.model_type = "prophet"
                 elif "arima" in model_uri or "statsmodels" in model_uri:
                     self.model_type = "statsmodels"
                 else:
                     logging.warning("Could not determine specific model type. Loading as python_function.")
                     self.model_type = "python_function"
            
            logging.info(f"Identified model type as: {self.model_type}")

            # Load model based on inferred type
            if self.model_type == "lightgbm":
                self.model = mlflow.lightgbm.load_model(model_uri)
                # Get features if available in signature
                try:
                    model_info = mlflow.models.get_model_info(model_uri)
                    if model_info.signature and model_info.signature.inputs:
                        self.features = [col.name for col in model_info.signature.inputs.to_list()]
                        logging.info(f"Loaded features for LightGBM model: {self.features}")
                except Exception as sig_e:
                    logging.warning(f"Could not retrieve features from model signature: {sig_e}")
            elif self.model_type == "prophet":
                self.model = mlflow.prophet.load_model(model_uri)
            elif self.model_type == "statsmodels":
                self.model = mlflow.statsmodels.load_model(model_uri)
            else: # Default to pyfunc
                self.model = mlflow.pyfunc.load_model(model_uri)

            logging.info(f"Model 	{self.registered_model_name}	 version 	{self.model_version.version}	 loaded successfully as type 	{self.model_type}	.")

        except Exception as e:
            logging.error(f"Error loading model from {model_uri}: {e}", exc_info=True)
            self.model = None
            self.model_version = None
            self.model_type = None

    def predict(self, input_data):
        """
        Generates predictions using the loaded model.
        Input format depends on the model type.
        """
        if self.model is None:
            logging.error("Model is not loaded. Cannot predict.")
            return None

        logging.info(f"Generating prediction using {self.model_type} model...")
        try:
            if self.model_type == "prophet":
                # Prophet expects a DataFrame with a \"ds\" column
                if not isinstance(input_data, pd.DataFrame) or "ds" not in input_data.columns:
                    logging.error("Prophet model requires a pandas DataFrame with a \"ds\" column.")
                    return None
                forecast = self.model.predict(input_data)
                # Return relevant columns (e.g., yhat, ds)
                return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            
            elif self.model_type == "lightgbm":
                # LightGBM expects a DataFrame with feature columns
                if not isinstance(input_data, pd.DataFrame):
                     logging.error("LightGBM model requires a pandas DataFrame input.")
                     return None
                # Ensure all required features are present
                if self.features:
                    missing_features = [f for f in self.features if f not in input_data.columns]
                    if missing_features:
                        logging.error(f"Missing required features for LightGBM prediction: {missing_features}")
                        return None
                    input_data = input_data[self.features] # Ensure correct column order
                else:
                    logging.warning("Feature list not available for LightGBM, using all columns in input_data.")
                
                predictions = self.model.predict(input_data)
                # Return as DataFrame for consistency
                return pd.DataFrame({"prediction": predictions}, index=input_data.index)

            elif self.model_type == "statsmodels":
                # Statsmodels (like ARIMA) often predicts steps ahead
                # Input might be number of steps or future exogenous variables
                if isinstance(input_data, int): # Assume input is number of steps
                    steps = input_data
                    predictions = self.model.forecast(steps=steps)
                    return predictions # Returns Series or array
                else:
                    # Handle prediction with exogenous variables if applicable
                    # predictions = self.model.predict(start=..., end=..., exog=input_data)
                    logging.error("Prediction logic for this Statsmodels type with given input not implemented.")
                    return None
            
            else: # Default to pyfunc
                # Pyfunc expects pandas DataFrame usually
                if not isinstance(input_data, pd.DataFrame):
                     logging.warning("Input is not a DataFrame. Trying to convert.")
                     try:
                         input_data = pd.DataFrame(input_data)
                     except Exception as convert_e:
                         logging.error(f"Could not convert input to DataFrame for pyfunc model: {convert_e}")
                         return None
                predictions = self.model.predict(input_data)
                return predictions # Output format depends on how model was saved

        except Exception as e:
            logging.error(f"Error during prediction: {e}", exc_info=True)
            return None

# --- Flask App for Local Deployment ---
# Global variables to hold the agent and app instance
deployment_agent = None
flask_app = Flask(__name__)
server_thread = None

@flask_app.route("/predict", methods=["POST"])
def handle_predict():
    if deployment_agent is None or deployment_agent.model is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400

        # --- Input Data Handling (Needs to be adapted based on expected format) ---
        # Example: Assuming input is JSON that can be converted to DataFrame
        # For Prophet: Expects { "ds": ["2023-01-01 00:00", ...] }
        # For LightGBM: Expects { "feature1": [...], "feature2": [...] }
        # For ARIMA (steps): Expects { "steps": 10 }
        
        input_df = None
        steps = None
        
        if deployment_agent.model_type == "prophet":
            if "ds" in data:
                input_df = pd.DataFrame(data)
                input_df["ds"] = pd.to_datetime(input_df["ds"])
            else:
                 return jsonify({"error": "Missing \"ds\" key for Prophet model"}), 400
        elif deployment_agent.model_type == "statsmodels" and "steps" in data:
             steps = data["steps"]
             if not isinstance(steps, int) or steps <= 0:
                 return jsonify({"error": "Invalid \"steps\" value for ARIMA model"}), 400
        else: # Assume tabular data for LightGBM or pyfunc
            try:
                input_df = pd.DataFrame(data)
                # Attempt to parse index if it looks like datetime
                if "index" in input_df.columns:
                     try:
                         input_df["index"] = pd.to_datetime(input_df["index"])
                         input_df = input_df.set_index("index")
                     except Exception:
                         logging.warning("Could not parse \"index\" column as datetime.")
            except Exception as df_e:
                 return jsonify({"error": f"Could not parse input JSON to DataFrame: {df_e}"}), 400
        # --- End Input Data Handling ---

        prediction_input = input_df if input_df is not None else steps
        if prediction_input is None:
             return jsonify({"error": "Failed to prepare input data for prediction"}), 400

        predictions = deployment_agent.predict(prediction_input)

        if predictions is None:
            return jsonify({"error": "Prediction failed"}), 500

        # Convert predictions to JSON serializable format
        if isinstance(predictions, pd.DataFrame):
            result = predictions.to_json(orient="split", date_format="iso")
        elif isinstance(predictions, pd.Series):
            result = predictions.to_json(orient="split", date_format="iso")
        elif isinstance(predictions, np.ndarray):
            result = pd.Series(predictions).to_json(orient="split", date_format="iso") # Convert numpy array
        else:
            result = str(predictions) # Fallback

        return jsonify({"prediction": result}), 200

    except Exception as e:
        logging.error(f"Error in /predict endpoint: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {e}"}), 500

@flask_app.route("/info", methods=["GET"])
def handle_info():
    if deployment_agent is None or deployment_agent.model_version is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    info = {
        "registered_model_name": deployment_agent.registered_model_name,
        "model_version": deployment_agent.model_version.version,
        "model_stage": deployment_agent.model_version.current_stage,
        "model_type": deployment_agent.model_type,
        "model_uri": deployment_agent.model_version.source,
        "run_id": deployment_agent.model_version.run_id
    }
    return jsonify(info), 200

def run_server(agent, host="0.0.0.0", port=5001):
    global deployment_agent
    deployment_agent = agent
    logging.info(f"Starting Flask server on {host}:{port}")
    # Run Flask in a separate thread
    global server_thread
    server_thread = threading.Thread(target=lambda: flask_app.run(host=host, port=port, use_reloader=False), daemon=True)
    server_thread.start()
    logging.info("Flask server started in background thread.")

# Example Usage
if __name__ == "__main__":
    # Needs a model registered in MLflow first (e.g., "DummyLoadForecaster" from modeling_agent example)
    registered_name = "DummyLoadForecaster"
    agent = ModelDeploymentAgent(registered_model_name=registered_name, stage="None")

    if agent.model:
        print(f"Model {registered_name} loaded successfully.")
        
        # Start the Flask server to serve predictions
        run_server(agent, port=5001)
        print(f"Prediction server running in background. Access endpoints like http://127.0.0.1:5001/info")
        
        # Keep the main thread alive to let the server run (e.g., for testing)
        try:
            while True:
                time.sleep(60) # Keep alive
        except KeyboardInterrupt:
            print("\nShutting down server...")
            # Note: Flask server in daemon thread might not shut down gracefully here
            # Proper shutdown requires more complex handling (e.g., using Werkzeug's shutdown)
    else:
        print(f"Failed to load model {registered_name}.")

