import requests
from typing import Optional


class PhoneIntelligenceValidator:
    """
    Service pour vérifier la validité d'un numéro de téléphone via AbstractAPI Phone Intelligence
    """

    def __init__(self, api_key: str = "882b1904d8434d64b13b3488c99c04c7"):
        self.api_key = api_key
        self.api_url = "https://phoneintelligence.abstractapi.com/v1/"

    def verify_phone_number(self, phone: str) -> Optional[bool]:
        """
        Vérifie la validité d'un numéro de téléphone via AbstractAPI

        Args:
            phone: Numéro de téléphone à vérifier (avec ou sans formatage)

        Returns:
            True si le numéro est valide
            False si le numéro est invalide
            None si erreur API ou pas de numéro

        Exemple de réponse API:
        {
            "phone": "14152007986",
            "valid": true,
            "format": {
                "international": "+14152007986",
                "local": "(415) 200-7986"
            },
            "country": {
                "code": "US",
                "name": "United States",
                "prefix": "+1"
            },
            "location": "California",
            "type": "mobile",
            "carrier": "T-Mobile USA, Inc."
        }
        """
        if not phone:
            return None

        # Nettoyer le numéro (enlever espaces, tirets, etc.)
        cleaned_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

        if not cleaned_phone:
            return None

        try:
            # Appel API
            response = requests.get(
                self.api_url,
                params={
                    "api_key": self.api_key,
                    "phone": cleaned_phone
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("valid", False)

                # Logs pour debug
                if is_valid:
                    country = data.get("country", {}).get("name", "Unknown")
                    phone_type = data.get("type", "Unknown")
                    print(f"✅ Numéro vérifié via AbstractAPI: {phone} → Valide ({country}, {phone_type})")
                else:
                    print(f"❌ Numéro vérifié via AbstractAPI: {phone} → Invalide")

                return is_valid

            elif response.status_code == 429:
                # Rate limit dépassé - on retourne None pour ne pas bloquer le traitement
                print(f"⚠️ Rate limit AbstractAPI dépassé pour {phone} - Validation ignorée")
                return None

            else:
                print(f"⚠️ Erreur API AbstractAPI Phone Intelligence (status {response.status_code}): {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout lors de la vérification du numéro: {phone}")
            return None
        except Exception as e:
            print(f"❌ Erreur lors de la vérification du numéro {phone}: {e}")
            return None


# Instance globale
phone_intelligence_validator = PhoneIntelligenceValidator()
