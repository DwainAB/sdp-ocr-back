from typing import Dict, Any, Optional, List, Tuple
from mysql.connector import MySQLConnection


def create(connection: MySQLConnection, group_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée un nouveau groupe dans la base de données

    Args:
        connection: Connexion MySQL
        group_data: Données du groupe (name, description, created_by)

    Returns:
        ID du groupe créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO `groups` (name, description, created_by)
            VALUES (%s, %s, %s)
        """

        cursor.execute(query, (
            group_data.get('name'),
            group_data.get('description'),
            group_data.get('created_by')
        ))

        connection.commit()
        group_id = cursor.lastrowid

        return group_id

    except Exception as e:
        print(f"Erreur création groupe : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: MySQLConnection, group_id: int,
              include_deleted: bool = False) -> Optional[Dict[str, Any]]:
    """
    Récupère un groupe par son ID

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe
        include_deleted: Inclure les groupes supprimés

    Returns:
        Dictionnaire avec les données du groupe ou None
    """
    try:
        cursor = connection.cursor(dictionary=True)

        where_clause = "WHERE id = %s"
        if not include_deleted:
            where_clause += " AND is_deleted = FALSE"

        query = f"SELECT * FROM `groups` {where_clause}"
        cursor.execute(query, (group_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération groupe : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: MySQLConnection, page: int = 1, size: int = 10,
            search: Optional[str] = None, include_deleted: bool = False) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les groupes avec pagination et recherche

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche
        include_deleted: Inclure les groupes supprimés

    Returns:
        Tuple (liste des groupes, total)
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Construire la clause WHERE
        where_conditions = []
        params = []

        # Filtrer les supprimés sauf si demandé
        if not include_deleted:
            where_conditions.append("is_deleted = FALSE")

        # Recherche
        if search:
            where_conditions.append("(name LIKE %s OR description LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM `groups` {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM `groups` {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        cursor.execute(query, params)
        groups = cursor.fetchall()

        return groups, total

    except Exception as e:
        print(f"Erreur récupération groupes : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: MySQLConnection, group_id: int,
           group_data: Dict[str, Any]) -> bool:
    """
    Met à jour un groupe

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe
        group_data: Nouvelles données (name, description)

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in group_data.items() if v is not None and v != ""}

        if not clean_data:
            return False

        # Construire la requête UPDATE avec updated_at automatique
        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        values = list(clean_data.values())
        values.append(group_id)

        query = f"""
            UPDATE `groups`
            SET {', '.join(set_clauses)}
            WHERE id = %s AND is_deleted = FALSE
        """

        cursor.execute(query, values)
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def soft_delete(connection: MySQLConnection, group_id: int) -> bool:
    """
    Suppression logique d'un groupe (is_deleted = TRUE)

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE `groups`
            SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_deleted = FALSE
        """

        cursor.execute(query, (group_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def restore(connection: MySQLConnection, group_id: int) -> bool:
    """
    Restaure un groupe supprimé (is_deleted = FALSE)

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE `groups`
            SET is_deleted = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_deleted = TRUE
        """

        cursor.execute(query, (group_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur restauration groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


# ======================================================================
# CUSTOMER-GROUP RELATIONS
# ======================================================================

def add_customer_to_group(connection: MySQLConnection, customer_id: int,
                         group_id: int, added_by: int) -> bool:
    """
    Ajoute un customer à un groupe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        group_id: ID du groupe
        added_by: ID de l'utilisateur qui ajoute

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Vérifier si la relation existe déjà
        cursor.execute(
            "SELECT id FROM customer_groups WHERE customer_id = %s AND group_id = %s",
            (customer_id, group_id)
        )
        if cursor.fetchone():
            return False  # Relation existe déjà

        # Insérer la relation
        cursor.execute("""
            INSERT INTO customer_groups (customer_id, group_id, added_by)
            VALUES (%s, %s, %s)
        """, (customer_id, group_id, added_by))

        connection.commit()
        return True

    except Exception as e:
        print(f"Erreur ajout customer au groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def remove_customer_from_group(connection: MySQLConnection, customer_id: int,
                               group_id: int) -> bool:
    """
    Retire un customer d'un groupe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM customer_groups
            WHERE customer_id = %s AND group_id = %s
        """, (customer_id, group_id))

        connection.commit()
        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur retrait customer du groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def get_group_customers(connection: MySQLConnection, group_id: int,
                       page: int = 1, size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customers d'un groupe avec pagination

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe
        page: Numéro de page
        size: Taille de page

    Returns:
        Tuple (liste des customers, total)
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Compter le total
        count_query = """
            SELECT COUNT(*) as total
            FROM customer_groups cg
            JOIN customers c ON cg.customer_id = c.id
            WHERE cg.group_id = %s
        """
        cursor.execute(count_query, (group_id,))
        total = cursor.fetchone()['total']

        # Récupérer les données avec pagination
        offset = (page - 1) * size
        query = """
            SELECT c.*, cg.added_at, cg.added_by
            FROM customer_groups cg
            JOIN customers c ON cg.customer_id = c.id
            WHERE cg.group_id = %s
            ORDER BY cg.added_at DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (group_id, size, offset))
        customers = cursor.fetchall()

        return customers, total

    except Exception as e:
        print(f"Erreur récupération customers du groupe : {e}")
        return [], 0
    finally:
        cursor.close()


def get_customer_groups(connection: MySQLConnection, customer_id: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les groupes d'un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Liste des groupes
    """
    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT g.*, cg.added_at, cg.added_by
            FROM customer_groups cg
            JOIN `groups` g ON cg.group_id = g.id
            WHERE cg.customer_id = %s AND g.is_deleted = FALSE
            ORDER BY cg.added_at DESC
        """

        cursor.execute(query, (customer_id,))
        groups = cursor.fetchall()

        return groups

    except Exception as e:
        print(f"Erreur récupération groupes du customer : {e}")
        return []
    finally:
        cursor.close()


def check_group_exists(connection: MySQLConnection, group_id: int) -> bool:
    """
    Vérifie si un groupe existe et n'est pas supprimé

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si le groupe existe, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM `groups` WHERE id = %s AND is_deleted = FALSE", (group_id,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification groupe : {e}")
        return False
    finally:
        cursor.close()


def check_customer_exists(connection: MySQLConnection, customer_id: int) -> bool:
    """
    Vérifie si un customer existe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        True si le customer existe, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification customer : {e}")
        return False
    finally:
        cursor.close()
