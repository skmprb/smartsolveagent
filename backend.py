from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from token_vault import TokenVault
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Allow HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
CORS(app)
vault = TokenVault()

REDIRECT_URI = "http://localhost:5000/callback"

def create_flow():
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client-secret.json",
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email", 
            "openid", 
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/tasks",
            "https://www.googleapis.com/auth/contacts.readonly"
        ],
        redirect_uri=REDIRECT_URI
    )

@app.route('/auth')
def auth():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline", 
        include_granted_scopes="true",
        prompt="select_account"
    )
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    try:
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Get user info to use email as key
        credentials = flow.credentials
        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')
        
        # Store tokens using email as key
        vault.store_token(user_email, flow.credentials)
        
        # Redirect back to frontend with email
        return redirect(f"http://localhost:3000?user_email={user_email}")
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        return f"Authentication failed: {str(e)}", 400

@app.route('/token/<user_email>')
def get_token(user_email):
    credentials = vault.get_token(user_email)
    if credentials:
        return jsonify({"access_token": credentials.token})
    return jsonify({"error": "Token not found"}), 404

if __name__ == '__main__':
    app.run(port=5000, debug=True)