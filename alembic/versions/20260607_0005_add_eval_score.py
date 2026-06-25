"""add eval_score column to risk_analyses

Revision ID: 20260607_0005
Revises: 20260521_0004
Create Date: 2026-06-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260607_0005"
down_revision: Union[str, Sequence[str], None] = "20260521_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "risk_analyses",
        sa.Column("eval_score", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_analyses", "eval_score")
