# /home/ubuntu/load_forecasting_webapp/src/models/project.py
from .user import db # Import db from user.py to avoid circular imports
import datetime

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    status = db.Column(db.String(50), default="New") # e.g., New, DataUploaded, Processing, Ready, Error
    # Store paths or references to data, models, results associated with the project
    raw_data_path = db.Column(db.String(255), nullable=True)
    processed_data_path = db.Column(db.String(255), nullable=True)
    mlflow_run_id = db.Column(db.String(100), nullable=True)
    best_model_name = db.Column(db.String(100), nullable=True)
    forecast_result_path = db.Column(db.String(255), nullable=True)
    # Store parameters used for the last run
    forecast_horizon = db.Column(db.String(50), nullable=True)
    forecast_granularity = db.Column(db.String(50), nullable=True)
    target_unit = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Project {self.name} (User: {self.user_id})>"

