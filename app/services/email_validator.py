import httpx
import asyncio
from typing import Optional, Dict, Any

class EmailValidatorService:
    """Service pour valider les emails avec Abstract API"""

    def __init__(self):
        self.api_key = "15dd76ad502a443dbb799de9d1eca131"
        self.base_url = "https://emailreputation.abstractapi.com/v1"

    async def validate_email(self, email: str) -> bool:
        """
        Valide un email avec Abstract API

        Args:
            email: L'adresse email à valider

        Returns:
            True si l'email est valide et délivrable, False sinon
        """
        if not email or "@" not in email:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": self.api_key,
                    "email": email
                }

                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                # Vérifier si l'email est délivrable selon la réponse Abstract API
                deliverability = data.get("email_deliverability", {})
                status = deliverability.get("status", "").lower()

                # L'email est considéré comme valide si le statut est "deliverable"
                return status == "deliverable"

        except Exception as e:
            print(f"Erreur validation email {email}: {e}")
            # En cas d'erreur API, on considère l'email comme non validé
            return False

    def validate_email_sync(self, email: str) -> bool:
        """
        Version synchrone de la validation d'email

        Args:
            email: L'adresse email à valider

        Returns:
            True si l'email est valide et délivrable, False sinon
        """
        if not email or "@" not in email:
            return False

        try:
            import requests

            params = {
                "api_key": self.api_key,
                "email": email
            }

            response = requests.get(self.base_url, params=params, timeout=10)

            # Gérer les différents codes d'erreur
            if response.status_code == 401:
                print(f"Erreur API: Clé API invalide ou non autorisée")
                return False
            elif response.status_code == 429:
                print(f"Erreur API: Limite de requêtes atteinte")
                return False
            elif response.status_code != 200:
                print(f"Erreur API: Code {response.status_code}")
                return False

            data = response.json()
            print(f"Réponse API pour {email}: {data}")

            # Vérifier si l'email est délivrable selon la réponse Abstract API
            deliverability = data.get("email_deliverability", {})
            status = deliverability.get("status", "").lower()

            # L'email est considéré comme valide si le statut est "deliverable"
            return status == "deliverable"

        except Exception as e:
            print(f"Erreur validation email {email}: {e}")
            # En cas d'erreur API, on considère l'email comme non validé
            return False

# Instance globale du service
email_validator = EmailValidatorService()