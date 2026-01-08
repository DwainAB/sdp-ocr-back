from typing import Dict, Any, Optional, List
import pymysql
from datetime import datetime


def create(
    connection: pymysql.connections.Connection,
    file_data: Dict[str, Any]
) -> Optional[int]:
    """
    Crée un nouveau customer_file dans la base de données

    Args:
        connection: Connexion MySQL
        file_data: Données du fichier (customer_id, customer_review_id, file_path, file_name, file_type, file_size, uploaded_at)

    Returns:
        ID du customer_file créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides (sauf customer_id et customer_review_id qui peuvent être None)
        clean_data = {}
        for k, v in file_data.items():
            if k in ['customer_id', 'customer_review_id']:
                clean_data[k] = v  # Garder même si None
            elif v is not None and v != "":
                clean_data[k] = v

        if not clean_data:
            return None

        columns = list(clean_data.keys())
        placeholders = ["%s"] * len(columns)
        values = list(clean_data.values())

        query = f"""
            INSERT INTO customer_files ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        cursor.execute(query, values)
        connection.commit()

        file_id = cursor.lastrowid
        return file_id

    except Exception as e:
        print(f"Erreur création customer_file : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    file_id: int
) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer_file par son ID

    Args:
        connection: Connexion MySQL
        file_id: ID du fichier

    Returns:
        Dictionnaire avec les données du fichier ou None
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, customer_review_id, file_path, file_name,
                   file_type, file_size, uploaded_at, created_at, updated_at
            FROM customer_files
            WHERE id = %s
        """
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer_file : {e}")
        return None
    finally:
        cursor.close()


def get_by_customer_id(
    connection: pymysql.connections.Connection,
    customer_id: int
) -> List[Dict[str, Any]]:
    """
    Récupère tous les fichiers d'un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Liste des fichiers
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, customer_review_id, file_path, file_name,
                   file_type, file_size, uploaded_at, created_at, updated_at
            FROM customer_files
            WHERE customer_id = %s
            ORDER BY uploaded_at DESC
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()

        return results

    except Exception as e:
        print(f"Erreur récupération fichiers customer : {e}")
        return []
    finally:
        cursor.close()


def get_by_customer_review_id(
    connection: pymysql.connections.Connection,
    customer_review_id: int
) -> List[Dict[str, Any]]:
    """
    Récupère tous les fichiers d'un customer_review

    Args:
        connection: Connexion MySQL
        customer_review_id: ID du customer_review

    Returns:
        Liste des fichiers
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, customer_review_id, file_path, file_name,
                   file_type, file_size, uploaded_at, created_at, updated_at
            FROM customer_files
            WHERE customer_review_id = %s
            ORDER BY uploaded_at DESC
        """
        cursor.execute(query, (customer_review_id,))
        results = cursor.fetchall()

        return results

    except Exception as e:
        print(f"Erreur récupération fichiers customer_review : {e}")
        return []
    finally:
        cursor.close()


def update(
    connection: pymysql.connections.Connection,
    file_id: int,
    file_data: Dict[str, Any]
) -> bool:
    """
    Met à jour un customer_file

    Args:
        connection: Connexion MySQL
        file_id: ID du fichier
        file_data: Nouvelles données

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides (sauf customer_id et customer_review_id)
        clean_data = {}
        for k, v in file_data.items():
            if k in ['customer_id', 'customer_review_id']:
                clean_data[k] = v
            elif v is not None and v != "":
                clean_data[k] = v

        if not clean_data:
            return False

        # Construire la requête UPDATE
        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values())
        values.append(file_id)

        query = f"""
            UPDATE customer_files
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        cursor.execute(query, values)
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour customer_file : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(
    connection: pymysql.connections.Connection,
    file_id: int
) -> bool:
    """
    Supprime un customer_file

    Args:
        connection: Connexion MySQL
        file_id: ID du fichier

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM customer_files WHERE id = %s"
        cursor.execute(query, (file_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression customer_file : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def transfer_files_to_customer(
    connection: pymysql.connections.Connection,
    customer_review_id: int,
    customer_id: int
) -> bool:
    """
    Transfère tous les fichiers d'un customer_review vers un customer
    (Met à jour customer_id et met customer_review_id à NULL)

    Args:
        connection: Connexion MySQL
        customer_review_id: ID du customer_review source
        customer_id: ID du customer destination

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE customer_files
            SET customer_id = %s, customer_review_id = NULL
            WHERE customer_review_id = %s
        """
        cursor.execute(query, (customer_id, customer_review_id))
        connection.commit()

        rows_affected = cursor.rowcount
        print(f"✅ {rows_affected} fichier(s) transféré(s) de customer_review {customer_review_id} vers customer {customer_id}")
        return True

    except Exception as e:
        print(f"Erreur transfert fichiers : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
