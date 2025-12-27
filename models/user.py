from .db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    
    # --- SOCIAL LOGIN FIELDS ---
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    
    role = db.Column(db.String(50), default='User')

    # --- THE MISSING LINK (RESTORED) ---
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    # -----------------------------------

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # If user logged in with Google/GitHub, they might not have a password
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)