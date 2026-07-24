"""add_user_identifier

Revision ID: e7f8a2b1c3d4
Revises: a1b2c3d4e5f6
Create Date: 2026-07-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text
import random
import string


revision: str = 'e7f8a2b1c3d4'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _generate_identifier(last_name: str, existing_ids: set) -> str:
    prefix = last_name[:3].upper() if last_name else "XXX"
    prefix = prefix.ljust(3, 'X')
    while True:
        digits = ''.join(random.choices(string.digits, k=3))
        identifier = f"{prefix}{digits}"
        if identifier not in existing_ids:
            existing_ids.add(identifier)
            return identifier


def upgrade() -> None:
    connection = op.get_bind()

    result = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'identifier'")
    ).scalar()

    if not result:
        op.execute("ALTER TABLE users ADD COLUMN identifier VARCHAR(10) NULL")

    rows = connection.execute(text("SELECT id, last_name FROM users WHERE identifier IS NULL")).fetchall()

    existing_ids = set()
    existing = connection.execute(text("SELECT identifier FROM users WHERE identifier IS NOT NULL")).fetchall()
    for row in existing:
        existing_ids.add(row[0])

    for row in rows:
        identifier = _generate_identifier(row[1], existing_ids)
        connection.execute(
            text("UPDATE users SET identifier = :id_val WHERE id = :uid"),
            {"id_val": identifier, "uid": row[0]}
        )

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'identifier'")
    ).scalar()

    if col_exists:
        op.execute("ALTER TABLE users MODIFY COLUMN identifier VARCHAR(10) NOT NULL")

    idx_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.STATISTICS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'uq_users_identifier'")
    ).scalar()

    if not idx_exists:
        op.execute("CREATE UNIQUE INDEX uq_users_identifier ON users (identifier)")


def downgrade() -> None:
    connection = op.get_bind()

    idx_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.STATISTICS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'uq_users_identifier'")
    ).scalar()
    if idx_exists:
        op.execute("ALTER TABLE users DROP INDEX uq_users_identifier")

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'identifier'")
    ).scalar()
    if col_exists:
        op.execute("ALTER TABLE users DROP COLUMN identifier")
