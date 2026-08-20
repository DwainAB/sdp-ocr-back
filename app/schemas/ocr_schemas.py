from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class DocumentType(str, Enum):
    BLANK_SHEET = "blank_sheet"
    STUDIO_PARFUMS = "studio_parfums"
    UNKNOWN = "unknown"

class MistralDocumentAnnotation(BaseModel):
    """
    Schéma utilisé par Mistral Document AI (Annotations) pour renvoyer un JSON structuré.
    On garde un schéma "large" (champs optionnels) pour couvrir les 2 types de documents.
    
    Les descriptions Field() servent d'instructions à Mistral pour mieux identifier les champs.
    """
    document_type: Optional[DocumentType] = Field(
        None,
        description="Type de document détecté: 'studio_parfums' (formulaire Studio des Parfums), 'blank_sheet' (feuille blanche avec statistiques), ou 'unknown'"
    )

    # Studio des Parfums
    identifiant: Optional[str] = Field(
        None,
        description="Identifiant unique en haut de page (8 à 10 chiffres, commence toujours par '20'). Exemple: '202201008' ou '20201008'. Peut être écrit avec des espaces dans l'OCR comme '2022 01008'."
    )
    nom_parfum: Optional[str] = Field(
        None,
        description="Nom donné au parfum créé, écrit à la main par le client après un label du type 'Nom du parfum', 'Nom parfum' (français) ou 'Perfume name' (anglais), généralement en haut de la fiche à côté du numéro de création. Selon le modèle de fiche, ce label peut être absent. C'est un champ souvent laissé vide : ne jamais renvoyer 'LE STUDIO DES PARFUMS', 'Studio des Parfums' ou 'The Studio des Parfums' (c'est le titre imprimé de l'en-tête, pas une réponse du client). Si rien n'est écrit après le label, ou si le label est absent, renvoyer null."
    )
    genre: Optional[str] = Field(
        None,
        description="Genre de la personne: 'Mr', 'Mme', 'Mlle' ou 'Ms'. Chercher les cases cochées (☑, ✓, [x]) à côté de ces mentions."
    )
    nom: Optional[str] = Field(
        None,
        description="Nom de famille de la personne. Chercher après 'Nom:', 'Last name:' ou 'Name:'"
    )
    prenom: Optional[str] = Field(
        None,
        description="Prénom de la personne. Chercher après 'Prénom:' ou 'First name:'"
    )
    date: Optional[str] = Field(
        None,
        description="Date (généralement la date de remplissage du formulaire). Chercher après 'Date:'"
    )
    ville: Optional[str] = Field(
        None,
        description="Ville de résidence. Chercher après 'Ville:' ou 'City:'"
    )
    pays: Optional[str] = Field(
        None,
        description="Pays de résidence. Chercher après 'Pays:' ou 'Country:'"
    )
    tel: Optional[str] = Field(
        None,
        description="Numéro de téléphone. Chercher après 'Tel:', 'Phone:' ou 'Tel:'"
    )
    email: Optional[str] = Field(
        None,
        description="Adresse email. Chercher après 'Email:'"
    )
    profession: Optional[str] = Field(
        None,
        description="Profession de la personne. Chercher après 'Profession:'"
    )
    date_naissance: Optional[str] = Field(
        None,
        description="Date de naissance. Chercher après 'Date de naissance:', 'Date naissance:' ou 'Birthday:'"
    )
    groupe: Optional[str] = Field(
        None,
        description="Nom du groupe de la personne. Chercher après 'Groupe:' ou 'Group:'"
    )

    # Blank sheet
    month_year: Optional[str] = Field(
        None,
        description="Mois et année de la feuille blanche (ex: 'janvier 2024' ou '01/2024'). Généralement en haut de la page."
    )
    fiches_manquantes: Optional[List[str]] = Field(
        None,
        description="Liste des numéros de fiches manquantes. Chercher après 'fiches manquantes:' ou 'fiches manquantes' et extraire tous les numéros qui suivent."
    )
    doublons: Optional[List[str]] = Field(
        None,
        description="Liste des numéros de doublons détectés. Chercher après 'doublons:' ou 'doublons' et extraire tous les numéros qui suivent."
    )
    tel_list: Optional[List[str]] = Field(
        None,
        description="Liste des numéros de téléphone avec problèmes. Chercher après 'tel:' et extraire tous les numéros qui suivent."
    )
    mail_list: Optional[List[str]] = Field(
        None,
        description="Liste des emails avec problèmes. Chercher après 'mail:' et extraire tous les emails/numéros qui suivent."
    )

class BlankSheetData(BaseModel):
    month_year: Optional[str] = None
    fiches_manquantes: List[str] = []
    doublons: List[str] = []
    tel: List[str] = []
    mail: List[str] = []

class StudioParfumsData(BaseModel):
    title_detected: bool = False
    identifiant: Optional[str] = None
    nom_parfum: Optional[str] = None
    genre: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None
    profession: Optional[str] = None
    date_naissance: Optional[str] = None
    groupe: Optional[str] = None

class ProcessedPage(BaseModel):
    page_number: int
    document_type: DocumentType
    confidence: float
    raw_text: str
    extracted_data: Dict[str, Any]

class OCRResponse(BaseModel):
    success: bool
    filename: str
    total_pages: int
    processed_pages: List[ProcessedPage]
    summary: Dict[str, Any]