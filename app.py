import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-123'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.String(20), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html', active_page='home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('home'))
        flash("Invalid Username or Password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/tasks')
@login_required
def tasks():
    today = datetime.now().strftime('%Y-%m-%d')
    user_tasks = Task.query.filter_by(date_created=today, user_id=current_user.id).all()
    return render_template('tasks.html', tasks=user_tasks, date=today, active_page='tasks')

@app.route('/history')
@login_required
def history():
    all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date_created.desc()).all()
    return render_template('history.html', tasks=all_tasks, active_page='history')

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    new_task = Task(content=data['content'], user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return jsonify({"success": True})

@app.route('/clear', methods=['POST'])
@login_required
def clear_tasks():
    today = datetime.now().strftime('%Y-%m-%d')
    Task.query.filter_by(date_created=today, user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})

with app.app_context():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)