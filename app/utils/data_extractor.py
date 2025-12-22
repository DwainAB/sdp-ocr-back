import re
from typing import List, Dict, Any
from app.schemas.ocr_schemas import DocumentType, BlankSheetData, StudioParfumsData


class DataExtractor:
    def __init__(self):
        pass

    # =====================================================================
    # ENTRY POINT
    # =====================================================================

    def extract_data(self, text: str, document_type: DocumentType) -> Dict[str, Any]:
        """
        Extract structured data based on document type
        """
        if document_type == DocumentType.BLANK_SHEET:
            return self._extract_blank_sheet_data(text)
        elif document_type == DocumentType.STUDIO_PARFUMS:
            return self._extract_studio_parfums_data(text)
        else:
            return {"raw_text": text}

    # =====================================================================
    # BLANK SHEET
    # =====================================================================

    def _extract_blank_sheet_data(self, text: str) -> Dict[str, Any]:
        data = BlankSheetData()

        data.month_year = self._extract_month_year(text)
        data.fiches_manquantes = self._extract_numbers_after_keyword(text, "fiches manquantes")
        data.doublons = self._extract_numbers_after_keyword(text, "doublons")
        data.tel = self._extract_numbers_after_keyword(text, "tel")
        data.mail = self._extract_numbers_after_keyword(text, "mail")

        return data.dict()

    # =====================================================================
    # STUDIO DES PARFUMS
    # =====================================================================

    def _extract_studio_parfums_data(self, text: str) -> Dict[str, Any]:
        data = StudioParfumsData()

        # Détection du titre
        data.title_detected = any(keyword in text.lower() for keyword in [
            "le studio des parfums",
            "studio des parfums",
            "studio parfums"
        ])

        # Identifiant (en haut de page, correction OCR)
        data.identifiant = self._extract_identifiant(text)

        # Genre (cases cochées)
        data.genre = self._extract_genre(text)

        # Champs personnels (français/anglais) - ordre important pour éviter conflits
        data.prenom = self._extract_field_value(text, ["prenom", "prénom", "first name"])
        data.nom = self._extract_field_value(text, ["nom", "last name", "name"])
        data.date = self._extract_field_value(text, "date")
        data.ville = self._extract_field_value(text, ["ville", "city"])
        data.pays = self._extract_field_value(text, ["pays", "country"])

        tel_raw = self._extract_field_value(text, ["tel", "phone", "phone nb"])
        data.tel = self._format_phone_number(tel_raw) if tel_raw else None

        data.email = self._extract_field_value(text, "email")
        data.profession = self._extract_field_value(text, "profession")
        data.date_naissance = self._extract_field_value(
            text, ["date de naissance", "date naissance", "birthday"]
        )

        return data.dict()

    # =====================================================================
    # IDENTIFIANT STUDIO DES PARFUMS (ROBUSTE OCR)
    # =====================================================================

    def _extract_identifiant(self, text: str) -> str:
        """
        Extract Studio des Parfums identifiant from top of page.

        Business rules (terrain-validées):
        - Identifiant = suite de chiffres (8 à 10)
        - Toujours commence par '20'
        - OCR peut lire :
            '20' → '6'
            '20' → '06'
            '20' → '020'
            '2022 01008' → espaces dans l'OCR
        """

        # On ne regarde QUE le haut de la page
        lines = text.split('\n')[:5]

        for line in lines:
            # Chercher d'abord les identifiants sans espaces
            matches = re.findall(r'\b\d{8,10}\b', line)

            for raw_ident in matches:
                ident = raw_ident.lstrip("0")  # enlever zéros en tête

                # Cas nominal
                if ident.startswith("20"):
                    return ident

                # OCR : 6xxxxxxx → 20xxxxxxx
                if ident.startswith("6"):
                    return "20" + ident[1:]

                # OCR : 62xxxxxx → 202xxxxx
                if ident.startswith("62"):
                    return "202" + ident[2:]

            # Si pas trouvé, chercher des identifiants avec espaces (ex: "2022 01008")
            spaced_matches = re.findall(r'\b(\d{4})\s+(\d{5})\b', line)
            for part1, part2 in spaced_matches:
                combined = part1 + part2
                if combined.startswith("20"):
                    return combined

            # Autres patterns avec espaces possibles
            other_spaced = re.findall(r'\b(20\d{2})\s+(\d{5})\b', line)
            for part1, part2 in other_spaced:
                return part1 + part2

        return None

    # =====================================================================
    # UTILITAIRES
    # =====================================================================

    def _extract_month_year(self, text: str) -> str:
        lines = text.split('\n')[:5]

        for line in lines:
            match = re.search(
                r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b',
                line,
                re.IGNORECASE
            )
            if match:
                return match.group(0)

            match = re.search(r'\b\d{1,2}[/-]\d{4}\b', line)
            if match:
                return match.group(0)

        return None

    def _extract_numbers_after_keyword(self, text: str, keyword: str) -> List[str]:
        text_lower = text.lower()
        keyword_pos = text_lower.find(keyword.lower())

        if keyword_pos == -1:
            return []

        text_after = text[keyword_pos + len(keyword):keyword_pos + len(keyword) + 200]
        numbers = re.findall(r'\b\d+\b', text_after)

        seen = set()
        return [n for n in numbers if not (n in seen or seen.add(n))]

    def _extract_genre(self, text: str) -> str:
        for line in text.split('\n'):
            lower = line.lower()
            # Français : Mr/Mme/Mlle OU Anglais : Mr./Ms.
            if any(g in lower for g in ['mr ', 'mr.', 'mme ', 'mlle ', 'ms.', 'ms ']):
                if any(mark in line for mark in ['☑', '✓', '✅', '[x]', ' x ']):
                    if any(m in lower for m in ['mr ', 'mr.']):
                        return "Mr"
                    if 'mme ' in lower:
                        return "Mme"
                    if 'mlle ' in lower:
                        return "Mlle"
                    if any(ms in lower for ms in ['ms.', 'ms ']):
                        return "Ms"
        return None

    def _extract_field_value(self, text: str, field_names) -> str:
        if isinstance(field_names, str):
            field_names = [field_names]

        # Sort fields by length (longest first) to match most specific patterns first
        field_names = sorted(field_names, key=len, reverse=True)

        for line in text.split('\n'):
            for field in field_names:
                # Match field name followed by colon, capture until next field or end
                pattern = rf'{re.escape(field)}\s*:\s*([^:]+?)(?:\s+(?:Tel|Email|Pays|Ville|City|Country|Phone|Nom|Prénom|Date|Profession|First name|Last name):|$)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Remove trailing punctuation (dots, commas, etc.)
                    value = re.sub(r'[^\w\s@./+-]+$', '', value)
                    value = re.sub(r'\.$', '', value)  # Remove trailing dot specifically
                    return value.strip()
        return None

    def _format_phone_number(self, phone: str) -> str:
        clean = re.sub(r'[^\d+]', '', phone)

        if clean.startswith('+33'):
            prefix, digits = '+33 ', clean[3:]
        elif clean.startswith('0033'):
            prefix, digits = '0033 ', clean[4:]
        else:
            prefix, digits = '', clean

        return prefix + ' '.join(digits[i:i+2] for i in range(0, len(digits), 2))


data_extractor = DataExtractor()
