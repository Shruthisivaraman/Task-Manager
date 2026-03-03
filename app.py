from flask import Flask
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pymysql
import config

pymysql.install_as_MySQLdb()
 
app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- DATABASE MODELS ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', tasks=tasks)


@app.route('/add_task', methods=['GET','POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        task = Task(title=title, user_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_task.html')


@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    task = Task.query.get(id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.status = request.form['status']
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task)


@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Task.query.get(id)
    task.status = "Completed"
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify old password
        if not old_password or current_user.password != old_password:
            return render_template('profile.html', error='Old password is incorrect')

        # Check if new passwords match
        if new_password != confirm_password:
            return render_template('profile.html', error='New passwords do not match')

        # Check if new password is not empty
        if not new_password:
            return render_template('profile.html', error='New password cannot be empty')

        # Update password
        current_user.password = new_password
        db.session.commit()
        return render_template('profile.html', success='Password updated successfully!')

    return render_template('profile.html', username=current_user.username)


@app.route('/summary')
@login_required
def summary():
    # Get all tasks for the current user
    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Calculate statistics
    total_tasks = len(all_tasks)
    completed_tasks = len([task for task in all_tasks if task.status == 'Completed'])
    pending_tasks = len([task for task in all_tasks if task.status == 'Pending'])
    
    return render_template('summary.html', 
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)