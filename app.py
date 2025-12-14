import streamlit as st

st.title("Configuration Check")

# Check if secrets are configured
try:
    secrets = st.secrets["auth"]
    st.write("✅ Secrets loaded successfully")
    
    # Check each required field
    required_fields = ["client_id", "client_secret", "redirect_uri", "cookie_secret"]
    for field in required_fields:
        if field in secrets:
            if "YOUR_" in str(secrets[field]):
                st.error(f"❌ {field} still has placeholder value")
            else:
                st.write(f"✅ {field} configured")
        else:
            st.error(f"❌ Missing {field}")
            
except Exception as e:
    st.error(f"❌ Error loading secrets: {e}")
    st.stop()

st.write("---")
st.write("If all fields show ✅, try the login:")

# Simple login test
if st.button("Test Login"):
    try:
        st.login()
    except Exception as e:
        st.error(f"Login error: {e}")