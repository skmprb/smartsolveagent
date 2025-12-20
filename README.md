# Google OAuth with Token Vault

Streamlit app with secure OAuth token management using Token Vault pattern.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Add `http://localhost:5000/callback` to authorized redirect URIs
   - Download JSON file as `client-secret.json`

3. Run backend service:
```bash
python backend.py
```

4. Run frontend (new terminal):
```bash
streamlit run app.py
```

## Architecture

- **Frontend**: Streamlit UI (port 8501)
- **Backend**: Flask OAuth service (port 5000)
- **Token Storage**: Local `tokens.json` file

## Usage

1. Click "Sign in with Google" → redirects to Flask backend
2. Complete OAuth flow → tokens stored securely
3. Redirected back to Streamlit with session ID
4. User info displayed using stored tokens

## Token Management

Tokens stored in `tokens.json` mapped by session UUID. Automatic refresh handling included.