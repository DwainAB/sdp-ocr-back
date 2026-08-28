import urllib.parse

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.formula_schemas import (
    FormulaResponse,
    FormulaUpdateNotes,
    FormulaDeleteResponse,
)
from app.repositories.formula_repository import formula_repository
from app.repositories.customer_repository import customer_repository
from app.services.pdf.formula_sheet_pdf_service import generate_formula_sheet_pdf

router = APIRouter()


@router.get("/{formula_id}", response_model=FormulaResponse)
async def get_formula(formula_id: int):
    """
    Récupère une formule par son ID avec toutes ses notes
    """
    formula = formula_repository.get_formula_by_id(formula_id)
    if not formula:
        raise HTTPException(
            status_code=404,
            detail=f"Formule avec ID {formula_id} non trouvée"
        )

    return FormulaResponse(**formula)


@router.get("/{formula_id}/pdf")
async def get_formula_pdf(formula_id: int):
    """
    Génère et retourne la fiche formule en PDF (pyramide olfactive avec
    toutes les notes, quantités et informations client).

    Sert notamment pour les formules qui n'ont aucun document/fiche
    associé (ex: formules créées digitalement) afin de fournir un
    téléchargement de remplacement.
    """
    formula = formula_repository.get_formula_by_id(formula_id)
    if not formula:
        raise HTTPException(
            status_code=404,
            detail=f"Formule avec ID {formula_id} non trouvée"
        )

    customer = {}
    if formula.get("customer_id"):
        customer = customer_repository.get_customer_by_id(formula["customer_id"]) or {}

    pdf_bytes = generate_formula_sheet_pdf(customer, formula)

    reference = formula.get("reference") or f"formule-{formula_id}"
    safe_filename = urllib.parse.quote(f"fiche-{reference}.pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        },
    )


@router.put("/{formula_id}/notes", response_model=FormulaResponse)
async def update_formula_notes(formula_id: int, notes_update: FormulaUpdateNotes):
    """
    Met à jour les notes d'une formule.

    Pour chaque type de note (tête/cœur/fond):
    - Notes avec 'id' → UPDATE si modifiées
    - Notes sans 'id' → INSERT (nouvelles notes)
    - Notes absentes de la liste → DELETE (supprimées)

    Exemple de payload:
    {
        "top_notes": [
            {"id": 1, "name": "Bergamote", "quantity": "3"},  // UPDATE
            {"name": "Citron", "quantity": "2"}              // INSERT (pas d'id)
        ],
        "heart_notes": [
            {"id": 5, "name": "Rose", "quantity": "4"}       // UPDATE
        ],
        "base_notes": []  // Toutes les notes de fond seront supprimées
    }
    """
    # Vérifier que la formule existe
    existing_formula = formula_repository.get_formula_by_id(formula_id)
    if not existing_formula:
        raise HTTPException(
            status_code=404,
            detail=f"Formule avec ID {formula_id} non trouvée"
        )

    # Convertir les NoteUpdate en dict pour le repository
    top_notes_dict = None
    if notes_update.top_notes is not None:
        top_notes_dict = [note.model_dump() for note in notes_update.top_notes]

    heart_notes_dict = None
    if notes_update.heart_notes is not None:
        heart_notes_dict = [note.model_dump() for note in notes_update.heart_notes]

    base_notes_dict = None
    if notes_update.base_notes is not None:
        base_notes_dict = [note.model_dump() for note in notes_update.base_notes]

    # Mettre à jour les notes, le commentaire, la référence, le nom du parfum et/ou la date (skip_correction=True car modification manuelle)
    success = formula_repository.update_formula_notes(
        formula_id,
        top_notes=top_notes_dict,
        heart_notes=heart_notes_dict,
        base_notes=base_notes_dict,
        comment=notes_update.comment,
        reference=notes_update.reference,
        perfume_name=notes_update.perfume_name,
        date=notes_update.date,
        box_type=notes_update.box_type,
        skip_correction=True,  # Pas de correction automatique pour les modifications manuelles
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la mise à jour des notes"
        )

    # Récupérer la formule mise à jour
    updated_formula = formula_repository.get_formula_by_id(formula_id)
    return FormulaResponse(**updated_formula)


@router.delete("/{formula_id}", response_model=FormulaDeleteResponse)
async def delete_formula(formula_id: int):
    """
    Supprime une formule et toutes ses notes associées
    """
    # Vérifier que la formule existe
    existing_formula = formula_repository.get_formula_by_id(formula_id)
    if not existing_formula:
        raise HTTPException(
            status_code=404,
            detail=f"Formule avec ID {formula_id} non trouvée"
        )

    # Supprimer la formule
    success = formula_repository.delete_formula(formula_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de la formule"
        )

    return FormulaDeleteResponse(
        success=True,
        message=f"Formule {formula_id} et ses notes supprimées avec succès",
        formula_id=formula_id
    )
