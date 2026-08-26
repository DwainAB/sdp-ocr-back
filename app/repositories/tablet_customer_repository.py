from typing import Any, Dict, List, Optional

from app.database import get_connection
from app.crud import crud_customer, crud_formula, crud_notes


class TabletCustomerRepository:
    """
    Repository pour la recherche de client et l'historique de formules
    côté formulaire tablette (aglae-form).
    """

    def search_by_contact(self, email: Optional[str], phone: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Retrouve un client par email (prioritaire) puis par téléphone.
        En cas de plusieurs correspondances possibles, retourne la première trouvée.
        """
        email = (email or "").strip().lower() or None
        phone = (phone or "").strip() or None

        if not email and not phone:
            return None

        connection = get_connection()
        if not connection:
            return None

        try:
            customer = None
            if email:
                customer = crud_customer.get_by_email(connection, email)
            if not customer and phone:
                customer = crud_customer.get_by_phone_normalized(connection, phone)
            return customer
        finally:
            connection.close()

    def get_formula_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Historique des formules d'un client, plus récentes en premier."""
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_formula.get_by_customer_id(connection, customer_id)
        finally:
            connection.close()

    def get_formula_detail(self, formula_id: int) -> Optional[Dict[str, Any]]:
        """Détail complet d'une formule (infos + notes tête/cœur/fond)."""
        connection = get_connection()
        if not connection:
            return None

        try:
            formula = crud_formula.get_by_id(connection, formula_id)
            if not formula:
                return None

            formula["top_notes"] = crud_notes.get_notes_by_type(connection, "top_note", formula_id)
            formula["heart_notes"] = crud_notes.get_notes_by_type(connection, "heart_note", formula_id)
            formula["base_notes"] = crud_notes.get_notes_by_type(connection, "base_note", formula_id)
            formula["booster_notes"] = crud_notes.get_notes_by_type(connection, "booster_note", formula_id)
            return formula
        finally:
            connection.close()

    def reuse_formula(self, formula_id: int) -> Optional[Dict[str, Any]]:
        """Incrémente le compteur de réutilisation d'une formule existante."""
        connection = get_connection()
        if not connection:
            return None

        try:
            new_count = crud_formula.increment_reuse_count(connection, formula_id)
            if new_count is None:
                return None
            return {"formula_id": formula_id, "reuse_count": new_count}
        finally:
            connection.close()


tablet_customer_repository = TabletCustomerRepository()
