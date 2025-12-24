from typing import Dict, Any, Optional, List, Tuple
from app.db.connection import get_connection

class CustomerService:
    """
    Service pour gérer les customers dans la base de données
    """

    def insert_customer_if_not_exists(self, extracted_data: Dict[str, Any]) -> Optional[int]:
        """
        Insère un customer dans la base pour chaque PDF traité (peu importe les données)

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            ID du customer inséré ou None si erreur
        """
        # Mapper les champs OCR vers les colonnes DB
        customer_data = self._map_ocr_to_customer(extracted_data)

        # Vérifier si le customer existe déjà (seulement si on a email ou téléphone)
        if customer_data.get('email') or customer_data.get('phone'):
            if self._customer_exists(customer_data.get('email'), customer_data.get('phone')):
                print(f"Customer déjà existant : {customer_data.get('email')} / {customer_data.get('phone')}")
                return None

        # Insérer le customer TOUJOURS (même complètement vide)
        return self._insert_customer(customer_data)

    def _map_ocr_to_customer(self, extracted_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Mappe les données OCR vers les champs customer
        """
        def safe_strip(value):
            """Fonction helper pour éviter les erreurs None.strip()"""
            if value is None:
                return None
            return str(value).strip() or None

        return {
            'first_name': safe_strip(extracted_data.get('prenom')),
            'last_name': safe_strip(extracted_data.get('nom')),
            'email': safe_strip(extracted_data.get('email')),
            'phone': safe_strip(extracted_data.get('tel')),
            'job': safe_strip(extracted_data.get('profession')),
            'city': safe_strip(extracted_data.get('ville')),
            'country': safe_strip(extracted_data.get('pays')),
            'reference': safe_strip(extracted_data.get('identifiant'))
        }

    def _customer_exists(self, email: Optional[str], phone: Optional[str]) -> bool:
        """
        Vérifie si un customer existe déjà avec cet email ou ce téléphone
        """
        if not email and not phone:
            return False

        connection = get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Construire la requête selon les champs disponibles
            conditions = []
            params = []

            if email:
                conditions.append("email = %s")
                params.append(email)

            if phone:
                conditions.append("phone = %s")
                params.append(phone)

            query = f"SELECT id FROM customers WHERE {' OR '.join(conditions)} LIMIT 1"

            cursor.execute(query, params)
            result = cursor.fetchone()

            return result is not None

        except Exception as e:
            print(f"Erreur vérification customer : {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def _insert_customer(self, customer_data: Dict[str, str]) -> Optional[int]:
        """
        Insère un customer dans la base
        """
        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v}

        # Si aucune donnée, insérer une ligne vide quand même
        if not clean_data:
            print("Insertion d'une ligne vide")
            clean_data = {}  # MySQL accepte les INSERT sans colonnes

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
                    INSERT INTO customers ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                cursor.execute(query, values)
            else:
                # Insertion ligne vide (seulement ID auto-increment)
                query = "INSERT INTO customers () VALUES ()"
                cursor.execute(query)

            connection.commit()
            customer_id = cursor.lastrowid
            print(f"Customer inséré avec ID: {customer_id}")
            print(f"Données: {clean_data}")

            return customer_id

        except Exception as e:
            print(f"Erreur insertion customer : {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    # ======================================================================
    # CRUD OPERATIONS
    # ======================================================================

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau customer avec validation
        """
        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

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
            print(f"Customer créé avec ID: {customer_id}")

            return customer_id

        except Exception as e:
            print(f"Erreur création customer : {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un customer par son ID
        """
        connection = get_connection()
        if not connection:
            return None

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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_all_customers(self, page: int = 1, size: int = 10, search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les customers avec pagination et recherche
        """
        connection = get_connection()
        if not connection:
            return [], 0

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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer
        """
        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

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
            values.append(customer_id)  # Pour le WHERE

            query = f"""
                UPDATE customers
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cursor.execute(query, values)
            connection.commit()

            # Vérifier si une ligne a été modifiée
            success = cursor.rowcount > 0

            if success:
                print(f"Customer {customer_id} mis à jour")
            else:
                print(f"Customer {customer_id} non trouvé")

            return success

        except Exception as e:
            print(f"Erreur mise à jour customer : {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def delete_customer(self, customer_id: int) -> bool:
        """
        Supprime un customer
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            query = "DELETE FROM customers WHERE id = %s"
            cursor.execute(query, (customer_id,))
            connection.commit()

            # Vérifier si une ligne a été supprimée
            success = cursor.rowcount > 0

            if success:
                print(f"Customer {customer_id} supprimé")
            else:
                print(f"Customer {customer_id} non trouvé")

            return success

        except Exception as e:
            print(f"Erreur suppression customer : {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

customer_service = CustomerService()