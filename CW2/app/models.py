from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Many-to-Many Relationship Table
user_crime = db.Table('user_crime',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('crime_id', db.Integer, db.ForeignKey('crime_report.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))
    home_address = db.Column(db.String(255))
    work_address = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(150))
    bookmarked_locations = db.Column(db.String(500))  # Can store multiple locations as a string
    notification_radius = db.Column(db.Float, default=1.0)  # Radius in km
    crime_preferences = db.Column(db.String(500), nullable=True, default="")  # Default value is an empty string

    def set_password(self, password):
        self.password = generate_password_hash(password)  # Corrected to use 'self.password'

    def check_password(self, password):
        return check_password_hash(self.password, password)  # Corrected to use 'self.password'

# CrimeReport Model
class CrimeReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Changed to nullable=True
    location = db.Column(db.String(150), nullable=False)
    date_reported = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class CrimeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    safety_tips = db.relationship('SafetyTip', backref='crime_type', lazy=True)

class SafetyTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    crime_type_id = db.Column(db.Integer, db.ForeignKey('crime_type.id'), nullable=False)

    def __repr__(self):
        return f"<SafetyTip {self.content}>"