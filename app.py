import streamlit as st

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = {'name': 'Demo User', 'email': 'demo@example.com'}

# Main app
if not st.session_state.logged_in:
    st.title("Welcome to SmartSolve!")
    st.write("Please log in to continue.")
    
    if st.button("Demo Login"):
        st.session_state.logged_in = True
        st.rerun()
else:
    # Main Application
    user = st.session_state.user_info
    
    # Sidebar with user info and logout
    with st.sidebar:
        st.write(f"👋 {user.get('name', 'User')}")
        st.write(f"📧 {user.get('email', 'N/A')}")
        if st.button("🚪 Log out"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
    
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