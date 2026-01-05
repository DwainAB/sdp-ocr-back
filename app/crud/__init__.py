"""
Module CRUD contenant toutes les opérations de base de données pures
"""

from app.crud import (
    crud_customer,
    crud_user,
    crud_group,
    crud_login_history,
    crud_customer_review
)

__all__ = [
    'crud_customer',
    'crud_user',
    'crud_group',
    'crud_login_history',
    'crud_customer_review'
]
