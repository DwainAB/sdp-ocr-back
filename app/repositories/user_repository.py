from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_user


class UserRepository:
    """
    Repository pour gérer l'accès aux données users (Data Access Layer)
    """

    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau user

        Args:
            user_data: Données du user

        Returns:
            ID du user créé ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            user_id = crud_user.create(connection, user_data)
            if user_id:
                print(f"User créé avec ID: {user_id}")
            return user_id
        finally:
            if connection.is_connected():
                connection.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un user par son ID

        Args:
            user_id: ID du user

        Returns:
            Dictionnaire avec les données du user ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_user.get_by_id(connection, user_id)
        finally:
            if connection.is_connected():
                connection.close()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un user par son email

        Args:
            email: Email du user

        Returns:
            Dictionnaire avec les données du user ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_user.get_by_email(connection, email)
        finally:
            if connection.is_connected():
                connection.close()

    def get_all_users(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                     role: Optional[str] = None, team: Optional[str] = None,
                     is_online: Optional[bool] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les users avec pagination et filtres

        Args:
            page: Numéro de page
            size: Taille de page
            search: Terme de recherche
            role: Filtre par rôle
            team: Filtre par équipe
            is_online: Filtre par statut de connexion

        Returns:
            Tuple (liste des users, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_user.get_all(connection, page, size, search, role, team, is_online)
        finally:
            if connection.is_connected():
                connection.close()

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Met à jour un user

        Args:
            user_id: ID du user
            user_data: Nouvelles données

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_user.update(connection, user_id, user_data)

            if success:
                print(f"User {user_id} mis à jour")
            else:
                print(f"User {user_id} non trouvé")

            return success
        finally:
            if connection.is_connected():
                connection.close()

    def update_user_login_status(self, user_id: int, is_online: bool) -> bool:
        """
        Met à jour le statut de connexion et last_login_at

        Args:
            user_id: ID du user
            is_online: Statut de connexion

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_user.update_login_status(connection, user_id, is_online)

            if success:
                status = "connecté" if is_online else "déconnecté"
                print(f"User {user_id} {status} - last_login_at mis à jour")

            return success
        finally:
            if connection.is_connected():
                connection.close()

    def delete_user(self, user_id: int) -> bool:
        """
        Supprime un user

        Args:
            user_id: ID du user

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_user.delete(connection, user_id)

            if success:
                print(f"User {user_id} supprimé")
            else:
                print(f"User {user_id} non trouvé")

            return success
        finally:
            if connection.is_connected():
                connection.close()

    def get_online_users(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les users en ligne

        Returns:
            Liste des users en ligne
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_user.get_online_users(connection)
        finally:
            if connection.is_connected():
                connection.close()

    def get_users_by_team(self, team: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les users d'une équipe

        Args:
            team: Nom de l'équipe

        Returns:
            Liste des users de l'équipe
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_user.get_by_team(connection, team)
        finally:
            if connection.is_connected():
                connection.close()

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les users d'un rôle

        Args:
            role: Nom du rôle

        Returns:
            Liste des users du rôle
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_user.get_by_role(connection, role)
        finally:
            if connection.is_connected():
                connection.close()


user_repository = UserRepository()
