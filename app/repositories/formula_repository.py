from typing import Dict, Any, List, Optional, Tuple

from app.database import get_connection
from app.crud import crud_formula, crud_notes
from app.utils.note_corrector import note_corrector


class FormulaRepository:
    """
    Repository pour gérer les formules et leurs notes associées.
    """

    def create_formula_with_notes(
        self,
        customer_id: Optional[int],
        file_id: int,
        extracted_data: Dict[str, Any],
        customer_review_id: Optional[int] = None,
        reference: Optional[str] = None,
        perfume_name: Optional[str] = None,
        box_type: Optional[str] = None,
    ) -> Tuple[Optional[int], bool]:
        """
        Crée une formule liée à un customer (optionnel) et à un fichier,
        puis insère les notes de tête / cœur / fond associées.

        Args:
            customer_id: ID du customer ou None (pour customers_review)
            file_id: ID du fichier source (customer_files.id)
            extracted_data: Données extraites de l'OCR, incluant
                            éventuellement notes_de_tete, notes_de_coeur,
                            notes_de_fond, et date.
            customer_review_id: ID du customer_review (optionnel)
            reference: Référence/identifiant de la formule (optionnel)
            perfume_name: Nom du parfum (optionnel)
            box_type: Coffret utilisé (optionnel)

        Returns:
            Tuple (formula_id, notes_were_corrected)
            - formula_id: ID de la formule créée ou None si erreur
            - notes_were_corrected: True si au moins une note a été corrigée
        """
        connection = get_connection()
        if not connection:
            return None, False

        try:
            # Extraire la date des données OCR
            date = (extracted_data.get('date') or '').strip() or None

            formula_id = crud_formula.create(
                connection, customer_id, file_id, customer_review_id=customer_review_id, reference=reference, perfume_name=perfume_name, date=date, box_type=box_type
            )
            if not formula_id:
                return None, False

            notes_were_corrected = False

            def _normalize_notes(key: str) -> List[Dict[str, Any]]:
                nonlocal notes_were_corrected
                raw_notes = extracted_data.get(key) or []
                if not isinstance(raw_notes, list):
                    return []
                normalized: List[Dict[str, Any]] = []
                for note in raw_notes:
                    if not isinstance(note, dict):
                        continue
                    name = (note.get("essence") or "").strip()
                    if not name or name == "---":
                        continue
                    
                    # Correction du nom via Fuzzy Matching
                    corrected_name = note_corrector.correct_note_name(name)
                    
                    # Vérifier si le nom a été modifié ou est inconnu
                    if corrected_name == "A définir":
                        notes_were_corrected = True
                        print(f"❓ Note inconnue : '{name}' → 'A définir'")
                    elif corrected_name != name:
                        notes_were_corrected = True
                        print(f"🔧 Note corrigée : '{name}' → '{corrected_name}'")
                    
                    quantity_raw = note.get("quantite_ml")
                    quantity = None
                    if quantity_raw is not None:
                        quantity = str(quantity_raw).strip()
                    normalized.append({"name": corrected_name, "quantity": quantity})
                return normalized

            top_notes = _normalize_notes("notes_de_tete")
            heart_notes = _normalize_notes("notes_de_coeur")
            base_notes = _normalize_notes("notes_de_fond")

            for note in top_notes:
                crud_notes.create_top_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            for note in heart_notes:
                crud_notes.create_heart_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            for note in base_notes:
                crud_notes.create_base_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            return formula_id, notes_were_corrected

        finally:
            connection.close()

    def get_formula_by_id(self, formula_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une formule par son ID avec toutes ses notes.

        Args:
            formula_id: ID de la formule

        Returns:
            Dictionnaire avec les données de la formule et ses notes, ou None si non trouvée
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            # Récupérer la formule
            formula = crud_formula.get_by_id(connection, formula_id)
            if not formula:
                return None

            # Récupérer les notes
            formula["top_notes"] = crud_notes.get_notes_by_type(connection, "top_note", formula_id)
            formula["heart_notes"] = crud_notes.get_notes_by_type(connection, "heart_note", formula_id)
            formula["base_notes"] = crud_notes.get_notes_by_type(connection, "base_note", formula_id)
            formula["booster_notes"] = crud_notes.get_notes_by_type(connection, "booster_note", formula_id)

            return formula

        finally:
            connection.close()

    def delete_formula(self, formula_id: int) -> bool:
        """
        Supprime une formule et toutes ses notes associées.

        Args:
            formula_id: ID de la formule à supprimer

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            # Supprimer d'abord toutes les notes
            crud_notes.delete_all_notes_by_formula(connection, formula_id)

            # Puis supprimer la formule
            success = crud_formula.delete(connection, formula_id)

            if success:
                print(f"✅ Formule {formula_id} et ses notes supprimées avec succès")

            return success

        finally:
            connection.close()

    def update_formula_notes(
        self,
        formula_id: int,
        top_notes: Optional[List[Dict[str, Any]]] = None,
        heart_notes: Optional[List[Dict[str, Any]]] = None,
        base_notes: Optional[List[Dict[str, Any]]] = None,
        comment: Optional[str] = None,
        reference: Optional[str] = None,
        perfume_name: Optional[str] = None,
        date: Optional[str] = None,
        box_type: Optional[str] = None,
        skip_correction: bool = True,
    ) -> bool:
        """
        Met à jour les notes et/ou le commentaire d'une formule.

        Pour chaque type de note (tête/cœur/fond):
        - Notes avec 'id' → UPDATE si modifiées
        - Notes sans 'id' → INSERT (nouvelles notes)
        - Notes absentes de la liste → DELETE (notes supprimées)

        Args:
            formula_id: ID de la formule
            top_notes: Liste des notes de tête (optionnel)
            heart_notes: Liste des notes de cœur (optionnel)
            base_notes: Liste des notes de fond (optionnel)
            comment: Commentaire de la formule (optionnel)
            reference: Référence/identifiant de la formule (optionnel)
            perfume_name: Nom du parfum (optionnel)
            date: Date de la formule (optionnel)
            box_type: Coffret utilisé (optionnel)
            skip_correction: Si True, ne pas corriger automatiquement les noms (défaut: True pour modifications manuelles)

        Format attendu pour chaque note:
        {
            "id": 123,  # Optionnel - présent = UPDATE, absent = INSERT
            "name": "Bergamote",
            "quantity": "2"
        }

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            # Vérifier que la formule existe
            formula = crud_formula.get_by_id(connection, formula_id)
            if not formula:
                print(f"❌ Formule {formula_id} non trouvée")
                return False

            def _update_notes_by_type(
                table_name: str,
                new_notes: Optional[List[Dict[str, Any]]],
            ) -> bool:
                """
                Met à jour les notes d'un type donné.
                """
                if new_notes is None:
                    return True

                # Récupérer les notes existantes
                existing_notes = crud_notes.get_notes_by_type(connection, table_name, formula_id)
                existing_ids = {note["id"] for note in existing_notes}

                # IDs présents dans la nouvelle liste
                new_ids = {note.get("id") for note in new_notes if note.get("id")}

                # 1) Supprimer les notes qui ne sont plus dans la liste
                ids_to_delete = existing_ids - new_ids
                for note_id in ids_to_delete:
                    crud_notes.delete_note(connection, table_name, note_id)
                    print(f"🗑️ Note {note_id} supprimée de {table_name}")

                # 2) Mettre à jour ou créer les notes
                for note in new_notes:
                    note_id = note.get("id")
                    name = note.get("name", "").strip()
                    quantity = note.get("quantity")

                    if not name:
                        continue

                    # Correction du nom via Fuzzy Matching (seulement si skip_correction=False)
                    corrected_name = name
                    if not skip_correction:
                        corrected_name = note_corrector.correct_note_name(name)
                        if corrected_name != name:
                            print(f"🔧 Note corrigée : '{name}' → '{corrected_name}'")

                    if note_id and note_id in existing_ids:
                        # UPDATE
                        crud_notes.update_note(
                            connection,
                            table_name,
                            note_id,
                            name=corrected_name,
                            quantity=quantity,
                        )
                        print(f"✏️ Note {note_id} mise à jour dans {table_name}")
                    else:
                        # INSERT
                        if table_name == "top_note":
                            crud_notes.create_top_note(connection, formula_id, corrected_name, quantity)
                        elif table_name == "heart_note":
                            crud_notes.create_heart_note(connection, formula_id, corrected_name, quantity)
                        elif table_name == "base_note":
                            crud_notes.create_base_note(connection, formula_id, corrected_name, quantity)
                        print(f"➕ Nouvelle note créée dans {table_name}: {corrected_name}")

                return True

            # Mettre à jour chaque type de note
            if top_notes is not None:
                _update_notes_by_type("top_note", top_notes)

            if heart_notes is not None:
                _update_notes_by_type("heart_note", heart_notes)

            if base_notes is not None:
                _update_notes_by_type("base_note", base_notes)

            # Mettre à jour le commentaire, la référence, le nom du parfum et/ou la date si fournis
            update_kwargs = {}
            if comment is not None:
                update_kwargs['comment'] = comment
            if reference is not None:
                update_kwargs['reference'] = reference
            if perfume_name is not None:
                update_kwargs['perfume_name'] = perfume_name
            if date is not None:
                update_kwargs['date'] = date
            if box_type is not None:
                update_kwargs['box_type'] = box_type

            if update_kwargs:
                crud_formula.update(connection, formula_id, **update_kwargs)
                if comment is not None:
                    print(f"💬 Commentaire de la formule {formula_id} mis à jour")
                if reference is not None:
                    print(f"🏷️ Référence de la formule {formula_id} mise à jour")
                if perfume_name is not None:
                    print(f"🍶 Nom du parfum de la formule {formula_id} mis à jour")
                if date is not None:
                    print(f"📅 Date de la formule {formula_id} mise à jour")
                if box_type is not None:
                    print(f"🎁 Coffret de la formule {formula_id} mis à jour")

            print(f"✅ Formule {formula_id} mise à jour avec succès")
            return True

        except Exception as e:
            print(f"❌ Erreur mise à jour notes formule {formula_id}: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()


formula_repository = FormulaRepository()

