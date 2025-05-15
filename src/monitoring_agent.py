# /home/ubuntu/load_forecasting_agents/agents/monitoring_agent.py
import pandas as pd
import numpy as np
import logging
from scipy.stats import ks_2samp
import requests
import time
import schedule # For scheduling checks
import threading

# Assuming metrics calculation is similar to ModelingAgent
from sklearn.metrics import mean_absolute_percentage_error, r2_score, mean_absolute_error

logging.basicConfig(level=logging.INFO, format=\"%(asctime)s - %(levelname)s - %(message)s\")

# --- Alerting Placeholder ---
# In a real system, this would integrate with PagerDuty, Slack, Email, etc.
def trigger_alert(severity: str, component: str, message: str):
    alert_message = f"ALERT [{severity.upper()}] - Component: {component} - Message: {message}"
    logging.critical(alert_message) # Use critical level for alerts to make them stand out
    # TODO: Add actual alerting integrations here (e.g., send to Slack webhook, email)
    print(f"*** {alert_message} ***") # Print prominently for simulation
# --- End Alerting Placeholder ---

class MonitoringAgent:
    def __init__(self, training_data_path: str, value_col: str, 
                 prediction_service_url: str = "http://127.0.0.1:5001",
                 drift_threshold: float = 0.05, # p-value threshold for KS test
                 mape_threshold: float = 0.15, # Example threshold for MAPE degradation
                 check_interval_minutes: int = 60):
        """
        Initializes the Monitoring Agent.

        Args:
            training_data_path: Path to the (processed) training data used for the deployed model.
            value_col: Name of the target variable column.
            prediction_service_url: URL of the deployed prediction service.
            drift_threshold: p-value threshold for the Kolmogorov-Smirnov test for data drift.
            mape_threshold: Threshold for acceptable Mean Absolute Percentage Error.
            check_interval_minutes: How often to run monitoring checks (in minutes).
        """
        self.training_data_path = training_data_path
        self.value_col = value_col
        self.prediction_service_url = prediction_service_url
        self.drift_threshold = drift_threshold
        self.mape_threshold = mape_threshold
        self.check_interval_minutes = check_interval_minutes
        self.reference_data = self._load_reference_data()
        self.stop_scheduler = threading.Event()
        self.scheduler_thread = None

        if self.reference_data is None:
            logging.error("Failed to load reference training data. Monitoring agent may not function correctly.")

        logging.info("MonitoringAgent initialized.")

    def _load_reference_data(self) -> pd.DataFrame | None:
        """Loads the reference training data."""
        try:
            df = pd.read_csv(self.training_data_path)
            logging.info(f"Loaded reference training data from {self.training_data_path}. Shape: {df.shape}")
            return df
        except Exception as e:
            logging.error(f"Error loading reference data from {self.training_data_path}: {e}")
            return None

    def check_data_drift(self, current_data: pd.DataFrame, column: str) -> bool:
        """
        Checks for data drift in a specific column using the KS test.
        Triggers an alert if drift is detected.
        """
        # ... (previous checks for data availability remain the same)
        if self.reference_data is None or column not in self.reference_data.columns:
            logging.error(f"Reference data or column \'{column}\' not available for drift check.")
            return False
        if current_data is None or column not in current_data.columns:
            logging.error(f"Current data or column \'{column}\' not available for drift check.")
            return False

        reference_col_data = self.reference_data[column].dropna()
        current_col_data = current_data[column].dropna()

        if len(reference_col_data) < 2 or len(current_col_data) < 2:
            logging.warning(f"Not enough data points in column \'{column}\' for KS test.")
            return False

        try:
            ks_statistic, p_value = ks_2samp(reference_col_data, current_col_data)
            logging.info(f"Data drift check for column \'{column}\': KS Statistic={ks_statistic:.4f}, p-value={p_value:.4f}")
            
            if p_value < self.drift_threshold:
                alert_msg = f"Data drift detected in column \'{column}\' (p-value: {p_value:.4f} < threshold: {self.drift_threshold})"
                trigger_alert(severity="warning", component="Data Drift", message=alert_msg)
                return True # Drift detected
            else:
                return False # No significant drift detected
        except Exception as e:
            logging.error(f"Error during KS test for column \'{column}\': {e}")
            return False

    def check_model_performance(self, recent_predictions: pd.Series, recent_actuals: pd.Series) -> bool:
        """
        Checks if the model performance on recent data meets the threshold.
        Triggers an alert if performance degradation is detected.
        """
        # ... (previous checks for data availability remain the same)
        if recent_predictions is None or recent_actuals is None or len(recent_predictions) != len(recent_actuals):
            logging.error("Invalid input for performance check.")
            return False
        if len(recent_predictions) == 0:
            logging.info("No recent data points for performance check.")
            return False

        try:
            mask = recent_actuals != 0
            if np.sum(mask) == 0:
                 mape = 0.0 if np.allclose(recent_predictions, 0) else float(\"inf\")
            else:
                 mape = mean_absolute_percentage_error(recent_actuals[mask], recent_predictions[mask])
            
            logging.info(f"Model performance check: Current MAPE = {mape:.4f}")

            if mape > self.mape_threshold:
                alert_msg = f"Model performance degradation detected! Current MAPE ({mape:.4f}) exceeds threshold ({self.mape_threshold})"
                trigger_alert(severity="warning", component="Model Performance", message=alert_msg)
                return True # Degradation detected
            else:
                return False # Performance is acceptable
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {e}")
            return False

    def check_system_health(self) -> bool:
        """
        Checks the health of the prediction service endpoint.
        Triggers an alert if the service is unhealthy.
        """
        try:
            response = requests.get(f"{self.prediction_service_url}/info", timeout=5)
            if response.status_code == 200:
                logging.info(f"System health check: Prediction service at {self.prediction_service_url} is UP.")
                return True
            else:
                alert_msg = f"System health check failed! Prediction service at {self.prediction_service_url} returned status code {response.status_code}."
                trigger_alert(severity="error", component="System Health", message=alert_msg)
                return False
        except requests.exceptions.RequestException as e:
            alert_msg = f"System health check failed! Could not connect to prediction service at {self.prediction_service_url}: {e}"
            trigger_alert(severity="error", component="System Health", message=alert_msg)
            return False

    def run_monitoring_checks(self, current_data: pd.DataFrame = None, recent_predictions: pd.Series = None, recent_actuals: pd.Series = None):
        """
        Runs all monitoring checks: system health, data drift, and model performance.
        """
        logging.info("Running periodic monitoring checks...")
        
        # 1. System Health
        is_healthy = self.check_system_health()
        
        # 2. Data Drift
        if current_data is not None and self.reference_data is not None:
            columns_to_check = [self.value_col] + [col for col in [\"hour\", \"dayofweek\"] if col in self.reference_data.columns and col in current_data.columns]
            drift_detected = False
            for col in columns_to_check:
                if self.check_data_drift(current_data, col):
                    drift_detected = True # Alert is triggered within check_data_drift
            if drift_detected:
                 logging.warning("Data drift detected in one or more columns. Model retraining might be needed.")
        else:
            logging.info("Skipping data drift check: Current data or reference data not available.")

        # 3. Model Performance
        if recent_predictions is not None and recent_actuals is not None:
            performance_degraded = self.check_model_performance(recent_predictions, recent_actuals) # Alert is triggered within check_model_performance
            if performance_degraded:
                logging.warning("Model performance degradation detected. Model retraining or investigation needed.")
        else:
            logging.info("Skipping model performance check: Recent predictions or actuals not available.")
            
        logging.info("Monitoring checks completed.")

    def start_scheduled_monitoring(self):
        """
        Starts the monitoring checks on a schedule in a background thread.
        """
        # ... (scheduler setup remains the same)
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logging.warning("Scheduler already running.")
            return

        logging.info(f"Starting scheduled monitoring every {self.check_interval_minutes} minutes.")
        # For demonstration, schedule the full check (requires data to be passed somehow)
        # In a real system, data fetching would be part of the scheduled job.
        # Here, we just schedule the health check for simplicity.
        schedule.every(self.check_interval_minutes).minutes.do(self.check_system_health)
        
        def run_scheduler():
            while not self.stop_scheduler.is_set():
                schedule.run_pending()
                time.sleep(1)
            logging.info("Monitoring scheduler stopped.")

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduled_monitoring(self):
        """
        Stops the background scheduler thread.
        """
        # ... (scheduler stopping remains the same)
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logging.info("Stopping scheduled monitoring...")
            self.stop_scheduler.set()
            self.scheduler_thread.join(timeout=5)
            if self.scheduler_thread.is_alive():
                 logging.warning("Scheduler thread did not stop gracefully.")
            self.scheduler_thread = None
            self.stop_scheduler.clear()
        else:
            logging.info("Scheduler not running.")

# Example Usage (Conceptual)
if __name__ == \"__main__\":
    train_data_file = \"/home/ubuntu/load_forecasting_agents/data/processed/processed_dummy_load_data_v2.csv\"
    service_url = "http://127.0.0.1:5001"

    if not os.path.exists(train_data_file):
        print(f"Error: Training data file not found at {train_data_file}")
    else:
        monitor_agent = MonitoringAgent(training_data_path=train_data_file, value_col=\"load_kw\", prediction_service_url=service_url, check_interval_minutes=1)
        
        if monitor_agent.reference_data is not None:
            print("Monitoring Agent initialized with alerting.")
            
            print("\n--- Running Manual Checks (Simulation) ---")
            dummy_current_data = monitor_agent.reference_data.tail(5).copy()
            # Simulate drift by adding noise
            dummy_current_data[monitor_agent.value_col] += np.random.normal(0, 50, size=len(dummy_current_data))
            # Simulate performance degradation
            dummy_preds = dummy_current_data[monitor_agent.value_col] * 1.5 # Significant error
            dummy_actuals = monitor_agent.reference_data.tail(5)[monitor_agent.value_col] # Use original values as actuals
            
            monitor_agent.run_monitoring_checks(current_data=dummy_current_data, 
                                                recent_predictions=dummy_preds, 
                                                recent_actuals=dummy_actuals)
            
            # Simulate system down
            print("\n--- Simulating System Down Check ---")
            monitor_agent.prediction_service_url = "http://127.0.0.1:9999" # Non-existent port
            monitor_agent.check_system_health()
            monitor_agent.prediction_service_url = service_url # Restore for scheduler

            print("\n--- Starting Scheduled Health Checks (every 1 min) ---")
            monitor_agent.start_scheduled_monitoring()
            
            print("Scheduled monitoring running in background. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                monitor_agent.stop_scheduled_monitoring()
                print("Scheduler stopped.")
        else:
            print("Failed to initialize Monitoring Agent due to missing reference data.")

