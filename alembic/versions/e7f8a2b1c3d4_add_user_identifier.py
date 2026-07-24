"""add_user_identifier

Revision ID: e7f8a2b1c3d4
Revises: a1b2c3d4e5f6
Create Date: 2026-07-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
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
    op.execute("ALTER TABLE users ADD COLUMN identifier VARCHAR(10) NULL")

    connection = op.get_bind()
    rows = connection.execute("SELECT id, last_name FROM users WHERE identifier IS NULL").fetchall()

    existing_ids = set()
    existing = connection.execute("SELECT identifier FROM users WHERE identifier IS NOT NULL").fetchall()
    for row in existing:
        existing_ids.add(row[0])

    for row in rows:
        identifier = _generate_identifier(row[1], existing_ids)
        connection.execute(
            "UPDATE users SET identifier = %s WHERE id = %s",
            (identifier, row[0])
        )

    op.execute("ALTER TABLE users MODIFY COLUMN identifier VARCHAR(10) NOT NULL")
    op.execute("ALTER TABLE users ADD UNIQUE INDEX uq_users_identifier (identifier)")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP INDEX uq_users_identifier")
    op.execute("ALTER TABLE users DROP COLUMN identifier")
