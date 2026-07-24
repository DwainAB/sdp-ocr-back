from pydantic import BaseModel
from typing import Optional


class RoleBase(BaseModel):
    """Schéma de base pour les rôles"""
    name: str
    csv_download_limit: int = 0
    email_sending: bool = False
    pdf_extraction_limit: int = 0
    customers_access: bool = False
    customers_edit: bool = False
    access_to_extraction: bool = False
    customers_review_access: bool = False
    formula_edit: bool = False
    full_access: bool = False
    devices_access: bool = False


class RoleCreate(RoleBase):
    """Schéma pour la création d'un rôle"""
    pass


class RoleUpdate(BaseModel):
    """Schéma pour la mise à jour d'un rôle"""
    name: Optional[str] = None
    csv_download_limit: Optional[int] = None
    email_sending: Optional[bool] = None
    pdf_extraction_limit: Optional[int] = None
    customers_access: Optional[bool] = None
    customers_edit: Optional[bool] = None
    access_to_extraction: Optional[bool] = None
    customers_review_access: Optional[bool] = None
    formula_edit: Optional[bool] = None
    full_access: Optional[bool] = None
    devices_access: Optional[bool] = None


class RoleResponse(RoleBase):
    """Schéma de réponse pour un rôle"""
    id: int
    csv_download_limit: Optional[int] = 0
    pdf_extraction_limit: Optional[int] = 0

    class Config:
        from_attributes = True
