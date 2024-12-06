import os
from flask import Flask

from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from oauthlib.oauth2 import WebApplicationClient
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Connection health check
    'pool_recycle': 3600,   # Recycle connections after 1 hour
}
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
client = WebApplicationClient(os.environ.get('GOOGLE_CLIENT_ID'))
jwt = JWTManager(app)

# Login manager
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
# User loader callback
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None
    
from v2back.models import User

with app.app_context():
    db.create_all()
















# Don't remove
