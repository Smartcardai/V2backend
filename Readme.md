## Run the app
`uvicorn app.app:app --reload`

### ENV
create .env file in same level as /app folder
```sh
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=       
DATABASE_URL=mysql+mysqlconnector://wwwsmart:d7Jso5AOk2a@smartcardai.com/wwwsmart_users_creds
SECRET_KEY=     # random string for security
OAUTHLIB_INSECURE_TRANSPORT=1 # For bypassing http error, development only, OAuth requires https in production. Remove this
LLM_KEY=    # not used as of now
ACCESS_TOKEN_EXPIRE_HOURS=2     # change as needed. for jwt tokens
```

* GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET required for OAuth.
* Get these at https://console.cloud.google.com/apis/credentials
* Create OAuth 2.0 Client ID
   

### Accessing home route
* API should have a header with:\
"key": "Authorization",\
"value": "Bearer <access_token_generated_by_login>"


### Logout
* Frontend should clear the token from localStorage or cookies
* Example if the JWT is stored in localStorage
`localStorage.removeItem('access_token');`
* Example if the JWT is stored in cookies
`document.cookie = 'access_token=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';`