from functools import wraps
from flask import session, redirect, url_for, request, flash, jsonify
import logging

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For API routes, return a JSON response
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            # For web routes, redirect to login
            return redirect(url_for('serve', path='login.html'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('serve', path='login.html'))
        
        # Check if user is admin (implementation depends on your user model)
        # For simplicity, just checking admin flag in session
        if not session.get('is_admin', False):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin privileges required'}), 403
            # For web routes, flash message and redirect to dashboard
            flash('Admin privileges required')
            return redirect(url_for('serve', path='dashboard.html'))
        
        return f(*args, **kwargs)
    return decorated_function