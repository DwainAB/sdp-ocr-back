#!/usr/bin/env python3
"""
Simple startup script for Render deployment
"""
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("python-dotenv not available, skipping .env loading")
except Exception as e:
    print(f"Error loading .env: {e}")

if __name__ == "__main__":
    import uvicorn

    # Get port from environment (Render provides this)
    port = int(os.environ.get("PORT", 8000))

    print(f"Starting server on 0.0.0.0:{port}")

    # Check if MISTRAL_API_KEY is set
    if not os.environ.get("MISTRAL_API_KEY"):
        print("WARNING: MISTRAL_API_KEY environment variable not set!")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )