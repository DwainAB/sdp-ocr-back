from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Schema de base pour les users"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job: Optional[str] = None
    role: Optional[str] = None
    is_online: Optional[bool] = False
    team: Optional[str] = None

class UserCreate(UserBase):
    """Schema pour créer un user"""
    pass

class UserUpdate(UserBase):
    """Schema pour modifier un user"""
    pass

class UserResponse(UserBase):
    """Schema de réponse avec l'ID"""
    id: int
    last_login_at: Optional[datetime] = None

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