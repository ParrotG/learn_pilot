"""Add conversation-first chat core schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260417_0003"
down_revision = "20260417_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="New chat"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="complete"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_messages_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_messages_user_id"), "messages", ["user_id"], unique=False)

    op.create_table(
        "conversation_documents",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("attached_by_message_id", sa.String(length=36), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attached_by_message_id"], ["messages.id"], name=op.f("fk_conversation_documents_attached_by_message_id_messages"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_conversation_documents_conversation_id_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_conversation_documents_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_documents")),
        sa.UniqueConstraint("conversation_id", "document_id", name=op.f("uq_conversation_documents_conversation_id")),
    )
    op.create_index(op.f("ix_conversation_documents_conversation_id"), "conversation_documents", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_conversation_documents_document_id"), "conversation_documents", ["document_id"], unique=False)
    op.create_index(op.f("ix_conversation_documents_attached_by_message_id"), "conversation_documents", ["attached_by_message_id"], unique=False)

    op.create_table(
        "message_attachments",
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_message_attachments_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], name=op.f("fk_message_attachments_message_id_messages"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_attachments")),
        sa.UniqueConstraint("message_id", "document_id", name=op.f("uq_message_attachments_message_id")),
    )
    op.create_index(op.f("ix_message_attachments_message_id"), "message_attachments", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_attachments_document_id"), "message_attachments", ["document_id"], unique=False)

    op.create_table(
        "assistant_runs",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("trace", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_assistant_runs_conversation_id_conversations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], name=op.f("fk_assistant_runs_message_id_messages"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_assistant_runs_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_runs")),
    )
    op.create_index(op.f("ix_assistant_runs_conversation_id"), "assistant_runs", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_assistant_runs_message_id"), "assistant_runs", ["message_id"], unique=False)
    op.create_index(op.f("ix_assistant_runs_user_id"), "assistant_runs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assistant_runs_user_id"), table_name="assistant_runs")
    op.drop_index(op.f("ix_assistant_runs_message_id"), table_name="assistant_runs")
    op.drop_index(op.f("ix_assistant_runs_conversation_id"), table_name="assistant_runs")
    op.drop_table("assistant_runs")

    op.drop_index(op.f("ix_message_attachments_document_id"), table_name="message_attachments")
    op.drop_index(op.f("ix_message_attachments_message_id"), table_name="message_attachments")
    op.drop_table("message_attachments")

    op.drop_index(op.f("ix_conversation_documents_attached_by_message_id"), table_name="conversation_documents")
    op.drop_index(op.f("ix_conversation_documents_document_id"), table_name="conversation_documents")
    op.drop_index(op.f("ix_conversation_documents_conversation_id"), table_name="conversation_documents")
    op.drop_table("conversation_documents")

    op.drop_index(op.f("ix_messages_user_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_table("conversations")
