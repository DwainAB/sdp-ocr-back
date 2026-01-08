from typing import Dict, Any, Optional, Tuple
from app.database import get_connection
from app.crud import crud_customer, crud_customer_review
from app.services.email import email_validator, email_domain_corrector, email_domain_validator
from app.services.country import country_corrector
from app.services.phone import phone_validator, phone_intelligence_validator
from app.services.city import city_normalizer


class CustomerBusinessService:
    """
    Service pour la logique métier des customers (validation, règles business)
    """

    def insert_customer_if_not_exists(self, extracted_data: Dict[str, Any]) -> Tuple[Optional[int], str]:
        """
        Insère un customer dans la base pour chaque PDF traité (peu importe les données)
        Gère la détection de doublons, corrections d'email/phone et l'insertion dans customers_review si nécessaire

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            Tuple (ID du customer/review inséré, type d'entité: "customer" ou "customer_review")
            ou (None, "error") si erreur
        """
        # Mapper les champs OCR vers les colonnes DB
        customer_data, was_email_corrected, phone_error = self._map_ocr_to_customer(extracted_data)

        connection = get_connection()
        if not connection:
            return None, "error"

        try:
            # Si erreur sur le numéro de téléphone, mettre dans customers_review
            if phone_error:
                print(f"Customer avec erreur de numéro → customers_review (type: {phone_error})")
                review_id = crud_customer_review.create(connection, customer_data, phone_error)
                return review_id, "customer_review"

            # Si l'email a été corrigé, mettre dans customers_review avec type "Modifié"
            if was_email_corrected:
                print(f"Customer avec email corrigé → customers_review (type: Modifié)")
                review_id = crud_customer_review.create(connection, customer_data, "Modifié")
                return review_id, "customer_review"

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
                    review_id = crud_customer_review.create(connection, customer_data, duplicate_type)
                    return review_id, "customer_review"

            # Insérer le customer TOUJOURS (même complètement vide)
            customer_id = crud_customer.create(connection, customer_data)
            return customer_id, "customer"

        finally:
            if connection.open:
                connection.close()

    def _map_ocr_to_customer(self, extracted_data: Dict[str, Any]) -> Tuple[Dict[str, str], bool, Optional[str]]:
        """
        Mappe les données OCR vers les champs customer et valide l'email et le téléphone

        Args:
            extracted_data: Données extraites de l'OCR

        Returns:
            Tuple (customer_data, was_email_corrected, phone_error)
            - customer_data: Dictionnaire mappé avec les champs customer
            - was_email_corrected: True si l'email a été corrigé (domaine, extension, ponctuation)
            - phone_error: Type d'erreur téléphone ("Erreur - Numéro", "Modifié", None)
        """
        def safe_strip(value):
            """Fonction helper pour éviter les erreurs None.strip()"""
            if value is None:
                return None
            return str(value).strip() or None

        email = safe_strip(extracted_data.get('email'))
        verified_email = None
        verified_domain = None
        was_email_corrected = False

        # Corriger le domaine email s'il contient une faute
        if email:
            corrected_email, was_corrected, original_domain = email_domain_corrector.correct_email(email)

            if was_corrected:
                was_email_corrected = True
                print(f"📧 Email corrigé : {email} → {corrected_email}")
                email = corrected_email  # Utiliser l'email corrigé

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

        # Corriger le pays s'il contient une erreur
        country = safe_strip(extracted_data.get('pays'))
        if country:
            corrected_country, was_country_corrected = country_corrector.correct_country(country)
            country = corrected_country  # Utiliser le pays corrigé

        # Valider et normaliser le téléphone (APRÈS avoir le pays corrigé)
        phone = safe_strip(extracted_data.get('tel'))
        phone_error = None
        verified_phone = None

        if phone:
            normalized_phone, was_phone_modified, error_type = phone_validator.validate_phone_number(phone, country)

            if error_type == "invalid_length":
                # Numéro invalide → Erreur
                phone_error = "Erreur - Numéro"
                phone = normalized_phone  # Garder le numéro nettoyé même s'il est invalide
            elif was_phone_modified:
                # Numéro modifié/formaté → Modifié
                phone_error = "Modifié"
                phone = normalized_phone
            else:
                # Numéro valide sans modification
                phone = normalized_phone if normalized_phone else phone

        # Vérifier le numéro via AbstractAPI Phone Intelligence
        if phone:
            print(f"Validation du téléphone : {phone}")
            verified_phone = phone_intelligence_validator.verify_phone_number(phone)
            print(f"Résultat validation téléphone : {verified_phone}")

        customer_data = {
            'first_name': safe_strip(extracted_data.get('prenom')),
            'last_name': safe_strip(extracted_data.get('nom')),
            'email': email,
            'phone': phone,
            'job': safe_strip(extracted_data.get('profession')),
            'city': safe_strip(extracted_data.get('ville')),
            'country': country,
            'reference': safe_strip(extracted_data.get('identifiant')),
            'date': safe_strip(extracted_data.get('date')),
            'verified_email': verified_email,
            'verified_domain': verified_domain,
            'verified_phone': verified_phone
        }

        return customer_data, was_email_corrected, phone_error

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

        # Valider le téléphone si présent
        phone = customer_data.get('phone')
        if phone and 'verified_phone' not in customer_data:
            print(f"Validation du téléphone : {phone}")
            customer_data['verified_phone'] = phone_intelligence_validator.verify_phone_number(phone)
            print(f"Résultat validation téléphone : {customer_data['verified_phone']}")

        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_customer.create(connection, customer_data)
        finally:
            if connection.open:
                connection.close()


    def update_customer_with_validation(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        """
        Met à jour un customer avec validation d'email et de téléphone si modifiés

        Args:
            customer_id: ID du customer à mettre à jour
            customer_data: Données à mettre à jour (dict partiel)

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            # Récupérer le customer existant
            existing_customer = crud_customer.get_by_id(connection, customer_id)
            if not existing_customer:
                return False

            # Préparer les données à mettre à jour
            update_data = customer_data.copy()

            # Si l'email est modifié, valider et corriger
            if 'email' in customer_data and customer_data['email'] != existing_customer.get('email'):
                email = customer_data['email']
                if email:
                    # Corriger le domaine email s'il contient une faute
                    corrected_email, was_corrected, original_domain = email_domain_corrector.correct_email(email)

                    if was_corrected:
                        update_data['email'] = corrected_email
                        print(f"📧 Domaine corrigé : {email} → {corrected_email}")

                    # Vérifier le domaine via MX DNS
                    email = update_data['email']
                    is_valid_domain, details = email_domain_validator.verify_email_domain(email)
                    update_data['verified_domain'] = is_valid_domain
                    print(f"🔍 Vérification domaine : {email} → {is_valid_domain} ({details})")

                    # Valider l'email
                    print(f"Validation de l'email : {email}")
                    update_data['verified_email'] = email_validator.validate_email_sync(email)
                    print(f"Résultat validation : {update_data['verified_email']}")

            # Si le téléphone est modifié, valider
            if 'phone' in customer_data and customer_data['phone'] != existing_customer.get('phone'):
                phone = customer_data['phone']
                if phone:
                    print(f"Validation du téléphone : {phone}")
                    update_data['verified_phone'] = phone_intelligence_validator.verify_phone_number(phone)
                    print(f"Résultat validation téléphone : {update_data['verified_phone']}")

            # Mettre à jour le customer
            return crud_customer.update(connection, customer_id, update_data)

        finally:
            if connection.open:
                connection.close()


customer_business_service = CustomerBusinessService()
