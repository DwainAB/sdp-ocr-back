from pydantic import BaseModel
from typing import Optional, List


class NoteBase(BaseModel):
    """
    Schéma de base pour une note de parfum
    """
    name: str
    quantity: Optional[str] = None


class NoteCreate(NoteBase):
    """
    Schéma pour créer une note (sans ID)
    """
    pass


class NoteUpdate(BaseModel):
    """
    Schéma pour mettre à jour une note
    """
    id: Optional[int] = None  # Si présent = UPDATE, si absent = INSERT
    name: str
    quantity: Optional[str] = None


class NoteResponse(NoteBase):
    """
    Schéma de réponse pour une note
    """
    id: int
    formula_id: int

    class Config:
        from_attributes = True


class FormulaBase(BaseModel):
    """
    Schéma de base pour une formule
    """
    customer_id: Optional[int] = None
    file_id: Optional[int] = None
    customer_review_id: Optional[int] = None
    comment: Optional[str] = None
    reference: Optional[str] = None
    perfume_name: Optional[str] = None
    date: Optional[str] = None
    quantity: Optional[str] = None
    source: Optional[str] = None
    supervisor_id: Optional[int] = None


class FormulaCreate(FormulaBase):
    """
    Schéma pour créer une formule avec ses notes (issue d'une fiche scannée)
    """
    file_id: int
    top_notes: List[NoteCreate] = []
    heart_notes: List[NoteCreate] = []
    base_notes: List[NoteCreate] = []


class FormulaUpdateNotes(BaseModel):
    """
    Schéma pour mettre à jour les notes d'une formule

    Pour chaque type de note:
    - Notes avec 'id' → UPDATE si modifiées
    - Notes sans 'id' → INSERT (nouvelles notes)
    - Notes absentes de la liste → DELETE (supprimées)
    """
    top_notes: Optional[List[NoteUpdate]] = None
    heart_notes: Optional[List[NoteUpdate]] = None
    base_notes: Optional[List[NoteUpdate]] = None
    comment: Optional[str] = None
    reference: Optional[str] = None
    perfume_name: Optional[str] = None
    date: Optional[str] = None


class FormulaResponse(FormulaBase):
    """
    Schéma de réponse pour une formule avec ses notes
    """
    id: int
    supervisor_name: Optional[str] = None
    top_notes: List[NoteResponse] = []
    heart_notes: List[NoteResponse] = []
    base_notes: List[NoteResponse] = []

    class Config:
        from_attributes = True


class FormulaDeleteResponse(BaseModel):
    """
    Schéma de réponse pour la suppression d'une formule
    """
    success: bool
    message: str
    formula_id: int
