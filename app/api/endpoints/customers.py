from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.db.customer_service import customer_service
from app.schemas.customer_schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse
)

router = APIRouter()

@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate):
    """
    Créer un nouveau customer
    """
    try:
        customer_id = customer_service.create_customer(customer.dict())

        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la création du customer"
            )

        # Récupérer le customer créé
        created_customer = customer_service.get_customer_by_id(customer_id)
        if not created_customer:
            raise HTTPException(
                status_code=500,
                detail="Customer créé mais impossible à récupérer"
            )

        return CustomerResponse(**created_customer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("", response_model=CustomerListResponse)
async def get_customers(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de page"),
    search: Optional[str] = Query(None, description="Recherche dans nom, email, téléphone, ville")
):
    """
    Récupérer tous les customers avec pagination et recherche
    """
    try:
        customers, total = customer_service.get_all_customers(page, size, search)

        return CustomerListResponse(
            customers=[CustomerResponse(**customer) for customer in customers],
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    """
    Récupérer un customer par son ID
    """
    try:
        customer = customer_service.get_customer_by_id(customer_id)

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer avec ID {customer_id} non trouvé"
            )

        return CustomerResponse(**customer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, customer: CustomerUpdate):
    """
    Mettre à jour un customer
    """
    try:
        # Vérifier que le customer existe
        existing_customer = customer_service.get_customer_by_id(customer_id)
        if not existing_customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer avec ID {customer_id} non trouvé"
            )

        # Mettre à jour
        success = customer_service.update_customer(
            customer_id,
            customer.dict(exclude_unset=True)
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la mise à jour"
            )

        # Récupérer le customer mis à jour
        updated_customer = customer_service.get_customer_by_id(customer_id)
        return CustomerResponse(**updated_customer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.delete("/{customer_id}")
async def delete_customer(customer_id: int):
    """
    Supprimer un customer
    """
    try:
        # Vérifier que le customer existe
        existing_customer = customer_service.get_customer_by_id(customer_id)
        if not existing_customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer avec ID {customer_id} non trouvé"
            )

        # Supprimer
        success = customer_service.delete_customer(customer_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la suppression"
            )

        return {"message": f"Customer {customer_id} supprimé avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/stats/summary")
async def get_customers_stats():
    """
    Statistiques sur les customers
    """
    try:
        customers, total = customer_service.get_all_customers(page=1, size=1000)

        # Calculer quelques stats basiques
        stats = {
            "total_customers": total,
            "with_email": len([c for c in customers if c.get('email')]),
            "with_phone": len([c for c in customers if c.get('phone')]),
            "with_city": len([c for c in customers if c.get('city')]),
            "countries": list(set([c.get('country') for c in customers if c.get('country')])),
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")