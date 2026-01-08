import re
from typing import Tuple, Optional


class PhoneValidator:
    """
    Service pour valider et normaliser les numéros de téléphone selon le pays
    """

    # Règles de validation par pays
    PHONE_RULES = {
        'France': {
            'min_digits': 10,
            'max_digits': 10,
            'format': '{} {} {} {} {}',  # XX XX XX XX XX
            'chunk_sizes': [2, 2, 2, 2, 2],
            'example': '06 12 34 56 78'
        },
        'Belgique': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {} {}',  # XXX XX XX XX ou XX XX XX XX
            'chunk_sizes': [3, 2, 2, 2],  # Pour 9 chiffres
            'chunk_sizes_10': [2, 2, 2, 2, 2],  # Pour 10 chiffres
            'example': '012 34 56 78'
        },
        'Suisse': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {} {}',  # XXX XXX XX XX
            'chunk_sizes': [3, 3, 2, 2],
            'example': '021 234 56 78'
        },
        'États-Unis': {
            'min_digits': 10,
            'max_digits': 10,
            'format': '{}-{}-{}',  # XXX-XXX-XXXX
            'chunk_sizes': [3, 3, 4],
            'example': '555-123-4567'
        },
        'Canada': {
            'min_digits': 10,
            'max_digits': 10,
            'format': '{}-{}-{}',  # XXX-XXX-XXXX
            'chunk_sizes': [3, 3, 4],
            'example': '514-123-4567'
        },
        'Royaume-Uni': {
            'min_digits': 10,
            'max_digits': 11,
            'format': '{} {} {}',  # XXXX XXX XXXX ou XXX XXXX XXXX
            'chunk_sizes': [4, 3, 4],
            'example': '0207 123 4567'
        },
        'Allemagne': {
            'min_digits': 10,
            'max_digits': 11,
            'format': '{} {} {}',  # XXX XXX XXXX
            'chunk_sizes': [3, 3, 4],
            'example': '030 123 4567'
        },
        'Espagne': {
            'min_digits': 9,
            'max_digits': 9,
            'format': '{} {} {} {}',  # XXX XX XX XX
            'chunk_sizes': [3, 2, 2, 2],
            'example': '612 34 56 78'
        },
        'Italie': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {}',  # XXX XXX XXX ou XXX XXX XXXX
            'chunk_sizes': [3, 3, 3],
            'example': '06 1234 5678'
        },
        'Portugal': {
            'min_digits': 9,
            'max_digits': 9,
            'format': '{} {} {} {}',  # XXX XX XX XX
            'chunk_sizes': [3, 2, 2, 2],
            'example': '912 345 678'
        },
        'Pays-Bas': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {}',  # XX XXX XXXX
            'chunk_sizes': [2, 3, 4],
            'example': '06 1234 5678'
        },
        'Maroc': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {} {}',  # XXXX XX XX XX
            'chunk_sizes': [4, 2, 2, 2],
            'example': '0612 34 56 78'
        },
        'Algérie': {
            'min_digits': 9,
            'max_digits': 10,
            'format': '{} {} {} {}',  # XXXX XX XX XX
            'chunk_sizes': [4, 2, 2, 2],
            'example': '0555 12 34 56'
        },
        'Tunisie': {
            'min_digits': 8,
            'max_digits': 8,
            'format': '{} {} {}',  # XX XXX XXX
            'chunk_sizes': [2, 3, 3],
            'example': '20 123 456'
        },
    }

    def clean_phone_number(self, phone: str) -> str:
        """
        Nettoie un numéro de téléphone en ne gardant que les chiffres

        Args:
            phone: Numéro de téléphone brut

        Returns:
            Numéro nettoyé (chiffres uniquement)

        Exemples:
            >>> clean_phone_number("06 12 34 56 78")
            "0612345678"

            >>> clean_phone_number("+33 6 12 34 56 78")
            "33612345678"

            >>> clean_phone_number("(555) 123-4567")
            "5551234567"
        """
        if not phone:
            return ""

        # Retirer tous les caractères non numériques
        cleaned = re.sub(r'[^\d]', '', phone)
        return cleaned

    def format_phone_number(self, digits: str, country: str) -> str:
        """
        Formate un numéro de téléphone selon les règles du pays

        Args:
            digits: Numéros (chiffres uniquement)
            country: Nom du pays

        Returns:
            Numéro formaté selon le standard du pays

        Exemples:
            >>> format_phone_number("0612345678", "France")
            "06 12 34 56 78"

            >>> format_phone_number("5551234567", "États-Unis")
            "555-123-4567"
        """
        if not digits or not country:
            return digits

        rules = self.PHONE_RULES.get(country)
        if not rules:
            return digits

        # Cas spécial pour la Belgique (9 ou 10 chiffres)
        if country == 'Belgique' and len(digits) == 10:
            chunk_sizes = rules['chunk_sizes_10']
        else:
            chunk_sizes = rules['chunk_sizes']

        # Découper le numéro en morceaux
        chunks = []
        start = 0
        for size in chunk_sizes:
            if start + size <= len(digits):
                chunks.append(digits[start:start + size])
                start += size

        # S'il reste des chiffres, les ajouter au dernier chunk
        if start < len(digits):
            if chunks:
                chunks[-1] += digits[start:]
            else:
                chunks.append(digits[start:])

        # Formatter selon le template
        try:
            formatted = rules['format'].format(*chunks)
            return formatted
        except:
            # Si le formatage échoue, retourner les chiffres bruts
            return digits

    def validate_phone_number(self, phone: str, country: Optional[str]) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Valide et normalise un numéro de téléphone

        Args:
            phone: Numéro de téléphone à valider
            country: Pays du client (peut être None)

        Returns:
            Tuple (phone_normalized, was_modified, error_type)
            - phone_normalized: Numéro normalisé ou None si invalide
            - was_modified: True si le numéro a été modifié/formaté
            - error_type: Type d'erreur ("invalid_length", "no_country", None)

        Exemples:
            >>> validate_phone_number("0612345678", "France")
            ("06 12 34 56 78", True, None)

            >>> validate_phone_number("061234", "France")
            (None, False, "invalid_length")

            >>> validate_phone_number("0612345678", None)
            ("0612345678", False, "no_country")
        """
        if not phone:
            return None, False, None

        # Nettoyer le numéro
        cleaned = self.clean_phone_number(phone)

        if not cleaned:
            return None, False, None

        # Si pas de pays, on ne peut pas valider
        if not country:
            print(f"⚠️ Numéro sans pays : {phone}")
            return cleaned, False, "no_country"

        # Récupérer les règles du pays
        rules = self.PHONE_RULES.get(country)
        if not rules:
            print(f"⚠️ Pas de règles pour le pays : {country}")
            return cleaned, False, "no_country"

        # Vérifier le nombre de chiffres
        min_digits = rules['min_digits']
        max_digits = rules['max_digits']
        digit_count = len(cleaned)

        if digit_count < min_digits or digit_count > max_digits:
            print(f"❌ Numéro invalide pour {country} : {phone} ({digit_count} chiffres, attendu {min_digits}-{max_digits})")
            return None, False, "invalid_length"

        # Formatter le numéro
        formatted = self.format_phone_number(cleaned, country)

        # Vérifier si le numéro a été modifié
        was_modified = (phone != formatted)

        if was_modified:
            print(f"📞 Numéro formaté : {phone} → {formatted}")

        return formatted, was_modified, None


# Instance globale
phone_validator = PhoneValidator()
