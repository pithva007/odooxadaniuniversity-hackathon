from app import app, db
from models.user import User
from models.team import Team

with app.app_context():
    # 1. Drop everything to clean the slate
    db.drop_all()
    db.create_all()
    
    # 2. Create the IT Team
    it_team = Team(name="IT Support")
    db.session.add(it_team)
    db.session.commit() # Commit to get the ID

    # 3. Create the SUPER ADMIN
    # We explicitly set role="Admin"
    admin = User(username="admin", password="123", role="Admin", team_id=it_team.id)
    db.session.add(admin)
    db.session.commit()

    print("✅ RESET COMPLETE.")
    print("👤 Login with: admin / 123")