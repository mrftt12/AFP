from src.models.user import db
from datetime import datetime
import json

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(255), nullable=True)
    model_config = db.Column(db.Text, nullable=True)  # Store as JSON
    status = db.Column(db.String(50), default='created')  # created, processing, completed, failed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def set_model_config(self, config_dict):
        """Set model configuration using a dictionary"""
        self.model_config = json.dumps(config_dict)
    
    def get_model_config(self):
        """Get model configuration as a dictionary"""
        if self.model_config:
            return json.loads(self.model_config)
        return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'data_source': self.data_source,
            'model_config': self.get_model_config(),
            'status': self.status,
            'user_id': self.user_id
        }