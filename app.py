import streamlit as st
import requests
from urllib.parse import urlencode
import secrets as py_secrets

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# Get OAuth config
config = st.secrets["auth"]

# Handle OAuth callback
query_params = st.query_params
if 'code' in query_params and not st.session_state.logged_in:
    code = query_params['code']
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': config['redirect_uri']
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' in token_json:
            # Get user info
            user_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token_json["access_token"]}'}
            )
            st.session_state.user_info = user_response.json()
            st.session_state.logged_in = True
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

# Main app
if not st.session_state.logged_in:
    st.title("Welcome to SmartSolve!")
    st.write("Please log in with Google to continue.")
    
    if st.button("Log in with Google"):
        # Generate OAuth URL
        auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode({
            'client_id': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': py_secrets.token_urlsafe(32)
        })
        st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
else:
    # Logged in UI
    user = st.session_state.user_info
    st.title(f"Welcome, {user.get('name', 'User')}!")
    st.write(f"Your email: {user.get('email', 'N/A')}")
    
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()