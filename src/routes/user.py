from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
import logging

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    if not request.is_json:
        return jsonify({'error': 'Invalid content type, expected JSON'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    try:
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.password = data['password']  # This will use the password setter to hash
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred during registration'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """Log in a user"""
    if not request.is_json:
        return jsonify({'error': 'Invalid content type, expected JSON'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Find user by username
    user = User.query.filter_by(username=data['username']).first()
    
    # Verify user and password
    if user is None or not user.verify_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200

@user_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the current user"""
    session.pop('user_id', None)
    session.pop('username', None)
    
    return jsonify({'message': 'Logged out successfully'}), 200

@user_bp.route('/profile', methods=['GET'])
def profile():
    """Get the current user's profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        # Session references a non-existent user, clear it
        session.pop('user_id', None)
        session.pop('username', None)
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200