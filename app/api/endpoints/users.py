from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.repositories.user_repository import user_repository
from app.repositories.role_repository import role_repository
from app.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserLoginUpdate,
    UserWithRoleResponse
)
from app.schemas.role_schemas import RoleResponse

router = APIRouter()

@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate):
    """
    Créer un nouveau user
    """
    try:
        # Vérifier si l'email existe déjà
        if user.email:
            existing_user = user_repository.get_user_by_email(user.email)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail=f"Un user avec l'email {user.email} existe déjà"
                )

        user_id = user_repository.create_user(user.dict())

        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la création du user"
            )

        # Récupérer le user créé
        created_user = user_repository.get_user_by_id(user_id)
        if not created_user:
            raise HTTPException(
                status_code=500,
                detail="User créé mais impossible à récupérer"
            )

        return UserResponse(**created_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de page"),
    search: Optional[str] = Query(None, description="Recherche dans nom, email, téléphone, job, équipe"),
    role_id: Optional[int] = Query(None, description="Filtrer par rôle (ID)"),
    team: Optional[str] = Query(None, description="Filtrer par équipe"),
    is_online: Optional[bool] = Query(None, description="Filtrer par statut en ligne")
):
    """
    Récupérer tous les users avec pagination et filtres
    """
    try:
        users, total = user_repository.get_all_users(page, size, search, role_id, team, is_online)

        return UserListResponse(
            users=[UserResponse(**user) for user in users],
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/online", response_model=list[UserResponse])
async def get_online_users():
    """
    Récupérer tous les users en ligne
    """
    try:
        users = user_repository.get_online_users()
        return [UserResponse(**user) for user in users]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/team/{team_name}", response_model=list[UserResponse])
async def get_users_by_team(team_name: str):
    """
    Récupérer tous les users d'une équipe
    """
    try:
        users = user_repository.get_users_by_team(team_name)
        return [UserResponse(**user) for user in users]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/role/{role_id}", response_model=list[UserResponse])
async def get_users_by_role(role_id: int):
    """
    Récupérer tous les users d'un rôle
    """
    try:
        users = user_repository.get_users_by_role_id(role_id)
        return [UserResponse(**user) for user in users]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/by-email", response_model=UserWithRoleResponse)
async def get_user_by_email(email: str = Query(..., description="Email de l'utilisateur")):
    """
    Récupérer un utilisateur par son email avec les informations complètes de son rôle.
    Utilisé pour la connexion Google OAuth.
    """
    try:
        # Nettoyer l'email (trim + lowercase)
        clean_email = email.strip().lower()
        user = user_repository.get_user_by_email(clean_email)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Utilisateur avec l'email {email} non trouvé"
            )

        # Récupérer les informations du rôle si l'utilisateur en a un
        role_data = None
        if user.get('role_id'):
            role = role_repository.get_role_by_id(user['role_id'])
            if role:
                role_data = RoleResponse(**role)

        return UserWithRoleResponse(
            id=user['id'],
            identifier=user.get('identifier'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
            email=user.get('email'),
            phone=user.get('phone'),
            job=user.get('job'),
            is_online=user.get('is_online', False),
            team=user.get('team'),
            last_login_at=user.get('last_login_at'),
            csv_download_count=user.get('csv_download_count', 0),
            csv_download_reset_at=user.get('csv_download_reset_at'),
            pdf_extraction_count=user.get('pdf_extraction_count', 0),
            pdf_extraction_reset_at=user.get('pdf_extraction_reset_at'),
            role=role_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/by-identifier", response_model=UserWithRoleResponse)
async def get_user_by_identifier(identifier: str = Query(..., description="Identifiant unique de l'utilisateur")):
    """
    Récupérer un utilisateur par son identifiant unique.
    Utilisé pour l'authentification superviseur sur l'application tablette.
    """
    try:
        clean_identifier = identifier.strip().upper()
        user = user_repository.get_user_by_identifier(clean_identifier)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Utilisateur avec l'identifiant {identifier} non trouvé"
            )

        role_data = None
        if user.get('role_id'):
            role = role_repository.get_role_by_id(user['role_id'])
            if role:
                role_data = RoleResponse(**role)

        return UserWithRoleResponse(
            id=user['id'],
            identifier=user.get('identifier'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
            email=user.get('email'),
            phone=user.get('phone'),
            job=user.get('job'),
            is_online=user.get('is_online', False),
            team=user.get('team'),
            last_login_at=user.get('last_login_at'),
            csv_download_count=user.get('csv_download_count', 0),
            csv_download_reset_at=user.get('csv_download_reset_at'),
            pdf_extraction_count=user.get('pdf_extraction_count', 0),
            pdf_extraction_reset_at=user.get('pdf_extraction_reset_at'),
            role=role_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    Récupérer un user par son ID
    """
    try:
        user = user_repository.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        return UserResponse(**user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate):
    """
    Mettre à jour un user
    """
    try:
        # Vérifier que le user existe
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        # Vérifier si l'email est unique (si modifié)
        if user.email and user.email != existing_user.get('email'):
            email_user = user_repository.get_user_by_email(user.email)
            if email_user and email_user['id'] != user_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Un user avec l'email {user.email} existe déjà"
                )

        # Mettre à jour
        success = user_repository.update_user(
            user_id,
            user.dict(exclude_unset=True)
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la mise à jour"
            )

        # Récupérer le user mis à jour
        updated_user = user_repository.get_user_by_id(user_id)
        return UserResponse(**updated_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.patch("/{user_id}/login-status")
async def update_user_login_status(user_id: int, login_data: UserLoginUpdate):
    """
    Mettre à jour le statut de connexion d'un user
    """
    try:
        # Vérifier que le user existe
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        # Mettre à jour le statut
        success = user_repository.update_user_login_status(user_id, login_data.is_online)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la mise à jour du statut"
            )

        return {"message": f"Statut de connexion mis à jour pour user {user_id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """
    Supprimer un user
    """
    try:
        # Vérifier que le user existe
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        # Supprimer
        success = user_repository.delete_user(user_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la suppression"
            )

        return {"message": f"User {user_id} supprimé avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/{user_id}/quotas")
async def get_user_quotas(user_id: int):
    """
    Récupérer les quotas d'un utilisateur
    """
    try:
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        quotas = user_repository.get_user_quotas(user_id)
        if not quotas:
            raise HTTPException(
                status_code=404,
                detail="Impossible de récupérer les quotas"
            )

        return {
            "csv": {
                "used": quotas["csv_current_count"],
                "limit": quotas["csv_download_limit"],
                "remaining": quotas["csv_download_limit"] - quotas["csv_current_count"],
                "reset_at": quotas["csv_next_reset"]
            },
            "pdf": {
                "used": quotas["pdf_current_count"],
                "limit": quotas["pdf_extraction_limit"],
                "remaining": quotas["pdf_extraction_limit"] - quotas["pdf_current_count"],
                "reset_at": quotas["pdf_next_reset"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/{user_id}/quotas/csv/consume")
async def consume_csv_quota(user_id: int):
    """
    Consommer un quota CSV pour l'utilisateur
    """
    try:
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        success = user_repository.consume_csv_quota(user_id)

        if not success:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": "Quota CSV mensuel dépassé",
                    "type": "csv"
                }
            )

        return {"message": "Quota CSV consommé", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/{user_id}/quotas/pdf/consume")
async def consume_pdf_quota(user_id: int):
    """
    Consommer un quota PDF pour l'utilisateur
    """
    try:
        existing_user = user_repository.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail=f"User avec ID {user_id} non trouvé"
            )

        success = user_repository.consume_pdf_quota(user_id)

        if not success:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": "Quota PDF mensuel dépassé",
                    "type": "pdf"
                }
            )

        return {"message": "Quota PDF consommé", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

