from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    created_by: int


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    created_by: int

    class Config:
        from_attributes = True


# Schémas pour gérer les relations clients-groupes
class AddCustomersToGroup(BaseModel):
    customer_ids: List[int]
    added_by: int


class RemoveCustomersFromGroup(BaseModel):
    customer_ids: List[int]


class CustomerGroupResponse(BaseModel):
    customer_id: int
    group_id: int
    added_at: datetime
    added_by: int

    class Config:
        from_attributes = True