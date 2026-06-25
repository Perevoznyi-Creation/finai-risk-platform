"""add embedding column to risk_analyses

Revision ID: 20260513_0003
Revises: 20260513_0002
Create Date: 2026-05-13 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "20260513_0003"
down_revision: Union[str, Sequence[str], None] = "20260513_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "risk_analyses",
        sa.Column("embedding", Vector(384), nullable=True),
    )
    op.create_index(
        "ix_risk_analyses_embedding",
        "risk_analyses",
        ["embedding"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )


def downgrade() -> None:
    op.drop_index("ix_risk_analyses_embedding", table_name="risk_analyses")
    op.drop_column("risk_analyses", "embedding")
