from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models.db import db
from datetime import datetime
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth # <--- REQUIRED FOR SOCIAL LOGIN

# Import Models
from models.user import User
from models.team import Team
from models.equipment import Equipment
from models.request import MaintenanceRequest

# 1. CREATE THE APP FIRST
app = Flask(__name__)

# 2. CONFIGURE IT
app.config.from_object(Config)

# Add the upload folder config
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- SOCIAL LOGIN CONFIGURATION (REPLACE WITH REAL KEYS) ---
app.config['GOOGLE_CLIENT_ID'] = 'YOUR_GOOGLE_CLIENT_ID_HERE'
app.config['GOOGLE_CLIENT_SECRET'] = 'YOUR_GOOGLE_SECRET_HERE'
app.config['GITHUB_CLIENT_ID'] = 'YOUR_GITHUB_CLIENT_ID_HERE'
app.config['GITHUB_CLIENT_SECRET'] = 'YOUR_GITHUB_SECRET_HERE'

# 3. INITIALIZE DB & LOGIN
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- OAUTH SETUP ---
oauth = OAuth(app)

# 1. Google Config
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# 2. GitHub Config
github = oauth.register(
    name='github',
    client_id=app.config['GITHUB_CLIENT_ID'],
    client_secret=app.config['GITHUB_CLIENT_SECRET'],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# --- USER LOADER ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- SETUP: CREATE TABLES ---
@app.before_request
def create_tables():
    if getattr(app, 'tables_created', False):
        return
    app.tables_created = True
    with app.app_context():
        db.create_all()

# --- AUTH SYSTEM (Standard) ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') 
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('signup'))
            
        new_user = User(username=username, role=role)
        new_user.set_password(password) # Use the method from models/user.py
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('auth/signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password): # Use check_password method
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- AUTH SYSTEM (Social) ---

# GOOGLE
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google')
def authorize_google():
    try:
        token = google.authorize_access_token()
        user_info = token['userinfo']
        
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            user = User(
                username=user_info['name'], 
                email=user_info['email'],
                role='User'
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash("Google Login Failed. Please try again.")
        return redirect(url_for('login'))

# GITHUB
@app.route('/login/github')
def login_github():
    redirect_uri = url_for('authorize_github', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/auth/github')
def authorize_github():
    try:
        token = github.authorize_access_token()
        resp = github.get('user').json()
        
        username = resp.get('login')
        # GitHub email might be hidden, create a fallback
        email = resp.get('email') or f"{username}@github.com"
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            user = User(
                username=username,
                email=email,
                role='User'
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash("GitHub Login Failed. Please try again.")
        return redirect(url_for('login'))


# --- DASHBOARD ---
@app.route('/')
@login_required
def dashboard():
    stats = {'new': 0, 'progress': 0, 'repaired': 0, 'scrap': 0}

    if current_user.role == 'Admin':
        stats['new'] = MaintenanceRequest.query.filter_by(status='New').count()
        stats['progress'] = MaintenanceRequest.query.filter_by(status='In Progress').count()
        stats['repaired'] = MaintenanceRequest.query.filter_by(status='Repaired').count()
        stats['scrap'] = MaintenanceRequest.query.filter_by(status='Scrap').count()
        
        recent_reqs = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).limit(10).all()
        return render_template('dashboard_admin.html', stats=stats, requests=recent_reqs)
    else:
        stats['new'] = MaintenanceRequest.query.filter_by(created_by_id=current_user.id, status='New').count()
        stats['progress'] = MaintenanceRequest.query.filter_by(created_by_id=current_user.id, status='In Progress').count()
        stats['repaired'] = MaintenanceRequest.query.filter_by(created_by_id=current_user.id, status='Repaired').count()
        stats['scrap'] = MaintenanceRequest.query.filter_by(created_by_id=current_user.id, status='Scrap').count()
        
        my_reqs = MaintenanceRequest.query.filter_by(created_by_id=current_user.id).order_by(MaintenanceRequest.created_at.desc()).all()
        return render_template('dashboard_user.html', stats=stats, requests=my_reqs)

# --- REQUEST SYSTEM ---

@app.route('/request/create', methods=['GET', 'POST'])
@login_required
def create_request():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')
        location = request.form.get('location') or "Unknown"
        eq_id = request.form.get('equipment_id')
        req_type = request.form.get('type')
        date_str = request.form.get('scheduled_date')
        
        file = request.files['attachment']
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        target_eq = Equipment.query.get(eq_id)
        sched_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        
        new_req = MaintenanceRequest(
            title=title, description=description, priority=priority,
            current_location=location, attachment=filename,
            equipment_id=eq_id, team_id=target_eq.team_id,
            request_type=req_type, scheduled_date=sched_date,
            created_by_id=current_user.id, status='New'
        )
        db.session.add(new_req)
        db.session.commit()
        return redirect(url_for('dashboard'))

    equipment_list = Equipment.query.all()
    active_tickets = MaintenanceRequest.query.filter(
        MaintenanceRequest.status.in_(['New', 'In Progress'])
    ).all()
    broken_ids = [t.equipment_id for t in active_tickets]

    return render_template('requests/create.html', 
                           equipment_list=equipment_list, 
                           broken_ids=broken_ids)

# --- ADMIN ACTIONS ---

@app.route('/kanban')
@login_required
def kanban_board():
    if current_user.role != 'Admin':
        return "Access Denied: Technicians Only", 403
    
    new_reqs = MaintenanceRequest.query.filter_by(status='New').all()
    progress_reqs = MaintenanceRequest.query.filter_by(status='In Progress').all()
    done_reqs = MaintenanceRequest.query.filter_by(status='Repaired').all()
    scrap_reqs = MaintenanceRequest.query.filter_by(status='Scrap').all()

    return render_template('requests/kanban.html', 
                         new=new_reqs, 
                         progress=progress_reqs, 
                         done=done_reqs, 
                         scrap=scrap_reqs)

@app.route('/request/respond/<int:id>', methods=['GET', 'POST'])
@login_required
def respond_request(id):
    if current_user.role != 'Admin': return redirect(url_for('dashboard'))
    
    req = MaintenanceRequest.query.get(id)
    if request.method == 'POST':
        req.status = request.form.get('status')
        req.admin_response = request.form.get('response')
        date_str = request.form.get('est_date')
        if date_str:
            req.estimated_completion = datetime.strptime(date_str, '%Y-%m-%d').date()
            
        db.session.commit()
        return redirect(url_for('kanban_board'))
        
    return render_template('requests/respond.html', req=req)

# --- ROUTES FOR ASSETS ---

@app.route('/equipment')
@login_required
def list_equipment():
    items = Equipment.query.all()
    return render_template('equipment/list.html', items=items)

@app.route('/equipment/create', methods=['GET', 'POST'])
@login_required
def create_equipment():
    if current_user.role != 'Admin':
        flash("Access Denied")
        return redirect(url_for('list_equipment'))
    
    teams = Team.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        serial = request.form.get('serial')
        location = request.form.get('location')
        team_id = request.form.get('team_id')
        
        warranty_str = request.form.get('warranty_date')
        warranty_date = None
        if warranty_str:
            warranty_date = datetime.strptime(warranty_str, '%Y-%m-%d').date()

        if Equipment.query.filter_by(serial_number=serial).first():
            flash(f"Error: Serial {serial} exists!")
            return render_template('equipment/create.html', teams=teams)

        new_eq = Equipment(
            name=name, 
            serial_number=serial, 
            location=location,
            warranty_expiration=warranty_date,
            team_id=team_id
        )
        db.session.add(new_eq)
        db.session.commit()
        return redirect(url_for('list_equipment'))
            
    return render_template('equipment/create.html', teams=teams)

@app.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    asset = Equipment.query.get_or_404(id)
    history = MaintenanceRequest.query.filter_by(equipment_id=id).order_by(MaintenanceRequest.created_at.desc()).all()
    stats = {'total': len(history), 'last': history[0].created_at.strftime('%Y-%m-%d') if history else "Never"}
    return render_template('equipment/view.html', asset=asset, history=history, stats=stats)


# --- TEAM MANAGEMENT ---
@app.route('/teams', methods=['GET', 'POST'])
@login_required
def manage_teams():
    if current_user.role != 'Admin':
        flash("Access Denied")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            existing = Team.query.filter_by(name=name).first()
            if not existing:
                new_team = Team(name=name)
                db.session.add(new_team)
                db.session.commit()
                flash(f"Team '{name}' added successfully!")
            else:
                flash("That team already exists.")
        return redirect(url_for('manage_teams'))

    teams = Team.query.all()
    return render_template('admin/teams.html', teams=teams)

# --- CALENDAR & EXPORTS ---

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.route('/calendar/events')
@login_required
def get_calendar_events():
    if current_user.role != 'Admin':
        return jsonify([])

    scheduled_reqs = MaintenanceRequest.query.filter(MaintenanceRequest.scheduled_date != None).all()
    deadline_reqs = MaintenanceRequest.query.filter(MaintenanceRequest.estimated_completion != None).all()
    
    events = []
    for req in scheduled_reqs:
        events.append({
            'title': f"📅 {req.team.name}: {req.title}",
            'start': req.scheduled_date.isoformat(),
            'url': f"/request/respond/{req.id}",
            'color': '#0d6efd'
        })
    for req in deadline_reqs:
        events.append({
            'title': f"🚨 Deadline: {req.title}",
            'start': req.estimated_completion.isoformat(),
            'url': f"/request/respond/{req.id}",
            'color': '#dc3545'
        })
    return jsonify(events)

@app.route('/calendar')
@login_required
def view_calendar():
    if current_user.role != 'Admin':
        return "Access Denied", 403
    return render_template('requests/calendar.html')

@app.route('/export/csv')
@login_required
def export_csv():
    if current_user.role != 'Admin':
        return "Access Denied", 403

    requests = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Title', 'Priority', 'Status', 'Equipment', 'Serial', 'Reported By', 'Date Created'])
    for req in requests:
        cw.writerow([
            req.id, 
            req.title, 
            req.priority, 
            req.status, 
            req.equipment.name, 
            req.equipment.serial_number,
            req.creator.username,
            req.created_at.strftime('%Y-%m-%d')
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=maintenance_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)