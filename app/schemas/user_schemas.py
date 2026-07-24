from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.schemas.role_schemas import RoleResponse

class UserBase(BaseModel):
    """Schema de base pour les users"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job: Optional[str] = None
    role_id: Optional[int] = None
    is_online: Optional[bool] = False
    team: Optional[str] = None
    identifier: Optional[str] = None
    csv_download_count: Optional[int] = 0
    csv_download_reset_at: Optional[datetime] = None
    pdf_extraction_count: Optional[int] = 0
    pdf_extraction_reset_at: Optional[datetime] = None

class UserCreate(UserBase):
    """Schema pour créer un user"""
    pass

class UserUpdate(UserBase):
    """Schema pour modifier un user"""
    pass

class UserResponse(UserBase):
    """Schema de réponse avec l'ID"""
    id: int
    identifier: Optional[str] = None
    last_login_at: Optional[datetime] = None
    csv_download_count: Optional[int] = 0
    csv_download_reset_at: Optional[datetime] = None
    pdf_extraction_count: Optional[int] = 0
    pdf_extraction_reset_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Schema pour la liste des users"""
    users: list[UserResponse]
    total: int
    page: int
    size: int

class UserLoginUpdate(BaseModel):
    """Schema pour mettre à jour le statut de connexion"""
    is_online: bool
    last_login_at: Optional[datetime] = None

class UserWithRoleResponse(BaseModel):
    """Schema de réponse avec les infos utilisateur et son rôle complet"""
    id: int
    identifier: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job: Optional[str] = None
    is_online: Optional[bool] = False
    team: Optional[str] = None
    last_login_at: Optional[datetime] = None
    csv_download_count: Optional[int] = 0
    csv_download_reset_at: Optional[datetime] = None
    pdf_extraction_count: Optional[int] = 0
    pdf_extraction_reset_at: Optional[datetime] = None
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True