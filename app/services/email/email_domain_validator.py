import dns.resolver
from typing import Tuple


class EmailDomainValidator:
    """
    Service pour vérifier si un domaine email peut recevoir des emails (via MX records)
    """

    def check_domain_has_mx(self, domain: str) -> Tuple[bool, str]:
        """
        Vérifie si un domaine possède des enregistrements MX (serveurs mail)

        Args:
            domain: Le domaine à vérifier (ex: "gmail.com", "sdp-paris.com")

        Returns:
            Tuple (has_mx, details)
            - has_mx: True si le domaine a des MX, False sinon
            - details: Message détaillé pour debug

        Exemples:
            >>> check_domain_has_mx("gmail.com")
            (True, "MX records found: gmail-smtp-in.l.google.com")

            >>> check_domain_has_mx("domaine-inexistant-xyz.com")
            (False, "Domain does not exist (NXDOMAIN)")
        """
        try:
            # Interroger les serveurs DNS pour les enregistrements MX
            mx_records = dns.resolver.resolve(domain, 'MX')

            # Extraire la liste des serveurs mail
            mx_hosts = [str(mx.exchange) for mx in mx_records]

            if mx_hosts:
                return True, f"MX records found: {', '.join(mx_hosts[:3])}"
            else:
                return False, "No MX records found"

        except dns.resolver.NXDOMAIN:
            # Le domaine n'existe pas
            return False, "Domain does not exist (NXDOMAIN)"

        except dns.resolver.NoAnswer:
            # Le domaine existe mais n'a pas d'enregistrement MX
            return False, "Domain exists but has no MX records"

        except dns.resolver.Timeout:
            # Timeout DNS (problème réseau)
            return False, "DNS query timeout"

        except Exception as e:
            # Autre erreur
            return False, f"Error: {str(e)}"

    def verify_email_domain(self, email: str) -> Tuple[bool, str]:
        """
        Vérifie si le domaine d'un email peut recevoir des emails

        Args:
            email: L'email complet (ex: "contact@sdp-paris.com")

        Returns:
            Tuple (is_valid, details)

        Exemples:
            >>> verify_email_domain("dwain@sdp-paris.com")
            (True, "MX records found: mx1.example.com")

            >>> verify_email_domain("contact@domaine-faux.com")
            (False, "Domain does not exist")
        """
        if '@' not in email:
            return False, "Invalid email format (no @)"

        # Extraire le domaine
        domain = email.split('@')[1].strip().lower()

        if not domain:
            return False, "Empty domain"

        return self.check_domain_has_mx(domain)


# Instance globale
email_domain_validator = EmailDomainValidator()
