"""add_box_type_to_formula

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'h4i5j6k7l8m9'
down_revision: Union[str, Sequence[str], None] = 'g3h4i5j6k7l8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'box_type'")
    ).scalar()

    if not col_exists:
        op.execute("ALTER TABLE formula ADD COLUMN box_type VARCHAR(255) NULL")


def downgrade() -> None:
    connection = op.get_bind()

    col_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'box_type'")
    ).scalar()

    if col_exists:
        op.execute("ALTER TABLE formula DROP COLUMN box_type")
