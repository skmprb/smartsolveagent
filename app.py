import streamlit as st

# Check if user is logged in using Streamlit's built-in auth
if not st.user.is_logged_in:
    st.title("Welcome to SmartSolve!")
    st.write("Please log in with Google to continue.")
    st.button("Log in with Google", on_click=st.login)
    st.stop()
# Main Application - User is logged in
# Sidebar with user info and logout
with st.sidebar:
    st.write(f"👋 {st.user.name}")
    st.write(f"📧 {st.user.email}")
    if st.button("🚪 Log out"):
        st.logout()

# Main app content
st.title("🧠 SmartSolve")
st.write("What would you like to work on today?")

# Your main application features go here
tab1, tab2, tab3 = st.tabs(["📝 Tasks", "📊 Analytics", "⚙️ Settings"])

with tab1:
    st.write("Task management features")
    
with tab2:
    st.write("Analytics dashboard")
    
with tab3:
    st.write("Application settings")