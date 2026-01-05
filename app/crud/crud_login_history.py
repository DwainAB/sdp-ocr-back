from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection, user_id: int, ip_address: str,
          city: str, country: str, log_type: str) -> Optional[int]:
    """
    Enregistre une nouvelle connexion ou déconnexion

    Args:
        connection: Connexion MySQL
        user_id: ID de l'utilisateur
        ip_address: Adresse IP
        city: Ville
        country: Pays
        log_type: Type de log ("login" ou "logout")

    Returns:
        ID du log créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO login_history (user_id, ip_address, city, country, type, logged_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """

        cursor.execute(query, (user_id, ip_address, city, country, log_type))
        connection.commit()
        record_id = cursor.lastrowid

        return record_id

    except Exception as e:
        print(f"Erreur création enregistrement log : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_user(connection: pymysql.connections.Connection, user_id: int,
               page: int = 1, size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère l'historique des connexions d'un utilisateur avec pagination

    Args:
        connection: Connexion MySQL
        user_id: ID de l'utilisateur
        page: Numéro de page
        size: Taille de page

    Returns:
        Tuple (liste des logs, total)
    """
    try:
        cursor = connection.cursor()

        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM login_history WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = """
            SELECT id, user_id, ip_address, city, country, type, logged_at
            FROM login_history
            WHERE user_id = %s
            ORDER BY logged_at DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (user_id, size, offset))
        records = cursor.fetchall()

        return records, total

    except Exception as e:
        print(f"Erreur récupération historique connexions : {e}")
        return [], 0
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection, page: int = 1,
           size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tout l'historique des connexions avec pagination

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page

    Returns:
        Tuple (liste des logs avec informations utilisateur, total)
    """
    try:
        cursor = connection.cursor()

        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM login_history"
        cursor.execute(count_query)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés avec informations utilisateur
        offset = (page - 1) * size
        query = """
            SELECT
                lh.id,
                lh.user_id,
                lh.ip_address,
                lh.city,
                lh.country,
                lh.type,
                lh.logged_at,
                u.email,
                u.first_name,
                u.last_name
            FROM login_history lh
            LEFT JOIN users u ON lh.user_id = u.id
            ORDER BY lh.logged_at DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (size, offset))
        records = cursor.fetchall()

        return records, total

    except Exception as e:
        print(f"Erreur récupération historique complet : {e}")
        return [], 0
    finally:
        cursor.close()
