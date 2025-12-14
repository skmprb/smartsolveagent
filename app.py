import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import os

REDIRECT_URI = "http://localhost:8501/"

def create_flow():
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            "client-secret.json",
            scopes=["https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/userinfo.profile"],
            redirect_uri=REDIRECT_URI
        )
        return flow
    except FileNotFoundError:
        st.error("client-secret.json file not found. Please download it from Google Cloud Console.")
        return None

def main():
    st.set_page_config(page_title="Google OAuth App", page_icon="🔐")
    st.title("🔐 Google OAuth Login Demo")
    
    # Initialize session state
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # Create OAuth flow
    flow = create_flow()
    if not flow:
        st.stop()
    
    # Check for authorization code in URL
    auth_code = st.query_params.get("code")
    
    if auth_code and st.session_state.user_info is None:
        try:
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Get user info
            user_info_service = build("oauth2", "v2", credentials=credentials)
            user_info = user_info_service.userinfo().get().execute()
            
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
        
        if st.button("🔑 Sign in with Google", type="primary"):
            authorization_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")
            st.markdown(f'<meta http-equiv="refresh" content="0; url={authorization_url}">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()