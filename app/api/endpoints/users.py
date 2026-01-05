from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.repositories.user_repository import user_repository
from app.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserLoginUpdate
)

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
    role: Optional[str] = Query(None, description="Filtrer par rôle"),
    team: Optional[str] = Query(None, description="Filtrer par équipe"),
    is_online: Optional[bool] = Query(None, description="Filtrer par statut en ligne")
):
    """
    Récupérer tous les users avec pagination et filtres
    """
    try:
        users, total = user_repository.get_all_users(page, size, search, role, team, is_online)

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

@router.get("/role/{role_name}", response_model=list[UserResponse])
async def get_users_by_role(role_name: str):
    """
    Récupérer tous les users d'un rôle
    """
    try:
        users = user_repository.get_users_by_role(role_name)
        return [UserResponse(**user) for user in users]

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

