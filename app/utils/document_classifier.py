import re
from typing import Tuple
from app.schemas.ocr_schemas import DocumentType

class DocumentClassifier:
    def __init__(self):
        self.studio_parfums_keywords = [
            "LE STUDIO DES PARFUMS",
            "STUDIO DES PARFUMS",
            "STUDIO PARFUMS"
        ]

        self.blank_sheet_keywords = [
            "fiches manquantes",
            "doublons",
            "tel",
            "mail"
        ]

    def classify_document(self, text: str) -> Tuple[DocumentType, float]:
        """
        Classify document based on extracted text
        Returns: (DocumentType, confidence_score)
        """
        text_lower = text.lower()

        # Check for Studio des Parfums
        studio_score = self._calculate_studio_score(text_lower)

        # Check for blank sheet indicators
        blank_score = self._calculate_blank_sheet_score(text_lower)

        # Determine document type based on scores
        if studio_score > blank_score and studio_score > 0.3:
            return DocumentType.STUDIO_PARFUMS, studio_score
        elif blank_score > studio_score and blank_score > 0.3:
            return DocumentType.BLANK_SHEET, blank_score
        else:
            return DocumentType.UNKNOWN, max(studio_score, blank_score)

    def _calculate_studio_score(self, text: str) -> float:
        """Calculate confidence score for Studio des Parfums document"""
        score = 0.0

        for keyword in self.studio_parfums_keywords:
            if keyword.lower() in text:
                score += 0.8
                break

        # Additional indicators
        if "parfum" in text:
            score += 0.2
        if "studio" in text:
            score += 0.2

        return min(score, 1.0)

    def _calculate_blank_sheet_score(self, text: str) -> float:
        """Calculate confidence score for blank sheet document"""
        score = 0.0
        found_keywords = 0

        for keyword in self.blank_sheet_keywords:
            if keyword in text:
                found_keywords += 1
                score += 0.25

        # Check for month/year pattern at the top
        month_year_patterns = [
            r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b',
            r'\b\d{1,2}/\d{4}\b',
            r'\b\d{1,2}-\d{4}\b'
        ]

        for pattern in month_year_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.3
                break

        # Bonus if multiple fields detected
        if found_keywords >= 3:
            score += 0.2

        return min(score, 1.0)

document_classifier = DocumentClassifier()