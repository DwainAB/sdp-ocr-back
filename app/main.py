from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints import ocr

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for PDF OCR processing with Mistral",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to SDP OCR Backend",
        "description": "PDF handwriting OCR service using Mistral",
        "endpoints": {
            "health": "/health",
            "upload_pdf": "/api/v1/ocr/upload-pdf"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SDP OCR Backend"}