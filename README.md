# Streamlit Google OAuth App

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Google OAuth:
   - Go to Google Cloud Console → APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Web application)
   - Add redirect URI: `http://localhost:8501/oauth2callback`

3. Update `.streamlit/secrets.toml` with your credentials:
   ```toml
   [auth]
   redirect_uri = "http://localhost:8501/oauth2callback"
   cookie_secret = "YOUR_RANDOM_SECRET_STRING"
   client_id = "YOUR_GOOGLE_CLIENT_ID"
   client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

4. Run the app:
```bash
streamlit run app.py
```