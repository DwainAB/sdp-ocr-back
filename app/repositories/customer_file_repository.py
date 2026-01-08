from typing import Dict, Any, Optional, List
from app.database import get_connection
from app.crud import crud_customer_file


class CustomerFileRepository:
    """
    Repository pour gérer l'accès aux données customer_files (Data Access Layer)
    """

    def create_customer_file(self, file_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau customer_file

        Args:
            file_data: Données du fichier

        Returns:
            ID du fichier créé ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer_file.create(connection, file_data)
        finally:
            if connection.open:
                connection.close()

    def get_customer_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un customer_file par son ID

        Args:
            file_id: ID du fichier

        Returns:
            Dictionnaire avec les données du fichier ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer_file.get_by_id(connection, file_id)
        finally:
            if connection.open:
                connection.close()

    def get_files_by_customer_id(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Récupère tous les fichiers d'un customer

        Args:
            customer_id: ID du customer

        Returns:
            Liste des fichiers
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_customer_file.get_by_customer_id(connection, customer_id)
        finally:
            if connection.open:
                connection.close()

    def get_files_by_customer_review_id(self, customer_review_id: int) -> List[Dict[str, Any]]:
        """
        Récupère tous les fichiers d'un customer_review

        Args:
            customer_review_id: ID du customer_review

        Returns:
            Liste des fichiers
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_customer_file.get_by_customer_review_id(connection, customer_review_id)
        finally:
            if connection.open:
                connection.close()

    def update_customer_file(self, file_id: int, file_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer_file

        Args:
            file_id: ID du fichier
            file_data: Nouvelles données

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer_file.update(connection, file_id, file_data)

            if success:
                print(f"Customer file {file_id} mis à jour")
            else:
                print(f"Customer file {file_id} non trouvé")

            return success
        finally:
            if connection.open:
                connection.close()

    def delete_customer_file(self, file_id: int) -> bool:
        """
        Supprime un customer_file

        Args:
            file_id: ID du fichier

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_customer_file.delete(connection, file_id)

            if success:
                print(f"Customer file {file_id} supprimé")
            else:
                print(f"Customer file {file_id} non trouvé")

            return success
        finally:
            if connection.open:
                connection.close()

    def transfer_files_to_customer(
        self,
        customer_review_id: int,
        customer_id: int
    ) -> bool:
        """
        Transfère tous les fichiers d'un customer_review vers un customer

        Args:
            customer_review_id: ID du customer_review source
            customer_id: ID du customer destination

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            return crud_customer_file.transfer_files_to_customer(
                connection,
                customer_review_id,
                customer_id
            )
        finally:
            if connection.open:
                connection.close()


customer_file_repository = CustomerFileRepository()
