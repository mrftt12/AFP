# /home/ubuntu/load_forecasting_webapp/src/routes/project.py
from flask import Blueprint, request, jsonify, session, current_app, send_file
from src.models.user import db, User
from src.models.project import Project
from src.utils.auth import login_required # Import decorator from utils
import os
import uuid
from werkzeug.utils import secure_filename
import logging
import threading

# Import ML pipeline logic (adjust paths/imports as needed)
# Assuming the original agents are in a place accessible by this app
import sys
# Add the directory containing the original agents to sys.path
original_agents_path = "/home/ubuntu/load_forecasting_agents"
if original_agents_path not in sys.path:
    sys.path.append(original_agents_path)

try:
    from agents.data_processing_agent import DataProcessingAgent
    from agents.modeling_agent import ModelingAgent
except ImportError as e:
    logging.error(f"Could not import agents: {e}. Ensure {original_agents_path} is correct and contains the agent files.")
    # Define dummy classes if import fails to allow app to run
    class DataProcessingAgent:
        def process_data(*args, **kwargs):
            logging.error("DataProcessingAgent not loaded.")
            return None
    class ModelingAgent:
        def __init__(self, *args, **kwargs):
            self.df = None
            logging.error("ModelingAgent not loaded.")
        def run_modeling_pipeline(*args, **kwargs):
            logging.error("ModelingAgent not loaded.")
            return {}, None, None

project_bp = Blueprint("project_bp", __name__)

# Define upload folder within the webapp directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_DATA_FOLDER, exist_ok=True)

# TODO: Add some sample CSV files to SAMPLE_DATA_FOLDER
# Example: Create a dummy sample file
dummy_sample_path = os.path.join(SAMPLE_DATA_FOLDER, "sample_energy_data.csv")
if not os.path.exists(dummy_sample_path):
    with open(dummy_sample_path, "w") as f:
        f.write("timestamp,load_kw\n")
        f.write("2023-01-01 00:00:00,100\n")
        f.write("2023-01-01 01:00:00,110\n")
        f.write("2023-01-01 02:00:00,105\n")

ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Project CRUD (Existing) ---
@project_bp.route("/", methods=["POST"])
@login_required
def create_project():
    user_id = session.get("user_id")
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Project name is required"}), 400
    project_name = data["name"]
    existing_project = Project.query.filter_by(user_id=user_id, name=project_name).first()
    if existing_project:
        return jsonify({"error": f"Project with name 	{project_name}	 already exists"}), 409
    new_project = Project(name=project_name, user_id=user_id)
    db.session.add(new_project)
    try:
        db.session.commit()
        return jsonify({
            "message": "Project created successfully", 
            "project": {"id": new_project.id, "name": new_project.name, "status": new_project.status, "created_at": new_project.created_at.isoformat()}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@project_bp.route("/", methods=["GET"])
@login_required
def list_projects():
    user_id = session.get("user_id")
    user_projects = Project.query.filter_by(user_id=user_id).order_by(Project.last_updated_at.desc()).all()
    projects_list = [
        {"id": p.id, "name": p.name, "status": p.status, "last_updated_at": p.last_updated_at.isoformat()}
        for p in user_projects
    ]
    return jsonify(projects_list), 200

@project_bp.route("/<int:project_id>", methods=["GET"])
@login_required
def get_project(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404
    project_details = {
        "id": project.id, "name": project.name, "status": project.status,
        "created_at": project.created_at.isoformat(), "last_updated_at": project.last_updated_at.isoformat(),
        "raw_data_path": project.raw_data_path, "processed_data_path": project.processed_data_path,
        "mlflow_run_id": project.mlflow_run_id, "best_model_name": project.best_model_name,
        "forecast_result_path": project.forecast_result_path, "forecast_horizon": project.forecast_horizon,
        "forecast_granularity": project.forecast_granularity, "target_unit": project.target_unit
        # TODO: Add metrics retrieval if stored
    }
    return jsonify(project_details), 200

@project_bp.route("/<int:project_id>", methods=["DELETE"])
@login_required
def delete_project(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404
    try:
        # TODO: Delete associated files
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# --- Data Input --- 
@project_bp.route("/<int:project_id>/data", methods=["POST"])
@login_required
def upload_or_select_data(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404

    data_source_type = request.form.get("source_type") # e.g., "upload", "sample"
    datetime_col = request.form.get("datetime_col", "timestamp")
    value_col = request.form.get("value_col", "load_kw")

    if not data_source_type:
        return jsonify({"error": "Missing \"source_type\" (upload or sample)"}), 400

    raw_data_file_path = None

    if data_source_type == "upload":
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            # Generate unique filename to avoid conflicts
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            raw_data_file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                file.save(raw_data_file_path)
            except Exception as e:
                 return jsonify({"error": f"Failed to save uploaded file: {str(e)}"}), 500
        else:
            return jsonify({"error": "File type not allowed (only .csv)"}), 400
    elif data_source_type == "sample":
        sample_filename = request.form.get("sample_filename")
        if not sample_filename:
            return jsonify({"error": "Missing \"sample_filename\" for source_type sample"}), 400
        # Basic security check
        safe_sample_filename = secure_filename(sample_filename)
        potential_path = os.path.join(SAMPLE_DATA_FOLDER, safe_sample_filename)
        # Check it actually exists within the sample folder
        if os.path.exists(potential_path) and os.path.commonpath([SAMPLE_DATA_FOLDER]) == os.path.commonpath([SAMPLE_DATA_FOLDER, potential_path]):
            raw_data_file_path = potential_path
        else:
            return jsonify({"error": "Invalid or non-existent sample file specified"}), 400
    else:
        return jsonify({"error": "Invalid \"source_type\" specified"}), 400

    if raw_data_file_path:
        # Update project status and data path
        project.raw_data_path = raw_data_file_path
        project.status = "DataUploaded"
        # Store column names specified by user (important for processing)
        project.datetime_col_name = datetime_col # Need to add these columns to Project model
        project.value_col_name = value_col     # Need to add these columns to Project model
        try:
            db.session.commit()
            return jsonify({"message": "Data source set successfully", "project_id": project.id, "status": project.status}), 200
        except Exception as e:
            db.session.rollback()
            # Clean up uploaded file if commit fails?
            if data_source_type == "upload" and os.path.exists(raw_data_file_path):
                 try: os.remove(raw_data_file_path) 
                 except: pass
            return jsonify({"error": f"Database error updating project: {str(e)}"}), 500
    else:
        # Should not happen if logic above is correct
        return jsonify({"error": "Failed to determine data file path"}), 500

# --- ML Pipeline Trigger --- 
# Placeholder for triggering the pipeline (will need background task execution)
@project_bp.route("/<int:project_id>/run", methods=["POST"])
@login_required
def run_pipeline(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404

    if project.status not in ["DataUploaded", "Ready", "Error"]: # Allow re-running if Ready/Error
        return jsonify({"error": f"Cannot start run when project status is {project.status}"}), 400
    if not project.raw_data_path or not os.path.exists(project.raw_data_path):
        return jsonify({"error": "Raw data path not set or file missing for project"}), 400

    # Get parameters from request
    data = request.get_json()
    horizon = data.get("horizon")
    granularity = data.get("granularity")
    target_unit = data.get("target_unit")

    if not horizon or not granularity:
        return jsonify({"error": "Forecast horizon and granularity are required"}), 400

    # Update project with parameters
    project.forecast_horizon = horizon
    project.forecast_granularity = granularity
    project.target_unit = target_unit
    project.status = "Processing"
    project.mlflow_run_id = None # Clear previous run ID
    project.best_model_name = None
    project.forecast_result_path = None
    project.processed_data_path = None
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error updating parameters: {str(e)}"}), 500

    # --- Trigger Background Task --- 
    # Using threading for simplicity in local dev. Use Celery/RQ for production.
    logging.info(f"Starting background ML pipeline for project {project_id}")
    thread = threading.Thread(target=execute_ml_pipeline, args=(project.id, current_app._get_current_object()))
    thread.start()
    # --- End Trigger --- 

    return jsonify({"message": "Forecast pipeline started", "project_id": project.id, "status": project.status}), 202 # Accepted

def execute_ml_pipeline(project_id, app):
    """Function to run in a background thread."""
    with app.app_context(): # Need app context for database access in thread
        project = Project.query.get(project_id)
        if not project:
            logging.error(f"[Thread-{project_id}] Project not found.")
            return

        logging.info(f"[Thread-{project_id}] Starting data processing.")
        try:
            data_processor = DataProcessingAgent()
            # Define output path for processed data
            processed_filename = f"processed_{secure_filename(project.name)}_{project.id}.csv"
            processed_output_path = os.path.join(UPLOAD_FOLDER, processed_filename) # Store processed data near raw
            
            # Get column names from project model (assuming they were added)
            datetime_col = getattr(project, "datetime_col_name", "timestamp")
            value_col = getattr(project, "value_col_name", "load_kw")

            processed_df = data_processor.process_data(
                source_path=project.raw_data_path,
                datetime_col=datetime_col,
                value_col=value_col,
                output_path=processed_output_path # Pass full path
            )
            
            if processed_df is None:
                raise ValueError("Data processing returned None.")
            
            project.processed_data_path = processed_output_path
            project.status = "Processed"
            db.session.commit()
            logging.info(f"[Thread-{project_id}] Data processing complete. Saved to {processed_output_path}")

        except Exception as e:
            logging.error(f"[Thread-{project_id}] Data processing failed: {e}", exc_info=True)
            project.status = "Error"
            db.session.commit()
            return # Stop pipeline

        logging.info(f"[Thread-{project_id}] Starting modeling pipeline.")
        try:
            # Use a unique name for the registered model per project/run?
            # For simplicity, maybe prefix with project ID
            registered_model_name = f"Project_{project_id}_{secure_filename(project.name)}"
            
            # Define MLflow tracking URI if needed (can be set globally or per agent)
            # mlflow_tracking_uri = "file:/path/to/shared/mlruns" 
            
            modeler = ModelingAgent(
                processed_data_path=project.processed_data_path,
                value_col=value_col, # Use the value col name stored in project
                registered_model_name=registered_model_name,
                # mlflow_tracking_uri=mlflow_tracking_uri # Optional
            )
            
            if modeler.df is None:
                 raise ValueError("Modeling agent failed to load processed data.")

            # Run modeling (adjust parameters like trials as needed)
            optuna_trials = 10 # Example
            modeling_results, best_model, registered_version = modeler.run_modeling_pipeline(optuna_trials=optuna_trials)

            if not modeling_results or not best_model or not registered_version:
                raise ValueError("Modeling pipeline did not return expected results or register a model.")

            project.mlflow_run_id = registered_version.run_id
            project.best_model_name = best_model
            project.status = "Ready"
            # TODO: Store metrics in DB? Generate forecast file?
            db.session.commit()
            logging.info(f"[Thread-{project_id}] Modeling pipeline complete. Best model: {best_model}. Run ID: {registered_version.run_id}")

        except Exception as e:
            logging.error(f"[Thread-{project_id}] Modeling pipeline failed: {e}", exc_info=True)
            project.status = "Error"
            db.session.commit()

# --- Status and Results Retrieval (Placeholders) --- 
@project_bp.route("/<int:project_id>/status", methods=["GET"])
@login_required
def get_pipeline_status(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404
    # Simple status return for now
    return jsonify({"project_id": project.id, "status": project.status}), 200

@project_bp.route("/<int:project_id>/results", methods=["GET"])
@login_required
def get_results(project_id):
    user_id = session.get("user_id")
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404
    
    if project.status != "Ready
(Content truncated due to size limit. Use line ranges to read in chunks)