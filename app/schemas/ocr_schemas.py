from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class DocumentType(str, Enum):
    BLANK_SHEET = "blank_sheet"
    STUDIO_PARFUMS = "studio_parfums"
    UNKNOWN = "unknown"

class BlankSheetData(BaseModel):
    month_year: Optional[str] = None
    fiches_manquantes: List[str] = []
    doublons: List[str] = []
    tel: List[str] = []
    mail: List[str] = []

class StudioParfumsData(BaseModel):
    title_detected: bool = False
    identifiant: Optional[str] = None  # L'ID en haut de page (commence par 20)
    genre: Optional[str] = None  # "Mr", "Mme", "Mlle"
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None
    profession: Optional[str] = None
    date_naissance: Optional[str] = None

class ProcessedPage(BaseModel):
    page_number: int
    document_type: DocumentType
    confidence: float
    raw_text: str
    extracted_data: Dict[str, Any]

class OCRResponse(BaseModel):
    success: bool
    filename: str
    total_pages: int
    processed_pages: List[ProcessedPage]
    summary: Dict[str, Any]