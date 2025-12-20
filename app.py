import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests

def get_user_info(access_token):
    credentials = Credentials(token=access_token)
    service = build("oauth2", "v2", credentials=credentials)
    return service.userinfo().get().execute()

def main():
    st.set_page_config(page_title="Google OAuth App", page_icon="🔑")
    st.title("🔑 Google OAuth Login Demo")
    
    # Check for user_id from backend callback
    query_params = st.query_params
    user_id = query_params.get("user_id")
    
    # Debug info
    if user_id:
        st.info(f"Found user_id: {user_id}")
    
    if user_id and "user_info" not in st.session_state:
        # Get token from backend
        try:
            st.info(f"Fetching token for user: {user_id}")
            response = requests.get(f"http://localhost:5000/token/{user_id}")
            if response.status_code == 200:
                token_data = response.json()
                st.success("Token retrieved successfully!")
                user_info = get_user_info(token_data["access_token"])
                st.session_state.user_info = user_info
                st.rerun()
            else:
                st.error(f"Failed to get token: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Failed to retrieve user info: {str(e)}")
    
    # Display content based on authentication status
    if "user_info" in st.session_state:
        # User is logged in
        st.success("✅ Successfully logged in with Google!")
        
        # Display user details
        user = st.session_state.user_info
        
        # Create a nice card layout
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if "picture" in user:
                    st.image(user["picture"], width=120, caption="Profile Picture")
                else:
                    st.write("👤 No profile picture")
            
            with col2:
                st.subheader(f"Welcome, {user.get('name', 'User')}! 👋")
                
                # User information in a clean format
                st.markdown("### Account Information")
                info_data = {
                    "📧 Email": user.get('email', 'N/A'),
                    "🆔 Google ID": user.get('id', 'N/A'),
                    "✅ Verified Email": "Yes" if user.get('verified_email') else "No",
                    "🌐 Locale": user.get('locale', 'N/A')
                }
                
                for label, value in info_data.items():
                    st.write(f"**{label}:** {value}")
        
        # Additional features section
        st.markdown("---")
        st.subheader("🔧 Available Actions")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Token", help="Refresh your authentication token"):
                st.info("Token refresh functionality can be implemented here")
        
        with col2:
            if st.button("📊 View Raw Data", help="Show raw user data from Google"):
                st.json(user)
        
        with col3:
            if st.button("🚪 Logout", type="primary", help="Sign out of your account"):
                del st.session_state.user_info
                st.rerun()
    
    else:
        # User is not logged in
        st.info("Please log in with your Google account to continue.")
        
        # Login link instead of button for better reliability
        st.markdown(
            '<a href="http://localhost:5000/auth" target="_self" style="display: inline-block; padding: 0.5rem 1rem; background-color: #ff4b4b; color: white; text-decoration: none; border-radius: 0.25rem; font-weight: bold;">🔑 Sign in with Google</a>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()