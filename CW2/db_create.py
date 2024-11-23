from config import SQLALCHEMY_DATABASE_URI # noqa
from app import db
import os.path # noqa

db.create_all()
