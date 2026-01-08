from typing import Optional, Tuple


class CountryCorrector:
    """
    Service pour normaliser et corriger les noms de pays
    """

    # Mapping des codes ISO 3166-1 alpha-2 vers les noms de pays en français
    COUNTRY_CODES = {
        # Europe
        'FR': 'France',
        'BE': 'Belgique',
        'CH': 'Suisse',
        'DE': 'Allemagne',
        'IT': 'Italie',
        'ES': 'Espagne',
        'PT': 'Portugal',
        'GB': 'Royaume-Uni',
        'UK': 'Royaume-Uni',
        'IE': 'Irlande',
        'NL': 'Pays-Bas',
        'LU': 'Luxembourg',
        'AT': 'Autriche',
        'GR': 'Grèce',
        'PL': 'Pologne',
        'SE': 'Suède',
        'NO': 'Norvège',
        'DK': 'Danemark',
        'FI': 'Finlande',
        'CZ': 'République tchèque',
        'HU': 'Hongrie',
        'RO': 'Roumanie',
        'BG': 'Bulgarie',
        'HR': 'Croatie',
        'SI': 'Slovénie',
        'SK': 'Slovaquie',
        'EE': 'Estonie',
        'LV': 'Lettonie',
        'LT': 'Lituanie',
        'CY': 'Chypre',
        'MT': 'Malte',

        # Amériques
        'US': 'États-Unis',
        'USA': 'États-Unis',
        'CA': 'Canada',
        'MX': 'Mexique',
        'BR': 'Brésil',
        'AR': 'Argentine',
        'CL': 'Chili',
        'CO': 'Colombie',
        'PE': 'Pérou',
        'VE': 'Venezuela',

        # Asie
        'CN': 'Chine',
        'JP': 'Japon',
        'IN': 'Inde',
        'KR': 'Corée du Sud',
        'TH': 'Thaïlande',
        'VN': 'Vietnam',
        'ID': 'Indonésie',
        'MY': 'Malaisie',
        'SG': 'Singapour',
        'PH': 'Philippines',
        'PK': 'Pakistan',
        'BD': 'Bangladesh',
        'AE': 'Émirats arabes unis',
        'SA': 'Arabie saoudite',
        'IL': 'Israël',
        'TR': 'Turquie',

        # Afrique
        'MA': 'Maroc',
        'DZ': 'Algérie',
        'TN': 'Tunisie',
        'EG': 'Égypte',
        'ZA': 'Afrique du Sud',
        'NG': 'Nigeria',
        'KE': 'Kenya',
        'GH': 'Ghana',
        'SN': 'Sénégal',
        'CI': 'Côte d\'Ivoire',

        # Océanie
        'AU': 'Australie',
        'NZ': 'Nouvelle-Zélande',
    }

    # Liste des noms de pays valides (en français)
    VALID_COUNTRIES = [
        # Europe
        'France',
        'Belgique',
        'Suisse',
        'Allemagne',
        'Italie',
        'Espagne',
        'Portugal',
        'Royaume-Uni',
        'Irlande',
        'Pays-Bas',
        'Luxembourg',
        'Autriche',
        'Grèce',
        'Pologne',
        'Suède',
        'Norvège',
        'Danemark',
        'Finlande',
        'République tchèque',
        'Hongrie',
        'Roumanie',
        'Bulgarie',
        'Croatie',
        'Slovénie',
        'Slovaquie',
        'Estonie',
        'Lettonie',
        'Lituanie',
        'Chypre',
        'Malte',

        # Amériques
        'États-Unis',
        'Canada',
        'Mexique',
        'Brésil',
        'Argentine',
        'Chili',
        'Colombie',
        'Pérou',
        'Venezuela',

        # Asie
        'Chine',
        'Japon',
        'Inde',
        'Corée du Sud',
        'Thaïlande',
        'Vietnam',
        'Indonésie',
        'Malaisie',
        'Singapour',
        'Philippines',
        'Pakistan',
        'Bangladesh',
        'Émirats arabes unis',
        'Arabie saoudite',
        'Israël',
        'Turquie',

        # Afrique
        'Maroc',
        'Algérie',
        'Tunisie',
        'Égypte',
        'Afrique du Sud',
        'Nigeria',
        'Kenya',
        'Ghana',
        'Sénégal',
        'Côte d\'Ivoire',

        # Océanie
        'Australie',
        'Nouvelle-Zélande',
    ]

    # Variantes communes (en anglais ou autres langues)
    COUNTRY_VARIANTS = {
        # Anglais → Français
        'united states': 'États-Unis',
        'united states of america': 'États-Unis',
        'usa': 'États-Unis',
        'united kingdom': 'Royaume-Uni',
        'great britain': 'Royaume-Uni',
        'england': 'Royaume-Uni',
        'scotland': 'Royaume-Uni',
        'wales': 'Royaume-Uni',
        'netherlands': 'Pays-Bas',
        'holland': 'Pays-Bas',
        'germany': 'Allemagne',
        'spain': 'Espagne',
        'italy': 'Italie',
        'switzerland': 'Suisse',
        'belgium': 'Belgique',
        'austria': 'Autriche',
        'portugal': 'Portugal',
        'greece': 'Grèce',
        'poland': 'Pologne',
        'sweden': 'Suède',
        'norway': 'Norvège',
        'denmark': 'Danemark',
        'finland': 'Finlande',
        'czech republic': 'République tchèque',
        'hungary': 'Hongrie',
        'romania': 'Roumanie',
        'bulgaria': 'Bulgarie',
        'croatia': 'Croatie',
        'slovenia': 'Slovénie',
        'slovakia': 'Slovaquie',
        'china': 'Chine',
        'japan': 'Japon',
        'india': 'Inde',
        'south korea': 'Corée du Sud',
        'thailand': 'Thaïlande',
        'vietnam': 'Vietnam',
        'indonesia': 'Indonésie',
        'malaysia': 'Malaisie',
        'singapore': 'Singapour',
        'philippines': 'Philippines',
        'australia': 'Australie',
        'new zealand': 'Nouvelle-Zélande',
        'brazil': 'Brésil',
        'argentina': 'Argentine',
        'canada': 'Canada',
        'mexico': 'Mexique',
        'morocco': 'Maroc',
        'algeria': 'Algérie',
        'tunisia': 'Tunisie',
        'egypt': 'Égypte',
        'south africa': 'Afrique du Sud',

        # Variantes françaises
        'etats-unis': 'États-Unis',
        'etats unis': 'États-Unis',
        'royaume uni': 'Royaume-Uni',
        'pays bas': 'Pays-Bas',
        'emirats arabes unis': 'Émirats arabes unis',
        'arabie saoudite': 'Arabie saoudite',
        'coree du sud': 'Corée du Sud',
        'afrique du sud': 'Afrique du Sud',
        'nouvelle zelande': 'Nouvelle-Zélande',
        'nouvelle-zelande': 'Nouvelle-Zélande',
        'republique tcheque': 'République tchèque',
    }

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calcule la distance de Levenshtein entre deux chaînes

        Args:
            s1: Première chaîne
            s2: Deuxième chaîne

        Returns:
            Distance de Levenshtein (nombre de modifications)
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def normalize_country_code(self, country: str) -> Optional[str]:
        """
        Convertit un code pays (FR, US, etc.) en nom complet

        Args:
            country: Code pays (2 ou 3 lettres)

        Returns:
            Nom du pays en français ou None

        Exemples:
            >>> normalize_country_code("FR")
            "France"

            >>> normalize_country_code("USA")
            "États-Unis"
        """
        country_upper = country.upper().strip()

        if country_upper in self.COUNTRY_CODES:
            return self.COUNTRY_CODES[country_upper]

        return None

    def normalize_country_variant(self, country: str) -> Optional[str]:
        """
        Convertit une variante de nom de pays en version française officielle

        Args:
            country: Nom du pays (variante)

        Returns:
            Nom du pays en français ou None

        Exemples:
            >>> normalize_country_variant("United States")
            "États-Unis"

            >>> normalize_country_variant("Holland")
            "Pays-Bas"
        """
        country_lower = country.lower().strip()

        if country_lower in self.COUNTRY_VARIANTS:
            return self.COUNTRY_VARIANTS[country_lower]

        return None

    def suggest_country(self, country: str, max_distance: int = 2) -> Optional[str]:
        """
        Suggère une correction pour un nom de pays mal orthographié

        Args:
            country: Le nom du pays à vérifier
            max_distance: Distance maximale acceptable (par défaut 2)

        Returns:
            Le nom du pays corrigé ou None

        Exemples:
            >>> suggest_country("Frence")
            "France"

            >>> suggest_country("Belguim")
            "Belgique"
        """
        country_lower = country.lower().strip()

        # Si le pays est déjà correct
        if country in self.VALID_COUNTRIES:
            return None

        best_match = None
        best_distance = float('inf')

        # Comparer avec tous les noms de pays valides
        for valid_country in self.VALID_COUNTRIES:
            distance = self.levenshtein_distance(country_lower, valid_country.lower())

            if distance <= max_distance and distance < best_distance:
                best_distance = distance
                best_match = valid_country

        return best_match

    def correct_country(self, country: str) -> Tuple[str, bool]:
        """
        Corrige et normalise automatiquement un nom de pays

        Args:
            country: Le nom ou code du pays à corriger

        Returns:
            Tuple (pays_corrigé, a_été_corrigé)
            - pays_corrigé: Le nom du pays normalisé en français
            - a_été_corrigé: True si une correction a été appliquée

        Exemples:
            >>> correct_country("FR")
            ("France", True)

            >>> correct_country("Frence")
            ("France", True)

            >>> correct_country("United States")
            ("États-Unis", True)

            >>> correct_country("France")
            ("France", False)
        """
        if not country:
            return country, False

        original_country = country
        country_stripped = country.strip()

        # Étape 1 : Vérifier si c'est déjà un nom de pays valide
        if country_stripped in self.VALID_COUNTRIES:
            return country_stripped, False

        # Étape 2 : Vérifier si c'est un code pays (2-3 lettres)
        if len(country_stripped) <= 3 and country_stripped.isalpha():
            normalized = self.normalize_country_code(country_stripped)
            if normalized:
                print(f"🌍 Code pays normalisé : {original_country} → {normalized}")
                return normalized, True

        # Étape 3 : Vérifier si c'est une variante connue (anglais, etc.)
        variant = self.normalize_country_variant(country_stripped)
        if variant:
            print(f"🌍 Variante normalisée : {original_country} → {variant}")
            return variant, True

        # Étape 4 : Corriger les fautes de frappe
        suggested = self.suggest_country(country_stripped)
        if suggested:
            print(f"🌍 Pays corrigé : {original_country} → {suggested}")
            return suggested, True

        # Aucune correction trouvée
        return country_stripped, False


# Instance globale
country_corrector = CountryCorrector()
