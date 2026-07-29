from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection, customer_data: Dict[str, Any]) -> Optional[int]:
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


def get_by_id(connection: pymysql.connections.Connection, customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son ID

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer : {e}")
        return None
    finally:
        cursor.close()


def get_by_email(connection: pymysql.connections.Connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son email

    Args:
        connection: Connexion MySQL
        email: Email du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE email = %s LIMIT 1"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par email : {e}")
        return None
    finally:
        cursor.close()


def get_by_phone(connection: pymysql.connections.Connection, phone: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son téléphone

    Args:
        connection: Connexion MySQL
        phone: Téléphone du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE phone = %s LIMIT 1"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par téléphone : {e}")
        return None
    finally:
        cursor.close()


def get_by_phone_normalized(connection: pymysql.connections.Connection, phone: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par téléphone en ignorant tout caractère non numérique
    (espaces, tirets, points) des deux côtés de la comparaison.

    Utile car les numéros sont stockés formatés (ex: "06 66 69 48 31") mais
    peuvent être saisis sans formatage (ex: "0666694831").

    Args:
        connection: Connexion MySQL
        phone: Téléphone du customer, formaté ou non

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    import re
    digits_only = re.sub(r"\D", "", phone or "")
    if not digits_only:
        return None

    try:
        cursor = connection.cursor()

        query = """
            SELECT * FROM customers
            WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                phone, ' ', ''), '-', ''), '.', ''), '(', ''), ')', ''
            ) = %s
            LIMIT 1
        """
        cursor.execute(query, (digits_only,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par téléphone normalisé : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection, page: int = 1, size: int = 10,
            search: Optional[str] = None, v2: bool = False,
            country: Optional[str] = None,
            year: Optional[str] = None,
            month: Optional[str] = None,
            verified: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customers avec pagination et recherche

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche (nom, email, téléphone, ville, référence de formule)
        v2: Filtre par version du formulaire
        country: Filtre par pays
        year: Filtre par année (created_at ou référence de formule)
        month: Filtre par mois (1-12, basé sur created_at)
        verified: Filtre email vérifié ("true" ou "false")

    Returns:
        Tuple (liste des customers, total)
    """
    try:
        cursor = connection.cursor()

        conditions = ["customers.v2 = %s"]
        params = [v2]

        if country:
            conditions.append("customers.country = %s")
            params.append(country)

        if year:
            year_expr = """
                COALESCE(
                    YEAR(customers.created_at),
                    (
                        SELECT CAST(LEFT(formula.reference, 4) AS UNSIGNED)
                        FROM formula
                        WHERE formula.customer_id = customers.id
                            AND formula.reference REGEXP '^[0-9]{4}'
                        ORDER BY formula.id ASC
                        LIMIT 1
                    )
                )
            """
            conditions.append(f"{year_expr} = %s")
            params.append(int(year))

        if month:
            conditions.append("MONTH(customers.created_at) = %s")
            params.append(int(month))

        if verified is not None:
            conditions.append("customers.verified_email = %s")
            params.append(1 if verified == 'true' else 0)

        if search:
            search_param = f"%{search}%"
            conditions.append("""
                (customers.first_name LIKE %s OR customers.last_name LIKE %s
                OR customers.email LIKE %s OR customers.phone LIKE %s OR customers.city LIKE %s
                OR customers.id IN (
                    SELECT formula.customer_id FROM formula WHERE formula.reference LIKE %s
                ))
            """)
            params.extend([search_param] * 6)

        where_clause = "WHERE " + " AND ".join(conditions)

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM customers {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM customers {where_clause}
            ORDER BY customers.id DESC
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


def update(connection: pymysql.connections.Connection, customer_id: int,
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

        # Vérifier d'abord que le customer existe
        check_query = "SELECT id FROM customers WHERE id = %s"
        cursor.execute(check_query, (customer_id,))
        if not cursor.fetchone():
            return False

        # Filtrer les valeurs None/vides MAIS garder les valeurs explicitement None pour les nettoyer
        clean_data = {}
        for k, v in customer_data.items():
            # Garder toutes les valeurs sauf les chaînes vides
            if v != "":
                clean_data[k] = v

        if not clean_data:
            # Pas de données à mettre à jour, mais le customer existe
            return True

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

        # Si rowcount == 0, ça peut être parce que les valeurs étaient déjà identiques
        # Mais on a vérifié l'existence au début, donc on retourne True
        return True

    except Exception as e:
        print(f"Erreur mise à jour customer : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection, customer_id: int) -> bool:
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


def check_duplicate_email(connection: pymysql.connections.Connection, email: str) -> bool:
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


def get_analytics(connection: pymysql.connections.Connection) -> Dict[str, Any]:
    """
    Calcule les statistiques d'analyse des clients :
    - Total clients ce mois-ci vs mois dernier
    - Répartition par mois pour l'année en cours
    - Répartition par année (toutes années)
    - Taux de rétention (clients avec >= 2 formules)
    - Top 5 pays par nombre de clients

    Args:
        connection: Connexion MySQL

    Returns:
        Dictionnaire avec les statistiques d'analyse
    """
    try:
        cursor = connection.cursor()

        # Clients ce mois-ci vs mois dernier
        cursor.execute("""
            SELECT
                SUM(CASE WHEN YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE()) THEN 1 ELSE 0 END) AS current_month,
                SUM(CASE WHEN YEAR(created_at) = YEAR(CURDATE() - INTERVAL 1 MONTH) AND MONTH(created_at) = MONTH(CURDATE() - INTERVAL 1 MONTH) THEN 1 ELSE 0 END) AS last_month
            FROM customers
        """)
        month_row = cursor.fetchone() or {}
        current_month = month_row.get('current_month') or 0
        last_month = month_row.get('last_month') or 0

        # Année effective d'un customer : created_at si présent, sinon l'année
        # de référence de sa première formule (les customers plus anciens
        # n'ont pas toujours de created_at renseigné)
        year_expr = """
            COALESCE(
                YEAR(customers.created_at),
                (
                    SELECT CAST(LEFT(formula.reference, 4) AS UNSIGNED)
                    FROM formula
                    WHERE formula.customer_id = customers.id
                        AND formula.reference REGEXP '^[0-9]{4}'
                    ORDER BY formula.id ASC
                    LIMIT 1
                )
            )
        """

        # Répartition par mois pour l'année en cours
        cursor.execute("""
            SELECT MONTH(created_at) AS month, COUNT(*) AS total
            FROM customers
            WHERE YEAR(created_at) = YEAR(CURDATE())
            GROUP BY MONTH(created_at)
            ORDER BY month ASC
        """)
        by_month = cursor.fetchall() or []

        # Répartition par année (toutes années)
        cursor.execute(f"""
            SELECT {year_expr} AS year, COUNT(*) AS total
            FROM customers
            GROUP BY year
            HAVING year IS NOT NULL
            ORDER BY year ASC
        """)
        by_year = cursor.fetchall() or []

        # Taux de rétention : clients avec au moins 2 formules
        cursor.execute("SELECT COUNT(*) AS total FROM customers")
        total_customers = (cursor.fetchone() or {}).get('total') or 0

        cursor.execute("""
            SELECT COUNT(*) AS total FROM (
                SELECT customer_id
                FROM formula
                WHERE customer_id IS NOT NULL
                GROUP BY customer_id
                HAVING COUNT(*) >= 2
            ) AS retained
        """)
        retained_customers = (cursor.fetchone() or {}).get('total') or 0

        retention_rate = round((retained_customers / total_customers) * 100, 2) if total_customers > 0 else 0

        # Top 5 pays par nombre de clients
        cursor.execute("""
            SELECT country, COUNT(*) AS total
            FROM customers
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country
            ORDER BY total DESC
            LIMIT 5
        """)
        top_countries = cursor.fetchall() or []

        return {
            "current_month_customers": current_month,
            "last_month_customers": last_month,
            "customers_by_month": by_month,
            "customers_by_year": by_year,
            "total_customers": total_customers,
            "retained_customers": retained_customers,
            "retention_rate": retention_rate,
            "top_countries": top_countries,
        }

    except Exception as e:
        print(f"Erreur récupération analytics customers : {e}")
        return {
            "current_month_customers": 0,
            "last_month_customers": 0,
            "customers_by_month": [],
            "customers_by_year": [],
            "total_customers": 0,
            "retained_customers": 0,
            "retention_rate": 0,
            "top_countries": [],
        }
    finally:
        cursor.close()


def get_countries(connection: pymysql.connections.Connection) -> List[str]:
    """
    Récupère la liste des pays distincts dans la table customers

    Args:
        connection: Connexion MySQL

    Returns:
        Liste des pays triés alphabétiquement
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT DISTINCT country
            FROM customers
            WHERE country IS NOT NULL AND country != ''
            ORDER BY country ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        return [row['country'] for row in rows]

    except Exception as e:
        print(f"Erreur récupération pays : {e}")
        return []
    finally:
        cursor.close()


def check_duplicate_phone(connection: pymysql.connections.Connection, phone: str) -> bool:
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
