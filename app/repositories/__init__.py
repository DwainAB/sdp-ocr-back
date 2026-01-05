"""
Module repositories contenant tous les repositories (Data Access Layer)
"""

from app.repositories.customer_repository import customer_repository
from app.repositories.user_repository import user_repository
from app.repositories.group_repository import group_repository
from app.repositories.login_history_repository import login_history_repository
from app.repositories.customer_review_repository import customer_review_repository

__all__ = [
    'customer_repository',
    'user_repository',
    'group_repository',
    'login_history_repository',
    'customer_review_repository'
]
