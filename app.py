import streamlit as st
import requests
from urllib.parse import urlencode
import json
import os

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
REDIRECT_URI = "http://localhost:8501"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def get_google_auth_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline"
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

def get_google_token(code):
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    return response.json()

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
    return response.json()

def main():
    st.set_page_config(page_title="Google OAuth App", page_icon="🔐")
    st.title("🔐 Google OAuth Login Demo")
    
    # Initialize session state
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # Check for authorization code in URL
    query_params = st.query_params
    if "code" in query_params and st.session_state.user_info is None:
        code = query_params["code"]
        try:
            token_data = get_google_token(code)
            if "access_token" in token_data:
                user_info = get_user_info(token_data["access_token"])
                st.session_state.user_info = user_info
                st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
    
    # Display content based on authentication status
    if st.session_state.user_info:
        # User is logged in
        st.success("✅ Successfully logged in!")
        
        # Display user details
        user = st.session_state.user_info
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if "picture" in user:
                st.image(user["picture"], width=100)
        
        with col2:
            st.subheader("User Details")
            st.write(f"**Name:** {user.get('name', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")
            st.write(f"**ID:** {user.get('id', 'N/A')}")
        
        # Logout button
        if st.button("🚪 Logout", type="primary"):
            st.session_state.user_info = None
            st.rerun()
    
    else:
        # User is not logged in
        st.info("Please log in with your Google account to continue.")
        
        auth_url = get_google_auth_url()
        st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#4285f4;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">🔑 Login with Google</button></a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()