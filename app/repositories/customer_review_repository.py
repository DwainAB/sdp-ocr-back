from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_customer_review
from app.services.email import email_validator, email_domain_corrector, email_domain_validator
from app.services.phone import phone_intelligence_validator


class CustomerReviewRepository:
    """
    Repository pour gérer l'accès aux données customers_review (Data Access Layer)
    """

    def insert_customer_review(self, customer_data: Dict[str, Any],
                               review_type: str) -> Optional[int]:
        """
        Insère un customer dans la table customers_review avec un type spécifique

        Args:
            customer_data: Données du customer
            review_type: Type de review (ex: "Doublon - Mail", "Doublon - Phone")

        Returns:
            ID du customer_review inséré ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            customer_review_id = crud_customer_review.create(
                connection,
                customer_data,
                review_type
            )

            if customer_review_id:
                print(f"Customer review créé avec ID: {customer_review_id}, type: {review_type}")

            return customer_review_id
        finally:
            connection.close()

    def get_customer_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un customer_review par son ID avec ses formules et notes

        Args:
            review_id: ID du customer_review

        Returns:
            Dictionnaire avec les données du customer_review enrichi avec formules et notes, ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            # 1) Récupération de base du customer_review
            review = crud_customer_review.get_by_id(connection, review_id)
            if not review:
                return None

            # 2) Enrichir avec les formules et notes
            def _get_notes(table_name: str, formula_id: int) -> List[Dict[str, Any]]:
                cursor = connection.cursor()
                try:
                    query = f"""
                        SELECT id, name, quantity
                        FROM {table_name}
                        WHERE formula_id = %s
                        ORDER BY id ASC
                    """
                    cursor.execute(query, (formula_id,))
                    return cursor.fetchall()
                except Exception as e:
                    print(f"Erreur récupération notes depuis {table_name} pour formula_id={formula_id} : {e}")
                    return []
                finally:
                    cursor.close()

            def _get_formulas_for_review(review_id: int) -> List[Dict[str, Any]]:
                cursor = connection.cursor()
                try:
                    # On passe par customer_files pour lier customers_review → files → formula
                    query = """
                        SELECT f.id, f.customer_id, f.file_id, f.comment, f.reference, f.perfume_name
                        FROM formula f
                        JOIN customer_files cf ON cf.id = f.file_id
                        WHERE cf.customer_review_id = %s
                        ORDER BY f.id ASC
                    """
                    cursor.execute(query, (review_id,))
                    formulas = cursor.fetchall() or []

                    for formula in formulas:
                        formula_id = formula["id"]
                        formula["top_notes"] = _get_notes("top_note", formula_id)
                        formula["heart_notes"] = _get_notes("heart_note", formula_id)
                        formula["base_notes"] = _get_notes("base_note", formula_id)

                    return formulas
                except Exception as e:
                    print(f"Erreur récupération formules pour customer_review_id={review_id} : {e}")
                    return []
                finally:
                    cursor.close()

            try:
                review["formulas"] = _get_formulas_for_review(review_id)
            except Exception as e:
                print(f"Erreur enrichissement formulas pour review {review_id}: {e}")
                review["formulas"] = []

            return review
        finally:
            connection.close()

    def get_all_customer_reviews(self, page: int = 1, size: int = 10,
                                 review_type: Optional[str] = None,
                                 search: Optional[str] = None,
                                 v2: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les customer_reviews avec pagination et filtres optionnels

        Args:
            page: Numéro de page
            size: Taille de page
            review_type: Filtre par type de review
            search: Recherche sur last_name, first_name ou reference (formule)

        Returns:
            Tuple (liste des customer_reviews, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            # 1) Récupération de base depuis customers_review
            reviews, total = crud_customer_review.get_all(connection, page, size, review_type, search, v2)

            # 2) Récupérer les formules de toutes les reviews de la page en UNE seule requête (évite le N+1)
            review_ids = [r.get("id") for r in reviews if r.get("id")]
            formulas_by_review: Dict[int, List[Dict[str, Any]]] = {}

            if review_ids:
                cursor = connection.cursor()
                try:
                    placeholders = ", ".join(["%s"] * len(review_ids))
                    query = f"""
                        SELECT f.id, f.customer_id, f.file_id, f.comment, f.reference, f.perfume_name,
                               cf.customer_review_id
                        FROM formula f
                        JOIN customer_files cf ON cf.id = f.file_id
                        WHERE cf.customer_review_id IN ({placeholders})
                        ORDER BY f.id ASC
                    """
                    cursor.execute(query, review_ids)
                    for formula in cursor.fetchall() or []:
                        review_id = formula.pop("customer_review_id")
                        formulas_by_review.setdefault(review_id, []).append(formula)
                except Exception as e:
                    print(f"Erreur récupération formules pour customer_reviews {review_ids} : {e}")
                finally:
                    cursor.close()

                for review in reviews:
                    review["formulas"] = formulas_by_review.get(review.get("id"), [])

            return reviews, total
        finally:
            connection.close()

    def update_customer_review(self, review_id: int,
                               customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer_review

        Args:
            review_id: ID du customer_review
            customer_data: Nouvelles données

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer_review.update(connection, review_id, customer_data)

            if success:
                print(f"Customer review {review_id} mis à jour")
            else:
                print(f"Customer review {review_id} non trouvé")

            return success
        finally:
            connection.close()

    def update_customer_review_with_validation(self, review_id: int,
                                               customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer_review avec validation d'email et de téléphone si modifiés

        Args:
            review_id: ID du customer_review à mettre à jour
            customer_data: Données à mettre à jour (dict partiel)

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            # Récupérer le customer_review existant
            existing_review = crud_customer_review.get_by_id(connection, review_id)
            if not existing_review:
                return False

            # Préparer les données à mettre à jour
            update_data = customer_data.copy()

            # Si l'email est modifié, valider et corriger
            if 'email' in customer_data and customer_data['email'] != existing_review.get('email'):
                email = customer_data['email']
                if email:
                    # Corriger le domaine email s'il contient une faute
                    corrected_email, was_corrected, original_domain = email_domain_corrector.correct_email(email)

                    if was_corrected:
                        update_data['email'] = corrected_email
                        print(f"📧 Domaine corrigé : {email} → {corrected_email}")

                    # Vérifier le domaine via MX DNS
                    email = update_data['email']
                    is_valid_domain, details = email_domain_validator.verify_email_domain(email)
                    update_data['verified_domain'] = is_valid_domain
                    print(f"🔍 Vérification domaine : {email} → {is_valid_domain} ({details})")

                    # Valider l'email
                    print(f"Validation de l'email : {email}")
                    update_data['verified_email'] = email_validator.validate_email_sync(email)
                    print(f"Résultat validation : {update_data['verified_email']}")

            # Si le téléphone est modifié, valider
            if 'phone' in customer_data and customer_data['phone'] != existing_review.get('phone'):
                phone = customer_data['phone']
                if phone:
                    print(f"Validation du téléphone : {phone}")
                    phone_validation_result = phone_intelligence_validator.verify_phone_number(phone)
                    # Ne mettre à jour verified_phone que si l'API a retourné un résultat (True ou False)
                    # Si None (erreur API, rate limit), on garde l'ancienne valeur
                    if phone_validation_result is not None:
                        update_data['verified_phone'] = phone_validation_result
                        print(f"Résultat validation téléphone : {phone_validation_result}")
                    else:
                        print(f"⚠️ Validation téléphone impossible (API error/rate limit) - verified_phone non modifié")

            # Mettre à jour le customer_review
            success = crud_customer_review.update(connection, review_id, update_data)

            if success:
                print(f"Customer review {review_id} mis à jour avec validation")
            else:
                print(f"Customer review {review_id} non trouvé")

            return success
        finally:
            connection.close()

    def delete_customer_review(self, review_id: int) -> bool:
        """
        Supprime un customer_review définitivement

        Args:
            review_id: ID du customer_review

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer_review.delete(connection, review_id)

            if success:
                print(f"Customer review {review_id} supprimé")
            else:
                print(f"Customer review {review_id} non trouvé")

            return success
        finally:
            connection.close()

    def transfer_to_customers(self, review_id: int) -> Optional[int]:
        """
        Transfère un customer_review vers la table customers puis le supprime de customers_review

        Args:
            review_id: ID du customer_review

        Returns:
            ID du nouveau customer créé ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            customer_id = crud_customer_review.transfer_to_customers(connection, review_id)

            if customer_id:
                print(f"Customer review {review_id} transféré vers customers avec ID: {customer_id}")

            return customer_id
        finally:
            connection.close()


customer_review_repository = CustomerReviewRepository()
