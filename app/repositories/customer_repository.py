import re
from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_customer
from app.services.customer import customer_business_service


class CustomerRepository:
    """
    Repository pour gérer l'accès aux données customers (Data Access Layer)
    """

    def insert_customer_if_not_exists(self, extracted_data: Dict[str, Any], v2: bool = False) -> Tuple[Optional[int], str]:
        """
        Insère un customer dans la base pour chaque PDF traité (peu importe les données)
        Délègue à customer_business_service

        Args:
            extracted_data: Données extraites de l'OCR
            v2: Indique si le formulaire est de type v2 (défaut False)

        Returns:
            Tuple (ID du customer/review inséré, type d'entité: "customer" ou "customer_review")
        """
        return customer_business_service.insert_customer_if_not_exists(extracted_data, v2=v2)

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau customer avec validation d'email
        Délègue à customer_business_service

        Args:
            customer_data: Données du customer

        Returns:
            ID du customer créé ou None si erreur
        """
        return customer_business_service.create_customer_with_validation(customer_data)

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un customer par son ID avec ses formules et notes

        Args:
            customer_id: ID du customer

        Returns:
            Dictionnaire avec les données du customer enrichi avec formules et notes, ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            # 1) Récupération de base du customer
            customer = crud_customer.get_by_id(connection, customer_id)
            if not customer:
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

            def _get_formulas_for_customer(customer_id: int) -> List[Dict[str, Any]]:
                cursor = connection.cursor()
                try:
                    # Récupérer directement les formules via formula.customer_id
                    query = """
                        SELECT id, customer_id, file_id, comment, reference, perfume_name
                        FROM formula
                        WHERE customer_id = %s
                        ORDER BY id ASC
                    """
                    cursor.execute(query, (customer_id,))
                    formulas = cursor.fetchall() or []

                    for formula in formulas:
                        formula_id = formula["id"]
                        formula["top_notes"] = _get_notes("top_note", formula_id)
                        formula["heart_notes"] = _get_notes("heart_note", formula_id)
                        formula["base_notes"] = _get_notes("base_note", formula_id)

                    return formulas
                except Exception as e:
                    print(f"Erreur récupération formules pour customer_id={customer_id} : {e}")
                    return []
                finally:
                    cursor.close()

            try:
                customer["formulas"] = _get_formulas_for_customer(customer_id)
            except Exception as e:
                print(f"Erreur enrichissement formulas pour customer {customer_id}: {e}")
                customer["formulas"] = []

            return customer
        finally:
            connection.close()

    def get_all_customers(self, page: int = 1, size: int = 10,
                         search: Optional[str] = None, v2: bool = False,
                         country: Optional[str] = None,
                         year: Optional[str] = None,
                         month: Optional[str] = None,
                         verified: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère les customers avec pagination et recherche (sans formules/notes,
        non utilisées par la liste, pour éviter le N+1 sur chaque page)

        Args:
            page: Numéro de page
            size: Taille de page
            search: Terme de recherche
            country: Filtre par pays
            year: Filtre par année
            month: Filtre par mois (1-12)
            verified: Filtre email vérifié ("true" ou "false")

        Returns:
            Tuple (liste des customers, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            customers, total = crud_customer.get_all(connection, page, size, search, v2,
                                                     country, year, month, verified)
            return customers, total
        finally:
            connection.close()

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer avec validation d'email et de téléphone si modifiés
        Délègue à customer_business_service

        Args:
            customer_id: ID du customer
            customer_data: Nouvelles données

        Returns:
            True si succès, False sinon
        """
        return customer_business_service.update_customer_with_validation(customer_id, customer_data)

    def delete_customer(self, customer_id: int) -> bool:
        """
        Supprime un customer

        Args:
            customer_id: ID du customer

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer.delete(connection, customer_id)

            if success:
                print(f"Customer {customer_id} supprimé")
            else:
                print(f"Customer {customer_id} non trouvé")

            return success
        finally:
            connection.close()


    def get_analytics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'analyse des clients (évolution mensuelle,
        répartition par mois/année, taux de rétention, top pays)

        Returns:
            Dictionnaire avec les statistiques d'analyse
        """
        connection = get_connection()
        if not connection:
            return {}

        try:
            return crud_customer.get_analytics(connection)
        finally:
            connection.close()

    def get_countries(self) -> List[str]:
        """
        Récupère la liste des pays distincts, nettoyée :
        - Supprime les entrées contenant un chiffre
        - Supprime les caractères spéciaux (garde lettres, espaces, tirets, apostrophes)
        - Déduplique et trie

        Returns:
            Liste des pays triés alphabétiquement
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            raw = crud_customer.get_countries(connection)
            seen = set()
            result = []
            for c in raw:
                if not c:
                    continue
                cleaned = re.sub(r"[^a-zA-ZÀ-ÿ\s\-']", '', c).strip()
                if not cleaned:
                    continue
                if re.search(r'\d', cleaned):
                    continue
                key = cleaned.lower()
                if key not in seen:
                    seen.add(key)
                    result.append(cleaned)
            return sorted(result)
        finally:
            connection.close()

    def bulk_update_customers(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Met à jour plusieurs customers en masse

        Args:
            updates: Liste de dictionnaires avec 'id' et les champs à modifier

        Returns:
            Liste de résultats avec id, success et error pour chaque customer
        """
        results = []

        for item in updates:
            customer_id = item.pop("id")
            try:
                existing = self.get_customer_by_id(customer_id)
                if not existing:
                    results.append({
                        "id": customer_id,
                        "success": False,
                        "error": f"Customer avec ID {customer_id} non trouvé"
                    })
                    continue

                success = self.update_customer(customer_id, item)
                results.append({
                    "id": customer_id,
                    "success": success,
                    "error": None if success else "Erreur lors de la mise à jour"
                })
            except Exception as e:
                results.append({
                    "id": customer_id,
                    "success": False,
                    "error": str(e)
                })

        return results


customer_repository = CustomerRepository()
