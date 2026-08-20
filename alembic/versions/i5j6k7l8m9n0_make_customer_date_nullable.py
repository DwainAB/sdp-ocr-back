"""make_customer_date_nullable

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2026-08-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'i5j6k7l8m9n0'
down_revision: Union[str, Sequence[str], None] = 'h4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Certaines fiches (notamment les formulaires anglais "Creation form")
    # n'ont pas de date lisible par l'OCR. La colonne doit accepter NULL
    # pour ne plus bloquer la création du customer dans ce cas.
    op.execute("ALTER TABLE customers MODIFY COLUMN date VARCHAR(255) NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE customers MODIFY COLUMN date VARCHAR(255) NOT NULL")
