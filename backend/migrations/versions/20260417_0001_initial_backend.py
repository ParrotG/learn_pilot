"""Initial LearnPilot backend schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260417_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "user_credentials",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column("llm_api_key_encrypted", sa.String(), nullable=True),
        sa.Column("google_access_token_encrypted", sa.String(), nullable=True),
        sa.Column("google_refresh_token_encrypted", sa.String(), nullable=True),
        sa.Column("google_token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("google_account_email", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_credentials_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_credentials")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_credentials_user_id")),
    )

    op.create_table(
        "documents",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("drive_file_id", sa.String(length=255), nullable=True),
        sa.Column("drive_folder_id", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_documents_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)

    op.create_table(
        "notes",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_points", sa.JSON(), nullable=False),
        sa.Column("action_items", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_notes_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_notes_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
        sa.UniqueConstraint("document_id", name=op.f("uq_notes_document_id")),
    )
    op.create_index(op.f("ix_notes_document_id"), "notes", ["document_id"], unique=False)
    op.create_index(op.f("ix_notes_user_id"), "notes", ["user_id"], unique=False)

    op.create_table(
        "candidate_events",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_candidate_events_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_candidate_events_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_events")),
    )
    op.create_index(op.f("ix_candidate_events_document_id"), "candidate_events", ["document_id"], unique=False)
    op.create_index(op.f("ix_candidate_events_user_id"), "candidate_events", ["user_id"], unique=False)

    op.create_table(
        "analysis_runs",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("requested_actions", sa.JSON(), nullable=False),
        sa.Column("completed_actions", sa.JSON(), nullable=False),
        sa.Column("raw_llm_output", sa.Text(), nullable=True),
        sa.Column("trace", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_analysis_runs_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_analysis_runs_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_runs")),
    )
    op.create_index(op.f("ix_analysis_runs_document_id"), "analysis_runs", ["document_id"], unique=False)
    op.create_index(op.f("ix_analysis_runs_user_id"), "analysis_runs", ["user_id"], unique=False)

    op.create_table(
        "calendar_records",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_event_id", sa.String(length=36), nullable=False),
        sa.Column("google_event_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_event_id"], ["candidate_events.id"], name=op.f("fk_calendar_records_candidate_event_id_candidate_events"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_calendar_records_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calendar_records")),
    )
    op.create_index(op.f("ix_calendar_records_candidate_event_id"), "calendar_records", ["candidate_event_id"], unique=False)
    op.create_index(op.f("ix_calendar_records_user_id"), "calendar_records", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_calendar_records_user_id"), table_name="calendar_records")
    op.drop_index(op.f("ix_calendar_records_candidate_event_id"), table_name="calendar_records")
    op.drop_table("calendar_records")

    op.drop_index(op.f("ix_analysis_runs_user_id"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_document_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")

    op.drop_index(op.f("ix_candidate_events_user_id"), table_name="candidate_events")
    op.drop_index(op.f("ix_candidate_events_document_id"), table_name="candidate_events")
    op.drop_table("candidate_events")

    op.drop_index(op.f("ix_notes_user_id"), table_name="notes")
    op.drop_index(op.f("ix_notes_document_id"), table_name="notes")
    op.drop_table("notes")

    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_table("user_credentials")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
