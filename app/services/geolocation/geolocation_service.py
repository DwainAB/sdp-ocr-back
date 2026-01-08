import requests
from typing import Dict, Optional
import ipaddress

class GeolocationService:
    """
    Service pour géolocaliser les adresses IP
    Utilise l'API gratuite ip-api.com
    """

    def __init__(self):
        self.api_url = "http://ip-api.com/json"

    def _is_private_ip(self, ip: str) -> bool:
        """
        Vérifie si l'IP est privée (locale)
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False

    def get_location_by_ip(self, ip_address: str) -> Dict[str, str]:
        """
        Récupère la géolocalisation d'une IP
        Retourne un dictionnaire avec city et country
        """
        # Valeurs par défaut
        default_location = {
            "city": "Unknown",
            "country": "Unknown"
        }

        # Si IP privée/locale, retourner valeurs par défaut
        if self._is_private_ip(ip_address) or ip_address in ["127.0.0.1", "localhost", "::1"]:
            return {
                "city": "Local",
                "country": "Local"
            }

        try:
            # Faire l'appel API
            response = requests.get(
                f"{self.api_url}/{ip_address}",
                timeout=5,
                params={"fields": "status,city,country"}
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == "success":
                    return {
                        "city": data.get("city", "Unknown"),
                        "country": data.get("country", "Unknown")
                    }
                else:
                    print(f"Erreur API géolocalisation : {data}")
                    return default_location
            else:
                print(f"Erreur HTTP géolocalisation : {response.status_code}")
                return default_location

        except requests.exceptions.RequestException as e:
            print(f"Erreur réseau géolocalisation : {e}")
            return default_location
        except Exception as e:
            print(f"Erreur générale géolocalisation : {e}")
            return default_location

geolocation_service = GeolocationService()