from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
import google_auth_oauthlib.flow
from token_vault import TokenVault
import uuid
import os

# Allow HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
CORS(app)
vault = TokenVault()

REDIRECT_URI = "http://localhost:5000/callback"

def create_flow():
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client-secret.json",
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/userinfo.profile"],
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
    flow = create_flow()
    flow.fetch_token(authorization_response=request.url)
    
    # Generate user session ID
    user_id = str(uuid.uuid4())
    
    # Store tokens
    vault.store_token(user_id, flow.credentials)
    
    # Redirect back to frontend with user_id
    return redirect(f"http://localhost:3000?user_id={user_id}")

@app.route('/token/<user_id>')
def get_token(user_id):
    credentials = vault.get_token(user_id)
    if credentials:
        return jsonify({"access_token": credentials.token})
    return jsonify({"error": "Token not found"}), 404

if __name__ == '__main__':
    app.run(port=5000, debug=True)