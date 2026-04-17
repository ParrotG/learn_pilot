"""Add tool calls, session notes, and approval state."""

from alembic import op
import sqlalchemy as sa


revision = "20260417_0004"
down_revision = "20260417_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_notes",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Study Note"),
        sa.Column("current_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_session_notes_conversation_id_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_session_notes_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_notes")),
        sa.UniqueConstraint("conversation_id", name=op.f("uq_session_notes_conversation_id")),
    )
    op.create_index(op.f("ix_session_notes_conversation_id"), "session_notes", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_session_notes_user_id"), "session_notes", ["user_id"], unique=False)

    op.create_table(
        "tool_calls",
        sa.Column("assistant_run_id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("arguments_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending_approval"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approval_reason", sa.Text(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assistant_run_id"], ["assistant_runs.id"], name=op.f("fk_tool_calls_assistant_run_id_assistant_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_tool_calls_conversation_id_conversations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_calls")),
    )
    op.create_index(op.f("ix_tool_calls_assistant_run_id"), "tool_calls", ["assistant_run_id"], unique=False)
    op.create_index(op.f("ix_tool_calls_conversation_id"), "tool_calls", ["conversation_id"], unique=False)

    op.create_table(
        "tool_approval_decisions",
        sa.Column("tool_call_id", sa.String(length=36), nullable=False),
        sa.Column("decided_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], name=op.f("fk_tool_approval_decisions_decided_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"], name=op.f("fk_tool_approval_decisions_tool_call_id_tool_calls"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_approval_decisions")),
    )
    op.create_index(op.f("ix_tool_approval_decisions_tool_call_id"), "tool_approval_decisions", ["tool_call_id"], unique=False)
    op.create_index(op.f("ix_tool_approval_decisions_decided_by_user_id"), "tool_approval_decisions", ["decided_by_user_id"], unique=False)

    op.create_table(
        "session_note_revisions",
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("assistant_run_id", sa.String(length=36), nullable=False),
        sa.Column("patch_format", sa.String(length=50), nullable=False, server_default="unified_diff"),
        sa.Column("patch_text", sa.Text(), nullable=False),
        sa.Column("result_markdown", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assistant_run_id"], ["assistant_runs.id"], name=op.f("fk_session_note_revisions_assistant_run_id_assistant_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["note_id"], ["session_notes.id"], name=op.f("fk_session_note_revisions_note_id_session_notes"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_note_revisions")),
    )
    op.create_index(op.f("ix_session_note_revisions_note_id"), "session_note_revisions", ["note_id"], unique=False)
    op.create_index(op.f("ix_session_note_revisions_assistant_run_id"), "session_note_revisions", ["assistant_run_id"], unique=False)

    with op.batch_alter_table("assistant_runs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pending_tool_call_id", sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f("ix_assistant_runs_pending_tool_call_id"), ["pending_tool_call_id"], unique=False)

    with op.batch_alter_table("candidate_events", schema=None) as batch_op:
        batch_op.alter_column("document_id", existing_type=sa.String(length=36), nullable=True)
        batch_op.add_column(sa.Column("conversation_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("tool_call_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("source_message_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("source_document_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("normalized_year_defaulted", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key(
            batch_op.f("fk_candidate_events_conversation_id_conversations"),
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_candidate_events_tool_call_id_tool_calls"),
            "tool_calls",
            ["tool_call_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_candidate_events_source_message_id_messages"),
            "messages",
            ["source_message_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_candidate_events_source_document_id_documents"),
            "documents",
            ["source_document_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_candidate_events_conversation_id"), ["conversation_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_candidate_events_tool_call_id"), ["tool_call_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_candidate_events_source_message_id"), ["source_message_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_candidate_events_source_document_id"), ["source_document_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("candidate_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_candidate_events_source_document_id"))
        batch_op.drop_index(batch_op.f("ix_candidate_events_source_message_id"))
        batch_op.drop_index(batch_op.f("ix_candidate_events_tool_call_id"))
        batch_op.drop_index(batch_op.f("ix_candidate_events_conversation_id"))
        batch_op.drop_constraint(batch_op.f("fk_candidate_events_source_document_id_documents"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_candidate_events_source_message_id_messages"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_candidate_events_tool_call_id_tool_calls"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_candidate_events_conversation_id_conversations"), type_="foreignkey")
        batch_op.drop_column("normalized_year_defaulted")
        batch_op.drop_column("source_document_id")
        batch_op.drop_column("source_message_id")
        batch_op.drop_column("tool_call_id")
        batch_op.drop_column("conversation_id")
        batch_op.alter_column("document_id", existing_type=sa.String(length=36), nullable=False)

    with op.batch_alter_table("assistant_runs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_assistant_runs_pending_tool_call_id"))
        batch_op.drop_column("pending_tool_call_id")

    op.drop_index(op.f("ix_session_note_revisions_assistant_run_id"), table_name="session_note_revisions")
    op.drop_index(op.f("ix_session_note_revisions_note_id"), table_name="session_note_revisions")
    op.drop_table("session_note_revisions")

    op.drop_index(op.f("ix_tool_approval_decisions_decided_by_user_id"), table_name="tool_approval_decisions")
    op.drop_index(op.f("ix_tool_approval_decisions_tool_call_id"), table_name="tool_approval_decisions")
    op.drop_table("tool_approval_decisions")

    op.drop_index(op.f("ix_tool_calls_conversation_id"), table_name="tool_calls")
    op.drop_index(op.f("ix_tool_calls_assistant_run_id"), table_name="tool_calls")
    op.drop_table("tool_calls")

    op.drop_index(op.f("ix_session_notes_user_id"), table_name="session_notes")
    op.drop_index(op.f("ix_session_notes_conversation_id"), table_name="session_notes")
    op.drop_table("session_notes")
