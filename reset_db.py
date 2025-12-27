import os
from app import app, db
from models.user import User
from models.team import Team

# 1. Define the path to the database
db_path = os.path.join(app.instance_path, 'gearguard.db')

# 2. FORCE DELETE the old database file if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️  Deleted old database at: {db_path}")
else:
    print("ℹ️  No existing database found (that's okay).")

# 3. Rebuild everything from scratch
with app.app_context():
    print("🔨 Creating new database tables...")
    db.create_all()
    
    # 4. Create Teams
    print("🌱 Seeding Teams...")
    it = Team(name="IT Support")
    mech = Team(name="Heavy Mechanics")
    db.session.add(it)
    db.session.add(mech)
    # Commit teams first so they get IDs
    db.session.commit() 

    # 5. Create Admin User
    print("👤 Creating Admin User...")
    # FIX: We use "Admin" as the role so the button appears!
    admin = User(username="admin", password="123", role="Admin", team_id=it.id)
    db.session.add(admin)
    
    db.session.commit()
    print("✅ SUCCESS! Database has been completely reset.")
    print("🚀 You can now run 'python3 app.py'")