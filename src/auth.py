# /home/ubuntu/load_forecasting_webapp/src/utils/auth.py
from functools import wraps
from flask import session, redirect, url_for, request, jsonify

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # For API requests, return 401 Unauthorized
            # Check if the request expects JSON or is hitting an API endpoint
            is_api_request = (request.accept_mimetypes.accept_json and 
                              not request.accept_mimetypes.accept_html) or \
                             (request.endpoint and (request.endpoint.startswith("api.") or request.blueprint in ["user_bp", "project_bp"])) # Include blueprint check
            
            if is_api_request:
                 return jsonify({"error": "Authentication required"}), 401
            else:
                # For web page requests, redirect to login
                return redirect(url_for("serve", path="login.html", _external=True))
        return f(*args, **kwargs)
    return decorated_function

