from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import List, Dict, Any
import asyncio
import os
import uuid
import time
import json
from datetime import datetime, timedelta

from app.core.mistral_client import mistral_ocr_client
from app.core.logger import get_logger
from app.utils.pdf_splitter import pdf_splitter
from app.utils.document_classifier import document_classifier
from app.utils.data_extractor import data_extractor
from app.repositories.customer_repository import customer_repository
from app.repositories.customer_file_repository import customer_file_repository
from app.repositories.formula_repository import formula_repository
from app.repositories.group_repository import group_repository
from app.services.file import file_storage_service
from app.schemas.ocr_schemas import OCRResponse, ProcessedPage, DocumentType

router = APIRouter()
logger = get_logger(__name__)

# ======================================================================
# JOBS EN MÉMOIRE
# ======================================================================

# Structure : job_id → { status, progress, total_pages, filename, result, error, created_at }
_jobs: Dict[str, Dict[str, Any]] = {}


async def _process_pdf_job(job_id: str, pdf_content: bytes, filename: str, v2: bool) -> None:
    """Traitement OCR complet en tâche de fond. Met à jour _jobs[job_id] au fil du traitement."""
    job = _jobs[job_id]
    try:
        try:
            page_pdfs = pdf_splitter.split_pdf_to_pages(pdf_content)
            if not page_pdfs:
                job['status'] = 'error'
                job['error'] = 'No pages found in PDF'
                return
        except Exception as e:
            logger.error(f"[Job {job_id}] Erreur découpage PDF: {e}")
            job['status'] = 'error'
            job['error'] = f'Error splitting PDF: {e}'
            return

        processed_pages = []
        start_time = time.time()
        total_pages = len(page_pdfs)
        page_times = []

        job['status'] = 'processing'
        job['total_pages'] = total_pages

        estimated_seconds = total_pages * 3.5
        logger.info(f"[Job {job_id}] {total_pages} pages — estimation: {estimated_seconds:.0f}s (~{estimated_seconds/60:.1f} min)")

        for i, page_pdf_bytes in enumerate(page_pdfs):
            page_number = i + 1
            page_start_time = time.time()

            try:
                logger.info(f"[Job {job_id}] [{page_number}/{total_pages}] OCR en cours ({len(page_pdf_bytes)} bytes)")

                extracted_data = {}
                raw_text = ""
                doc_type = DocumentType.UNKNOWN
                confidence = 0.0
                ann_response = None
                ocr_response = None

                try:
                    ann_response = await mistral_ocr_client.process_pdf_annotations(page_pdf_bytes)
                    ann = (
                        ann_response.get("document_annotation")
                        or ann_response.get("document_annotations")
                        or ann_response.get("annotation")
                    )
                    if "pages" in ann_response and len(ann_response["pages"]) > 0:
                        raw_text = ann_response["pages"][0].get("markdown", "")

                    is_schema_echo = isinstance(ann, dict) and ("$defs" in ann or "properties" in ann)
                    if isinstance(ann, dict) and not is_schema_echo:
                        extracted_data = ann
                        dt = ann.get("document_type")
                        if dt in (DocumentType.BLANK_SHEET.value, DocumentType.STUDIO_PARFUMS.value, DocumentType.UNKNOWN.value):
                            doc_type = DocumentType(dt)
                            confidence = 1.0
                        logger.info(f"[Job {job_id}] [Page {page_number}] Annotations extraites: document_type={dt}")
                    elif is_schema_echo:
                        logger.warning(f"[Job {job_id}] [Page {page_number}] Mistral a renvoyé le schéma → fallback OCR")
                except Exception as e:
                    logger.error(f"[Job {job_id}] [Page {page_number}] Échec annotations → fallback OCR: {e}")

                if not extracted_data:
                    ocr_response = await mistral_ocr_client.process_pdf_ocr(page_pdf_bytes)
                    if "pages" in ocr_response and len(ocr_response["pages"]) > 0:
                        raw_text = ocr_response["pages"][0].get("markdown", "")
                    doc_type, confidence = document_classifier.classify_document(raw_text)
                    extracted_data = data_extractor.extract_data(raw_text, doc_type)

                if doc_type == DocumentType.STUDIO_PARFUMS:
                    try:
                        tables_content = ""
                        response_with_tables = ann_response if ann_response else ocr_response
                        if response_with_tables and "pages" in response_with_tables and len(response_with_tables["pages"]) > 0:
                            page_data = response_with_tables["pages"][0]
                            if "tables" in page_data and len(page_data["tables"]) > 0:
                                tables_content = "\n\n".join([
                                    table.get("content", "")
                                    for table in page_data["tables"]
                                ])
                                logger.info(f"[Job {job_id}] [Page {page_number}] {len(page_data['tables'])} tableau(x) trouvé(s)")

                        if tables_content:
                            perfume_notes = data_extractor.extract_perfume_notes_from_markdown(tables_content)
                            extracted_data.update(perfume_notes)
                        else:
                            logger.warning(f"[Job {job_id}] [Page {page_number}] Aucun tableau trouvé")

                        logger.info(f"[Job {job_id}] [Page {page_number}] JSON final: {json.dumps(extracted_data, ensure_ascii=False)}")

                    except Exception as e:
                        logger.error(f"[Job {job_id}] [Page {page_number}] Erreur extraction notes: {e}", exc_info=True)

                customer_id = None
                customer_review_id = None
                entity_type = None

                if doc_type == DocumentType.STUDIO_PARFUMS and extracted_data:
                    try:
                        entity_id, entity_type = customer_repository.insert_customer_if_not_exists(extracted_data, v2=v2)

                        if entity_id:
                            if entity_type == "customer":
                                customer_id = entity_id
                                logger.info(f"[Job {job_id}] [Page {page_number}] Customer créé — ID: {customer_id}")
                            elif entity_type == "customer_review":
                                customer_review_id = entity_id
                                logger.warning(f"[Job {job_id}] [Page {page_number}] Customer review créé — ID: {customer_review_id}")

                            try:
                                pdf_path, image_paths = file_storage_service.save_pdf_and_images(
                                    page_pdf_bytes,
                                    customer_id,
                                    f"page_{page_number}_{filename}",
                                    customer_review_id=customer_review_id,
                                )

                                file_data = {
                                    'customer_id': customer_id,
                                    'customer_review_id': customer_review_id,
                                    'file_path': pdf_path,
                                    'file_name': os.path.basename(pdf_path),
                                    'file_type': 'application/pdf',
                                    'file_size': len(page_pdf_bytes),
                                    'uploaded_at': datetime.now()
                                }
                                pdf_file_id = customer_file_repository.create_customer_file(file_data)

                                for img_path in image_paths:
                                    img_data = {
                                        'customer_id': customer_id,
                                        'customer_review_id': customer_review_id,
                                        'file_path': img_path,
                                        'file_name': os.path.basename(img_path),
                                        'file_type': 'image/png',
                                        'file_size': 0,
                                        'uploaded_at': datetime.now()
                                    }
                                    customer_file_repository.create_customer_file(img_data)

                                logger.info(f"[Job {job_id}] [Page {page_number}] PDF + {len(image_paths)} image(s) sauvegardés (file_id: {pdf_file_id})")

                                try:
                                    reference = (extracted_data.get('identifiant') or '').strip() or None
                                    formula_id, notes_were_corrected = formula_repository.create_formula_with_notes(
                                        customer_id=customer_id,
                                        file_id=pdf_file_id,
                                        extracted_data=extracted_data,
                                        customer_review_id=customer_review_id,
                                        reference=reference
                                    )
                                    if formula_id:
                                        logger.info(f"[Job {job_id}] [Page {page_number}] Formule créée — ID: {formula_id}")
                                        if notes_were_corrected:
                                            logger.warning(f"[Job {job_id}] [Page {page_number}] Des notes ont été corrigées automatiquement")
                                    else:
                                        logger.warning(f"[Job {job_id}] [Page {page_number}] Formule non créée")
                                except Exception as e:
                                    logger.error(f"[Job {job_id}] [Page {page_number}] Erreur création formule/notes: {e}", exc_info=True)

                                groupe_name = (extracted_data.get('groupe') or '').strip()
                                if groupe_name and customer_id:
                                    try:
                                        group_id = group_repository.find_or_create_group(groupe_name)
                                        if group_id:
                                            assigned = group_repository.assign_customer_to_group(customer_id, group_id)
                                            if assigned:
                                                logger.info(f"[Job {job_id}] [Page {page_number}] Customer {customer_id} ajouté au groupe '{groupe_name}'")
                                    except Exception as e:
                                        logger.error(f"[Job {job_id}] [Page {page_number}] Erreur gestion groupe: {e}", exc_info=True)

                            except Exception as e:
                                logger.error(f"[Job {job_id}] [Page {page_number}] Erreur sauvegarde fichier: {e}", exc_info=True)
                        else:
                            logger.warning(f"[Job {job_id}] [Page {page_number}] Customer non créé (doublon ou données insuffisantes)")

                    except Exception as e:
                        logger.error(f"[Job {job_id}] [Page {page_number}] Erreur insertion customer: {e}", exc_info=True)

                processed_pages.append({
                    "page_number": page_number,
                    "document_type": doc_type.value,
                    "confidence": confidence,
                    "raw_text": raw_text,
                    "extracted_data": extracted_data,
                    "customer_id": customer_id,
                    "customer_review_id": customer_review_id
                })

            except Exception as e:
                logger.error(f"[Job {job_id}] [Page {page_number}] Erreur générale: {e}", exc_info=True)

            finally:
                page_duration = time.time() - page_start_time
                page_times.append(page_duration)

                elapsed_time = time.time() - start_time
                avg_time_per_page = elapsed_time / page_number
                remaining_pages = total_pages - page_number
                eta_seconds = avg_time_per_page * remaining_pages

                job['progress'] = page_number

                if remaining_pages > 0:
                    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                    logger.info(
                        f"[Job {job_id}] [{page_number}/{total_pages}] {page_number/total_pages*100:.0f}% — "
                        f"{page_duration:.1f}s — ETA: {eta_time.strftime('%H:%M:%S')}"
                    )
                else:
                    logger.info(f"[Job {job_id}] [{page_number}/{total_pages}] 100% — {page_duration:.1f}s")

        total_studio_parfums = sum(
            1 for p in processed_pages if p.get("document_type") == DocumentType.STUDIO_PARFUMS.value
        )

        if total_studio_parfums == 0:
            job['status'] = 'error'
            job['error'] = 'No Studio des Parfums forms found in this PDF'
            return

        total_duration = time.time() - start_time
        avg_page_time = sum(page_times) / len(page_times) if page_times else 0
        customers_created = sum(1 for p in processed_pages if p.get("customer_id") is not None)

        logger.info(
            f"[Job {job_id}] TERMINÉ — {total_pages} pages en {total_duration:.1f}s "
            f"(moy: {avg_page_time:.2f}s/page)"
        )

        job['status'] = 'completed'
        job['result'] = {
            "success": True,
            "total_studio_parfums_found": total_studio_parfums,
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
                "fastest_page_time": round(min(page_times), 2) if page_times else 0,
                "slowest_page_time": round(max(page_times), 2) if page_times else 0,
                "pages_per_minute": round(60 / avg_page_time, 1) if avg_page_time > 0 else 0,
            }
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Erreur fatale: {type(e).__name__}: {e}", exc_info=True)
        job['status'] = 'error'
        job['error'] = str(e) or repr(e)


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
        logger.info(f"Début du découpage PDF: {file.filename}")
        try:
            page_pdfs = pdf_splitter.split_pdf_to_pages(pdf_content)
            if not page_pdfs:
                raise HTTPException(status_code=400, detail="No pages found in PDF")
        except Exception as e:
            logger.error(f"Erreur découpage PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Error splitting PDF: {e}")

        processed_pages: List[ProcessedPage] = []
        total_blank_sheets = 0
        total_studio_parfums = 0

        logger.info(f"Traitement de {len(page_pdfs)} pages avec Mistral OCR")
        for i, page_pdf_bytes in enumerate(page_pdfs):
            page_number = i + 1
            try:
                logger.info(f"[Page {page_number}] OCR en cours ({len(page_pdf_bytes)} bytes)")

                extracted_data = {}
                raw_text = ""
                doc_type = DocumentType.UNKNOWN
                confidence = 0.0
                ann_response = None
                ocr_response = None

                try:
                    ann_response = await mistral_ocr_client.process_pdf_annotations(page_pdf_bytes)
                    ann = (
                        ann_response.get("document_annotation")
                        or ann_response.get("document_annotations")
                        or ann_response.get("annotation")
                    )
                    if "pages" in ann_response and len(ann_response["pages"]) > 0:
                        raw_text = ann_response["pages"][0].get("markdown", "")

                    is_schema_echo = isinstance(ann, dict) and ("$defs" in ann or "properties" in ann)
                    if isinstance(ann, dict) and not is_schema_echo:
                        extracted_data = ann
                        dt = ann.get("document_type")
                        if dt in (DocumentType.BLANK_SHEET.value, DocumentType.STUDIO_PARFUMS.value, DocumentType.UNKNOWN.value):
                            doc_type = DocumentType(dt)
                            confidence = 1.0
                        logger.info(f"[Page {page_number}] Annotations extraites: document_type={dt}")
                    elif is_schema_echo:
                        logger.warning(f"[Page {page_number}] Mistral a renvoyé le schéma au lieu des données → fallback OCR")
                    else:
                        logger.warning(f"[Page {page_number}] Annotations non exploitables → fallback OCR")
                except Exception as e:
                    logger.error(f"[Page {page_number}] Échec annotations → fallback OCR: {e}")

                if not extracted_data:
                    ocr_response = await mistral_ocr_client.process_pdf_ocr(page_pdf_bytes)

                    if "pages" in ocr_response and len(ocr_response["pages"]) > 0:
                        raw_text = ocr_response["pages"][0].get("markdown", "")

                    logger.info(f"[Page {page_number}] OCR texte: {len(raw_text)} caractères extraits")
                    doc_type, confidence = document_classifier.classify_document(raw_text)

                if doc_type == DocumentType.BLANK_SHEET:
                    total_blank_sheets += 1
                elif doc_type == DocumentType.STUDIO_PARFUMS:
                    total_studio_parfums += 1

                if not extracted_data:
                    extracted_data = data_extractor.extract_data(raw_text, doc_type)

                # Extraire les notes de parfum depuis les tableaux
                if doc_type == DocumentType.STUDIO_PARFUMS:
                    try:
                        tables_content = ""
                        response_with_tables = ann_response if ann_response else ocr_response

                        if response_with_tables and "pages" in response_with_tables and len(response_with_tables["pages"]) > 0:
                            page_data = response_with_tables["pages"][0]
                            if "tables" in page_data and len(page_data["tables"]) > 0:
                                tables_content = "\n\n".join([
                                    table.get("content", "")
                                    for table in page_data["tables"]
                                ])
                                logger.info(f"[Page {page_number}] {len(page_data['tables'])} tableau(x) trouvé(s)")

                        if tables_content:
                            perfume_notes = data_extractor.extract_perfume_notes_from_markdown(tables_content)
                            extracted_data.update(perfume_notes)
                            logger.info(
                                f"[Page {page_number}] Notes extraites: "
                                f"tête={len(perfume_notes.get('notes_de_tete', []))}, "
                                f"cœur={len(perfume_notes.get('notes_de_coeur', []))}, "
                                f"fond={len(perfume_notes.get('notes_de_fond', []))}"
                            )
                        else:
                            logger.warning(f"[Page {page_number}] Aucun tableau trouvé dans la réponse API")

                    except Exception as e:
                        logger.error(f"[Page {page_number}] Erreur extraction notes de parfum: {e}", exc_info=True)

                if doc_type == DocumentType.STUDIO_PARFUMS:
                    logger.info(f"[Page {page_number}] JSON final: {json.dumps(extracted_data, ensure_ascii=False)}")

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
                logger.error(f"[Page {page_number}] Erreur traitement: {type(e).__name__}: {e}", exc_info=True)
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
        logger.error(f"Erreur globale /upload-pdf: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e) or repr(e)}")




# ======================================================================
# OCR → CSV (PRODUCTION) - ASYNCHRONE AVEC SUIVI DE JOB
# ======================================================================

@router.post("/upload-pdf-csv")
async def upload_pdf_and_download_csv(file: UploadFile = File(...), v2: bool = Form(False)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_content = await file.read()
    if not pdf_content or len(pdf_content) < 100:
        raise HTTPException(status_code=400, detail="Invalid or empty PDF")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "total_pages": 0,
        "filename": file.filename,
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }

    asyncio.create_task(_process_pdf_job(job_id, pdf_content, file.filename, v2))

    logger.info(f"Job {job_id} créé pour {file.filename}")
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs")
async def list_jobs():
    return [{"job_id": jid, **{k: v for k, v in job.items() if k != "result"}} for jid, job in _jobs.items()]



# ======================================================================
# HEALTH
# ======================================================================

@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OCR service is running"}
