"""Store Google OAuth PKCE state and code verifier."""

from alembic import op
import sqlalchemy as sa


revision = "20260417_0002"
down_revision = "20260417_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_credentials",
        sa.Column("google_oauth_pending_state", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "user_credentials",
        sa.Column("google_oauth_code_verifier_encrypted", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_credentials", "google_oauth_code_verifier_encrypted")
    op.drop_column("user_credentials", "google_oauth_pending_state")
