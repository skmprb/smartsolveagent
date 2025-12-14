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

3. Update `.streamlit/secrets.toml` with your credentials

4. Run the app:
```bash
streamlit run app.py
```