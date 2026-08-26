from typing import Optional
import pymysql


def _insert_note(
    connection: pymysql.connections.Connection,
    table_name: str,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    """
    Helper générique pour insérer une note dans une table donnée.
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {
            "name": name,
            "quantity": quantity,
            "formula_id": formula_id,
        }
        clean_data = {k: v for k, v in clean_data.items() if v is not None and v != ""}

        columns = list(clean_data.keys())
        placeholders = ["%s"] * len(columns)
        values = list(clean_data.values())

        if not columns:
            return None

        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        cursor.execute(query, values)

        connection.commit()
        note_id = cursor.lastrowid

        return note_id

    except Exception as e:
        print(f"Erreur création note dans {table_name} : {e}")
        connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def create_top_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "top_note", formula_id, name, quantity)


def create_heart_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "heart_note", formula_id, name, quantity)


def create_base_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "base_note", formula_id, name, quantity)


def create_booster_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "booster_note", formula_id, name, quantity)


def update_note(
    connection: pymysql.connections.Connection,
    table_name: str,
    note_id: int,
    name: Optional[str] = None,
    quantity: Optional[str] = None,
) -> bool:
    """
    Met à jour une note dans une table donnée.

    Args:
        connection: Connexion MySQL
        table_name: Nom de la table (top_note, heart_note, base_note)
        note_id: ID de la note à mettre à jour
        name: Nouveau nom (optionnel)
        quantity: Nouvelle quantité (optionnel)

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Construire dynamiquement la requête UPDATE
        updates = []
        values = []

        if name is not None:
            updates.append("name = %s")
            values.append(name)

        if quantity is not None:
            updates.append("quantity = %s")
            values.append(quantity)

        if not updates:
            return False

        values.append(note_id)

        query = f"""
            UPDATE {table_name}
            SET {', '.join(updates)}
            WHERE id = %s
        """
        cursor.execute(query, values)

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur mise à jour note {note_id} dans {table_name} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def delete_note(
    connection: pymysql.connections.Connection,
    table_name: str,
    note_id: int,
) -> bool:
    """
    Supprime une note d'une table donnée.

    Args:
        connection: Connexion MySQL
        table_name: Nom de la table (top_note, heart_note, base_note)
        note_id: ID de la note à supprimer

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = f"""
            DELETE FROM {table_name}
            WHERE id = %s
        """
        cursor.execute(query, (note_id,))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur suppression note {note_id} dans {table_name} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def delete_all_notes_by_formula(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> bool:
    """
    Supprime toutes les notes (tête, cœur, fond) associées à une formule.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        tables = ["top_note", "heart_note", "base_note", "booster_note"]

        for table in tables:
            query = f"""
                DELETE FROM {table}
                WHERE formula_id = %s
            """
            cursor.execute(query, (formula_id,))

        connection.commit()

        return True

    except Exception as e:
        print(f"Erreur suppression notes pour formula {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def get_notes_by_type(
    connection: pymysql.connections.Connection,
    table_name: str,
    formula_id: int,
) -> list:
    """
    Récupère toutes les notes d'un type pour une formule donnée.

    Args:
        connection: Connexion MySQL
        table_name: Nom de la table (top_note, heart_note, base_note)
        formula_id: ID de la formule

    Returns:
        Liste de dictionnaires contenant les notes
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = f"""
            SELECT id, name, quantity, formula_id
            FROM {table_name}
            WHERE formula_id = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (formula_id,))

        return cursor.fetchall() or []

    except Exception as e:
        print(f"Erreur récupération notes depuis {table_name} pour formula {formula_id} : {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()

