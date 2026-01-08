from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime

class CustomerReviewBase(BaseModel):
    """
    Schéma de base pour les customers review
    """
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    job: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    reference: Optional[str] = None
    date: Optional[str] = None
    verified_email: Optional[str] = None
    verified_domain: Optional[str] = None
    verified_phone: Optional[str] = None
    type: str

class CustomerReviewCreate(CustomerReviewBase):
    """
    Schéma pour créer un customer review
    """
    pass

class CustomerReviewUpdate(BaseModel):
    """
    Schéma pour mettre à jour un customer review
    """
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    job: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    reference: Optional[str] = None
    date: Optional[str] = None
    verified_email: Optional[str] = None
    verified_domain: Optional[str] = None
    verified_phone: Optional[str] = None
    type: Optional[str] = None

class CustomerReviewResponse(CustomerReviewBase):
    """
    Schéma de réponse pour un customer review
    """
    id: int

    @field_validator('verified_email', 'verified_domain', 'verified_phone', mode='before')
    @classmethod
    def validate_verified_email(cls, v):
        """Convertit les valeurs non-string en string pour verified_email, verified_domain et verified_phone"""
        if v is None:
            return None
        return str(v) if v not in [0, ""] else None

    @field_validator('email', 'phone', 'job', 'city', 'country', 'reference', 'date', 'first_name', 'last_name', mode='before')
    @classmethod
    def validate_string_fields(cls, v):
        """Convertit les valeurs non-string en string et traite les valeurs vides"""
        if v is None or v == "" or v == 0:
            return None
        return str(v)

    class Config:
        from_attributes = True

class CustomerReviewListResponse(BaseModel):
    """
    Schéma de réponse pour la liste paginée de customers review
    """
    customers: List[CustomerReviewResponse]
    total: int
    page: int
    size: int
    total_pages: int

class TransferResponse(BaseModel):
    """
    Schéma de réponse pour le transfert d'un customer review vers customers
    """
    success: bool
    message: str
    customer_id: Optional[int] = None
    review_id: int