"""initial schema

Revision ID: 20260304_0001
Revises:
Create Date: 2026-03-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260304_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)
    op.create_index(op.f("ix_api_keys_name"), "api_keys", ["name"], unique=True)

    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=True),
        sa.Column("algorithm", sa.String(length=100), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_model_registry_is_current"),
        "model_registry",
        ["is_current"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_registry_version"),
        "model_registry",
        ["version"],
        unique=True,
    )

    op.create_table(
        "risk_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("mode", sa.Enum("rule", "ml", name="analysis_mode"), nullable=False),
        sa.Column("volatility", sa.Float(), nullable=False),
        sa.Column("max_drawdown", sa.Float(), nullable=False),
        sa.Column("mean_return", sa.Float(), nullable=False),
        sa.Column(
            "risk_level",
            sa.Enum("LOW", "MEDIUM", "HIGH", name="risk_level"),
            nullable=False,
        ),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_risk_analyses_created_at"),
        "risk_analyses",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_analyses_symbol"),
        "risk_analyses",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        "ix_risk_analyses_symbol_created_at",
        "risk_analyses",
        ["symbol", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_risk_analyses_symbol_created_at", table_name="risk_analyses")
    op.drop_index(op.f("ix_risk_analyses_symbol"), table_name="risk_analyses")
    op.drop_index(op.f("ix_risk_analyses_created_at"), table_name="risk_analyses")
    op.drop_table("risk_analyses")

    op.drop_index(op.f("ix_model_registry_version"), table_name="model_registry")
    op.drop_index(op.f("ix_model_registry_is_current"), table_name="model_registry")
    op.drop_table("model_registry")

    op.drop_index(op.f("ix_api_keys_name"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_table("api_keys")
