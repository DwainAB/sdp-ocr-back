from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_customer
from app.services.customer_service import customer_business_service


class CustomerRepository:
    """
    Repository pour gérer l'accès aux données customers (Data Access Layer)
    """

    def insert_customer_if_not_exists(self, extracted_data: Dict[str, Any]) -> Optional[int]:
        """
        Insère un customer dans la base pour chaque PDF traité (peu importe les données)
        Délègue à customer_business_service

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            ID du customer inséré ou None si erreur
        """
        return customer_business_service.insert_customer_if_not_exists(extracted_data)

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
        Récupère un customer par son ID

        Args:
            customer_id: ID du customer

        Returns:
            Dictionnaire avec les données du customer ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer.get_by_id(connection, customer_id)
        finally:
            if connection.is_connected():
                connection.close()

    def get_all_customers(self, page: int = 1, size: int = 10,
                         search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les customers avec pagination et recherche

        Args:
            page: Numéro de page
            size: Taille de page
            search: Terme de recherche

        Returns:
            Tuple (liste des customers, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_customer.get_all(connection, page, size, search)
        finally:
            if connection.is_connected():
                connection.close()

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer

        Args:
            customer_id: ID du customer
            customer_data: Nouvelles données

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer.update(connection, customer_id, customer_data)

            if success:
                print(f"Customer {customer_id} mis à jour")
            else:
                print(f"Customer {customer_id} non trouvé")

            return success
        finally:
            if connection.is_connected():
                connection.close()

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
            if connection.is_connected():
                connection.close()


customer_repository = CustomerRepository()
