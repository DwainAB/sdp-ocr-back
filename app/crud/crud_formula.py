from typing import Optional
import pymysql


def create(
    connection: pymysql.connections.Connection,
    customer_id: Optional[int],
    file_id: Optional[int],
    customer_review_id: Optional[int] = None,
    reference: Optional[str] = None,
    perfume_name: Optional[str] = None,
    date: Optional[str] = None,
    quantity: Optional[str] = None,
    source: Optional[str] = None,
    supervisor_id: Optional[int] = None,
    box_type: Optional[str] = None,
) -> Optional[int]:
    """
    Crée une nouvelle formule liée à un customer (ou customer_review) et à un fichier.

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer (peut être None si review)
        file_id: ID du fichier source (customer_files.id), None pour le flux tablette
        customer_review_id: ID du customer_review (peut être None si customer)
        reference: Référence/identifiant de la formule
        perfume_name: Nom du parfum
        date: Date extraite du formulaire OCR
        quantity: Quantité choisie (10ml, 30ml, 50ml, 100ml, Brume)
        source: Origine de la formule ('ocr' ou 'tablet')
        box_type: Coffret utilisé (optionnel)

    Returns:
        ID de la formule créée ou None si erreur
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Colonnes optionnelles (quantity/source) insérées seulement si fournies,
        # pour rester compatible avec une base sans ces colonnes
        data = {
            "customer_id": customer_id,
            "file_id": file_id,
            "customer_review_id": customer_review_id,
            "reference": reference,
            "perfume_name": perfume_name,
            "date": date,
        }
        if quantity is not None:
            data["quantity"] = quantity
        if source is not None:
            data["source"] = source
        if supervisor_id is not None:
            data["supervisor_id"] = supervisor_id
        if box_type is not None:
            data["box_type"] = box_type

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)

        query = f"""
            INSERT INTO formula ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        cursor.execute(query, list(data.values()))

        connection.commit()
        formula_id = cursor.lastrowid

        return formula_id

    except Exception as e:
        print(f"Erreur création formula : {e}")
        connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> Optional[dict]:
    """
    Récupère une formule par son ID.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        Dictionnaire avec les données de la formule ou None si non trouvée
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT f.id, f.customer_id, f.file_id, f.customer_review_id, f.comment,
                   f.reference, f.perfume_name, f.date, f.quantity, f.source, f.reuse_count,
                   f.supervisor_id, f.box_type,
                   CONCAT(u.first_name, ' ', u.last_name) AS supervisor_name
            FROM formula f
            LEFT JOIN users u ON u.id = f.supervisor_id
            WHERE f.id = %s
        """
        cursor.execute(query, (formula_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération formula {formula_id} : {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_customer_id(
    connection: pymysql.connections.Connection,
    customer_id: int,
) -> list[dict]:
    """
    Récupère l'historique des formules d'un client, triées des plus récentes aux plus anciennes.

    Args:
        connection: Connexion MySQL
        customer_id: ID du client

    Returns:
        Liste de dictionnaires (peut être vide)
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, perfume_name, date, quantity, reuse_count
            FROM formula
            WHERE customer_id = %s
            ORDER BY date DESC, id DESC
        """
        cursor.execute(query, (customer_id,))
        return cursor.fetchall() or []

    except Exception as e:
        print(f"Erreur récupération formules du customer {customer_id} : {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()


def increment_reuse_count(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> Optional[int]:
    """
    Incrémente le compteur de réutilisation d'une formule.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        Nouvelle valeur de reuse_count ou None si erreur/formule inconnue
    """
    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE formula SET reuse_count = reuse_count + 1 WHERE id = %s",
            (formula_id,),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return None

        cursor.execute("SELECT reuse_count FROM formula WHERE id = %s", (formula_id,))
        row = cursor.fetchone()
        return row["reuse_count"] if row else None

    except Exception as e:
        print(f"Erreur incrémentation reuse_count formula {formula_id} : {e}")
        connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_reference(
    connection: pymysql.connections.Connection,
    reference: str,
) -> Optional[dict]:
    """
    Récupère une formule par sa référence.

    Args:
        connection: Connexion MySQL
        reference: Référence de la formule

    Returns:
        Dictionnaire avec les données de la formule ou None si non trouvée
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, file_id, customer_review_id, comment, reference, perfume_name, date
            FROM formula
            WHERE reference = %s
        """
        cursor.execute(query, (reference,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération formula par référence {reference} : {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()


def generate_tablet_reference(
    connection: pymysql.connections.Connection,
    year_month: str,
) -> str:
    """
    Génère la prochaine référence tablette au même format que les références OCR
    (suite de chiffres commençant par '20'), sur le préfixe année+mois donné.

    Args:
        connection: Connexion MySQL
        year_month: Préfixe 'YYMM' (ex: '2607' pour juillet 2026)

    Returns:
        Référence au format '20{YYMM}{NNNNN}' (ex: '20260700001')
    """
    prefix = f"20{year_month}"
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT reference
            FROM formula
            WHERE reference LIKE %s
            ORDER BY reference DESC
            LIMIT 1
        """
        cursor.execute(query, (f"{prefix}%",))
        result = cursor.fetchone()

        last_sequence = 0
        if result and result.get("reference"):
            suffix = result["reference"][len(prefix):]
            if suffix.isdigit():
                last_sequence = int(suffix)

        next_sequence = last_sequence + 1
        return f"{prefix}{next_sequence:05d}"

    finally:
        if cursor is not None:
            cursor.close()


def delete(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> bool:
    """
    Supprime une formule par son ID.
    Les notes associées sont supprimées automatiquement via CASCADE.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule à supprimer

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM formula
            WHERE id = %s
        """
        cursor.execute(query, (formula_id,))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur suppression formula {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def update(
    connection: pymysql.connections.Connection,
    formula_id: int,
    **kwargs,
) -> bool:
    """
    Met à jour une formule avec les champs fournis.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule
        **kwargs: Champs à mettre à jour (customer_id, file_id, customer_review_id, comment)

    Returns:
        True si succès, False sinon
    """
    if not kwargs:
        return True

    cursor = None
    try:
        cursor = connection.cursor()

        # Construire la requête dynamiquement
        allowed_fields = {"customer_id", "file_id", "customer_review_id", "comment", "reference", "perfume_name", "date", "box_type"}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not fields_to_update:
            return True

        set_clause = ", ".join([f"{field} = %s" for field in fields_to_update.keys()])
        values = list(fields_to_update.values()) + [formula_id]

        query = f"""
            UPDATE formula
            SET {set_clause}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur mise à jour formula {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def transfer_formulas_to_customer(
    connection: pymysql.connections.Connection,
    customer_review_id: int,
    customer_id: int
) -> bool:
    """
    Transfère toutes les formules d'un customer_review vers un customer.
    Met à jour customer_id et met customer_review_id à NULL.

    Args:
        connection: Connexion MySQL
        customer_review_id: ID du customer_review source
        customer_id: ID du customer destination

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            UPDATE formula
            SET customer_id = %s, customer_review_id = NULL
            WHERE customer_review_id = %s
        """
        cursor.execute(query, (customer_id, customer_review_id))
        connection.commit()

        rows_affected = cursor.rowcount
        print(f"✅ {rows_affected} formule(s) transférée(s) de customer_review {customer_review_id} vers customer {customer_id}")
        return True

    except Exception as e:
        print(f"Erreur transfert formules : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()

