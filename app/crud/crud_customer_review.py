from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection, customer_data: Dict[str, Any],
          review_type: str) -> Optional[int]:
    """
    Insère un customer dans la table customers_review avec un type spécifique

    Args:
        connection: Connexion MySQL
        customer_data: Données du customer
        review_type: Type de review (ex: "Doublon - Mail", "Doublon - Phone")

    Returns:
        ID du customer_review créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

        if clean_data:
            # Ajouter le type à la liste des colonnes
            clean_data['type'] = review_type

            columns = list(clean_data.keys())
            placeholders = ["%s"] * len(columns)
            values = list(clean_data.values())

            query = f"""
                INSERT INTO customers_review ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            cursor.execute(query, values)
        else:
            # Insertion avec seulement le type si pas d'autres données
            query = "INSERT INTO customers_review (type) VALUES (%s)"
            cursor.execute(query, (review_type,))

        connection.commit()
        customer_review_id = cursor.lastrowid

        return customer_review_id

    except Exception as e:
        print(f"Erreur création customer review : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection, review_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer_review par son ID

    Args:
        connection: Connexion MySQL
        review_id: ID du customer_review

    Returns:
        Dictionnaire avec les données du customer_review ou None
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, last_name, first_name, phone, email, job, country, city,
                   reference, date, verified_email, verified_domain, verified_phone, type
            FROM customers_review
            WHERE id = %s
        """
        cursor.execute(query, (review_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer review : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection, page: int = 1, size: int = 10,
           review_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customer_reviews avec pagination et filtre optionnel par type

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        review_type: Filtre par type de review

    Returns:
        Tuple (liste des customer_reviews, total)
    """
    try:
        cursor = connection.cursor()

        # Construire la requête avec filtre optionnel
        where_clause = ""
        params = []

        if review_type:
            where_clause = "WHERE type = %s"
            params.append(review_type)

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM customers_review {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT id, last_name, first_name, phone, email, job, country, city,
                   reference, date, verified_email, verified_domain, verified_phone, type
            FROM customers_review {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        cursor.execute(query, params)
        reviews = cursor.fetchall()

        return reviews, total

    except Exception as e:
        print(f"Erreur récupération customer reviews : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection, review_id: int,
          customer_data: Dict[str, Any]) -> bool:
    """
    Met à jour un customer_review

    Args:
        connection: Connexion MySQL
        review_id: ID du customer_review
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
        values.append(review_id)  # Pour le WHERE

        query = f"""
            UPDATE customers_review
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        cursor.execute(query, values)
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour customer review : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection, review_id: int) -> bool:
    """
    Supprime un customer_review définitivement

    Args:
        connection: Connexion MySQL
        review_id: ID du customer_review

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM customers_review WHERE id = %s"
        cursor.execute(query, (review_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression customer review : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def transfer_to_customers(connection: pymysql.connections.Connection, review_id: int) -> Optional[int]:
    """
    Transfère un customer_review vers la table customers puis le supprime de customers_review
    Si l'email existe déjà dans customers, fusionne avec le customer existant au lieu de créer un nouveau

    Args:
        connection: Connexion MySQL
        review_id: ID du customer_review

    Returns:
        ID du customer (nouveau ou existant) ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # 1. Récupérer les données du customer_review
        query = "SELECT * FROM customers_review WHERE id = %s"
        cursor.execute(query, (review_id,))
        review_data = cursor.fetchone()

        if not review_data:
            return None

        # 2. Vérifier si l'email existe déjà dans customers
        email = review_data.get('email')
        existing_customer_id = None

        if email:
            check_query = "SELECT id FROM customers WHERE email = %s LIMIT 1"
            cursor.execute(check_query, (email,))
            existing_customer = cursor.fetchone()

            if existing_customer:
                existing_customer_id = existing_customer['id']
                print(f"📧 Email {email} existe déjà dans customers (ID: {existing_customer_id})")
                print(f"🔄 Fusion: Les fichiers de customer_review {review_id} seront transférés vers customer {existing_customer_id}")

        # 3a. Si email existe déjà → Fusionner
        if existing_customer_id:
            # Transférer les fichiers de customer_review vers le customer existant
            from app.crud import crud_customer_file
            crud_customer_file.transfer_files_to_customer(connection, review_id, existing_customer_id)

            # Déplacer physiquement les fichiers du dossier pending vers le dossier du customer
            from app.services.file import file_storage_service
            files = crud_customer_file.get_by_customer_review_id(connection, review_id)
            for file in files:
                try:
                    old_path = file['file_path']
                    if 'pending' in old_path:
                        new_path = file_storage_service.move_file_to_customer(old_path, existing_customer_id)
                        # Mettre à jour le chemin dans la base de données
                        crud_customer_file.update(connection, file['id'], {'file_path': new_path})
                except Exception as e:
                    print(f"⚠️ Erreur déplacement fichier {file['id']}: {e}")

            # Supprimer de customers_review
            delete_query = "DELETE FROM customers_review WHERE id = %s"
            cursor.execute(delete_query, (review_id,))

            connection.commit()
            print(f"✅ Fusion terminée: customer_review {review_id} fusionné avec customer {existing_customer_id}")
            return existing_customer_id

        # 3b. Si email n'existe pas → Créer nouveau customer
        else:
            # Préparer les données pour customers (sans id, created_at, updated_at, type)
            customer_data = {k: v for k, v in review_data.items()
                           if k not in ['id', 'created_at', 'updated_at', 'type'] and v is not None and v != ""}

            # Insérer dans customers
            if customer_data:
                columns = list(customer_data.keys())
                placeholders = ["%s"] * len(columns)
                values = list(customer_data.values())

                insert_query = f"""
                    INSERT INTO customers ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                cursor.execute(insert_query, values)
            else:
                # Insertion ligne vide
                insert_query = "INSERT INTO customers () VALUES ()"
                cursor.execute(insert_query)

            customer_id = cursor.lastrowid

            # Transférer les fichiers vers le nouveau customer
            from app.crud import crud_customer_file
            crud_customer_file.transfer_files_to_customer(connection, review_id, customer_id)

            # Déplacer physiquement les fichiers du dossier pending vers le dossier du customer
            from app.services.file import file_storage_service
            files = crud_customer_file.get_by_customer_id(connection, customer_id)
            for file in files:
                try:
                    old_path = file['file_path']
                    if 'pending' in old_path:
                        new_path = file_storage_service.move_file_to_customer(old_path, customer_id)
                        # Mettre à jour le chemin dans la base de données
                        crud_customer_file.update(connection, file['id'], {'file_path': new_path})
                except Exception as e:
                    print(f"⚠️ Erreur déplacement fichier {file['id']}: {e}")

            # Supprimer de customers_review
            delete_query = "DELETE FROM customers_review WHERE id = %s"
            cursor.execute(delete_query, (review_id,))

            connection.commit()
            print(f"✅ Nouveau customer créé (ID: {customer_id}) depuis customer_review {review_id}")
            return customer_id

    except Exception as e:
        print(f"Erreur transfert customer review : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
