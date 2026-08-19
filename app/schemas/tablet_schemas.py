from typing import List, Optional
from pydantic import BaseModel, Field


class TabletNote(BaseModel):
    """Note choisie sur la tablette (nom canonique du référentiel)"""
    name: str
    quantity: Optional[str] = None


class TabletSubmissionCreate(BaseModel):
    """Payload complet envoyé par la tablette après confirmation"""
    gender: Optional[str] = None
    first_name: str
    last_name: str
    birth_date: Optional[str] = Field(None, description="Format YYYY-MM-DD")
    job: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    phone: str
    email: str
    has_allergy: Optional[bool] = None
    liability_accepted: Optional[bool] = None
    rgpd_consent: bool
    quantity: Optional[str] = None
    perfume_name: Optional[str] = None
    supervisor_id: Optional[int] = None
    top_notes: List[TabletNote] = []
    heart_notes: List[TabletNote] = []
    base_notes: List[TabletNote] = []


class TabletSubmissionResponse(BaseModel):
    """Résultat de l'enregistrement d'une soumission tablette"""
    customer_id: int
    formula_id: int
    customer_was_existing: bool
    matched_by: Optional[str] = Field(None, description="'email' ou 'phone' si client existant")


class NoteCatalogItem(BaseModel):
    """Une note du référentiel"""
    code: str
    name: str


class NotesCatalogResponse(BaseModel):
    """Référentiel des notes disponibles, groupées par type"""
    top_notes: List[NoteCatalogItem]
    heart_notes: List[NoteCatalogItem]
    base_notes: List[NoteCatalogItem]


class CustomerSearchResult(BaseModel):
    """Client retrouvé par email ou téléphone, à faire valider par le client"""
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class FormulaHistoryItem(BaseModel):
    """Une formule passée d'un client, pour l'écran de choix"""
    id: int
    perfume_name: Optional[str] = None
    date: Optional[str] = None
    quantity: Optional[str] = None
    reuse_count: int = 0


class FormulaDetail(FormulaHistoryItem):
    """Détail complet d'une formule, pour la modal de consultation"""
    top_notes: List[TabletNote] = []
    heart_notes: List[TabletNote] = []
    base_notes: List[TabletNote] = []


class FormulaReuseResponse(BaseModel):
    """Résultat de l'incrémentation du compteur de réutilisation"""
    formula_id: int
    reuse_count: int


class SuggestQuantitiesRequest(BaseModel):
    """Notes choisies + préférences client, pour dosage IA en ml"""
    top_notes: List[str] = []
    heart_notes: List[str] = []
    base_notes: List[str] = []
    intensity: str = Field(..., description="'light', 'moderate' ou 'strong' (libellé localisé accepté)")
    total_volume_ml: float = Field(..., gt=0, description="Taille du flacon souhaitée, en ml")
    box_set: Optional[str] = Field(
        None, description="Coffret choisi (ex: 'Classic'), pour appliquer les bonnes règles de dosage max"
    )


class SuggestedNoteQuantity(BaseModel):
    """Quantité en ml calculée par l'IA pour une note"""
    name: str
    quantity_ml: float


class SuggestQuantitiesResponse(BaseModel):
    """Répartition en ml de chaque note, calculée par l'IA selon l'intensité et le volume total"""
    top_notes: List[SuggestedNoteQuantity] = []
    heart_notes: List[SuggestedNoteQuantity] = []
    base_notes: List[SuggestedNoteQuantity] = []
    total_volume_ml: float
