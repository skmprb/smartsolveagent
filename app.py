import streamlit as st

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