"""Add export artifacts for Pandoc exports and Drive uploads."""

from alembic import op
import sqlalchemy as sa


revision = "20260417_0005"
down_revision = "20260417_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "export_artifacts",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("assistant_run_id", sa.String(length=36), nullable=False),
        sa.Column("tool_call_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_format", sa.String(length=50), nullable=False, server_default="markdown"),
        sa.Column("target_format", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("drive_file_id", sa.String(length=255), nullable=True),
        sa.Column("drive_folder_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assistant_run_id"], ["assistant_runs.id"], name=op.f("fk_export_artifacts_assistant_run_id_assistant_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_export_artifacts_conversation_id_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["note_id"], ["session_notes.id"], name=op.f("fk_export_artifacts_note_id_session_notes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"], name=op.f("fk_export_artifacts_tool_call_id_tool_calls"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_export_artifacts_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_artifacts")),
    )
    op.create_index(op.f("ix_export_artifacts_assistant_run_id"), "export_artifacts", ["assistant_run_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_conversation_id"), "export_artifacts", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_note_id"), "export_artifacts", ["note_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_tool_call_id"), "export_artifacts", ["tool_call_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_user_id"), "export_artifacts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_artifacts_user_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_tool_call_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_note_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_conversation_id"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_assistant_run_id"), table_name="export_artifacts")
    op.drop_table("export_artifacts")
