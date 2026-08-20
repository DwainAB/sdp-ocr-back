import re
from typing import List, Dict, Any, Optional
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

        # Nom du parfum (en haut de page, à côté du numéro de création)
        # Selon le modèle de fiche : FR "Nom du parfum"/"Nom parfum", EN "Perfume name"
        data.nom_parfum = self._extract_field_value(
            text, ["nom du parfum", "nom parfum", "perfume name"]
        )

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
        data.groupe = self._extract_field_value(text, ["groupe", "group"])

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
    # CORRECTION POST-EXTRACTION DE LA RÉFÉRENCE (avant insertion BDD)
    # =====================================================================

    # Lettres fréquemment confondues avec des chiffres par l'OCR
    # (confirmé terrain : S→5, B→3, A→4 ; complété par les substitutions visuelles classiques)
    _OCR_LETTER_TO_DIGIT = {
        "S": "5", "s": "5",
        "B": "3",
        "A": "4",
        "O": "0", "o": "0",
        "I": "1", "l": "1",
        "Z": "2",
        "G": "6",
        "T": "7",
    }

    def fix_reference_ocr_digits(self, reference: str) -> str:
        """
        Corrige une référence de formule déjà extraite en remplaçant les lettres
        que l'OCR confond avec des chiffres (une référence est toujours numérique).
        À appliquer une fois la référence récupérée, juste avant l'ajout en BDD —
        ne modifie pas la logique d'extraction elle-même.
        """
        if not reference:
            return reference
        return "".join(self._OCR_LETTER_TO_DIGIT.get(ch, ch) for ch in reference)

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
                pattern = rf'{re.escape(field)}\s*:\s*([^:]+?)(?:\s+(?:Tel|Email|Pays|Ville|City|Country|Phone|Nom|Prénom|Date|Profession|First name|Last name|Groupe|Group):|$)'
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

    # =====================================================================
    # EXTRACTION DES NOTES DE PARFUM DEPUIS TABLEAUX MARKDOWN
    # =====================================================================

    def extract_perfume_notes_from_markdown(self, markdown_text: str) -> Dict[str, Any]:
        """
        Extrait les notes de parfum (tête, cœur, fond) depuis le texte markdown
        en parsant les tableaux.
        
        Retourne un dict avec:
        - notes_de_tete: List[Dict[str, Any]] avec {"essence": str, "quantite_ml": str}
          (quantite_ml est toujours une string, ex: "1", "2", "2 + 1", "1 + 1", etc.)
        - notes_de_coeur: List[Dict[str, Any]] avec {"essence": str, "quantite_ml": str}
        - notes_de_fond: List[Dict[str, Any]] avec {"essence": str, "quantite_ml": str}
        """
        result = {
            "notes_de_tete": [],
            "notes_de_coeur": [],
            "notes_de_fond": []
        }

        if not markdown_text:
            return result

        # Chercher les sections et leurs tableaux
        result["notes_de_tete"] = self._parse_perfume_table(markdown_text, "tête")
        result["notes_de_coeur"] = self._parse_perfume_table(markdown_text, "cœur")
        result["notes_de_fond"] = self._parse_perfume_table(markdown_text, "fond")

        return result

    def _parse_perfume_table(self, markdown_text: str, note_type: str) -> List[Dict[str, Any]]:
        """
        Parse un tableau markdown pour un type de note donné.
        
        Structure attendue du tableau:
        | Code ess. | Notes de tête | Qté en ml | Qté utile |   |
        | --- | --- | --- | --- | --- |
        |   | Essence 1 | 1 |  |  |
        |   | Essence 2 | 2 |  |  |
        
        L'essence est dans la 2ème colonne, la quantité dans la 3ème colonne.
        
        Args:
            markdown_text: Texte markdown complet
            note_type: "tête", "cœur" ou "fond"
        
        Returns:
            Liste de dicts avec {"essence": str, "quantite_ml": float}
        """
        notes = []
        
        # Patterns pour trouver la section (insensible à la casse, avec variantes)
        patterns = {
            "tête": [r"notes?\s+de\s+tête", r"note\s+de\s+tete", r"header\s+note"],
            "cœur": [r"notes?\s+de\s+cœur", r"notes?\s+de\s+coeur", r"heart\s+note"],
            "fond": [r"notes?\s+de\s+fond", r"base\s+note"]
        }
        
        if note_type not in patterns:
            return notes
        
        # Trouver la ligne d'en-tête de la section (ex: "| Code ess. | Notes de tête | Qté en ml |")
        section_header_pattern = None
        for pattern in patterns[note_type]:
            # Chercher le pattern dans une ligne de tableau
            section_header_pattern = rf'\|[^|]*\|\s*{pattern}[^|]*\|'
            match = re.search(section_header_pattern, markdown_text, re.IGNORECASE)
            if match:
                section_start = match.start()
                break
        else:
            return notes
        
        # Extraire toutes les lignes du tableau markdown
        lines = markdown_text.split('\n')
        section_lines = []
        in_section = False
        found_header = False
        
        # Trouver où commence notre section et où elle se termine
        for i, line in enumerate(lines):
            # Vérifier si c'est notre ligne d'en-tête de section
            for pattern in patterns[note_type]:
                if re.search(rf'\|[^|]*\|\s*{pattern}[^|]*\|', line, re.IGNORECASE):
                    in_section = True
                    found_header = True
                    # Skip la ligne d'en-tête et le séparateur suivant
                    continue
            
            if in_section:
                # Si on trouve une nouvelle section (autre que la nôtre), on s'arrête
                is_other_section = False
                for other_type, other_patterns in patterns.items():
                    if other_type != note_type:
                        for other_pattern in other_patterns:
                            if re.search(rf'\|[^|]*\|\s*{other_pattern}[^|]*\|', line, re.IGNORECASE):
                                in_section = False
                                is_other_section = True
                                break
                        if is_other_section:
                            break
                if is_other_section:
                    break
                
                # Si c'est une ligne de tableau, l'ajouter
                if '|' in line and found_header:
                    section_lines.append(line)
        
        # Parser les lignes de la section
        for line in section_lines:
            # Split par | en gardant les cellules vides pour préserver l'index
            cells = [cell.strip() for cell in line.split('|')]
            # Enlever la première et dernière cellule vides (début et fin de ligne markdown)
            if cells and not cells[0]:
                cells = cells[1:]
            if cells and not cells[-1]:
                cells = cells[:-1]
            
            # Structure: [Code ess., Notes de tête/cœur/fond, Qté en ml, Qté utile, ...]
            # L'essence est dans la 2ème colonne (index 1), la quantité dans la 3ème (index 2)
            if len(cells) >= 3:
                essence = cells[1].strip()  # 2ème colonne
                quantite_str = cells[2].strip()  # 3ème colonne
                
                # Ignorer les lignes vides ou les en-têtes
                if not essence or essence.lower() in ["notes de tête", "notes de coeur", "notes de cœur", "notes de fond", 
                                                       "note de tête", "note de coeur", "note de cœur", "note de fond",
                                                       "code ess.", "code ess", "qté en ml", "quantité", "quantite"]:
                    continue
                
                # Extraire la quantité (peut contenir des choses comme "1", "1 + 2", "5 + 2", etc.)
                # On garde toujours comme string, même pour les nombres simples
                if quantite_str:
                    # Nettoyer l'expression mais garder tout comme string
                    quantite_ml = quantite_str.strip()
                else:
                    quantite_ml = None
                
                # Ajouter la note
                notes.append({
                    "essence": essence,
                    "quantite_ml": quantite_ml
                })
        
        return notes


data_extractor = DataExtractor()
