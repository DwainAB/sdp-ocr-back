"""
Script de test pour vérifier la validation de domaines email via MX DNS
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.email_domain_validator import email_domain_validator


def test_email_domains():
    """
    Test des emails fournis par l'utilisateur
    """
    test_emails = [
        "dwain@yumco.fr",
        "dwain@yumko.fr",
    ]

    print("=" * 80)
    print("TEST DE VALIDATION DE DOMAINES EMAIL (MX DNS)")
    print("=" * 80)
    print()

    for email in test_emails:
        is_valid, details = email_domain_validator.verify_email_domain(email)

        status = "✅ VALIDE" if is_valid else "❌ INVALIDE"
        domain = email.split('@')[1] if '@' in email else 'N/A'

        print(f"Email: {email}")
        print(f"Domaine: {domain}")
        print(f"Statut: {status}")
        print(f"Détails: {details}")
        print("-" * 80)
        print()


if __name__ == "__main__":
    test_email_domains()
