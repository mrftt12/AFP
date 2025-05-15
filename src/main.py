# /home/ubuntu/load_forecasting_webapp/src/main.py
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session, redirect, url_for, request

# Import models and db
from src.models.user import db, User # Import User model as well
from src.models.project import Project # Import Project model

# Import blueprints
from src.routes.user import user_bp
from src.routes.project import project_bp # Import project blueprint

# Import login_required decorator
from src.utils.auth import login_required

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "default_dev_secret_key_replace_me") # Use env var or default

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    print("Database tables created/verified.")

# Register Blueprints
app.register_blueprint(user_bp, url_prefix="/api/auth") # Changed prefix for clarity
app.register_blueprint(project_bp, url_prefix="/api/projects") # Register project blueprint

# --- Login Required Decorator is now imported from src.utils.auth ---

# --- Serve Frontend Files (Adjusted for Auth) ---
@app.route("/")
def index():
    if "user_id" in session:
        # If logged in, serve index.html which should redirect to dashboard
        return send_from_directory(app.static_folder, "index.html")
    return redirect(url_for("serve", path="login.html"))

@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Define public and protected pages/assets
    public_paths = ["login.html", "register.html", "styles.css", "script.js"] # Add CSS/JS etc.
    # Assume everything else requires login unless explicitly public

    requested_file_path = os.path.join(static_folder_path, path)

    # Handle login/register redirection if already logged in
    if path in ["login.html", "register.html"] and "user_id" in session:
         return redirect(url_for("serve", path="index.html")) # Redirect to index, which should handle dashboard redirect

    # Check if the path exists
    if os.path.exists(requested_file_path) and os.path.isfile(requested_file_path):
        # Check if accessing a non-public path without being logged in
        if path not in public_paths and "user_id" not in session:
             return redirect(url_for("serve", path="login.html"))
        # Serve the file
        return send_from_directory(static_folder_path, path)
    else:
        # If path doesn't exist, try serving index.html (for SPA routing)
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            # Check login status before serving index.html for potential client-side routing
            if "user_id" in session:
                 return send_from_directory(static_folder_path, "index.html")
            else:
                 # If not logged in and trying to access root or non-existent path, redirect to login
                 return redirect(url_for("serve", path="login.html"))
        else:
            # If index.html doesn't exist either
            return "Not Found", 404

if __name__ == "__main__":
    # Use port 5000 for local dev, deployment tool will handle production port
    app.run(host="0.0.0.0", port=5000, debug=True)

