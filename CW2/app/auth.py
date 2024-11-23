from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from app.forms import LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(username) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        else:
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Account created!', category='success')
            return redirect(url_for('views.dashboard'))  # Redirect to the dashboard

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('views.dashboard'))  # Redirect to the dashboard
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='success')
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)