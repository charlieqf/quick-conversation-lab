"""
Voice Model Lab - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import models, websocket, history, users, data_manage
from app.database import engine
from app import models as db_models

# Init DB tables
db_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Voice Model Lab API",
    description="Backend API for multi-model voice conversation testing",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(users.router, prefix="/api/user", tags=["users"])
app.include_router(data_manage.router, prefix="/api/data", tags=["data"])


@app.get("/")
async def root():
    return {"message": "Voice Model Lab API", "version": "0.1.0"}

@app.get("/api/debug/config")
async def debug_config():
    """Debug endpoint to verify Cloud Run environment"""
    import os
    import socket
    key = settings.gemini_api_key
    
    # Connection Test
    conn_result = "Skipped"
    try:
        # Simple TCP check to googleapicapis
        host = "generativelanguage.googleapis.com"
        s = socket.create_connection((host, 443), timeout=2)
        s.close()
        conn_result = f"Success connecting to {host}:443"
    except Exception as e:
        conn_result = f"Failed to connect to {host}: {e}"

    openai_key = os.getenv("OPENAI_API_KEY")
    try:
        # Simple DNS check for openai
        socket.gethostbyname("api.openai.com")
        openai_conn = "DNS Resolved"
    except:
        openai_conn = "DNS Failed"

    return {
        "env_vars": {
            "GEMINI_API_KEY_LEN": len(key) if key else 0,
            "GEMINI_API_KEY_PREFIX": key[:4] if key else "None",
            "OPENAI_API_KEY_LEN": len(openai_key) if openai_key else 0,
            "OPENAI_API_KEY_PREFIX": openai_key[:7] if openai_key else "None",
            "GCP_PROJECT": os.getenv("GCP_PROJECT_ID", "Not Set"),
            "Is_Cloud_Run": os.getenv("K_SERVICE") is not None
        },
        "connectivity": {
             "google": conn_result,
             "openai": openai_conn
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
