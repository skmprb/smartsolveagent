import streamlit as st

# Check if secrets are configured
try:
    secrets = st.secrets["auth"]
    if "YOUR_GOOGLE_CLIENT_ID" in secrets.client_id:
        st.error("Please configure your Google OAuth credentials in .streamlit/secrets.toml")
        st.stop()
except KeyError:
    st.error("Missing auth configuration in .streamlit/secrets.toml")
    st.stop()

# If user is not logged in yet
if not st.user.is_logged_in:
    st.title("Welcome to SmartSolve!")
    st.write("Please log in with Google to continue.")
    if st.button("Log in with Google"):
        st.login()
    st.stop()

# Logged-in UI
st.title(f"Welcome, {st.user.name}!")
st.write(f"Your email: {st.user.email}")

if st.button("Log out"):
    st.logout()