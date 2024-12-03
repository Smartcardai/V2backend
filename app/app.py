import datetime
import uuid
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Security
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import requests
from oauthlib.oauth2 import WebApplicationClient
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
import dotenv
import uvicorn
dotenv.load_dotenv()

templates = Jinja2Templates(directory="templates")
# Environment Variables (you should use .env file or environment)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
DATABASE_URL = os.getenv('DATABASE_URL')  # e.g., 'mysql+mysqlconnector://user:password@host/database'
SECRET_KEY = os.getenv('SECRET_KEY')

# SQLAlchemy Setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(100), primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(100))
    email = Column(String(100), unique=True)
    tnc_accepted = Column(Boolean, default=True)
    privacy_accepted = Column(Boolean, default=True)
    signup_date = Column(DateTime, default=datetime.datetime.now())
    last_login = Column(DateTime, default=datetime.datetime.now())
    

# Pydantic Models for Type Hints
class UserCreate(BaseModel):
    id: str
    username: str = None
    password: str = None
    email: str
    tnc_accepted: bool = True
    privacy_accepted: bool = True

# FastAPI App and Login Manager
app = FastAPI()
login_manager = LoginManager(SECRET_KEY, token_url='/login')

# OAuth Client
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def check_authentication(token: str = Security(oauth2_scheme)):
    try:
        payload = login_manager.decode_token(token)
        if payload:
            return True
    except Exception:
        return False
    return False

# User Loader for Login Manager
@login_manager.user_loader()
def load_user(user_id: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()

@app.get('/')
async def root(request: Request, db: Session = Depends(get_db)):
    # token = request.cookies.get('access_token')
    # if token:
    #     try:
    #         payload = login_manager.decode_token(token)
    #         user_id = payload.get("sub")
    #         if user_id is not None:
    #             user = db.query(User).filter(User.id == user_id).first()
    #             if user is not None:
    #                 return RedirectResponse(url='/home')
    #     except Exception as e:
    #         print(e)
    #         pass
    return RedirectResponse(url='/login')

@app.get('/register')
async def register(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})

from fastapi import HTTPException

@app.post('/register')
async def register_post(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.json()  # Expecting JSON payload
    except:
        form_data = await request.form()  # Fallback to form data

    user_data = {
        'id': uuid.uuid4().hex,
        'username': form_data['username'],
        'email': form_data['email'],
        'password': form_data['password'], 
        'tnc_accepted': 'tnc_accepted' in form_data,
        'privacy_accepted': 'privacy_accepted' in form_data
    }
    
    # Check if username or email already exists
    username_exist = db.query(User).filter(User.username == form_data.get('username')).first() is not None
    email_exist = db.query(User).filter(User.email == form_data.get('email')).first() is not None
    
    if username_exist:
        if request.headers.get('content-type') == 'application/json':
            raise HTTPException(status_code=400, detail="Username already exists!")
        return templates.TemplateResponse('register.html', {'request': request, 'message': 'Username already exists!'})
    if email_exist:
        if request.headers.get('content-type') == 'application/json':
            raise HTTPException(status_code=400, detail="Email already exists!")
        return templates.TemplateResponse('register.html', {'request': request, 'message': 'Email already exists!'})

    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if request.headers.get('content-type') == 'application/json':
        return {"message": "User created successfully!"}
    
    return RedirectResponse('/login', status_code=303)


@app.get('/login')
async def login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@app.post('/login')
async def login_post(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    if 'login_form' in form_data:
        # Check credentials
        user = db.query(User).filter(User.username == form_data['username']).first()
        if not user or user.password != form_data['password']:
            raise InvalidCredentialsException
        # Create access token
        access_token = login_manager.create_access_token(
            data=dict(sub=user.id)
        )
        # Redirect with token
        response = RedirectResponse(url="/home")
        login_manager.set_cookie(response, access_token)
        return response
    
    if 'oauth' in form_data:
        # Find the Google provider configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
        # Generate the URL to request access from Google's OAuth 2.0 server
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri="http://localhost:8000/login/callback",
            scope=["openid", "email", "profile"],
        )
        return RedirectResponse(url=request_uri, status_code=303)
    return templates.TemplateResponse('login.html', {'request': request})

@app.get("/login/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    # Get authorization code Google sent back
    code = request.query_params.get("code")

    # Fetch Google provider configuration
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=str(request.url),
        redirect_url=str(request.base_url) + "login/callback",
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens
    client.parse_request_body_response(token_response.text)

    # Get user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Verify email
    if userinfo_response.json().get("email_verified"):
        user_data = {
            'id': userinfo_response.json()["sub"],
            'email': userinfo_response.json()["email"]
        }

        # Check if user exists, if not create
        existing_user = db.query(User).filter(User.email == user_data['email']).first()
        
        if not existing_user:
            # Create new user
            new_user = User(**user_data)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
        else:
            user = existing_user

        # Create access token
        access_token = login_manager.create_access_token(
            data=dict(sub=user.id)
        )

        # Redirect with token
        response = RedirectResponse(url="/home")
        login_manager.set_cookie(response, access_token)
        
        return response
    
    # If verification fails
    raise HTTPException(status_code=400, detail="Google OAuth failed")

@app.get('/home')
async def home(request: Request):
    return templates.TemplateResponse('home.html', {'request': request})

@app.post('/home')
async def home_post(request: Request):
    return templates.TemplateResponse('home.html', {'request': request})


@app.get('/logout')
async def logout():
    response = RedirectResponse(url='/login')
    login_manager.set_cookie(response, '')  # Clear the cookie
    return response

Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)