import os
from google.adk.cli.fast_api import get_fast_api_app
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure FastAPI application"""
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    allowed_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")

    return get_fast_api_app(
        agents_dir=agent_dir,
        session_service_uri=None,
        allow_origins=allowed_origins,
        web=True
    )

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host=host, port=port, reload=True)
