from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response, FileResponse
from typing import List
import os
import uuid
from datetime import datetime

from app.core.mistral_client import mistral_ocr_client
from app.utils.document_classifier import document_classifier
from app.utils.data_extractor import data_extractor
from app.utils.csv_generator import csv_generator
from app.schemas.ocr_schemas import OCRResponse, ProcessedPage, DocumentType

router = APIRouter()

GENERATED_DIR = "generated_files"


# ======================================================================
# OCR JSON (debug / API)
# ======================================================================

@router.post("/upload-pdf")
async def upload_pdf_for_ocr(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        pdf_content = await file.read()
        if not pdf_content or len(pdf_content) < 100:
            raise HTTPException(status_code=400, detail="Invalid or empty PDF")

        try:
            # Traiter le PDF complet avec Mistral OCR
            raw_text = await mistral_ocr_client.process_pdf_ocr(pdf_content)
            doc_type, confidence = document_classifier.classify_document(raw_text)
            extracted_data = data_extractor.extract_data(raw_text, doc_type)

            # Créer une seule "page" représentant tout le PDF
            processed_page = ProcessedPage(
                page_number=1,
                document_type=doc_type,
                confidence=confidence,
                raw_text=raw_text,
                extracted_data=extracted_data,
            )

            total_blank_sheets = 1 if doc_type == DocumentType.BLANK_SHEET else 0
            total_studio_parfums = 1 if doc_type == DocumentType.STUDIO_PARFUMS else 0

            summary = {
                "total_pages": 1,
                "blank_sheets": total_blank_sheets,
                "studio_parfums_sheets": total_studio_parfums,
                "unknown_sheets": 1 if doc_type == DocumentType.UNKNOWN else 0,
                "processing_errors": 1 if doc_type == DocumentType.UNKNOWN else 0,
            }

            response = OCRResponse(
                success=True,
                filename=file.filename,
                total_pages=1,
                processed_pages=[processed_page],
                summary=summary,
            )

        except Exception as e:
            # En cas d'erreur OCR
            processed_page = ProcessedPage(
                page_number=1,
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                raw_text=f"Error: {str(e)}",
                extracted_data={},
            )

            response = OCRResponse(
                success=True,
                filename=file.filename,
                total_pages=1,
                processed_pages=[processed_page],
                summary={"total_pages": 1, "processing_errors": 1},
            )

        return response.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


# ======================================================================
# OCR → CSV (PRODUCTION)
# ======================================================================

@router.post("/upload-pdf-csv")
async def upload_pdf_and_download_csv(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        pdf_content = await file.read()
        if not pdf_content or len(pdf_content) < 100:
            raise HTTPException(status_code=400, detail="Invalid or empty PDF")

        # ✅ s'assurer que le dossier existe
        os.makedirs(GENERATED_DIR, exist_ok=True)

        # Traiter le PDF complet avec Mistral OCR
        raw_text = await mistral_ocr_client.process_pdf_ocr(pdf_content)
        doc_type, confidence = document_classifier.classify_document(raw_text)
        extracted_data = data_extractor.extract_data(raw_text, doc_type)

        # Créer une seule "page" représentant tout le PDF
        processed_pages = [{
            "page_number": 1,
            "document_type": doc_type.value,
            "confidence": confidence,
            "raw_text": raw_text,
            "extracted_data": extracted_data,
        }]

        csv_content = csv_generator.generate_studio_parfums_csv(processed_pages)

        if not csv_content.strip() or csv_content.count("\n") <= 1:
            raise HTTPException(
                status_code=404,
                detail="No Studio des Parfums forms found in this PDF"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_name = file.filename.replace(".pdf", "").replace(" ", "_")
        csv_filename = f"studio_parfums_{base_name}_{timestamp}_{unique_id}.csv"

        file_path = os.path.join(GENERATED_DIR, csv_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        return {
            "success": True,
            "filename": csv_filename,
            "download_url": f"/api/v1/ocr/download/{csv_filename}",
            "total_studio_parfums_found": 1 if doc_type == DocumentType.STUDIO_PARFUMS else 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


# ======================================================================
# DOWNLOAD CSV
# ======================================================================

@router.get("/download/{filename}")
async def download_csv(filename: str):
    file_path = os.path.join(GENERATED_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/csv; charset=utf-8"
    )


# ======================================================================
# LIST FILES
# ======================================================================

@router.get("/list-files")
async def list_generated_files():
    if not os.path.exists(GENERATED_DIR):
        return {"files": []}

    files = []
    for f in os.listdir(GENERATED_DIR):
        if f.endswith(".csv"):
            files.append({
                "filename": f,
                "download_url": f"/api/v1/ocr/download/{f}",
                "created": datetime.fromtimestamp(
                    os.path.getctime(os.path.join(GENERATED_DIR, f))
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })

    return {"files": files}


# ======================================================================
# HEALTH
# ======================================================================

@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OCR service is running"}
