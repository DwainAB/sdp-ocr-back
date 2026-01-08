from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CustomerFileBase(BaseModel):
    """Schema de base pour les fichiers customers"""
    customer_id: Optional[int] = None
    customer_review_id: Optional[int] = None
    file_path: str
    file_name: str
    file_type: str
    file_size: int


class CustomerFileCreate(CustomerFileBase):
    """Schema pour créer un fichier customer"""
    pass


class CustomerFileUpdate(BaseModel):
    """Schema pour mettre à jour un fichier customer"""
    customer_id: Optional[int] = None
    customer_review_id: Optional[int] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None


class CustomerFileResponse(CustomerFileBase):
    """Schema de réponse avec l'ID et timestamps"""
    id: int
    uploaded_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerFileListResponse(BaseModel):
    """Schema pour la liste des fichiers d'un customer"""
    files: List[CustomerFileResponse]
    total: int
