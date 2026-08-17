from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.tablet_schemas import (
    CustomerSearchResult,
    FormulaDetail,
    FormulaHistoryItem,
    FormulaReuseResponse,
    NoteCatalogItem,
    NotesCatalogResponse,
    SuggestedNoteQuantity,
    SuggestQuantitiesRequest,
    SuggestQuantitiesResponse,
    TabletSubmissionCreate,
    TabletSubmissionResponse,
)
from app.repositories.tablet_submission_repository import tablet_submission_repository
from app.repositories.tablet_customer_repository import tablet_customer_repository
from app.services.perfumer import perfumer_service
from app.utils.note_corrector import NoteCorrector

router = APIRouter()


@router.get("/notes", response_model=NotesCatalogResponse)
async def get_notes_catalog():
    """
    Référentiel des notes disponibles pour la composition sur tablette,
    groupées par type (tête / cœur / fond).
    """
    def _items(category: str):
        return sorted(
            (
                NoteCatalogItem(code=code, name=name)
                for code, name in NoteCorrector.DATA[category].items()
            ),
            key=lambda item: item.name,
        )

    return NotesCatalogResponse(
        top_notes=_items("T"),
        heart_notes=_items("C"),
        base_notes=_items("F"),
    )


@router.post("/formulas/suggest-quantities", response_model=SuggestQuantitiesResponse)
async def suggest_note_quantities(request: SuggestQuantitiesRequest):
    """
    Calcule intelligemment (IA) la quantité en ml de chaque note choisie,
    à partir de l'intensité souhaitée et du volume total du flacon.
    Ne persiste rien : le front envoie ensuite la soumission finale (avec les
    quantités, éventuellement ajustées) à /submissions.
    """
    if not request.top_notes and not request.heart_notes and not request.base_notes:
        raise HTTPException(status_code=422, detail="Au moins une note est requise")

    quantities = perfumer_service.suggest_quantities(
        top_notes=request.top_notes,
        heart_notes=request.heart_notes,
        base_notes=request.base_notes,
        intensity=request.intensity,
        total_volume_ml=request.total_volume_ml,
    )

    def _to_items(family: str, notes: list[str]) -> list[SuggestedNoteQuantity]:
        return [
            SuggestedNoteQuantity(name=note, quantity_ml=quantities[family][note])
            for note in notes
        ]

    return SuggestQuantitiesResponse(
        top_notes=_to_items("top", request.top_notes),
        heart_notes=_to_items("heart", request.heart_notes),
        base_notes=_to_items("base", request.base_notes),
        total_volume_ml=request.total_volume_ml,
    )


@router.post("/submissions", response_model=TabletSubmissionResponse)
async def create_tablet_submission(submission: TabletSubmissionCreate):
    """
    Enregistre une soumission du formulaire tablette :
    - retrouve le client par email (prioritaire) ou téléphone, sinon le crée
    - crée la formule (source 'tablet', sans fiche scannée) et ses notes
    """
    if not submission.top_notes and not submission.heart_notes and not submission.base_notes:
        raise HTTPException(status_code=422, detail="Au moins une note est requise")

    result, error = tablet_submission_repository.create_submission(submission)
    if error:
        raise HTTPException(status_code=500, detail=error)

    return TabletSubmissionResponse(**result)


@router.get("/customers/search", response_model=CustomerSearchResult)
async def search_customer(
    email: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
):
    """
    Retrouve un client par email (prioritaire) ou téléphone, pour la tablette.
    Retourne 404 si aucun client ne correspond.
    """
    if not email and not phone:
        raise HTTPException(status_code=422, detail="Email ou téléphone requis")

    customer = tablet_customer_repository.search_by_contact(email, phone)
    if not customer:
        raise HTTPException(status_code=404, detail="Aucun client trouvé")

    return CustomerSearchResult(**customer)


@router.get("/customers/{customer_id}/formulas", response_model=list[FormulaHistoryItem])
async def get_customer_formula_history(customer_id: int):
    """Historique des formules d'un client, de la plus récente à la plus ancienne."""
    formulas = tablet_customer_repository.get_formula_history(customer_id)
    return [FormulaHistoryItem(**f) for f in formulas]


@router.get("/formulas/{formula_id}", response_model=FormulaDetail)
async def get_formula_detail(formula_id: int):
    """Détail complet d'une formule (notes tête/cœur/fond incluses)."""
    formula = tablet_customer_repository.get_formula_detail(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formule introuvable")

    return FormulaDetail(**formula)


@router.post("/formulas/{formula_id}/reuse", response_model=FormulaReuseResponse)
async def reuse_formula(formula_id: int):
    """Incrémente le compteur de réutilisation d'une formule existante."""
    result = tablet_customer_repository.reuse_formula(formula_id)
    if not result:
        raise HTTPException(status_code=404, detail="Formule introuvable")

    return FormulaReuseResponse(**result)
