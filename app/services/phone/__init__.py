"""
Services de validation et normalisation des numéros de téléphone
"""

from app.services.phone.phone_validator import phone_validator
from app.services.phone.phone_intelligence_validator import phone_intelligence_validator

__all__ = [
    'phone_validator',
    'phone_intelligence_validator',
]
