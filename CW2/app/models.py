from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# This creates a many-to-many relationship between users and crime reports
user_crime = db.Table('user_crime',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')), # noqa
    db.Column('crime_id', db.Integer, db.ForeignKey('crime_report.id'))
)


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))
    home_address = db.Column(db.String(255))
    work_address = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(150))
    bookmarked_locations = db.Column(db.String(500))
    notification_radius = db.Column(db.Float, default=1.0)
    crime_preferences = db.Column(db.String(500), nullable=True, default="")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# CrimeReport Model
class CrimeReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False)
    date_reported = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)


# CrimeType Model
class CrimeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    safety_tips = db.relationship('SafetyTip', backref='crime_type', lazy=True)


# SafetyTip Model
class SafetyTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    crime_type_id = db.Column(db.Integer, db.ForeignKey('crime_type.id'), nullable=False) # noqa

    def __repr__(self):
        return f"<SafetyTip {self.content}>"


# BlogPost Model
class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    crime_type = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # noqa
    author = db.relationship('User', backref='blog_posts', lazy=True)
