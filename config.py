import os

# Environment-based configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://smartsolve-frontend-xxx.run.app')
    BACKEND_URL = os.getenv('BACKEND_URL', 'https://smartsolve-backend-xxx.run.app')
    AGENT_URL = os.getenv('AGENT_URL', 'https://smartsolve-agent-xxx.run.app')
    REDIRECT_URI = f"{BACKEND_URL}/callback"
else:
    FRONTEND_URL = "http://localhost:5173"
    BACKEND_URL = "http://localhost:5000"
    AGENT_URL = "http://localhost:8080"
    REDIRECT_URI = "http://localhost:5000/callback"

# Update OAuth redirect URI in Google Console with production URL
# Add: https://smartsolve-backend-xxx.run.app/callback