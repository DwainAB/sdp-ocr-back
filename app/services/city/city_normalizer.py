import re
from typing import Optional


class CityNormalizer:
    """
    Service pour normaliser les noms de villes
    """

    # Prépositions et articles qui restent en minuscules
    LOWERCASE_WORDS = [
        'de', 'du', 'des', 'le', 'la', 'les', 'l',
        'sur', 'sous', 'en', 'aux', 'et', 'à',
        'lez', 'lès',  # Utilisé dans les noms de villes françaises
    ]

    def remove_numbers(self, city: str) -> str:
        """
        Retire tous les chiffres d'un nom de ville

        Args:
            city: Nom de ville

        Returns:
            Nom de ville sans chiffres

        Exemples:
            >>> remove_numbers("Paris 75001")
            "Paris"

            >>> remove_numbers("93100 Montreuil")
            "Montreuil"

            >>> remove_numbers("Saint-Denis 93")
            "Saint-Denis"
        """
        if not city:
            return city

        # Retirer tous les chiffres
        cleaned = re.sub(r'\d+', '', city)

        # Nettoyer les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Retirer les espaces au début et à la fin
        cleaned = cleaned.strip()

        return cleaned

    def capitalize_word(self, word: str, is_first_word: bool = False) -> str:
        """
        Capitalise un mot selon les règles françaises

        Args:
            word: Mot à capitaliser
            is_first_word: True si c'est le premier mot

        Returns:
            Mot capitalisé

        Exemples:
            >>> capitalize_word("paris")
            "Paris"

            >>> capitalize_word("de")
            "de"

            >>> capitalize_word("de", is_first_word=True)
            "De"
        """
        if not word:
            return word

        word_lower = word.lower()

        # Si c'est le premier mot, toujours capitaliser
        if is_first_word:
            return word_lower.capitalize()

        # Si c'est un mot qui doit rester en minuscules
        if word_lower in self.LOWERCASE_WORDS:
            return word_lower

        # Sinon, capitaliser
        return word_lower.capitalize()

    def normalize_city(self, city: str) -> str:
        """
        Normalise un nom de ville :
        - Retire les chiffres (codes postaux)
        - Met en forme : Première lettre en majuscule, reste en minuscule
        - Gère les tirets et apostrophes
        - Respecte les prépositions (de, le, la, etc.)

        Args:
            city: Nom de ville brut

        Returns:
            Nom de ville normalisé

        Exemples:
            >>> normalize_city("PARIS")
            "Paris"

            >>> normalize_city("saint-denis")
            "Saint-Denis"

            >>> normalize_city("aix-en-provence")
            "Aix-en-Provence"

            >>> normalize_city("l'haÿ-les-roses")
            "L'Haÿ-les-Roses"

            >>> normalize_city("75001 Paris")
            "Paris"

            >>> normalize_city("93100 MONTREUIL")
            "Montreuil"

            >>> normalize_city("boulogne-billancourt")
            "Boulogne-Billancourt"

            >>> normalize_city("saint-germain-en-laye")
            "Saint-Germain-en-Laye"
        """
        if not city:
            return city

        # Étape 1 : Retirer les chiffres
        city = self.remove_numbers(city)

        if not city:
            return city

        # Étape 2 : Gérer les tirets et apostrophes
        # On découpe par espaces, tirets et apostrophes tout en gardant les séparateurs
        parts = re.split(r"([ \-'])", city)

        # Étape 3 : Capitaliser chaque partie
        normalized_parts = []
        word_index = 0  # Compteur de mots réels (pas les séparateurs)

        for i, part in enumerate(parts):
            if not part:
                continue

            # Si c'est un séparateur (espace, tiret, apostrophe), le garder tel quel
            if part in [' ', '-', "'"]:
                normalized_parts.append(part)
                continue

            # C'est un mot, le capitaliser
            is_first_word = (word_index == 0)
            normalized_parts.append(self.capitalize_word(part, is_first_word))
            word_index += 1

        normalized = ''.join(normalized_parts)

        print(f"🏙️ Ville normalisée : {city} → {normalized}")

        return normalized


# Instance globale
city_normalizer = CityNormalizer()
