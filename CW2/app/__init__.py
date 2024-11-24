from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config

# Initialize extensions (do not attach them to the app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    # Import Blueprints inside the function to avoid circular imports
    from app.views import views,blog
    from app.auth import auth
    from app.api import api
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(blog, url_prefix='/blog')

    # Configure mail server settings
    app.config['MAIL_SERVER'] = 'smtp.example.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@example.com'
    app.config['MAIL_PASSWORD'] = 'your-email-password'

    # Add the user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    def seed_crime_types():
        """Populate the CrimeType table with default values."""
        from app.models import CrimeType  # Import model inside the function to avoid circular imports
        sample_types = [
            "Theft", "Assault", "Burglary", "Vehicle Crime", "Shoplifting",
            "Antisocial behaviour", "Arson", "Public Order", "Drugs", "Possession of weapons"
        ]
        for crime_name in sample_types:
            if not CrimeType.query.filter_by(name=crime_name).first():
                db.session.add(CrimeType(name=crime_name))
                print(f"Added Crime Type: {crime_name}")  # Debugging output
        db.session.commit()
        print("Crime types populated!")  # Confirmation message

    # Initialize database and scheduler
    with app.app_context():
        try:
            # Create database tables
            db.create_all()
            seed_crime_types()

            # Load crime data
            from app.populate_crime_data import load_crime_data
            crime_data_path = '/Users/maryamellathy/Desktop/Web Application 2/CW2/app/static/2024-09-west-yorkshire-street.csv'
            load_crime_data(crime_data_path)

            # Schedule crime alerts (only if not already running)
            from app.check_for_crime_alerts import check_for_crime_alerts
            if not scheduler.running:
                scheduler.add_job(func=check_for_crime_alerts, trigger="interval", minutes=10)
                scheduler.start()

        except Exception as e:
            app.logger.error(f"Error during app initialization: {e}")

    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        """Shutdown the scheduler when the app context is torn down."""
        if scheduler.running:
            scheduler.shutdown(wait=False)

    return app