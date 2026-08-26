"""create_booster_note_table

Revision ID: j6k7l8m9n0o1
Revises: i5j6k7l8m9n0
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'j6k7l8m9n0o1'
down_revision: Union[str, Sequence[str], None] = 'i5j6k7l8m9n0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Boosters (coffret "Odyssée" uniquement) : même structure que top_note/heart_note/
    # base_note, quantité toujours fixe à "5" côté application (jamais dosée par l'IA).
    op.execute("""
        CREATE TABLE IF NOT EXISTS booster_note (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            quantity VARCHAR(255) NULL,
            formula_id INT NOT NULL
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS booster_note")
