from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, CrimeReport, CrimeType, SafetyTip, BlogPost
from app.forms import RegistrationForm, LoginForm
from app import db, mail, create_app
import os
from flask import current_app
from flask_mail import Message
from app.analytics import predict_crime_hotspots
from app.populate_crime_data import load_crime_data
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from geopy.distance import geodesic
from datetime import datetime
from app.populate_crime_data import load_crime_data
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
    except Exception as e:
        api_success = False
        data_source = "Backup CSV"

    # Load from backup CSV here if needed
    if not api_success:
        backup_csv_path = os.path.join(current_app.root_path, 'static', '2024-09-west-yorkshire-street.csv')
        
    crimes = CrimeReport.query.all()

    # Filter crimes based on user preferences if logged in
    if current_user.is_authenticated and current_user.crime_preferences:
        preferences = [pref.strip().lower() for pref in current_user.crime_preferences.split(',')]
        crimes = [crime for crime in crimes if crime.title.strip().lower() in preferences]

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
            flash('Username must be greater than 1 character.', category='error')
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
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', category='error')
            return render_template('register.html')

    # Render registration page
    return render_template('register.html')

@views.route('/api/crime-data', methods=['GET'])
@login_required
def get_crime_data():
    preferences = current_user.crime_preferences.split(',') if current_user.crime_preferences else []

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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        # Login logic
        pass
    return render_template('login.html')
    

@views.route('/send-emergency-alert', methods=['POST'])
@login_required
def send_emergency_alert():
    user_location = request.form.get('user_location')
    message = f"Emergency alert from {current_user.email}. Last known location: {user_location}"
    send_crime_alert_email(current_user.emergency_contact, message)
    return "Alert sent!"

@views.route('/dashboard')
@login_required
def dashboard():
    # Ensure crime_preferences is not None
    crime_preferences = current_user.crime_preferences or ""  # Default to an empty string
    recommendations = get_safety_recommendations(current_user)

    return render_template(
        'dashboard.html',
        user=current_user,
        recommendations=recommendations,
    )

@views.route('/update_user_info', methods=['POST'])
@login_required
def update_user_info():
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
    preferences = request.form.getlist('crime_preferences')  # Extract selected preferences
    if preferences:
        # Save preferences as a comma-separated string
        current_user.crime_preferences = ','.join(preferences)
        db.session.commit()
        flash('Preferences updated successfully!', 'success')
    else:
        flash('No preferences selected. Please choose at least one.', 'error')
    return redirect(url_for('views.dashboard'))

def send_crime_alert_email(user_email, crime_details):
    msg = Message(
        "Crime Alert!",
        sender="your-email@example.com",
        recipients=[user_email]
    )
    msg.body = f"A crime has been reported near your location: {crime_details}"
    mail.send(msg)
    
def check_for_crime_alerts():
    app = create_app()  # Create the app instance
    with app.app_context():  # Use the app context
        users = User.query.all()
        crimes = CrimeReport.query.all()

        for user in users:
            if not user.bookmarked_locations:
                continue  # Skip users without bookmarked locations
            
            user_coords = tuple(map(float, user.bookmarked_locations.split(',')))
            preferences = user.crime_preferences.split(',') if user.crime_preferences else []

            for crime in crimes:
                if crime.title not in preferences:
                    continue  # Skip crimes not in user's preferences
                
                crime_coords = (crime.latitude, crime.longitude)
                distance = geodesic(user_coords, crime_coords).km

                if distance <= user.notification_radius:
                    crime_details = (
                        f"{crime.title} reported at {crime.location} on {crime.date_reported.strftime('%Y-%m-%d')}"
                    )
                    send_crime_alert_email(user.email, crime_details)

scheduler = BackgroundScheduler()
scheduler.add_job(check_for_crime_alerts, 'interval', minutes=5)
scheduler.start()

def send_crime_summary():
    users = User.query.filter_by(summary_preference='daily').all()
    today = datetime.now().date()
    crimes_today = CrimeReport.query.filter(CrimeReport.date == today).all()

    for user in users:
        crime_details = "\n".join([f"{crime.title}: {crime.description}" for crime in crimes_today])
        send_crime_alert_email(user.email, crime_details)

scheduler.add_job(send_crime_summary, 'cron', hour=8)

# Add at the bottom of views.py
import logging
from app import create_app
from geopy.distance import geodesic
from app.models import User, CrimeReport
from app.email import send_crime_alert_email

logging.basicConfig(level=logging.INFO)

def check_for_crime_alerts():
    logging.info("Starting alert check...")
    with current_app.app_context():
        users = User.query.all()
        crimes = CrimeReport.query.all()
        for user in users:
            logging.info(f"Checking for user: {user.email}")
            if user.bookmarked_locations:
                user_coords = tuple(map(float, user.bookmarked_locations.split(',')))
                for crime in crimes:
                    crime_coords = (crime.latitude, crime.longitude)
                    distance = geodesic(user_coords, crime_coords).km
                    logging.info(f"Distance to crime: {distance} km")
                    if distance <= user.notification_radius:
                        logging.info(f"Alert triggered for {user.email}")
                        send_crime_alert_email(
                            user.email,
                            f"{crime.title} reported at {crime.location} on {crime.date_reported.strftime('%Y-%m-%d')}"
                        )

@views.route('/test-alerts')
def test_alerts():
    from app.models import User, CrimeReport

    # Create a test user
    test_user = User(
        username="Test User",
        email="testuser@example.com",
        bookmarked_locations="51.505,-0.09",  # Mock coordinates
        notification_radius=1  # 1 km radius
    )

    # Mock crimes data
    test_crime = CrimeReport(
        latitude=51.505,
        longitude=-0.09,
        title="Mock Crime",
        description="This is a test crime alert",
        location="Mock Location",
        date_reported=datetime.now()
    )

    # Simulate alert logic
    user_coords = tuple(map(float, test_user.bookmarked_locations.split(',')))
    crime_coords = (test_crime.latitude, test_crime.longitude)
    distance = geodesic(user_coords, crime_coords).km

    if distance <= test_user.notification_radius:
        alert_message = f"ALERT: {test_crime.title} at {test_crime.location}, {distance} km away."
        return jsonify({"alert": alert_message})

    return jsonify({"message": "No alerts triggered."})

@views.route('/trigger-alerts')
def trigger_alerts():
    check_for_crime_alerts()
    return "Alerts triggered!"

def get_safety_recommendations(user):
    # Check if the user has bookmarked locations
    if not user.bookmarked_locations:
        return ["No bookmarked locations found. Please add a location to receive safety recommendations."]

    try:
        user_coords = tuple(map(float, user.bookmarked_locations.split(',')))
    except (ValueError, TypeError):
        return ["Invalid bookmarked location format. Please update your location settings."]

    crimes = CrimeReport.query.all()
    crime_types = {}

    for crime in crimes:
        crime_coords = (crime.latitude, crime.longitude)
        distance = geodesic(user_coords, crime_coords).km
        if distance <= user.notification_radius:
            crime_types[crime.title] = crime_types.get(crime.title, 0) + 1

    recommendations = []
    if 'Anti-social behaviour' in crime_types:
        recommendations.append("Avoid crowded areas and report any disturbances to the authorities.")
    if 'Criminal damage and arson' in crime_types:
        recommendations.append("Secure your property and ensure fire alarms are functional.")
    if 'Violence and sexual offences' in crime_types:
        recommendations.append("Avoid poorly lit areas and consider carrying personal safety devices.")
    if 'Other crime' in crime_types:
        recommendations.append("Be cautious and report any suspicious activity.")
    if 'Public order' in crime_types:
        recommendations.append("Stay away from large gatherings or protests that could escalate.")
    if 'Vehicle crime' in crime_types:
        recommendations.append("Park in well-lit areas and use anti-theft devices for your vehicle.")
    if 'Shoplifting' in crime_types:
        recommendations.append("Be vigilant while shopping and report any suspicious activities.")
    if 'Burglary' in crime_types:
        recommendations.append("Ensure your doors and windows are locked and consider installing security cameras.")
    if 'Other theft' in crime_types:
        recommendations.append("Keep your belongings secure and avoid displaying valuables in public.")
    if 'Bicycle theft' in crime_types:
        recommendations.append("Use sturdy locks and park your bicycle in monitored areas.")
    if 'Drugs' in crime_types:
        recommendations.append("Report any drug-related activity to the authorities immediately.")
    if 'Robbery' in crime_types:
        recommendations.append("Avoid carrying large sums of money and remain alert in public places.")
    if 'Theft from the person' in crime_types:
        recommendations.append("Keep your belongings close and avoid distractions while in public.")
    if 'Possession of weapons' in crime_types:
        recommendations.append("Stay alert and report any suspicious activity to the authorities.")

    return recommendations or ["No significant crimes found near your location."]

@views.route('/safety-tips', methods=['GET', 'POST'])
@login_required
def safety_tips():
    # Fetch all crime types for the dropdown
    crime_types = CrimeType.query.all()

    # Get the selected crime type from the query parameter
    selected_crime_type = request.args.get('crime_type')
    tips = []

    if selected_crime_type:
        crime_type = CrimeType.query.filter_by(name=selected_crime_type).first()
        if crime_type:
            tips = crime_type.safety_tips  # Fetch safety tips linked to the crime type
        else:
            print(f"No matching crime type found for: {selected_crime_type}")  # Debugging output

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
        "Antisocial behaviour", "Arson", "Public Order", "Drugs", "Possession of weapons"
    ]
    for crime_name in sample_types:
        if not CrimeType.query.filter_by(name=crime_name).first():
            db.session.add(CrimeType(name=crime_name))
    db.session.commit()

@views.route('/debug-crime-types')
def debug_crime_types():
    crime_types = CrimeType.query.all()
    return jsonify([crime_type.name for crime_type in crime_types])

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
            flash("All fields are required to create a new post.", "danger")
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
    posts = BlogPost.query.filter_by(crime_type=crime_filter).all() if crime_filter else BlogPost.query.all()

    # Prepare posts with author username
    posts_with_usernames = [
        {
            'id': post.id,
            'title': post.title,
            'location': post.location,
            'description': post.description,
            'crime_type': post.crime_type,
            'username': post.author.username if post.author else "Unknown Author"
        }
        for post in posts
    ]
    return render_template('blog.html', posts=posts_with_usernames)

@blog.route('/api/blog-posts', methods=['GET'])
def get_blog_posts():
    crime_type = request.args.get('crime_type')  # Get crime_type from query params

    if crime_type:
        posts = BlogPost.query.filter_by(crime_type=crime_type).all()  # Filter posts
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

@blog.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # Ensure the current user is the author of the post
    if post.created_by != current_user.id:
        flash("You don't have permission to delete this post.", "danger")
        return redirect(url_for('blog.blog_page'))

    # Delete the post
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully.", "success")
    return redirect(url_for('blog.blog_page'))