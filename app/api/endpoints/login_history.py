from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
import math

from app.schemas.login_history_schemas import (
    LoginHistoryCreate,
    LoginHistoryResponse,
    LoginHistoryListResponse
)
from app.repositories.login_history_repository import login_history_repository
from app.repositories.user_repository import user_repository
from app.services.geolocation_service import geolocation_service

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """
    Récupère l'adresse IP réelle du client
    """
    # Vérifier les headers de proxy en premier
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Prendre la première IP de la liste (IP originale)
        return forwarded_for.split(",")[0].strip()

    # Vérifier d'autres headers communs
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Utiliser l'IP de la connection directe
    client_host = getattr(request.client, "host", "127.0.0.1")
    return client_host

@router.post("/record", response_model=dict)
async def record_log(request: Request, login_data: LoginHistoryCreate):
    """
    Enregistre un log de connexion ou déconnexion
    - Récupère automatiquement l'IP du client
    - Géolocalise l'IP pour obtenir ville et pays
    - Enregistre tout dans la base de données avec le type spécifié
    """
    # Vérifier que l'utilisateur existe
    user = user_repository.get_user_by_id(login_data.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Utilisateur avec ID {login_data.user_id} non trouvé"
        )

    # Récupérer l'IP du client
    client_ip = get_client_ip(request)

    # Géolocaliser l'IP
    location = geolocation_service.get_location_by_ip(client_ip)

    # Enregistrer en base de données
    record_id = login_history_repository.create_login_record(
        user_id=login_data.user_id,
        ip_address=client_ip,
        city=location["city"],
        country=location["country"],
        log_type=login_data.type
    )

    if not record_id:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de la connexion"
        )

    return {
        "success": True,
        "message": f"Log {login_data.type} enregistré avec succès",
        "record_id": record_id,
        "type": login_data.type,
        "ip_address": client_ip,
        "location": location
    }

@router.get("/user/{user_id}", response_model=LoginHistoryListResponse)
async def get_user_logs(
    user_id: int,
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de la page")
):
    """
    Récupère tous les logs (connexions + déconnexions) d'un utilisateur spécifique
    """
    # Vérifier que l'utilisateur existe
    user = user_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Utilisateur avec ID {user_id} non trouvé"
        )

    # Récupérer l'historique
    records, total = login_history_repository.get_login_history_by_user(
        user_id=user_id,
        page=page,
        size=size
    )

    # Calculer le nombre total de pages
    total_pages = math.ceil(total / size) if total > 0 else 0

    return LoginHistoryListResponse(
        records=records,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )

@router.get("/", response_model=LoginHistoryListResponse)
async def get_all_logs(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de la page")
):
    """
    Récupère tous les logs (connexions + déconnexions) de tous les utilisateurs
    Inclut les informations utilisateur (email, nom, prénom)
    """
    # Récupérer l'historique complet
    records, total = login_history_repository.get_all_login_history(
        page=page,
        size=size
    )

    # Calculer le nombre total de pages
    total_pages = math.ceil(total / size) if total > 0 else 0

    return LoginHistoryListResponse(
        records=records,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )