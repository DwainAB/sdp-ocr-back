from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_order, crud_order_item, crud_customer, crud_formula, crud_notes


class OrderRepository:
    """Repository pour la gestion des commandes"""

    def create_order(self, order_data: Dict[str, Any]) -> Optional[int]:
        """Créer une nouvelle commande avec ses items"""
        connection = get_connection()
        if not connection:
            return None
        try:
            # Extraire les items avant de créer la commande
            items = order_data.pop('items', None)

            # Créer la commande
            order_id = crud_order.create(connection, order_data)
            if order_id and items:
                # Créer les items associés
                crud_order_item.create_many(connection, order_id, items)

            if order_id:
                print(f"Commande créée avec ID: {order_id}")
            return order_id
        finally:
            connection.close()

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer une commande par son ID avec ses items, client et formule (avec notes)"""
        connection = get_connection()
        if not connection:
            return None
        try:
            order = crud_order.get_by_id(connection, order_id)
            if order:
                # Enrichir avec les items
                order['items'] = crud_order_item.get_by_order_id(connection, order_id)
                # Enrichir avec le client
                if order.get('customer_id'):
                    order['customer'] = crud_customer.get_by_id(connection, order['customer_id'])
                # Enrichir avec la formule et ses notes
                if order.get('formula_id'):
                    formula = crud_formula.get_by_id(connection, order['formula_id'])
                    if formula:
                        formula['top_notes'] = crud_notes.get_notes_by_type(connection, 'top_note', order['formula_id'])
                        formula['heart_notes'] = crud_notes.get_notes_by_type(connection, 'heart_note', order['formula_id'])
                        formula['base_notes'] = crud_notes.get_notes_by_type(connection, 'base_note', order['formula_id'])
                        formula['booster_notes'] = crud_notes.get_notes_by_type(connection, 'booster_note', order['formula_id'])
                    order['formula'] = formula
            return order
        finally:
            connection.close()

    def get_all_orders(self, page: int = 1, size: int = 10,
                       search: Optional[str] = None,
                       customer_id: Optional[int] = None,
                       status: Optional[str] = None,
                       formula_id: Optional[int] = None,
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None,
                       customer_name: Optional[str] = None,
                       order_type: Optional[str] = None,
                       responsible: Optional[int] = None,
                       reference: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Récupérer toutes les commandes avec pagination et infos client"""
        connection = get_connection()
        if not connection:
            return [], 0
        try:
            orders, total = crud_order.get_all(
                connection, page, size, search, customer_id, status, formula_id,
                date_from, date_to, customer_name, order_type, responsible, reference
            )
            # Enrichir chaque commande avec ses items et le client
            for order in orders:
                order['items'] = crud_order_item.get_by_order_id(connection, order['id'])
                # Enrichir avec le client
                if order.get('customer_id'):
                    order['customer'] = crud_customer.get_by_id(connection, order['customer_id'])
            return orders, total
        finally:
            connection.close()

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> bool:
        """Mettre à jour une commande"""
        connection = get_connection()
        if not connection:
            return False
        try:
            success = crud_order.update(connection, order_id, order_data)
            if success:
                print(f"Commande {order_id} mise à jour")
            else:
                print(f"Commande {order_id} non trouvée")
            return success
        finally:
            connection.close()

    def delete_order(self, order_id: int) -> bool:
        """Supprimer une commande et ses items"""
        connection = get_connection()
        if not connection:
            return False
        try:
            # Supprimer d'abord les items
            crud_order_item.delete_by_order_id(connection, order_id)
            # Puis supprimer la commande
            success = crud_order.delete(connection, order_id)
            if success:
                print(f"Commande {order_id} supprimée")
            return success
        finally:
            connection.close()

    # ==================== ORDER ITEMS ====================

    def add_item_to_order(self, order_id: int, item_data: Dict[str, Any]) -> Optional[int]:
        """Ajouter un item à une commande"""
        connection = get_connection()
        if not connection:
            return None
        try:
            item_data['order_id'] = order_id
            item_id = crud_order_item.create(connection, item_data)
            if item_id:
                print(f"Item {item_id} ajouté à la commande {order_id}")
            return item_id
        finally:
            connection.close()

    def get_order_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un item par son ID"""
        connection = get_connection()
        if not connection:
            return None
        try:
            return crud_order_item.get_by_id(connection, item_id)
        finally:
            connection.close()

    def update_order_item(self, item_id: int, item_data: Dict[str, Any]) -> bool:
        """Mettre à jour un item de commande"""
        connection = get_connection()
        if not connection:
            return False
        try:
            success = crud_order_item.update(connection, item_id, item_data)
            if success:
                print(f"Item {item_id} mis à jour")
            return success
        finally:
            connection.close()

    def delete_order_item(self, item_id: int) -> bool:
        """Supprimer un item de commande"""
        connection = get_connection()
        if not connection:
            return False
        try:
            success = crud_order_item.delete(connection, item_id)
            if success:
                print(f"Item {item_id} supprimé")
            return success
        finally:
            connection.close()


order_repository = OrderRepository()
