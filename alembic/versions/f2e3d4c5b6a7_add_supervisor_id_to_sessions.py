"""add_supervisor_id_to_sessions

Revision ID: f2e3d4c5b6a7
Revises: e7f8a2b1c3d4
Create Date: 2026-07-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'f2e3d4c5b6a7'
down_revision: Union[str, Sequence[str], None] = 'e7f8a2b1c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sessions' AND COLUMN_NAME = 'supervisor_id'")
    ).scalar()

    if not col_exists:
        op.execute("ALTER TABLE sessions ADD COLUMN supervisor_id INT NULL")
        op.execute("ALTER TABLE sessions ADD CONSTRAINT fk_sessions_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id) ON DELETE SET NULL")


def downgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sessions' AND COLUMN_NAME = 'supervisor_id'")
    ).scalar()

    if col_exists:
        op.execute("ALTER TABLE sessions DROP FOREIGN KEY fk_sessions_supervisor")
        op.execute("ALTER TABLE sessions DROP COLUMN supervisor_id")
