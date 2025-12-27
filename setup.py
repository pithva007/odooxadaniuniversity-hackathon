from app import app, db
from models.user import User
from models.team import Team

with app.app_context():
    # 1. Create the database tables
    db.create_all()
    
    # 2. Create Teams (so you have something to assign assets to)
    if not Team.query.first():
        db.session.add(Team(name="IT Support"))
        db.session.add(Team(name="Heavy Mechanics"))
        print("✅ Teams Created: IT Support, Heavy Mechanics")

    # 3. Create the Admin User
    if not User.query.filter_by(username="admin").first():
        # In a real app, hash the password! For Hackathon, plain text is fine.
        admin = User(username="admin", password="123", role="Manager")
        db.session.add(admin)
        print("✅ Admin User Created (admin / 123)")

    db.session.commit()
    print("🚀 Database Setup Complete!")