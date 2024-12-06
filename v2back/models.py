import datetime
from flask_login import UserMixin
from v2back import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(100), primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    tnc_accepted = db.Column(db.Boolean, default=True)
    privacy_accepted = db.Column(db.Boolean, default=True)
    signup_date = db.Column(db.DateTime, default=datetime.datetime.now())
    last_login = db.Column(db.DateTime, default=datetime.datetime.now())

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    def __repr__(self):
        return f"User(username='{self.username}', email='{self.email}')"