from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Optional

from app.repositories.customer_file_repository import customer_file_repository
from app.services.file import file_storage_service
from app.schemas.customer_file_schemas import CustomerFileResponse, CustomerFileListResponse

router = APIRouter()


@router.get("/customers/{customer_id}/files", response_model=CustomerFileListResponse)
async def get_customer_files(customer_id: int):
    """
    Récupère tous les fichiers d'un customer
    """
    try:
        files = customer_file_repository.get_files_by_customer_id(customer_id)

        file_responses = [CustomerFileResponse(**file) for file in files]

        return CustomerFileListResponse(
            files=file_responses,
            total=len(file_responses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/customer-reviews/{customer_review_id}/files", response_model=CustomerFileListResponse)
async def get_customer_review_files(customer_review_id: int):
    """
    Récupère tous les fichiers d'un customer_review
    """
    try:
        files = customer_file_repository.get_files_by_customer_review_id(customer_review_id)

        file_responses = [CustomerFileResponse(**file) for file in files]

        return CustomerFileListResponse(
            files=file_responses,
            total=len(file_responses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}")
async def get_file(file_id: int):
    """
    Récupère les informations d'un fichier
    """
    try:
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        return CustomerFileResponse(**file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}/content")
async def get_file_content(file_id: int):
    """
    Télécharge le contenu d'un fichier (PDF ou Image)
    """
    try:
        # Récupérer les informations du fichier
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        # Récupérer le contenu du fichier
        file_bytes = file_storage_service.get_file_bytes(file['file_path'])

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Contenu du fichier non trouvé: {file['file_path']}"
            )

        # Déterminer le media type
        media_type = file.get('file_type', 'application/octet-stream')

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'inline; filename="{file["file_name"]}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}/download")
async def download_file(file_id: int):
    """
    Force le téléchargement d'un fichier (au lieu de l'affichage inline)
    """
    try:
        # Récupérer les informations du fichier
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        # Récupérer le contenu du fichier
        file_bytes = file_storage_service.get_file_bytes(file['file_path'])

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Contenu du fichier non trouvé: {file['file_path']}"
            )

        # Déterminer le media type
        media_type = file.get('file_type', 'application/octet-stream')

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{file["file_name"]}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
