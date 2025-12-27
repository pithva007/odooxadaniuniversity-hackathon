from .db import db

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g., "IT Support"
    members = db.relationship('User', backref='team', lazy=True)