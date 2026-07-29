from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.repositories.customer_repository import customer_repository
from app.schemas.customer_schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerBulkUpdateRequest,
    CustomerBulkUpdateResponse,
    CustomerBulkUpdateResultItem
)

router = APIRouter()

@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate):
    """
    Créer un nouveau customer
    """
    try:
        customer_id = customer_repository.create_customer(customer.dict())

        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la création du customer"
            )

        # Récupérer le customer créé
        created_customer = customer_repository.get_customer_by_id(customer_id)
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
    search: Optional[str] = Query(None, description="Recherche dans nom, email, téléphone, ville, référence de formule"),
    v2: bool = Query(False, description="Filtrer par version du formulaire (true=v2, false=v1)"),
    country: Optional[str] = Query(None, description="Filtrer par pays")
):
    """
    Récupérer tous les customers avec pagination, recherche et filtre pays
    """
    try:
        customers, total = customer_repository.get_all_customers(page, size, search, v2, country)

        customer_responses = []
        for customer in customers:
            # Assurer que verified_email est toujours présent
            if 'verified_email' not in customer or customer['verified_email'] is None:
                customer['verified_email'] = False
            elif customer['verified_email'] == 0:
                customer['verified_email'] = False
            elif customer['verified_email'] == 1:
                customer['verified_email'] = True

            # Assurer que verified_domain est toujours présent
            if 'verified_domain' not in customer or customer['verified_domain'] is None:
                customer['verified_domain'] = False
            elif customer['verified_domain'] == 0:
                customer['verified_domain'] = False
            elif customer['verified_domain'] == 1:
                customer['verified_domain'] = True

            # Assurer que verified_phone est toujours présent
            if 'verified_phone' not in customer or customer['verified_phone'] is None:
                customer['verified_phone'] = False
            elif customer['verified_phone'] == 0:
                customer['verified_phone'] = False
            elif customer['verified_phone'] == 1:
                customer['verified_phone'] = True

            customer_response = CustomerResponse(**customer)
            print(f"Debug - Customer {customer.get('id')}: verified_email = {customer.get('verified_email')}, verified_domain = {customer.get('verified_domain')}, verified_phone = {customer.get('verified_phone')}")
            customer_responses.append(customer_response)

        return CustomerListResponse(
            customers=customer_responses,
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.put("/bulk", response_model=CustomerBulkUpdateResponse)
async def bulk_update_customers(request: CustomerBulkUpdateRequest):
    """
    Mettre à jour plusieurs customers en masse.
    Chaque item contient un id et les champs à modifier.
    """
    try:
        updates = [
            customer.dict(exclude_unset=True)
            for customer in request.customers
        ]

        results = customer_repository.bulk_update_customers(updates)

        result_items = [CustomerBulkUpdateResultItem(**r) for r in results]
        total_updated = sum(1 for r in results if r["success"])

        return CustomerBulkUpdateResponse(
            updated=result_items,
            total_requested=len(updates),
            total_updated=total_updated
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/stats/analytics")
async def get_customers_analytics():
    """
    Statistiques d'analyse des clients : évolution mensuelle, répartition
    par mois/année, taux de rétention (>= 2 formules), top 5 pays
    """
    try:
        return customer_repository.get_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/countries", response_model=List[str])
async def get_countries():
    """
    Récupère la liste des pays distincts
    """
    try:
        countries = customer_repository.get_countries()
        return countries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    """
    Récupérer un customer par son ID
    """
    try:
        customer = customer_repository.get_customer_by_id(customer_id)

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
        existing_customer = customer_repository.get_customer_by_id(customer_id)
        if not existing_customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer avec ID {customer_id} non trouvé"
            )

        # Mettre à jour
        success = customer_repository.update_customer(
            customer_id,
            customer.dict(exclude_unset=True)
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Erreur lors de la mise à jour"
            )

        # Récupérer le customer mis à jour
        updated_customer = customer_repository.get_customer_by_id(customer_id)
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
        existing_customer = customer_repository.get_customer_by_id(customer_id)
        if not existing_customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer avec ID {customer_id} non trouvé"
            )

        # Supprimer
        success = customer_repository.delete_customer(customer_id)

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
        customers, total = customer_repository.get_all_customers(page=1, size=1000)

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