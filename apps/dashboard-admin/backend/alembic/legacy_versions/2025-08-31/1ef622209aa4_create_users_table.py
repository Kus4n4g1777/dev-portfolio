"""create users table

Revision ID: 1ef622209aa4
Revises: 
Create Date: 2025-08-28 04:59:59.331517
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1ef622209aa4'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("username", sa.String, unique=True, index=True, nullable=False),
        sa.Column("email", sa.String, unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=True),
    )

def downgrade() -> None:
    op.drop_table("users")
