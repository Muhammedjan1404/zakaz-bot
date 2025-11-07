import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    assignments = db.relationship('Assignment', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    subjects = db.Column(db.String(500), nullable=False)
    deadline = db.Column(db.String(50), nullable=False)
    task_source = db.Column(db.String(50), nullable=False)
    work_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables and add admin user if not exists
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()

# Mock data for the form
FACULTIES = ["Факультет 1", "Факультет 2", "Факультет 3"]
COURSES = ["1 курс", "2 курс", "3 курс", "4 курс"]
WORK_TYPES = ["Промежуточная работа", "Практическая работа", "Проектная работа", "Задание за весь семестр"]

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, password=password)  # In production, hash the password
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        assignments = Assignment.query.order_by(Assignment.status, Assignment.deadline).all()
    else:
        assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.status, Assignment.deadline).all()
    
    return render_template('dashboard.html', assignments=assignments, is_admin=current_user.is_admin)

@app.route('/assignment/new', methods=['GET', 'POST'])
@login_required
def new_assignment():
    if request.method == 'POST':
        course = request.form.get('course')
        semester = request.form.get('semester')
        faculty = request.form.get('faculty')
        subjects = request.form.getlist('subjects')
        deadline = request.form.get('deadline')
        task_source = request.form.get('task_source')
        work_type = request.form.get('work_type')
        
        assignment = Assignment(
            course=course,
            semester=semester,
            faculty=faculty,
            subjects=", ".join(subjects),
            deadline=deadline,
            task_source=task_source,
            work_type=work_type,
            user_id=current_user.id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Задание успешно создано!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('new_assignment.html', 
                         courses=COURSES, 
                         faculties=FACULTIES,
                         work_types=WORK_TYPES)

@app.route('/api/subjects')
@login_required
def get_subjects():
    faculty = request.args.get('faculty')
    # In a real app, you would fetch subjects based on the selected faculty
    subjects = {
        "Факультет 1": ["Предмет 1.1", "Предмет 1.2", "Предмет 1.3"],
        "Факультет 2": ["Предмет 2.1", "Предмет 2.2", "Предмет 2.3"],
        "Факультет 3": ["Предмет 3.1", "Предмет 3.2", "Предмет 3.3"]
    }
    return jsonify(subjects.get(faculty, []))

@app.route('/api/semesters')
@login_required
def get_semesters():
    course = request.args.get('course')
    if course:
        course_num = int(course.split()[0])
        semesters = [f"{2*course_num - 1} семестр", f"{2*course_num} семестр"]
        return jsonify(semesters)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
