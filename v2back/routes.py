import datetime
import os
import uuid
import requests
from v2back import app, db, bcrypt, jwt, client
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity 
from flask import jsonify, make_response, redirect, request
from v2back.models import User

@app.route('/')
def root():
    return jsonify({'message': 'Hello, World!'})

@app.route('/register', methods=['POST'])
def register():
    form_data = request.get_json()
    user_data = {
        'id': uuid.uuid4().hex,
        'username': form_data['username'],
        'email': form_data['email'],
        'password': form_data['password'],
        'tnc_accepted': 'tnc_accepted' in form_data and form_data['tnc_accepted'],
        'privacy_accepted': 'privacy_accepted' in form_data and form_data['privacy_accepted']
    }

    # Check if username or email already exists
    username_exist = User.query.filter_by(username=user_data['username']).first()
    email_exist = User.query.filter_by(email=user_data['email']).first()

    if username_exist:
        return make_response(jsonify({"detail": "Username already exists!"}), 400)
    if email_exist:
        return make_response(jsonify({"detail": "Email already exists!"}), 400)
    if not user_data['tnc_accepted'] or not user_data['privacy_accepted']:
        return make_response(jsonify({"detail": "Terms and Conditions or Privacy Policy not accepted"}), 400)

    user_data['password'] = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
    new_user = User(**user_data)
    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)
        return make_response(jsonify({"message": "User created successfully!"}))
    except Exception as e:
        db.session.rollback()
        print(f"Error saving user to the database: {e}")
        return make_response(jsonify({"detail": "Error saving user to the database"}), 500)
    
@app.route('/login', methods=['POST'])
def login_post():
    form_data = request.get_json()  # Expecting JSON payload
    
    # Check credentials
    user = User.query.filter_by(username=form_data['username']).first()
    if not user or not bcrypt.check_password_hash(user.password, form_data['password']):
        return make_response(jsonify({"detail": "Invalid username or password"}), 400)
    
    # Update last login
    user.last_login = datetime.datetime.now()
    db.session.commit()
    db.session.refresh(user)

    # Create access token
    access_token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer"
    })

def check_authentication(token: str):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = payload.get("sub")

        if user_id is None:
            return None, "Invalid token"
        
        # Fetch user from database
        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return None, "User not found"

        return user, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.PyJWTError:
        return None, "Invalid token"
    
@app.route('/home', methods=['GET'])
@jwt_required()  # This decorator ensures the user is authenticated
def home():
    try:
        # Get the current user's identity (user_id) from the JWT token
        current_user_id = get_jwt_identity()

        # Fetch the user from the database
        user = User.query.filter_by(id=current_user_id).first()

        if user is None:
            return make_response(jsonify({"msg": "User not found"}), 401)

        return jsonify({"message": "Welcome to the home page!", "user_email": user.email})

    except jwt.ExpiredSignatureError:
        # Token is expired
        return jsonify({"msg": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        # Invalid token
        return jsonify({"msg": "Invalid token"}), 401
    except Exception as e:
        # Catch all other exceptions and send a generic error
        return jsonify({"msg": "Invalid token"}), 401
    
@app.route('/login/oauth')
def login_oauth():
    google_provider_cfg = requests.get(os.environ.get('GOOGLE_DISCOVERY_URL')).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri= str(os.environ.get('WEBSITE_DOM')) + "login/oauth/callback",  # Adjust the callback URL
        scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

@app.route("/login/oauth/callback")
def oauth_callback():
    # Get authorization code
    code = request.args.get("code")
    google_provider_cfg = requests.get(os.environ.get('GOOGLE_DISCOVERY_URL')).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request for the token
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url= str(os.environ.get('WEBSITE_DOM')) + "api/login/oauth/callback",  # Same callback URL
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(os.getenv('GOOGLE_CLIENT_ID'), os.getenv('GOOGLE_CLIENT_SECRET')),
    )
    client.parse_request_body_response(token_response.text)

    # Fetch user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    user_info = userinfo_response.json()

    if user_info.get("email_verified"):
        user_data = {
            'id': user_info["sub"],
            'email': user_info["email"]
        }

        existing_user = db.session.query(User).filter(User.email == user_data['email']).first()
        if not existing_user:
            new_user = User(**user_data)
            db.session.add(new_user)
            db.session.commit()
            db.session.refresh(new_user)
            user = new_user
        else:
            user = existing_user

        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, token_type="bearer")

    return jsonify({"msg": "Google OAuth failed"}), 400

@app.route('/logout', methods=['POST'])
def logout():    
    # Frontend should clear the token from localStorage or cookies
    # Example if the JWT is stored in localStorage
        # localStorage.removeItem('access_token');
    # Example if the JWT is stored in cookies
        # document.cookie = 'access_token=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
    return {"message": "You have successfully logged out."}