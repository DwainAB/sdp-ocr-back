from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints import ocr, customers, users
from app.db.connection import get_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for PDF OCR processing with Mistral",
    version="1.0.0"
)

test = get_connection()
test

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sdp-ocr-front.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to SDP OCR Backend",
        "description": "PDF handwriting OCR service using Mistral",
        "endpoints": {
            "health": "/health",
            "upload_pdf": "/api/v1/ocr/upload-pdf",
            "customers": "/api/v1/customers",
            "users": "/api/v1/users",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SDP OCR Backend"}

# For Render deployment
if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )