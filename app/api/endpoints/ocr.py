from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response, FileResponse
from typing import List
import os
import uuid
import time
from datetime import datetime, timedelta

from app.core.mistral_client import mistral_ocr_client
from app.utils.pdf_splitter import pdf_splitter
from app.utils.document_classifier import document_classifier
from app.utils.data_extractor import data_extractor
from app.utils.csv_generator import csv_generator
from app.repositories.customer_repository import customer_repository
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

        # Split PDF into pages using pikepdf (évite limite 32MB)
        print(f"Starting PDF splitting for file: {file.filename}")
        try:
            page_pdfs = pdf_splitter.split_pdf_to_pages(pdf_content, max_pages=None)
            if not page_pdfs:
                raise HTTPException(status_code=400, detail="No pages found in PDF")
        except Exception as e:
            print(f"Error during PDF splitting: {e}")
            raise HTTPException(status_code=500, detail=f"Error splitting PDF: {e}")

        processed_pages: List[ProcessedPage] = []
        total_blank_sheets = 0
        total_studio_parfums = 0

        print(f"Processing {len(page_pdfs)} pages with Mistral OCR")
        for i, page_pdf_bytes in enumerate(page_pdfs):
            page_number = i + 1
            try:
                print(f"OCR processing page {page_number} ({len(page_pdf_bytes)} bytes)")

                # OCR de la page individuelle avec Mistral
                ocr_response = await mistral_ocr_client.process_pdf_ocr(page_pdf_bytes)

                # Extraire le texte de la première page de la réponse
                raw_text = ""
                if "pages" in ocr_response and len(ocr_response["pages"]) > 0:
                    raw_text = ocr_response["pages"][0].get("markdown", "")

                print(f"Page {page_number}: extracted {len(raw_text)} characters")

                doc_type, confidence = document_classifier.classify_document(raw_text)

                if doc_type == DocumentType.BLANK_SHEET:
                    total_blank_sheets += 1
                elif doc_type == DocumentType.STUDIO_PARFUMS:
                    total_studio_parfums += 1

                extracted_data = data_extractor.extract_data(raw_text, doc_type)

                processed_pages.append(
                    ProcessedPage(
                        page_number=page_number,
                        document_type=doc_type,
                        confidence=confidence,
                        raw_text=raw_text,
                        extracted_data=extracted_data,
                    )
                )

            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
                print(f"Error type: {type(e)}")
                processed_pages.append(
                    ProcessedPage(
                        page_number=page_number,
                        document_type=DocumentType.UNKNOWN,
                        confidence=0.0,
                        raw_text=f"Error: {str(e)}",
                        extracted_data={},
                    )
                )

        total_pages = len(processed_pages)
        summary = {
            "total_pages": total_pages,
            "blank_sheets": total_blank_sheets,
            "studio_parfums_sheets": total_studio_parfums,
            "unknown_sheets": total_pages - total_blank_sheets - total_studio_parfums,
            "processing_errors": sum(
                1 for p in processed_pages if p.document_type == DocumentType.UNKNOWN
            ),
        }

        response = OCRResponse(
            success=True,
            filename=file.filename,
            total_pages=total_pages,
            processed_pages=processed_pages,
            summary=summary,
        )

        return response.dict()

    except Exception as e:
        print(f"Global error in endpoint: {e}")
        print(f"Global error type: {type(e)}")
        print(f"Global error str: '{str(e)}'")
        print(f"Global error repr: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e) or repr(e)}")




# ======================================================================
# OCR → CSV (PRODUCTION) - ANCIEN SYSTÈME SYNCHRONE
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

        # Split PDF into pages using pikepdf (évite limite 32MB)
        print(f"Starting PDF splitting for CSV generation: {file.filename}")
        try:
            page_pdfs = pdf_splitter.split_pdf_to_pages(pdf_content, max_pages=50)  #static number for test
            if not page_pdfs:
                raise HTTPException(status_code=400, detail="No pages found in PDF")
        except Exception as e:
            print(f"Error during PDF splitting: {e}")
            raise HTTPException(status_code=500, detail=f"Error splitting PDF: {e}")

        processed_pages = []

        # Monitoring des performances
        start_time = time.time()
        total_pages = len(page_pdfs)
        page_times = []

        print(f"Processing {total_pages} pages for CSV generation")
        estimated_seconds = total_pages * 3.5
        estimated_minutes = estimated_seconds / 60
        print(f"📊 Estimation: {estimated_seconds:.0f}s (~{estimated_minutes:.1f} min) - {total_pages} pages at 3.5s/page")

        for i, page_pdf_bytes in enumerate(page_pdfs):
            page_number = i + 1
            page_start_time = time.time()

            try:
                print(f"[{page_number}/{total_pages}] OCR processing page {page_number} ({len(page_pdf_bytes)} bytes)")

                # OCR de la page individuelle avec Mistral
                ocr_response = await mistral_ocr_client.process_pdf_ocr(page_pdf_bytes)

                # Extraire le texte de la première page de la réponse
                raw_text = ""
                if "pages" in ocr_response and len(ocr_response["pages"]) > 0:
                    raw_text = ocr_response["pages"][0].get("markdown", "")

                doc_type, confidence = document_classifier.classify_document(raw_text)
                extracted_data = data_extractor.extract_data(raw_text, doc_type)

                # Si c'est un formulaire Studio des Parfums, insérer en base de données
                customer_id = None
                if doc_type == DocumentType.STUDIO_PARFUMS and extracted_data:
                    try:
                        customer_id = customer_repository.insert_customer_if_not_exists(extracted_data)
                        if customer_id:
                            print(f"Customer créé avec ID: {customer_id} pour page {page_number}")
                        else:
                            print(f"Customer non créé pour page {page_number} (existe déjà ou données insuffisantes)")
                    except Exception as e:
                        print(f"Erreur insertion customer page {page_number}: {e}")

                processed_pages.append({
                    "page_number": page_number,
                    "document_type": doc_type.value,
                    "confidence": confidence,
                    "raw_text": raw_text,
                    "extracted_data": extracted_data,
                    "customer_id": customer_id  # Ajouter l'ID customer pour référence
                })

            except Exception as e:
                print(f"Error processing page {page_number} for CSV: {e}")
                continue  # on ignore la page mais on continue

            finally:
                # Calculer les temps et progression
                page_duration = time.time() - page_start_time
                page_times.append(page_duration)

                # Calcul progression et ETA
                elapsed_time = time.time() - start_time
                progress_percent = (page_number / total_pages) * 100
                avg_time_per_page = elapsed_time / page_number
                remaining_pages = total_pages - page_number
                eta_seconds = avg_time_per_page * remaining_pages

                # Logs de progression
                print(f"Page {page_number} processed in {page_duration:.2f}s")
                print(f"Progress: {progress_percent:.1f}% ({page_number}/{total_pages})")

                if remaining_pages > 0:
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    print(f"ETA: {eta_seconds:.0f}s remaining (finish at {eta_time.strftime('%H:%M:%S')})")
                    print(f"Average: {avg_time_per_page:.2f}s/page")

                print("─" * 50)

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

        # Calculs finaux de performance
        total_duration = time.time() - start_time
        avg_page_time = sum(page_times) / len(page_times) if page_times else 0
        fastest_page = min(page_times) if page_times else 0
        slowest_page = max(page_times) if page_times else 0

        # Compter les customers créés
        customers_created = sum(
            1 for p in processed_pages
            if p.get("customer_id") is not None
        )

        # Log final
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETED!")
        print(f"Total time: {total_duration:.1f}s for {total_pages} pages")
        print(f"Average: {avg_page_time:.2f}s/page")
        print(f"Fastest page: {fastest_page:.2f}s | Slowest: {slowest_page:.2f}s")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "filename": csv_filename,
            "download_url": f"/api/v1/ocr/download/{csv_filename}",
            "total_studio_parfums_found": sum(
                1 for p in processed_pages
                if p.get("document_type") == DocumentType.STUDIO_PARFUMS.value
            ),
            "customers_created": customers_created,
            "customers_skipped": sum(
                1 for p in processed_pages
                if p.get("document_type") == DocumentType.STUDIO_PARFUMS.value
                and p.get("customer_id") is None
            ),
            "performance": {
                "total_pages": total_pages,
                "total_duration_seconds": round(total_duration, 2),
                "avg_time_per_page": round(avg_page_time, 2),
                "fastest_page_time": round(fastest_page, 2),
                "slowest_page_time": round(slowest_page, 2),
                "pages_per_minute": round(60 / avg_page_time, 1) if avg_page_time > 0 else 0,
                "estimated_time_for_100_pages": round(avg_page_time * 100, 0) if avg_page_time > 0 else 0
            }
        }

    except Exception as e:
        print(f"Global error in endpoint: {e}")
        print(f"Global error type: {type(e)}")
        print(f"Global error str: '{str(e)}'")
        print(f"Global error repr: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e) or repr(e)}")


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
