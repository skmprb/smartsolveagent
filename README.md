# Google OAuth Streamlit App

A minimal Streamlit application with Google OAuth login/logout functionality.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add `http://localhost:8501` to authorized redirect URIs
   - Download the JSON file and rename it to `client-secret.json`

4. Run the app:
```bash
streamlit run app.py
```

## Features

- Google OAuth login/logout
- Display user profile information
- Session management
- Responsive UI