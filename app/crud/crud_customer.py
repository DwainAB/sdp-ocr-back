from typing import Dict, Any, Optional, List, Tuple
from mysql.connector import MySQLConnection


def create(connection: MySQLConnection, customer_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée un nouveau customer dans la base de données

    Args:
        connection: Connexion MySQL
        customer_data: Données du customer

    Returns:
        ID du customer créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

        if clean_data:
            columns = list(clean_data.keys())
            placeholders = ["%s"] * len(columns)
            values = list(clean_data.values())

            query = f"""
                INSERT INTO customers ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            cursor.execute(query, values)
        else:
            # Insertion ligne vide
            query = "INSERT INTO customers () VALUES ()"
            cursor.execute(query)

        connection.commit()
        customer_id = cursor.lastrowid

        return customer_id

    except Exception as e:
        print(f"Erreur création customer : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: MySQLConnection, customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son ID

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer : {e}")
        return None
    finally:
        cursor.close()


def get_by_email(connection: MySQLConnection, email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son email

    Args:
        connection: Connexion MySQL
        email: Email du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM customers WHERE email = %s LIMIT 1"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par email : {e}")
        return None
    finally:
        cursor.close()


def get_by_phone(connection: MySQLConnection, phone: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son téléphone

    Args:
        connection: Connexion MySQL
        phone: Téléphone du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM customers WHERE phone = %s LIMIT 1"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par téléphone : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: MySQLConnection, page: int = 1, size: int = 10,
            search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customers avec pagination et recherche

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche

    Returns:
        Tuple (liste des customers, total)
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Construire la requête avec recherche
        where_clause = ""
        params = []

        if search:
            where_clause = """
                WHERE first_name LIKE %s OR last_name LIKE %s
                OR email LIKE %s OR phone LIKE %s OR city LIKE %s
            """
            search_param = f"%{search}%"
            params = [search_param] * 5

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM customers {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM customers {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        cursor.execute(query, params)
        customers = cursor.fetchall()

        return customers, total

    except Exception as e:
        print(f"Erreur récupération customers : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: MySQLConnection, customer_id: int,
           customer_data: Dict[str, Any]) -> bool:
    """
    Met à jour un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        customer_data: Nouvelles données

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

        if not clean_data:
            return False

        # Construire la requête UPDATE
        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values())
        values.append(customer_id)  # Pour le WHERE

        query = f"""
            UPDATE customers
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        cursor.execute(query, values)
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour customer : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: MySQLConnection, customer_id: int) -> bool:
    """
    Supprime un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression customer : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def check_duplicate_email(connection: MySQLConnection, email: str) -> bool:
    """
    Vérifie si un email existe déjà

    Args:
        connection: Connexion MySQL
        email: Email à vérifier

    Returns:
        True si l'email existe, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "SELECT id FROM customers WHERE email = %s LIMIT 1"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification email : {e}")
        return False
    finally:
        cursor.close()


def check_duplicate_phone(connection: MySQLConnection, phone: str) -> bool:
    """
    Vérifie si un téléphone existe déjà

    Args:
        connection: Connexion MySQL
        phone: Téléphone à vérifier

    Returns:
        True si le téléphone existe, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "SELECT id FROM customers WHERE phone = %s LIMIT 1"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification téléphone : {e}")
        return False
    finally:
        cursor.close()
