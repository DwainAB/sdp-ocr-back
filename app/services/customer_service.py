from typing import Dict, Any, Optional
from app.database import get_connection
from app.crud import crud_customer, crud_customer_review
from app.services.email_validator import email_validator
from app.services.email_domain_corrector import email_domain_corrector
from app.services.email_domain_validator import email_domain_validator


class CustomerBusinessService:
    """
    Service pour la logique métier des customers (validation, règles business)
    """

    def insert_customer_if_not_exists(self, extracted_data: Dict[str, Any]) -> Optional[int]:
        """
        Insère un customer dans la base pour chaque PDF traité (peu importe les données)
        Gère la détection de doublons et l'insertion dans customers_review si nécessaire

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            ID du customer inséré ou None si erreur
        """
        # Mapper les champs OCR vers les colonnes DB
        customer_data = self._map_ocr_to_customer(extracted_data)

        connection = get_connection()
        if not connection:
            return None

        try:
            # Vérifier si le customer existe déjà (seulement si on a email ou téléphone)
            if customer_data.get('email') or customer_data.get('phone'):
                duplicate_type = self._check_duplicate_type(
                    connection,
                    customer_data.get('email'),
                    customer_data.get('phone')
                )
                if duplicate_type:
                    print(f"Customer doublon détecté : {duplicate_type}")
                    # Insérer dans customers_review avec le type de doublon
                    return crud_customer_review.create(connection, customer_data, duplicate_type)

            # Insérer le customer TOUJOURS (même complètement vide)
            return crud_customer.create(connection, customer_data)

        finally:
            if connection.is_connected():
                connection.close()

    def _map_ocr_to_customer(self, extracted_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Mappe les données OCR vers les champs customer et valide l'email

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            Dictionnaire mappé avec les champs customer
        """
        def safe_strip(value):
            """Fonction helper pour éviter les erreurs None.strip()"""
            if value is None:
                return None
            return str(value).strip() or None

        email = safe_strip(extracted_data.get('email'))
        verified_email = None
        verified_domain = None
        original_email = None

        # Corriger le domaine email s'il contient une faute
        if email:
            corrected_email, was_corrected, original_domain = email_domain_corrector.correct_email(email)

            if was_corrected:
                original_email = email  # Sauvegarder l'email original
                email = corrected_email  # Utiliser l'email corrigé
                print(f"📧 Domaine corrigé : {original_email} → {email}")

        # Vérifier le domaine via MX DNS
        if email:
            is_valid_domain, details = email_domain_validator.verify_email_domain(email)
            verified_domain = is_valid_domain
            print(f"🔍 Vérification domaine : {email} → {verified_domain} ({details})")

        # Valider l'email s'il existe
        if email:
            print(f"Validation de l'email : {email}")
            verified_email = email_validator.validate_email_sync(email)
            print(f"Résultat validation : {verified_email}")

        return {
            'first_name': safe_strip(extracted_data.get('prenom')),
            'last_name': safe_strip(extracted_data.get('nom')),
            'email': email,
            'phone': safe_strip(extracted_data.get('tel')),
            'job': safe_strip(extracted_data.get('profession')),
            'city': safe_strip(extracted_data.get('ville')),
            'country': safe_strip(extracted_data.get('pays')),
            'reference': safe_strip(extracted_data.get('identifiant')),
            'date': safe_strip(extracted_data.get('date')),
            'verified_email': verified_email,
            'verified_domain': verified_domain
        }

    def _check_duplicate_type(self, connection, email: Optional[str],
                             phone: Optional[str]) -> Optional[str]:
        """
        Vérifie si un customer existe déjà et retourne le type de doublon

        Args:
            connection: Connexion MySQL
            email: Email à vérifier
            phone: Téléphone à vérifier

        Returns:
            "Doublon - Mail" si l'email existe déjà
            "Doublon - Phone" si le téléphone existe déjà
            "Doublon - Mail et Phone" si les deux existent
            None si pas de doublon
        """
        if not email and not phone:
            return None

        duplicate_types = []

        # Vérifier l'email
        if email and crud_customer.check_duplicate_email(connection, email):
            duplicate_types.append("Mail")

        # Vérifier le téléphone
        if phone and crud_customer.check_duplicate_phone(connection, phone):
            duplicate_types.append("Phone")

        if duplicate_types:
            return f"Doublon - {' et '.join(duplicate_types)}"

        return None

    def create_customer_with_validation(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau customer avec validation d'email et correction du domaine

        Args:
            customer_data: Données du customer

        Returns:
            ID du customer créé ou None si erreur
        """
        # Corriger le domaine email s'il contient une faute
        email = customer_data.get('email')
        if email:
            corrected_email, was_corrected, original_domain = email_domain_corrector.correct_email(email)

            if was_corrected:
                customer_data['email'] = corrected_email
                print(f"📧 Domaine corrigé : {email} → {corrected_email}")

        # Vérifier le domaine via MX DNS
        email = customer_data.get('email')
        if email and 'verified_domain' not in customer_data:
            is_valid_domain, details = email_domain_validator.verify_email_domain(email)
            customer_data['verified_domain'] = is_valid_domain
            print(f"🔍 Vérification domaine : {email} → {is_valid_domain} ({details})")

        # Valider l'email si présent
        email = customer_data.get('email')
        if email and 'verified_email' not in customer_data:
            print(f"Validation de l'email : {email}")
            customer_data['verified_email'] = email_validator.validate_email_sync(email)
            print(f"Résultat validation : {customer_data['verified_email']}")

        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer.create(connection, customer_data)
        finally:
            if connection.is_connected():
                connection.close()


customer_business_service = CustomerBusinessService()
