import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

def create_app(test_config=None):
    """Application factory for Flask app"""
    
    # Create and configure the app
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
    
    # Enable CORS for development
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
    
    # Load default config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "default_dev_secret_key_replace_me"),
        SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Load test config if passed in
    if test_config is not None:
        app.config.update(test_config)
    
    # Initialize database
    from src.models.user import db
    db.init_app(app)
    
    # Create tables if needed
    with app.app_context():
        db.create_all()
        print("Database tables created/verified.")
    
    # Register blueprints
    from src.routes.user import user_bp
    from src.routes.project import project_bp
    
    app.register_blueprint(user_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    
    # Health check endpoint
    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok", "message": "API is operational"})
    
    # Serve frontend files
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        # For API routes, let them be handled by the appropriate blueprints
        if path.startswith("api/"):
            return app.view_functions[request.endpoint]()
        
        # For all other routes, serve the React app and let client-side routing handle it
        build_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
        
        # If in production, serve from the frontend/build directory
        if os.path.exists(build_folder):
            if path != "" and os.path.exists(os.path.join(build_folder, path)):
                return send_from_directory(build_folder, path)
            return send_from_directory(build_folder, "index.html")
        
        # In development, serve static files if they exist
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404
            
        requested_file_path = os.path.join(static_folder_path, path)
        
        # Check if the path exists
        if path and os.path.exists(requested_file_path) and os.path.isfile(requested_file_path):
            return send_from_directory(static_folder_path, path)
        else:
            # If path doesn't exist or is the root, serve index.html
            index_path = os.path.join(static_folder_path, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, "index.html")
            else:
                # Fallback for development without static files built
                return jsonify({"message": "API server is running. Frontend build not found."}), 200
    
    return app