from .db import db

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    
    # --- NEW: WARRANTY FIELDS ---
    warranty_expiration = db.Column(db.Date, nullable=True) 
    
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    status = db.Column(db.String(20), default='Active')

    assigned_team = db.relationship('Team', backref='equipment_list')