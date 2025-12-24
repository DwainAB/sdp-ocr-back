from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from app.db.connection import get_connection

class UserService:
    """
    Service pour gérer les users dans la base de données
    """

    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau user
        """
        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in user_data.items() if v is not None and v != ""}

        connection = get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()

            if clean_data:
                # Insertion avec données
                columns = list(clean_data.keys())
                placeholders = ["%s"] * len(columns)
                values = list(clean_data.values())

                query = f"""
                    INSERT INTO users ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                cursor.execute(query, values)
            else:
                # Insertion ligne vide
                query = "INSERT INTO users () VALUES ()"
                cursor.execute(query)

            connection.commit()
            user_id = cursor.lastrowid
            print(f"User créé avec ID: {user_id}")

            return user_id

        except Exception as e:
            print(f"Erreur création user : {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un user par son ID
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()

            return result

        except Exception as e:
            print(f"Erreur récupération user : {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un user par son email
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            return result

        except Exception as e:
            print(f"Erreur récupération user par email : {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_all_users(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                     role: Optional[str] = None, team: Optional[str] = None,
                     is_online: Optional[bool] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les users avec pagination et filtres
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            cursor = connection.cursor(dictionary=True)

            # Construire la requête avec filtres
            where_clauses = []
            params = []

            if search:
                where_clauses.append("""
                    (first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
                     OR phone LIKE %s OR job LIKE %s OR team LIKE %s)
                """)
                search_param = f"%{search}%"
                params.extend([search_param] * 6)

            if role:
                where_clauses.append("role = %s")
                params.append(role)

            if team:
                where_clauses.append("team = %s")
                params.append(team)

            if is_online is not None:
                where_clauses.append("is_online = %s")
                params.append(is_online)

            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)

            # Compter le total
            count_query = f"SELECT COUNT(*) as total FROM users {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Récupérer les résultats paginés
            offset = (page - 1) * size
            query = f"""
                SELECT * FROM users {where_clause}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            params.extend([size, offset])

            cursor.execute(query, params)
            users = cursor.fetchall()

            return users, total

        except Exception as e:
            print(f"Erreur récupération users : {e}")
            return [], 0
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Met à jour un user
        """
        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in user_data.items() if v is not None and v != ""}

        if not clean_data:
            return False

        connection = get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Construire la requête UPDATE
            set_clauses = [f"{col} = %s" for col in clean_data.keys()]
            values = list(clean_data.values())
            values.append(user_id)  # Pour le WHERE

            query = f"""
                UPDATE users
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cursor.execute(query, values)
            connection.commit()

            # Vérifier si une ligne a été modifiée
            success = cursor.rowcount > 0

            if success:
                print(f"User {user_id} mis à jour")
            else:
                print(f"User {user_id} non trouvé")

            return success

        except Exception as e:
            print(f"Erreur mise à jour user : {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_login_status(self, user_id: int, is_online: bool) -> bool:
        """
        Met à jour le statut de connexion et last_login_at
        - Connexion (is_online=true) : met à jour last_login_at avec l'heure de connexion
        - Déconnexion (is_online=false) : met à jour last_login_at avec l'heure de déconnexion
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Dans tous les cas, on met à jour last_login_at avec l'heure actuelle
            # - Si connexion : heure de connexion
            # - Si déconnexion : heure de déconnexion (dernière fois qu'il était connecté)
            query = """
                UPDATE users
                SET is_online = %s, last_login_at = NOW()
                WHERE id = %s
            """

            cursor.execute(query, (is_online, user_id))
            connection.commit()

            success = cursor.rowcount > 0
            if success:
                status = "connecté" if is_online else "déconnecté"
                print(f"User {user_id} {status} - last_login_at mis à jour")

            return success

        except Exception as e:
            print(f"Erreur mise à jour statut connexion : {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def delete_user(self, user_id: int) -> bool:
        """
        Supprime un user
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            query = "DELETE FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            connection.commit()

            # Vérifier si une ligne a été supprimée
            success = cursor.rowcount > 0

            if success:
                print(f"User {user_id} supprimé")
            else:
                print(f"User {user_id} non trouvé")

            return success

        except Exception as e:
            print(f"Erreur suppression user : {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_online_users(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les users en ligne
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE is_online = 1 ORDER BY last_login_at DESC"
            cursor.execute(query)
            users = cursor.fetchall()

            return users

        except Exception as e:
            print(f"Erreur récupération users en ligne : {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_users_by_team(self, team: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les users d'une équipe
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE team = %s ORDER BY first_name, last_name"
            cursor.execute(query, (team,))
            users = cursor.fetchall()

            return users

        except Exception as e:
            print(f"Erreur récupération users par équipe : {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les users d'un rôle
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE role = %s ORDER BY first_name, last_name"
            cursor.execute(query, (role,))
            users = cursor.fetchall()

            return users

        except Exception as e:
            print(f"Erreur récupération users par rôle : {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

user_service = UserService()