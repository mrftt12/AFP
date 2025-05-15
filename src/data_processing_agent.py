# /home/ubuntu/load_forecasting_agents/agents/data_processing_agent.py
import pandas as pd
import numpy as np
import logging
import os
from urllib.parse import urlparse
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
class DataProcessingAgent    def __init__(self, raw_data_dir='/home/ubuntu/load_forecasting_agents/data/raw',
                 processed_data_dir='/home/ubuntu/load_forecasting_agents/data/processed'):     self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        self.datetime_col = None
        self.value_col = None
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        logging.info("DataProcessingAgent initialized.")

    def _load_data(self, source_path: str) -> pd.DataFrame | None:
        """
        Internal method to load data from a CSV file (local path or URL).
        Handles path resolution and basic column checks.
        """
        logging.info(f"Attempting to load data from: {source_path}")
        try:
            parsed_url = urlparse(source_path)
            is_url = all([parsed_url.scheme, parsed_url.netloc])

            if not is_url and not os.path.isabs(source_path) and not os.path.exists(source_path):
                 potential_path = os.path.join(self.raw_data_dir, source_path)
                 if os.path.exists(potential_path):
                     source_path = potential_path
                     logging.info(f"Found file in raw data directory: {source_path}")
                 else:
                     logging.error(f"Local file not found: {source_path} or {potential_path}")
                     return None
            elif not is_url and not os.path.exists(source_path):
                logging.error(f"Local file not found: {source_path}")
                return None

            df = pd.read_csv(source_path)
            logging.info(f"Successfully loaded data. Shape: {df.shape}")

            if self.datetime_col not in df.columns:
                logging.error(f"Datetime column \'{self.datetime_col}\' not found.")
                return None
            if self.value_col not in df.columns:
                logging.error(f"Value column \'{self.value_col}\' not found.")
                return None

            # Save raw copy if needed
            if is_url or not os.path.abspath(source_path).startswith(os.path.abspath(self.raw_data_dir)):
                 raw_filename = os.path.basename(source_path)
                 raw_save_path = os.path.join(self.raw_data_dir, raw_filename)
                 try:
                     df.to_csv(raw_save_path, index=False)
                     logging.info(f"Saved raw data copy to: {raw_save_path}")
                 except Exception as save_err:
                     logging.warning(f"Could not save raw data copy to {raw_save_path}: {save_err}")

            return df[[self.datetime_col, self.value_col]].copy()

        except FileNotFoundError:
            logging.error(f"File not found error for: {source_path}")
            return None
        except Exception as e:
            logging.error(f"Error loading data from {source_path}: {e}")
            return None

    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """Validates, cleans, and standardizes the loaded dataframe."""
        logging.info("Starting data validation and cleaning...")
        if df is None or df.empty:
            logging.error("Input DataFrame is empty or None.")
            return None

        # 1. Handle Datetime Column
        try:
            df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
            logging.info(f"Converted \'{self.datetime_col}\' to datetime objects.")
        except Exception as e:
            logging.error(f"Error converting \'{self.datetime_col}\' to datetime: {e}. Attempting inference.")
            try:
                df[self.datetime_col] = pd.to_datetime(df[self.datetime_col], infer_datetime_format=True)
                logging.info(f"Successfully converted \'{self.datetime_col}\' with format inference.")
            except Exception as e2:
                 logging.error(f"Failed to convert \'{self.datetime_col}\' to datetime even with inference: {e2}")
                 return None

        # 2. Handle Value Column
        try:
            df[self.value_col] = pd.to_numeric(df[self.value_col], errors=\'coerce\')
            logging.info(f"Converted \'{self.value_col}\' to numeric.")
        except Exception as e:
            logging.error(f"Error converting \'{self.value_col}\' to numeric: {e}")
            return None

        # 3. Set Index and Sort
        df = df.set_index(self.datetime_col).sort_index()
        logging.info(f"Set \'{self.datetime_col}\' as index and sorted.")

        # 4. Handle Duplicates (keep first by default)
        initial_rows = len(df)
        df = df[~df.index.duplicated(keep=\'first\')]
        if len(df) < initial_rows:
            logging.warning(f"Removed {initial_rows - len(df)} duplicate index entries.")

        # 5. Handle Missing Values (Load Value Column)
        missing_count = df[self.value_col].isnull().sum()
        if missing_count > 0:
            logging.warning(f"Found {missing_count} missing values in \'{self.value_col}\'. Imputing with forward fill.")
            # Simple imputation: forward fill. More sophisticated methods could be added.
            df[self.value_col] = df[self.value_col].ffill()
            # Check if any NaNs remain (e.g., at the beginning)
            remaining_nan = df[self.value_col].isnull().sum()
            if remaining_nan > 0:
                logging.warning(f"{remaining_nan} NaNs remain after ffill (likely at start). Imputing with back fill.")
                df[self.value_col] = df[self.value_col].bfill()
                if df[self.value_col].isnull().any(): # Still NaNs? Fill with 0 or mean/median?
                     logging.error("Could not impute all NaNs. Filling remaining with 0.")
                     df[self.value_col] = df[self.value_col].fillna(0)

        # 6. Infer Frequency and Resample if needed (Optional - depends on use case)
        # inferred_freq = pd.infer_freq(df.index)
        # logging.info(f"Inferred frequency: {inferred_freq}")
        # If a specific frequency is required by the user/model, resample here.
        # Example: df = df.resample(\'H\').mean() # Resample to hourly, taking the mean

        logging.info("Data validation and cleaning completed.")
        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineers time-based features."""
        logging.info("Starting feature engineering...")
        if df is None or df.empty:
            logging.error("Input DataFrame for feature engineering is empty or None.")
            return df # Return original empty/None df

        df[\'hour\'] = df.index.hour
        df[\'dayofweek\'] = df.index.dayofweek # Monday=0, Sunday=6
        df[\'dayofyear\'] = df.index.dayofyear
        df[\'month\'] = df.index.month
        df[\'year\'] = df.index.year
        df[\'weekofyear\'] = df.index.isocalendar().week.astype(int)
        df[\'quarter\'] = df.index.quarter

        # Example Lag Feature (can be customized or expanded)
        # df[f\'{self.value_col}_lag1\'] = df[self.value_col].shift(1)
        # df = df.dropna() # Drop rows with NaNs created by lag features

        logging.info("Feature engineering completed.")
        return df

    def process_data(self, source_path: str, datetime_col: str, value_col: str, output_filename: str = None) -> pd.DataFrame | None:
        """
        Orchestrates the data loading, cleaning, and feature engineering process.

        Args:
            source_path: Path or URL to the raw CSV data.
            datetime_col: Name of the datetime column.
            value_col: Name of the value (load) column.
            output_filename: (Optional) Filename to save the processed data CSV.
                             If None, defaults to processed_<original_basename>.csv.

        Returns:
            A pandas DataFrame with the processed data, or None if processing fails.
        """
        self.datetime_col = datetime_col
        self.value_col = value_col
        logging.info(f"Starting data processing for source: {source_path}")

        # 1. Load
        df_raw = self._load_data(source_path)
        if df_raw is None:
            return None

        # 2. Validate & Clean
        df_clean = self._validate_and_clean(df_raw)
        if df_clean is None:
            return None

        # 3. Engineer Features
        df_processed = self._engineer_features(df_clean)
        if df_processed is None:
             logging.error("Feature engineering failed.")
             return None # Should not happen if df_clean was valid, but check anyway

        # 4. Save Processed Data
        if output_filename is None:
            base_name = os.path.basename(source_path)
            name, ext = os.path.splitext(base_name)
            output_filename = f"processed_{name}.csv"

        save_path = os.path.join(self.processed_data_dir, output_filename)
        try:
            df_processed.to_csv(save_path)
            logging.info(f"Successfully saved processed data to: {save_path}")
        except Exception as e:
            logging.error(f"Error saving processed data to {save_path}: {e}")
            # Return the dataframe even if saving fails, but log the error

        logging.info("Data processing pipeline finished.")
        return df_processed

# Example usage (for testing within the script)
if __name__ == \'__main__\':
    # Create a dummy CSV for testing with missing data and duplicates
    dummy_data = {
        \'timestamp\': pd.to_datetime([\'2023-01-01 00:00\', \'2023-01-01 01:00\', \'2023-01-01 01:00\', \'2023-01-01 02:00\', \'2023-01-01 03:00\', \'2023-01-01 05:00\']),
        \'load_kw\': [100, 110, 111, np.nan, 105, 120],
        \'other_col\': [\'a\', \'b\', \'b_dup\', \'c\', \'d\', \'f\']
    }
    dummy_df = pd.DataFrame(dummy_data)
    dummy_path = \'/home/ubuntu/load_forecasting_agents/data/raw/dummy_load_data_v2.csv\'
    os.makedirs(os.path.dirname(dummy_path), exist_ok=True)
    dummy_df.to_csv(dummy_path, index=False)
    print(f"Created dummy data at {dummy_path}")

    agent = DataProcessingAgent()
    processed_df = agent.process_data(source_path=dummy_path, datetime_col=\'timestamp\', value_col=\'load_kw\')

    if processed_df is not None:
        print("\n--- Processed Data ---")
        print(processed_df.head())
        print("\nInfo:")
        processed_df.info()
        print("\nNaN check:")
        print(processed_df.isnull().sum())
    else:
        print("\nFailed to process data.")

    # Test URL loading again (using the same simple example)
    url = "https://raw.githubusercontent.com/cs109/2014_data/master/countries.csv"
    print(f"\nTesting URL processing from: {url}")
    # These columns will likely fail validation, demonstrating error handling
    url_processed_df = agent.process_data(source_path=url, datetime_col=\'Year\', value_col=\'LifeExpectancy\') # Example columns
    if url_processed_df is not None:
        print("\nURL Data processed successfully (using example columns):")
        print(url_processed_df.head())
    else:
        print("\nFailed to process URL data (likely due to column type validation failures).")

