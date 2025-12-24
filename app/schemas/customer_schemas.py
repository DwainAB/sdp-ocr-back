from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    """Schema de base pour les customers"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    reference: Optional[str] = None

class CustomerCreate(CustomerBase):
    """Schema pour créer un customer"""
    pass

class CustomerUpdate(CustomerBase):
    """Schema pour modifier un customer"""
    pass

class CustomerResponse(CustomerBase):
    """Schema de réponse avec l'ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    """Schema pour la liste des customers"""
    customers: list[CustomerResponse]
    total: int
    page: int
    size: int