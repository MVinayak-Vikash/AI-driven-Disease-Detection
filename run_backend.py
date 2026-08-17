"""
Quick Start Launcher for CardioNav AI Backend.
Automatically configures sys.path and launches Uvicorn server.
"""

import os
import sys
import uvicorn

# Ensure the project root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    print("=" * 65)
    print("🫀 Starting CardioNav AI Backend Server...")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print("🚀 API Documentation: http://localhost:8000/docs")
    print("=" * 65)
    
    # Run uvicorn server directly
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir=PROJECT_ROOT
    )
