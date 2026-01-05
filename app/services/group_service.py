from typing import Dict, Any, List
from app.database import get_connection
from app.crud import crud_group


class GroupBusinessService:
    """
    Service pour la logique métier des groupes
    """

    def add_customers_to_group(self, group_id: int, customer_ids: List[int],
                              added_by: int) -> Dict[str, Any]:
        """
        Ajoute plusieurs customers à un groupe avec gestion des erreurs détaillée

        Args:
            group_id: ID du groupe
            customer_ids: Liste des IDs des customers à ajouter
            added_by: ID de l'utilisateur qui ajoute

        Returns:
            Dict avec succès/échecs détaillés
        """
        connection = get_connection()
        if not connection:
            return {"success": False, "message": "Erreur de connexion à la base de données"}

        try:
            # Vérifier que le groupe existe et n'est pas supprimé
            if not crud_group.check_group_exists(connection, group_id):
                return {"success": False, "message": "Groupe non trouvé ou supprimé"}

            success_count = 0
            failed_count = 0
            already_exists = 0
            errors = []

            for customer_id in customer_ids:
                # Vérifier si le customer existe
                if not crud_group.check_customer_exists(connection, customer_id):
                    failed_count += 1
                    errors.append(f"Customer {customer_id} n'existe pas")
                    continue

                # Ajouter le customer au groupe
                result = crud_group.add_customer_to_group(
                    connection,
                    customer_id,
                    group_id,
                    added_by
                )

                if result:
                    success_count += 1
                else:
                    already_exists += 1

            return {
                "success": True,
                "message": f"{success_count} clients ajoutés, {already_exists} déjà présents, {failed_count} échecs",
                "details": {
                    "success_count": success_count,
                    "already_exists": already_exists,
                    "failed_count": failed_count,
                    "errors": errors
                }
            }

        except Exception as e:
            return {"success": False, "message": f"Erreur lors de l'ajout : {str(e)}"}
        finally:
            if connection.is_connected():
                connection.close()

    def remove_customers_from_group(self, group_id: int,
                                   customer_ids: List[int]) -> Dict[str, Any]:
        """
        Retire plusieurs customers d'un groupe

        Args:
            group_id: ID du groupe
            customer_ids: Liste des IDs des customers à retirer

        Returns:
            Dict avec succès/échecs détaillés
        """
        connection = get_connection()
        if not connection:
            return {"success": False, "message": "Erreur de connexion à la base de données"}

        try:
            # Vérifier que le groupe existe
            if not crud_group.get_by_id(connection, group_id, include_deleted=True):
                return {"success": False, "message": "Groupe non trouvé"}

            success_count = 0
            not_found_count = 0

            for customer_id in customer_ids:
                # Supprimer la relation
                result = crud_group.remove_customer_from_group(
                    connection,
                    customer_id,
                    group_id
                )

                if result:
                    success_count += 1
                else:
                    not_found_count += 1

            return {
                "success": True,
                "message": f"{success_count} clients retirés, {not_found_count} n'étaient pas dans le groupe",
                "details": {
                    "success_count": success_count,
                    "not_found_count": not_found_count
                }
            }

        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la suppression : {str(e)}"}
        finally:
            if connection.is_connected():
                connection.close()


group_business_service = GroupBusinessService()
