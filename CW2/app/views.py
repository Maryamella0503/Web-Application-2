from flask import Blueprint, render_template, redirect
from flask import url_for, flash, request, jsonify
from flask_login import login_user, login_required, current_user
from app.models import User, CrimeReport, CrimeType, BlogPost
from app import db
import os
from flask import current_app
from app.analytics import predict_crime_hotspots
from werkzeug.security import generate_password_hash, check_password_hash
from app.fetch_crime_data_from_api import fetch_crime_data_from_api

views = Blueprint('views', __name__)
auth = Blueprint('auth', __name__)
blog = Blueprint('blog', __name__)


@views.route('/')
def home():
    try:
        # Attempt to fetch data from the API
        api_success = fetch_crime_data_from_api()
        data_source = "API" if api_success else "Backup CSV"
    except Exception as e: # noqa
        api_success = False
        data_source = "Backup CSV"

    # Load from backup CSV here if needed
    if not api_success:
        backup_csv_path = os.path.join(current_app.root_path, 'static', '2024-09-west-yorkshire-street.csv') # noqa
    crimes = CrimeReport.query.all()

    # Filter crimes based on user preferences if logged in
    if current_user.is_authenticated and current_user.crime_preferences:
        preferences = [pref.strip().lower() for pref in current_user.crime_preferences.split(',')] # noqa
        crimes = [crime for crime in crimes if crime.title.strip().lower() in preferences] # noqa

    crime_data = [
        {
            'latitude': crime.latitude,
            'longitude': crime.longitude,
            'title': crime.title,
            'description': crime.description,
            'location': crime.location,
            'date_reported': crime.date_reported.strftime('%Y-%m-%d')
        }
        for crime in crimes
    ]

    return render_template(
        'home.html',
        user=current_user if current_user.is_authenticated else None,
        data_source=data_source,
        crime_data=crime_data
    )


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Fetch form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Validate input
        if not username or len(username) < 2:
            flash('Username must be greater than 1 character', category='error') # noqa
            return render_template('register.html')
        if not email or len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
            return render_template('register.html')
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', category='error')
            return render_template('register.html')

        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
            return render_template('register.html')

        try:
            # Create a new user
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)  # Log in the user
            flash('Account created successfully!', category='success')
            return redirect(url_for('views.home'))
        except Exception as e: # noqa
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', category='error') # noqa
            return render_template('register.html')

    # Render registration page
    return render_template('register.html')


@views.route('/api/crime-data', methods=['GET'])
@login_required
def get_crime_data():
    preferences = current_user.crime_preferences.split(',') if current_user.crime_preferences else [] # noqa

    # Fetch crimes matching the user's preferences
    crimes = CrimeReport.query.filter(CrimeReport.title.in_(preferences)).all()

    data = [
        {
            'date_reported': crime.date_reported.strftime('%Y-%m'),
            'latitude': crime.latitude,
            'longitude': crime.longitude,
            'title': crime.title,
            'description': crime.description,
            'location': crime.location
        }
        for crime in crimes
    ]
    return jsonify(data)


@views.route('/api/crime-hotspots', methods=['GET'])
def get_crime_hotspots():
    hotspots = predict_crime_hotspots()
    return jsonify(hotspots)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', category='success')

            # Redirect to the home page instead of the dashboard
            return redirect(url_for('views.home'))
        else:
            flash('Login failed. Check your credentials.', category='error')
    return render_template('login.html')


@views.route('/dashboard')
@login_required
def dashboard():
    # Ensure crime_preferences is not None
    crime_preferences = current_user.crime_preferences or "" # noqa

    return render_template(
        'dashboard.html',
        user=current_user,
    )


@views.route('/update_user_info', methods=['POST'])
@login_required
def update_user_info():
    # Update user information from form inputs
    current_user.phone_number = request.form.get('phone_number')
    current_user.home_address = request.form.get('home_address')
    current_user.work_address = request.form.get('work_address')
    current_user.emergency_contact = request.form.get('emergency_contact')
    db.session.commit()
    flash('Your information has been updated!', 'success')
    return redirect(url_for('views.dashboard'))


@views.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    # Extract crime preferences from the form
    preferences = request.form.getlist('crime_preferences')
    if preferences:
        # Save preferences as a comma-separated string
        current_user.crime_preferences = ','.join(preferences)
        db.session.commit()
        flash('Preferences updated successfully!', 'success')
    else:
        flash('No preferences selected. Please choose at least one.', 'error')
    return redirect(url_for('views.dashboard'))


@views.route('/safety-tips', methods=['GET', 'POST'])
@login_required
def safety_tips():
    # Fetch all crime types for the dropdown
    crime_types = CrimeType.query.all()

    # Get the selected crime type from the query parameter
    selected_crime_type = request.args.get('crime_type')
    tips = []

    if selected_crime_type:
        crime_type = CrimeType.query.filter_by(name=selected_crime_type).first() # noqa
        if crime_type:
            tips = crime_type.safety_tips
        else:
            # Debugging output
            print(f"No matching crime type found for: {selected_crime_type}")

    return render_template(
        'safety_tips.html',
        user=current_user,  # Pass the current user
        crime_types=crime_types,
        selected_crime_type=selected_crime_type,
        tips=tips
    )


def populate_crime_types():
    sample_types = [
        "Robbery", "Assault", "Burglary", "Vehicle Crime", "Shoplifting",
        "Antisocial behaviour", "Arson", "Public Order", "Drugs",
        "Possession of weapons"
    ]
    for crime_name in sample_types:
        if not CrimeType.query.filter_by(name=crime_name).first():
            db.session.add(CrimeType(name=crime_name))
    db.session.commit()


@blog.route('/blog', methods=['GET', 'POST'])
@login_required
def blog_page():
    if request.method == 'POST':
        # Validate the presence of required fields
        title = request.form.get('title')
        location = request.form.get('location')
        description = request.form.get('description')
        crime_type = request.form.get('crime_type')

        # Ensure all fields are provided
        if not title or not location or not description or not crime_type:
            flash("Unable to delete post", "danger")
            return redirect(url_for('blog.blog_page'))

        # Create a new blog post
        new_post = BlogPost(
            title=title,
            location=location,
            description=description,
            crime_type=crime_type,
            created_by=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()

        flash("New post created successfully!", "success")
        return redirect(url_for('blog.blog_page'))

    # Fetch posts based on crime type filter
    crime_filter = request.args.get('crime_type')
    posts = BlogPost.query.filter_by(crime_type=crime_filter).all() if crime_filter else BlogPost.query.all() # noqa

    # Prepare posts with author username
    posts_with_usernames = [
        {
            'id': post.id,
            'title': post.title,
            'location': post.location,
            'description': post.description,
            'crime_type': post.crime_type,
            'username': post.author.username if post.author else "Unknown Author" # noqa
        }
        for post in posts
    ]
    return render_template('blog.html', posts=posts_with_usernames)


@blog.route('/api/blog-posts', methods=['GET'])
def get_blog_posts():
    crime_type = request.args.get('crime_type')  # Get crime_type from query

    if crime_type:
        # Filter posts by crime type
        posts = BlogPost.query.filter_by(crime_type=crime_type).all()
    else:
        posts = BlogPost.query.all()

    # Serialize posts for JSON response
    posts_data = [
        {
            'id': post.id,
            'title': post.title,
            'location': post.location,
            'description': post.description,
            'crime_type': post.crime_type,
            'author': post.author.username if post.author else 'Unknown',
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for post in posts
    ]
    return jsonify(posts_data)


# Route to delete a blog post
@blog.route('/delete_post/<int:post_id>', methods=['POST', 'GET'])
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if post.created_by != current_user.id:
        flash("You don't have permission to delete this post.", "danger")
        return redirect(url_for('blog.blog_page'))

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully.", "success")
    return redirect(url_for('blog.blog_page'))
