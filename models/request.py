from datetime import datetime
from .db import db

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # --- USER INPUTS ---
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default='Medium')
    attachment = db.Column(db.String(300), nullable=True)
    
    # NEW: Where should the technician go?
    current_location = db.Column(db.String(150), nullable=False) 
    
    # --- SYSTEM DATA ---
    request_type = db.Column(db.String(50), default='Corrective')
    scheduled_date = db.Column(db.Date, nullable=True)
    
    # Links
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Status & Admin
    status = db.Column(db.String(20), default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_response = db.Column(db.String(500), nullable=True)
    estimated_completion = db.Column(db.Date, nullable=True)

    # Relationships
    equipment = db.relationship('Equipment')
    team = db.relationship('Team')
    creator = db.relationship('User', backref='my_requests')