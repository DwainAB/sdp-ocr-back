from pydantic import BaseModel
from typing import List


class UserData(BaseModel):
    reference: str
    first_name: str
    last_name: str
    email: str
    phone: str
    job: str
    city: str
    country: str


class ExportRequest(BaseModel):
    data: List[UserData]