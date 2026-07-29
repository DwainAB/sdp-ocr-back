from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.database import get_connection
from app.crud import crud_customer, crud_formula, crud_notes
from app.services.customer import customer_business_service
from app.services.phone import phone_validator
from app.schemas.tablet_schemas import TabletSubmissionCreate


class TabletSubmissionRepository:
    """
    Repository pour les soumissions du formulaire tablette (aglae-form).

    Contrairement au flux OCR, un doublon email/téléphone n'est pas envoyé
    en customers_review : la nouvelle formule est rattachée au client existant.
    """

    def create_submission(
        self, submission: TabletSubmissionCreate
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Enregistre une soumission tablette : retrouve ou crée le client,
        puis crée la formule et ses notes.

        Returns:
            Tuple (résultat, erreur)
            - résultat: dict avec customer_id, formula_id, customer_was_existing, matched_by
            - erreur: message d'erreur ou None
        """
        email = (submission.email or "").strip().lower() or None
        phone = self._normalize_phone(submission.phone, submission.country)

        if not email and not phone:
            return None, "Email ou téléphone requis"

        connection = get_connection()
        if not connection:
            return None, "Connexion base de données impossible"

        try:
            # 1) Recherche d'un client existant (email prioritaire, téléphone en fallback)
            existing = None
            matched_by = None
            if email:
                existing = crud_customer.get_by_email(connection, email)
                if existing:
                    matched_by = "email"
            if not existing and phone:
                existing = crud_customer.get_by_phone_normalized(connection, phone)
                if existing:
                    matched_by = "phone"

            customer_fields = self._build_customer_fields(submission, email, phone)

            if existing:
                customer_id = existing["id"]
                # Compléter uniquement les champs vides du client existant
                missing = {
                    k: v for k, v in customer_fields.items()
                    if v is not None and not existing.get(k)
                }
                if missing:
                    crud_customer.update(connection, customer_id, missing)
            else:
                customer_id = customer_business_service.create_customer_with_validation(
                    customer_fields
                )
                if not customer_id:
                    return None, "Échec de la création du client"

            # 2) Créer la formule (pas de fiche scannée → file_id None)
            now = datetime.now()
            reference = crud_formula.generate_tablet_reference(
                connection, now.strftime("%y%m")
            )
            formula_id = crud_formula.create(
                connection,
                customer_id=customer_id,
                file_id=None,
                reference=reference,
                perfume_name=submission.perfume_name,
                date=now.strftime("%Y-%m-%d"),
                quantity=submission.quantity,
                source="tablet",
                supervisor_id=submission.supervisor_id,
            )
            if not formula_id:
                return None, "Échec de la création de la formule"

            # 3) Insérer les notes (noms canoniques venant du référentiel)
            for note in submission.top_notes:
                crud_notes.create_top_note(connection, formula_id, note.name, note.quantity)
            for note in submission.heart_notes:
                crud_notes.create_heart_note(connection, formula_id, note.name, note.quantity)
            for note in submission.base_notes:
                crud_notes.create_base_note(connection, formula_id, note.name, note.quantity)

            return {
                "customer_id": customer_id,
                "formula_id": formula_id,
                "customer_was_existing": existing is not None,
                "matched_by": matched_by,
            }, None

        finally:
            connection.close()

    @staticmethod
    def _normalize_phone(phone: Optional[str], country: Optional[str]) -> Optional[str]:
        phone = (phone or "").strip() or None
        if not phone:
            return None
        normalized, _, error_type = phone_validator.validate_phone_number(phone, country)
        if error_type == "invalid_length":
            # On garde le numéro saisi tel quel plutôt que de bloquer la vente
            return normalized or phone
        return normalized or phone

    @staticmethod
    def _build_customer_fields(
        submission: TabletSubmissionCreate,
        email: Optional[str],
        phone: Optional[str],
    ) -> Dict[str, Any]:
        def clean(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            return str(value).strip() or None

        return {
            "first_name": clean(submission.first_name),
            "last_name": clean(submission.last_name),
            "email": email,
            "phone": phone,
            "job": clean(submission.job),
            "city": clean(submission.city),
            "country": clean(submission.country),
            "gender": clean(submission.gender),
            "birth_date": clean(submission.birth_date),
            "has_allergy": submission.has_allergy,
            "liability_accepted": submission.liability_accepted,
            "rgpd_consent": submission.rgpd_consent,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }


tablet_submission_repository = TabletSubmissionRepository()
