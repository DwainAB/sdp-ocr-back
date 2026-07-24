"""add_supervisor_id_to_formula

Revision ID: g3h4i5j6k7l8
Revises: f2e3d4c5b6a7
Create Date: 2026-07-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'g3h4i5j6k7l8'
down_revision: Union[str, Sequence[str], None] = 'f2e3d4c5b6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'supervisor_id'")
    ).scalar()

    if not col_exists:
        op.execute("ALTER TABLE formula ADD COLUMN supervisor_id INT NULL")
        op.execute("ALTER TABLE formula ADD CONSTRAINT fk_formula_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id) ON DELETE SET NULL")


def downgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'supervisor_id'")
    ).scalar()

    if col_exists:
        op.execute("ALTER TABLE formula DROP FOREIGN KEY fk_formula_supervisor")
        op.execute("ALTER TABLE formula DROP COLUMN supervisor_id")
