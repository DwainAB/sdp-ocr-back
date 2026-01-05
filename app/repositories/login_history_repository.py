from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_login_history


class LoginHistoryRepository:
    """
    Repository pour gérer l'accès aux données login_history (Data Access Layer)
    """

    def create_login_record(self, user_id: int, ip_address: str, city: str,
                           country: str, log_type: str) -> Optional[int]:
        """
        Enregistre une nouvelle connexion ou déconnexion

        Args:
            user_id: ID de l'utilisateur
            ip_address: Adresse IP
            city: Ville
            country: Pays
            log_type: Type de log ("login" ou "logout")

        Returns:
            ID du log créé ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            record_id = crud_login_history.create(
                connection,
                user_id,
                ip_address,
                city,
                country,
                log_type
            )

            if record_id:
                print(f"Log {log_type} enregistré avec ID: {record_id}")

            return record_id
        finally:
            if connection.is_connected():
                connection.close()

    def get_login_history_by_user(self, user_id: int, page: int = 1,
                                  size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère l'historique des connexions d'un utilisateur avec pagination

        Args:
            user_id: ID de l'utilisateur
            page: Numéro de page
            size: Taille de page

        Returns:
            Tuple (liste des logs, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_login_history.get_by_user(connection, user_id, page, size)
        finally:
            if connection.is_connected():
                connection.close()

    def get_all_login_history(self, page: int = 1,
                             size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tout l'historique des connexions avec pagination

        Args:
            page: Numéro de page
            size: Taille de page

        Returns:
            Tuple (liste des logs avec informations utilisateur, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_login_history.get_all(connection, page, size)
        finally:
            if connection.is_connected():
                connection.close()


login_history_repository = LoginHistoryRepository()
