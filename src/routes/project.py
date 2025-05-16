from flask import Blueprint, request, jsonify, session
from src.models.project import db, Project
from src.utils.auth import login_required
import logging

project_bp = Blueprint('project', __name__)

@project_bp.route('/', methods=['GET'])
@login_required
def get_projects():
    """Get all projects for the current user"""
    try:
        projects = Project.query.filter_by(user_id=session['user_id']).all()
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving projects: {e}")
        return jsonify({'error': 'An error occurred retrieving projects'}), 500

@project_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get a specific project by ID"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
            
        # Check if the project belongs to the current user
        if project.user_id != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
            
        return jsonify({'project': project.to_dict()}), 200
    except Exception as e:
        logging.error(f"Error retrieving project {project_id}: {e}")
        return jsonify({'error': 'An error occurred retrieving the project'}), 500

@project_bp.route('/', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    if not request.is_json:
        return jsonify({'error': 'Invalid content type, expected JSON'}), 400
        
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data or not data['name']:
        return jsonify({'error': 'Project name is required'}), 400
        
    try:
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            data_source=data.get('data_source', ''),
            user_id=session['user_id']
        )
        
        # Set model config if provided
        if 'model_config' in data and data['model_config']:
            project.set_model_config(data['model_config'])
            
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
    except Exception as e:
        logging.error(f"Error creating project: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred creating the project'}), 500

@project_bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update an existing project"""
    if not request.is_json:
        return jsonify({'error': 'Invalid content type, expected JSON'}), 400
        
    data = request.get_json()
    
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
            
        # Check if the project belongs to the current user
        if project.user_id != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
            
        # Update fields
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'data_source' in data:
            project.data_source = data['data_source']
        if 'status' in data:
            project.status = data['status']
        if 'model_config' in data:
            project.set_model_config(data['model_config'])
            
        db.session.commit()
        
        return jsonify({
            'message': 'Project updated successfully',
            'project': project.to_dict()
        }), 200
    except Exception as e:
        logging.error(f"Error updating project {project_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred updating the project'}), 500

@project_bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
            
        # Check if the project belongs to the current user
        if project.user_id != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
            
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        logging.error(f"Error deleting project {project_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred deleting the project'}), 500