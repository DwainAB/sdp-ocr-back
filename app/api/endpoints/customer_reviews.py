from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math

from app.schemas.customer_review_schemas import (
    CustomerReviewCreate,
    CustomerReviewUpdate,
    CustomerReviewResponse,
    CustomerReviewListResponse,
    TransferResponse
)
from app.repositories.customer_review_repository import customer_review_repository

router = APIRouter()

@router.post("/", response_model=CustomerReviewResponse)
async def create_customer_review(customer_review: CustomerReviewCreate):
    """
    Crée un nouveau customer review
    """
    customer_data = customer_review.model_dump(exclude_unset=True)
    review_type = customer_data.pop('type')

    review_id = customer_review_repository.insert_customer_review(customer_data, review_type)

    if not review_id:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création du customer review"
        )

    # Récupérer le customer review créé
    created_review = customer_review_repository.get_customer_review_by_id(review_id)
    if not created_review:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération du customer review créé"
        )

    return CustomerReviewResponse(**created_review)

@router.get("/", response_model=CustomerReviewListResponse)
async def get_customer_reviews(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de la page"),
    review_type: Optional[str] = Query(None, description="Filtrer par type de review")
):
    """
    Récupère tous les customers review avec pagination et filtre optionnel par type
    """
    reviews, total = customer_review_repository.get_all_customer_reviews(
        page=page,
        size=size,
        review_type=review_type
    )

    # Calculer le nombre total de pages
    total_pages = math.ceil(total / size) if total > 0 else 0

    return CustomerReviewListResponse(
        customers=reviews,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )

@router.get("/{review_id}", response_model=CustomerReviewResponse)
async def get_customer_review(review_id: int):
    """
    Récupère un customer review par son ID
    """
    review = customer_review_repository.get_customer_review_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=404,
            detail=f"Customer review avec ID {review_id} non trouvé"
        )

    return CustomerReviewResponse(**review)

@router.put("/{review_id}", response_model=CustomerReviewResponse)
async def update_customer_review(review_id: int, customer_update: CustomerReviewUpdate):
    """
    Met à jour un customer review
    """
    # Vérifier que le review existe
    existing_review = customer_review_repository.get_customer_review_by_id(review_id)
    if not existing_review:
        raise HTTPException(
            status_code=404,
            detail=f"Customer review avec ID {review_id} non trouvé"
        )

    # Mettre à jour
    update_data = customer_update.model_dump(exclude_unset=True)
    success = customer_review_repository.update_customer_review(review_id, update_data)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la mise à jour du customer review"
        )

    # Récupérer le customer review mis à jour
    updated_review = customer_review_repository.get_customer_review_by_id(review_id)
    return CustomerReviewResponse(**updated_review)

@router.delete("/{review_id}")
async def delete_customer_review(review_id: int):
    """
    Supprime définitivement un customer review
    """
    # Vérifier que le review existe
    existing_review = customer_review_repository.get_customer_review_by_id(review_id)
    if not existing_review:
        raise HTTPException(
            status_code=404,
            detail=f"Customer review avec ID {review_id} non trouvé"
        )

    success = customer_review_repository.delete_customer_review(review_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression du customer review"
        )

    return {
        "success": True,
        "message": f"Customer review {review_id} supprimé avec succès"
    }

@router.post("/{review_id}/transfer", response_model=TransferResponse)
async def transfer_customer_review(review_id: int):
    """
    Transfère un customer review vers la table customers (validation)
    Le customer review est supprimé après le transfert
    """
    # Vérifier que le review existe
    existing_review = customer_review_repository.get_customer_review_by_id(review_id)
    if not existing_review:
        raise HTTPException(
            status_code=404,
            detail=f"Customer review avec ID {review_id} non trouvé"
        )

    # Effectuer le transfert
    customer_id = customer_review_repository.transfer_to_customers(review_id)

    if not customer_id:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors du transfert du customer review"
        )

    return TransferResponse(
        success=True,
        message=f"Customer review {review_id} transféré avec succès vers customers",
        customer_id=customer_id,
        review_id=review_id
    )