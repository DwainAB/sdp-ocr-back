import csv
import io
import re
from typing import List, Dict, Any, Optional
from app.schemas.ocr_schemas import DocumentType


class CSVGenerator:
    """
    Génère un CSV propre à partir des données extraites.
    Nettoie les erreurs OCR (email, tel, pays/ville collés, etc.)
    """

    HEADERS = [
        "identifiant",
        "genre",
        "nom",
        "prenom",
        "date",
        "ville",
        "pays",
        "tel",
        "email",
        "profession",
        "date_naissance",
    ]

    def generate_studio_parfums_csv(self, processed_pages: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.HEADERS,
            delimiter=";",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writeheader()

        # Filtrer les pages Studio des Parfums
        studio_pages = [
            page for page in processed_pages
            if page.get("document_type") == DocumentType.STUDIO_PARFUMS.value
        ]

        # Détecter le préfixe commun des identifiants existants
        prefix = self._detect_identifiant_prefix(studio_pages)

        for i, page in enumerate(studio_pages, 1):
            data = page.get("extracted_data") or {}

            # Générer l'identifiant s'il manque
            identifiant = self._clean_identifiant(data.get("identifiant"))
            if not identifiant and prefix:
                identifiant = f"{prefix}{i:03d}"  # Ex: 202201001, 202201002, etc.

            row = {
                "identifiant": identifiant,
                "genre": self._clean_simple(data.get("genre")),
                "nom": self._clean_simple(data.get("nom")),
                "prenom": self._clean_simple(data.get("prenom")),
                "date": self._clean_date(data.get("date")),
                "ville": self._clean_city(data.get("ville")),
                "pays": self._clean_country(data.get("pays")),
                "tel": self._clean_phone(data.get("tel")),
                "email": self._clean_email(data.get("email")),
                "profession": self._clean_simple(data.get("profession")),
                "date_naissance": self._clean_date(data.get("date_naissance")),
            }

            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()
        return csv_content

    # ------------------------------------------------------------------
    # NETTOYAGE DES CHAMPS
    # ------------------------------------------------------------------

    def _clean_simple(self, value: Optional[str]) -> str:
        if not value:
            return ""
        v = str(value).strip()
        v = re.sub(r"\s+", " ", v)
        return self._cut_on_labels(v)

    def _cut_on_labels(self, v: str) -> str:
        labels = [
            "Pays:", "Ville:", "Tel:", "Email:", "Profession:",
            "Date:", "Nom:", "Prénom:", "Date de naissance:"
        ]
        for label in labels:
            if label.lower() in v.lower():
                idx = v.lower().find(label.lower())
                return v[:idx].strip()
        return v.strip()

    def _clean_email(self, value: Optional[str]) -> str:
        if not value:
            return ""

        text = str(value).strip()

        # D'abord essayer le pattern standard
        match = re.search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(0)

        # Si échec, essayer de nettoyer les espaces OCR dans la partie locale
        # Pattern: mot(s) + espace(s) + @ + domaine
        ocr_match = re.search(
            r"([A-Z0-9._%-]+(?:\s+[A-Z0-9._%-]+)*)\s*@\s*([A-Z0-9.-]+\.[A-Z]{2,})",
            text,
            re.IGNORECASE
        )
        if ocr_match:
            local_part = re.sub(r'\s+', '', ocr_match.group(1))  # enlever espaces
            domain_part = re.sub(r'\s+', '', ocr_match.group(2))  # enlever espaces
            return f"{local_part}@{domain_part}"

        return ""

    def _clean_phone(self, value: Optional[str]) -> str:
        if not value:
            return ""

        digits = re.sub(r"[^\d]", "", value)

        if len(digits) == 10 and digits.startswith("0"):
            return " ".join(digits[i:i+2] for i in range(0, 10, 2))

        if digits.startswith("33") and len(digits) == 11:
            digits = digits[2:]
            return "+33 " + " ".join(digits[i:i+2] for i in range(0, 10, 2))

        return value.strip()

    def _clean_date(self, value: Optional[str]) -> str:
        if not value:
            return ""

        # Chercher pattern date (jour/mois/année ou mois/jour/année)
        match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
        if not match:
            return value.strip()

        part1, part2, year = match.groups()

        # Normaliser l'année (2 chiffres → 4 chiffres)
        if len(year) == 2:
            year_int = int(year)
            # Si année < 30, c'est probablement 20xx, sinon 19xx
            if year_int <= 30:
                year = "20" + year
            else:
                year = "19" + year

        # Convertir en entiers pour comparaison
        p1, p2 = int(part1), int(part2)

        # Déterminer si c'est DD/MM ou MM/DD
        # Si part1 > 12, c'est forcément DD/MM
        # Si part2 > 12, c'est forcément MM/DD
        # Sinon, on assume DD/MM (format européen par défaut)
        if p1 > 12:
            # part1 = jour, part2 = mois
            day, month = p1, p2
        elif p2 > 12:
            # part1 = mois, part2 = jour
            day, month = p2, p1
        else:
            # Ambiguë - on assume format DD/MM (européen)
            day, month = p1, p2

        return f"{day:02d}/{month:02d}/{year}"

    def _clean_city(self, value: Optional[str]) -> str:
        if not value:
            return ""
        v = str(value)
        v = re.sub(r"(?i)ville\s*:\s*", "", v)
        v = re.split(r"(?i)pays\s*:", v)[0]
        return v.strip()

    def _clean_country(self, value: Optional[str]) -> str:
        if not value:
            return ""
        v = str(value)
        v = re.sub(r"(?i)pays\s*:\s*", "", v)
        v = re.split(r"(?i)ville\s*:", v)[0]
        return v.strip()

    def _clean_identifiant(self, value: Optional[str]) -> str:
        if not value:
            return ""

        digits = re.sub(r"\D", "", str(value))

        if len(digits) >= 9:
            digits = digits[:9]

        if not digits.startswith("20"):
            digits = "20" + digits[2:]

        return digits

    def _detect_identifiant_prefix(self, studio_pages: List[Dict[str, Any]]) -> str:
        """
        Détecte le préfixe commun des identifiants existants.
        Ex: ["202201001", "202201005"] → "202201"
        """
        identifiants = []

        for page in studio_pages:
            data = page.get("extracted_data") or {}
            identifiant = self._clean_identifiant(data.get("identifiant"))
            if identifiant and len(identifiant) >= 6:  # Au moins 6 chiffres
                identifiants.append(identifiant)

        if not identifiants:
            return ""

        # Si un seul identifiant, prendre les 6 premiers chiffres
        if len(identifiants) == 1:
            return identifiants[0][:6]

        # Trouver le préfixe commun le plus long
        prefix = identifiants[0]
        for ident in identifiants[1:]:
            # Comparer caractère par caractère
            i = 0
            while i < min(len(prefix), len(ident)) and prefix[i] == ident[i]:
                i += 1
            prefix = prefix[:i]

        # S'assurer que le préfixe fait au moins 6 caractères
        if len(prefix) >= 6:
            return prefix[:6]  # Prendre exactement 6 chiffres

        return ""


csv_generator = CSVGenerator()
