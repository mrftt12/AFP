# /home/ubuntu/load_forecasting_agents/agents/modeling_agent.py
import pandas as pd
import numpy as np
import logging
import mlflow
import os
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, r2_score, mean_absolute_error
from mlflow.models import infer_signature

# Import model libraries (ensure they are installed)
from prophet import Prophet
import lightgbm as lgb
from statsmodels.tsa.arima.model import ARIMA
# from tensorflow.keras.models import Sequential # Placeholder for LSTM
# from tensorflow.keras.layers import LSTM, Dense # Placeholder for LSTM
from autots import AutoTS
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# Suppress Optuna info logs to avoid clutter
optuna.logging.set_verbosity(optuna.logging.WARNING)

class ModelingAgent:
    def __init__(self, processed_data_path: str, value_col: str, datetime_col: str = None,
                 mlflow_tracking_uri: str = "file:/home/ubuntu/load_forecasting_agents/mlruns",
                 experiment_name: str = "Load Forecasting Experiment",
                 registered_model_name: str = "LoadForecastingModel"):
        """
        Initializes the Modeling Agent.

        Args:
            processed_data_path: Path to the processed data CSV file (output from DataProcessingAgent).
            value_col: Name of the target variable column (e.g., \'load_kw\').
            datetime_col: Name of the datetime index column (if not already the index).
            mlflow_tracking_uri: URI for MLflow tracking server.
            experiment_name: Name for the MLflow experiment.
            registered_model_name: Name to use for registering the best model in MLflow Model Registry.
        """
        self.processed_data_path = processed_data_path
        self.value_col = value_col
        self.datetime_col = datetime_col # Often the index after processing
        self.registered_model_name = registered_model_name
        self.df = self._load_processed_data()

        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        # Handle potential race condition or delay in experiment creation
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                logging.warning(f"Experiment \'{experiment_name}\' not found, creating it.")
                self.experiment_id = mlflow.create_experiment(experiment_name)
            else:
                self.experiment_id = experiment.experiment_id
        except Exception as e:
            logging.error(f"Error setting up MLflow experiment: {e}. Creating experiment.")
            # Fallback to creating if get fails unexpectedly
            try:
                 self.experiment_id = mlflow.create_experiment(experiment_name, artifact_location=mlflow_tracking_uri)
            except Exception as create_e:
                 logging.error(f"Failed to create MLflow experiment: {create_e}")
                 self.experiment_id = "0" # Default experiment ID

        logging.info(f"ModelingAgent initialized. MLflow tracking URI: {mlflow_tracking_uri}, Experiment: {experiment_name} (ID: {self.experiment_id}), Registered Model Name: {self.registered_model_name}")

    def _load_processed_data(self) -> pd.DataFrame | None:
        """Loads the processed data."""
        try:
            df = pd.read_csv(self.processed_data_path)
            # Attempt to set datetime index if not already set
            datetime_col_to_set = None
            if self.datetime_col and self.datetime_col in df.columns:
                datetime_col_to_set = self.datetime_col
            elif df.columns[0].startswith(\'Unnamed\'): # Try inferring index col if not specified and first col is unnamed
                 logging.warning("First column seems like an unnamed index, attempting to parse as datetime index.")
                 datetime_col_to_set = df.columns[0]

            if datetime_col_to_set:
                try:
                    df[datetime_col_to_set] = pd.to_datetime(df[datetime_col_to_set])
                    df = df.set_index(datetime_col_to_set)
                    if not self.datetime_col: # Update internal reference if it was inferred
                        self.datetime_col = datetime_col_to_set
                    logging.info(f"Successfully set column \'{datetime_col_to_set}\' as datetime index.")
                except Exception as e:
                    logging.error(f"Failed to parse column \'{datetime_col_to_set}\' as datetime index: {e}. Proceeding without explicit datetime index.")
            elif pd.api.types.is_datetime64_any_dtype(df.index):
                 logging.info("Data already has a datetime index.")
            else:
                 logging.warning("Could not identify or set a datetime index. Some models might fail.")

            if self.value_col not in df.columns:
                logging.error(f"Value column \'{self.value_col}\' not found in processed data.")
                return None

            df = df.sort_index() # Ensure data is sorted by time
            logging.info(f"Loaded processed data from {self.processed_data_path}. Shape: {df.shape}")
            return df
        except Exception as e:
            logging.error(f"Error loading processed data from {self.processed_data_path}: {e}")
            return None

    def _split_data(self, test_size=0.2, validation_size=0.1) -> tuple | None:
        """Splits data into training, validation (optional), and testing sets based on time."""
        if self.df is None:
            logging.error("DataFrame not loaded, cannot split data.")
            return None

        if not (0 < test_size < 1) or not (0 <= validation_size < 1) or (test_size + validation_size >= 1):
            logging.error("Invalid split sizes. Ensure test_size > 0, validation_size >= 0, and test_size + validation_size < 1.")
            return None

        total_len = len(self.df)
        test_split_point = int(total_len * (1 - test_size))
        
        if validation_size > 0:
            val_split_point = int(total_len * (1 - test_size - validation_size))
            train_df = self.df.iloc[:val_split_point]
            val_df = self.df.iloc[val_split_point:test_split_point]
            test_df = self.df.iloc[test_split_point:]
            logging.info(f"Split data: Train shape {train_df.shape}, Validation shape {val_df.shape}, Test shape {test_df.shape}")
            return train_df, val_df, test_df
        else:
            train_df = self.df.iloc[:test_split_point]
            test_df = self.df.iloc[test_split_point:]
            logging.info(f"Split data: Train shape {train_df.shape}, Test shape {test_df.shape}")
            return train_df, None, test_df # Return None for validation set

    def _evaluate_model(self, y_true, y_pred):
        """Calculates evaluation metrics."""
        # Ensure inputs are numpy arrays
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        
        # Avoid division by zero in MAPE if y_true contains zeros
        mask = y_true != 0
        if np.sum(mask) == 0: # All true values are zero
             mape = 0.0 if np.allclose(y_pred, 0) else float(\'inf\')
        else:
             # Ensure y_pred corresponding to non-zero y_true are finite
             y_pred_masked = y_pred[mask]
             y_true_masked = y_true[mask]
             if not np.all(np.isfinite(y_pred_masked)):
                 logging.warning("Non-finite values found in predictions for MAPE calculation. Setting MAPE to infinity.")
                 mape = float(\'inf\')
             else:
                 mape = mean_absolute_percentage_error(y_true_masked, y_pred_masked)
        
        # Check for non-finite values before calculating MAE and R2
        if not np.all(np.isfinite(y_pred)):
            logging.warning("Non-finite values found in predictions. MAE and R2 might be invalid.")
            mae = float(\'inf\')
            r2 = -float(\'inf\') # Or some other indicator of invalidity
        else:
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
        
        metrics = {
            "MAPE": mape,
            "MAE": mae,
            "R2_Score": r2
        }
        logging.info(f"Evaluation Metrics: {metrics}")
        return metrics

    def train_prophet(self, train_df, test_df):
        """Trains and evaluates a Prophet model."""
        logging.info("Training Prophet model...")
        with mlflow.start_run(experiment_id=self.experiment_id, run_name="Prophet") as run:
            run_id = run.info.run_id
            model_artifact_path = "prophet-model"
            try:
                idx_name = self.df.index.name if self.df.index.name else self.datetime_col
                if not idx_name:
                     logging.error("Prophet requires a named datetime index or column.")
                     return None, None, None
                prophet_train_df = train_df.reset_index()[[idx_name, self.value_col]]
                prophet_train_df.columns = [\"ds\", \"y\"]

                model = Prophet()
                model.fit(prophet_train_df)

                future = model.make_future_dataframe(periods=len(test_df), freq=pd.infer_freq(test_df.index))
                forecast = model.predict(future)

                y_pred = forecast[\"yhat\"][-len(test_df):].values
                y_true = test_df[self.value_col].values

                metrics = self._evaluate_model(y_true, y_pred)
                mlflow.log_params({"model_type": "Prophet"})
                mlflow.log_metrics(metrics)
                
                # Infer signature for Prophet (Input: ds, Output: yhat)
                signature_input = future[-len(test_df):].drop(columns=["yhat"] if "yhat" in future.columns else [])
                signature_output = forecast[["yhat"]][-len(test_df):]
                signature = infer_signature(signature_input, signature_output)

                try:
                    mlflow.prophet.log_model(model, artifact_path=model_artifact_path, signature=signature)
                except AttributeError:
                    logging.warning("mlflow.prophet.log_model not available. Model not logged.")
                    model_artifact_path = None # Indicate model wasn\'t logged
                
                logging.info("Prophet training complete.")
                return metrics, model, f"runs:/{run_id}/{model_artifact_path}" if model_artifact_path else None
            except Exception as e:
                logging.error(f"Error training Prophet: {e}", exc_info=True)
                mlflow.log_param("status", "failed")
                mlflow.log_param("error", str(e))
                return None, None, None

    def train_lightgbm_with_optuna(self, train_df, val_df, test_df, n_trials=20):
        """Trains and evaluates a LightGBM model with Optuna hyperparameter tuning."""
        logging.info(f"Training LightGBM model with Optuna ({n_trials} trials)...")

        features = [col for col in train_df.columns if col != self.value_col]
        target = self.value_col

        X_train, y_train = train_df[features], train_df[target]
        X_val, y_val = val_df[features], val_df[target]
        X_test, y_test = test_df[features], test_df[target]

        def objective(trial):
            # Define params inside objective to be logged per trial by Optuna callback if used
            params = {
                "objective": "regression_l1", "metric": "mae", "verbose": -1, "n_jobs": -1, "seed": 42, "boosting_type": "gbdt",
                "n_estimators": trial.suggest_int("n_estimators", 100, 2000),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 20, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "feature_fraction": trial.suggest_float("feature_fraction", 0.4, 1.0),
                "bagging_fraction": trial.suggest_float("bagging_fraction", 0.4, 1.0),
                "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
                "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
            }
            model = lgb.LGBMRegressor(**params)
            model.fit(X_train, y_train,
                      eval_set=[(X_val, y_val)],
                      eval_metric="mae",
                      callbacks=[lgb.early_stopping(100, verbose=False)])
            preds = model.predict(X_val)
            mae = mean_absolute_error(y_val, preds)
            return mae

        # Run Optuna study within a parent MLflow run
        with mlflow.start_run(experiment_id=self.experiment_id, run_name="LightGBM_Optuna_Tuning") as parent_run:
            parent_run_id = parent_run.info.run_id
            model_artifact_path = "lightgbm-tuned-model"
            try:
                study = optuna.create_study(direction="minimize")
                # Optional: Add MLflow callback to log each trial
                # mlflow_callback = optuna.integration.MLflowCallback(
                #     tracking_uri=mlflow.get_tracking_uri(),
                #     metric_name="validation_mae",
                #     nest_trials=True # Log trials as nested runs
                # )
                # study.optimize(objective, n_trials=n_trials, callbacks=[mlflow_callback])
                study.optimize(objective, n_trials=n_trials)

                best_params = study.best_params
                best_value = study.best_value
                logging.info(f"Optuna finished. Best MAE (validation): {best_value:.4f}")
                logging.info(f"Best params: {best_params}")

                mlflow.log_params(best_params)
                mlflow.log_metric("best_validation_mae", best_value)
                mlflow.log_param("n_trials", n_trials)
                mlflow.log_param("model_type", "LightGBM_Tuned")

                # Train final model with best params on combined train+val data
                logging.info("Training final LightGBM model with best parameters...")
                final_params = best_params.copy()
                final_params.update({"objective": "regression_l1", "metric": "mae", "verbose": -1, "n_jobs": -1, "seed": 42, "boosting_type": "gbdt"})
                
                X_train_val = pd.concat([X_train, X_val])
                y_train_val = pd.concat([y_train, y_val])

                final_model = lgb.LGBMRegressor(**final_params)
                final_model.fit(X_train_val, y_train_val)

                # Evaluate on test set
                y_pred_test = final_model.predict(X_test)
                test_metrics = self._evaluate_model(y_test, y_pred_test)
                mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})

                # Infer signature for LightGBM
                signature = infer_signature(X_test, y_pred_test)
                mlflow.lightgbm.log_model(final_model, artifact_path=model_artifact_path, signature=signature)
                
                logging.info("Tuned LightGBM training complete.")
                return test_metrics, final_model, f"runs:/{parent_run_id}/{model_artifact_path}"

            except Exception as e:
                logging.error(f"Error during LightGBM Optuna tuning: {e}", exc_info=True)
                mlflow.log_param("status", "failed")
                mlflow.log_param("error", str(e))
                return None, None, None

    def train_arima(self, train_df, test_df, order=(5,1,0)):
        """Trains and evaluates an ARIMA model."""
        logging.info(f"Training ARIMA model with order {order}...")
        with mlflow.start_run(experiment_id=self.experiment_id, 
(Content truncated due to size limit. Use line ranges to read in chunks)