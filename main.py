# main.py
import os
from typing import Dict, List, Any

import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine

from google.adk.cli.fast_api import get_fast_api_app
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    allowed_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")

    return get_fast_api_app(
        agents_dir=os.path.dirname(os.path.abspath(__file__)),
        # agents_dir=os.getcwd(),
        session_service_uri=None,
        allow_origins=allowed_origins,
        web=True,
    )


app = create_app()


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/agent-info")
async def info() -> Dict[str, List[str]]:
    """Get agent information"""
    from smartsolve.agent import root_agent

    tools = [
        getattr(t, "name", type(t).__name__) for t in getattr(root_agent, "tools", [])
    ]
    return {"name": root_agent.name, "tools": tools}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    print(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )
