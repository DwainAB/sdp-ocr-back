from typing import Dict, Any, Optional, List, Tuple
from mysql.connector import MySQLConnection


def create(connection: MySQLConnection, user_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée un nouveau user dans la base de données

    Args:
        connection: Connexion MySQL
        user_data: Données du user

    Returns:
        ID du user créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in user_data.items() if v is not None and v != ""}

        if clean_data:
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

        return user_id

    except Exception as e:
        print(f"Erreur création user : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: MySQLConnection, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère un user par son ID

    Args:
        connection: Connexion MySQL
        user_id: ID du user

    Returns:
        Dictionnaire avec les données du user ou None
    """
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
        cursor.close()


def get_by_email(connection: MySQLConnection, email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un user par son email

    Args:
        connection: Connexion MySQL
        email: Email du user

    Returns:
        Dictionnaire avec les données du user ou None
    """
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
        cursor.close()


def get_all(connection: MySQLConnection, page: int = 1, size: int = 10,
            search: Optional[str] = None, role: Optional[str] = None,
            team: Optional[str] = None, is_online: Optional[bool] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les users avec pagination et filtres

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche
        role: Filtre par rôle
        team: Filtre par équipe
        is_online: Filtre par statut de connexion

    Returns:
        Tuple (liste des users, total)
    """
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
        cursor.close()


def update(connection: MySQLConnection, user_id: int,
           user_data: Dict[str, Any]) -> bool:
    """
    Met à jour un user

    Args:
        connection: Connexion MySQL
        user_id: ID du user
        user_data: Nouvelles données

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in user_data.items() if v is not None and v != ""}

        if not clean_data:
            return False

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

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour user : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def update_login_status(connection: MySQLConnection, user_id: int,
                       is_online: bool) -> bool:
    """
    Met à jour le statut de connexion et last_login_at

    Args:
        connection: Connexion MySQL
        user_id: ID du user
        is_online: Statut de connexion

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE users
            SET is_online = %s, last_login_at = NOW()
            WHERE id = %s
        """

        cursor.execute(query, (is_online, user_id))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour statut connexion : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: MySQLConnection, user_id: int) -> bool:
    """
    Supprime un user

    Args:
        connection: Connexion MySQL
        user_id: ID du user

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression user : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def get_online_users(connection: MySQLConnection) -> List[Dict[str, Any]]:
    """
    Récupère tous les users en ligne

    Args:
        connection: Connexion MySQL

    Returns:
        Liste des users en ligne
    """
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
        cursor.close()


def get_by_team(connection: MySQLConnection, team: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les users d'une équipe

    Args:
        connection: Connexion MySQL
        team: Nom de l'équipe

    Returns:
        Liste des users de l'équipe
    """
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
        cursor.close()


def get_by_role(connection: MySQLConnection, role: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les users d'un rôle

    Args:
        connection: Connexion MySQL
        role: Nom du rôle

    Returns:
        Liste des users du rôle
    """
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
        cursor.close()
