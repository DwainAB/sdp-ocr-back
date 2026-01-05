from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.group_schemas import GroupCreate, GroupUpdate, GroupResponse, AddCustomersToGroup, RemoveCustomersFromGroup
from app.repositories.group_repository import group_repository

router = APIRouter()


@router.post("/", response_model=GroupResponse)
async def create_group(group_data: GroupCreate):
    """
    Crée un nouveau groupe
    """
    try:
        group_dict = group_data.model_dump()
        group_id = group_repository.create_group(group_dict)

        if group_id is None:
            raise HTTPException(status_code=500, detail="Erreur lors de la création du groupe")

        # Récupérer le groupe créé pour le retourner
        created_group = group_repository.get_group_by_id(group_id)
        if created_group is None:
            raise HTTPException(status_code=500, detail="Groupe créé mais impossible de le récupérer")

        return created_group

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du groupe: {str(e)}")


@router.get("/", response_model=dict)
async def get_groups(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de page"),
    search: Optional[str] = Query(None, description="Terme de recherche"),
    include_deleted: bool = Query(False, description="Inclure les groupes supprimés")
):
    """
    Récupère la liste des groupes avec pagination
    """
    try:
        groups, total = group_repository.get_all_groups(
            page=page,
            size=size,
            search=search,
            include_deleted=include_deleted
        )

        return {
            "groups": groups,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size  # Calcul du nombre total de pages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des groupes: {str(e)}")


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int):
    """
    Récupère un groupe par son ID
    """
    try:
        group = group_repository.get_group_by_id(group_id)

        if group is None:
            raise HTTPException(status_code=404, detail="Groupe non trouvé")

        return group

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du groupe: {str(e)}")


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, group_data: GroupUpdate):
    """
    Met à jour un groupe
    """
    try:
        # Vérifier que le groupe existe
        existing_group = group_repository.get_group_by_id(group_id)
        if existing_group is None:
            raise HTTPException(status_code=404, detail="Groupe non trouvé")

        # Mettre à jour seulement les champs fournis
        update_dict = group_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

        success = group_repository.update_group(group_id, update_dict)

        if not success:
            raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du groupe")

        # Retourner le groupe mis à jour
        updated_group = group_repository.get_group_by_id(group_id)
        return updated_group

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du groupe: {str(e)}")


@router.delete("/{group_id}")
async def delete_group(group_id: int):
    """
    Supprime logiquement un groupe (soft delete)
    """
    try:
        success = group_repository.soft_delete_group(group_id)

        if not success:
            raise HTTPException(status_code=404, detail="Groupe non trouvé ou déjà supprimé")

        return {"message": f"Groupe {group_id} supprimé avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression du groupe: {str(e)}")


@router.post("/{group_id}/restore")
async def restore_group(group_id: int):
    """
    Restaure un groupe supprimé
    """
    try:
        success = group_repository.restore_group(group_id)

        if not success:
            raise HTTPException(status_code=404, detail="Groupe non trouvé ou pas supprimé")

        # Retourner le groupe restauré
        restored_group = group_repository.get_group_by_id(group_id)
        return {
            "message": f"Groupe {group_id} restauré avec succès",
            "group": restored_group
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la restauration du groupe: {str(e)}")


# ======================================================================
# GESTION DES RELATIONS CLIENTS-GROUPES
# ======================================================================

@router.post("/{group_id}/customers")
async def add_customers_to_group(group_id: int, request: AddCustomersToGroup):
    """
    Ajoute un ou plusieurs clients à un groupe
    """
    try:
        result = group_repository.add_customers_to_group(
            group_id=group_id,
            customer_ids=request.customer_ids,
            added_by=request.added_by
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout des clients: {str(e)}")


@router.delete("/{group_id}/customers")
async def remove_customers_from_group(group_id: int, request: RemoveCustomersFromGroup):
    """
    Retire un ou plusieurs clients d'un groupe
    """
    try:
        result = group_repository.remove_customers_from_group(
            group_id=group_id,
            customer_ids=request.customer_ids
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression des clients: {str(e)}")


@router.get("/{group_id}/customers")
async def get_group_customers(
    group_id: int,
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de page")
):
    """
    Récupère tous les clients d'un groupe avec pagination
    """
    try:
        customers, total = group_repository.get_group_customers(
            group_id=group_id,
            page=page,
            size=size
        )

        return {
            "customers": customers,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des clients: {str(e)}")


# Route bonus : récupérer les groupes d'un client spécifique
@router.get("/customer/{customer_id}")
async def get_customer_groups(customer_id: int):
    """
    Récupère tous les groupes d'un client spécifique
    """
    try:
        groups = group_repository.get_customer_groups(customer_id)

        return {
            "customer_id": customer_id,
            "groups": groups,
            "total": len(groups)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des groupes: {str(e)}")