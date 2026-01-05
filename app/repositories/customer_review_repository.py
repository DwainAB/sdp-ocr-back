from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_customer_review


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
            if connection.open:
                connection.close()

    def get_customer_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un customer_review par son ID

        Args:
            review_id: ID du customer_review

        Returns:
            Dictionnaire avec les données du customer_review ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer_review.get_by_id(connection, review_id)
        finally:
            if connection.open:
                connection.close()

    def get_all_customer_reviews(self, page: int = 1, size: int = 10,
                                 review_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les customer_reviews avec pagination et filtre optionnel par type

        Args:
            page: Numéro de page
            size: Taille de page
            review_type: Filtre par type de review

        Returns:
            Tuple (liste des customer_reviews, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_customer_review.get_all(connection, page, size, review_type)
        finally:
            if connection.open:
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
            if connection.open:
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
            if connection.open:
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
            if connection.open:
                connection.close()


customer_review_repository = CustomerReviewRepository()
