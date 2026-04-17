"use client";

import { useParams } from "next/navigation";
import { startTransition, useCallback, useEffect, useState } from "react";

import { ArtifactList } from "@/components/chat/artifact-list";
import { ChatComposer } from "@/components/chat/chat-composer";
import { MessageTimeline } from "@/components/chat/message-timeline";
import { SessionNotePanel } from "@/components/chat/session-note-panel";
import { ToolApprovalModal } from "@/components/chat/tool-approval-modal";
import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingState } from "@/components/ui/loading-state";
import { SectionHeading } from "@/components/ui/section-heading";
import {
  conversationsApi,
  driveApi,
  exportsApi,
  messagesApi,
  notesApi,
  runsApi,
  toolCallsApi,
  workspaceApi,
} from "@/lib/api";
import type {
  ApiError,
  AssistantRun,
  ConversationDetail,
  ConversationDocument,
  ExportArtifact,
  Message,
  SessionNote,
  ToolCall,
} from "@/lib/types";

function isTerminal(status: AssistantRun["status"]) {
  return status === "completed" || status === "failed";
}

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId;
  const { token } = useAuth();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<ConversationDocument[]>([]);
  const [artifacts, setArtifacts] = useState<ExportArtifact[]>([]);
  const [activeRun, setActiveRun] = useState<AssistantRun | null>(null);
  const [sessionNote, setSessionNote] = useState<SessionNote | null>(null);
  const [pendingToolCall, setPendingToolCall] = useState<ToolCall | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDocs, setShowDocs] = useState(false);
  const [artifactActionId, setArtifactActionId] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const loadConversationData = useCallback(async () => {
    if (!token) {
      return;
    }
    const [detail, messageList, documentList, note, artifactList] = await Promise.all([
      conversationsApi.detail(token, conversationId),
      messagesApi.list(token, conversationId),
      workspaceApi.listDocuments(token, conversationId),
      notesApi.getForConversation(token, conversationId),
      exportsApi.listForConversation(token, conversationId),
    ]);
    startTransition(() => {
      setConversation(detail);
      setMessages(messageList);
      setDocuments(documentList);
      setArtifacts(artifactList);
      setActiveRun(detail.latest_run);
      setSessionNote(note);
      setPendingToolCall(detail.pending_tool_call);
      setError(null);
      setLoading(false);
    });
  }, [conversationId, token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    loadConversationData().catch((requestError: ApiError) => {
      startTransition(() => {
        setError(requestError);
        setLoading(false);
      });
    });
  }, [loadConversationData, token]);

  useEffect(() => {
    if (!token || !activeRun || isTerminal(activeRun.status)) {
      return;
    }

    const intervalId = window.setInterval(async () => {
      try {
        const refreshedRun = await runsApi.get(token, activeRun.id);
        startTransition(() => {
          setActiveRun(refreshedRun);
        });
        if (refreshedRun.pending_tool_call_id) {
          const toolCall = await toolCallsApi.get(token, refreshedRun.pending_tool_call_id);
          startTransition(() => {
            setPendingToolCall(toolCall);
          });
        }
        if (isTerminal(refreshedRun.status) || refreshedRun.status === "waiting_for_approval") {
          window.clearInterval(intervalId);
          await loadConversationData();
        }
      } catch (requestError) {
        startTransition(() => {
          setError(requestError as ApiError);
        });
        window.clearInterval(intervalId);
      }
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [activeRun, loadConversationData, token]);

  async function handleSendMessage(content: string) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to send a message." } satisfies ApiError;
    }
    const response = await messagesApi.create(token, conversationId, { content });
    startTransition(() => {
      setMessages((current) => [...current, response.message]);
      setActiveRun(response.assistant_run);
    });
  }

  async function handleUploadDocument(file: File) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to upload a document." } satisfies ApiError;
    }
    await workspaceApi.uploadDocument(token, conversationId, file);
    await loadConversationData();
  }

  async function handleApproveToolCall() {
    if (!token || !pendingToolCall) {
      return;
    }
    const approval = await toolCallsApi.approve(token, pendingToolCall.id, {});
    const refreshedRun = await runsApi.get(token, approval.assistant_run_id);
    startTransition(() => {
      setPendingToolCall(null);
      setActiveRun(refreshedRun);
    });
  }

  async function handleRejectToolCall() {
    if (!token || !pendingToolCall) {
      return;
    }
    const rejection = await toolCallsApi.reject(token, pendingToolCall.id, {});
    const refreshedRun = await runsApi.get(token, rejection.assistant_run_id);
    startTransition(() => {
      setPendingToolCall(null);
      setActiveRun(refreshedRun);
    });
  }

  async function handleDownloadArtifact(artifact: ExportArtifact) {
    if (!token) {
      return;
    }
    setArtifactActionId(artifact.id);
    try {
      const blob = await exportsApi.download(token, artifact.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = artifact.filename;
      link.click();
      window.URL.revokeObjectURL(url);
    } finally {
      setArtifactActionId(null);
    }
  }

  async function handleUploadArtifactToDrive(artifact: ExportArtifact) {
    if (!token) {
      return;
    }
    setArtifactActionId(artifact.id);
    try {
      const response = await driveApi.requestUploadArtifact(token, artifact.id);
      startTransition(() => {
        setPendingToolCall(response.tool_call);
        setActiveRun(response.assistant_run);
      });
      await loadConversationData();
    } finally {
      setArtifactActionId(null);
    }
  }

  if (loading) {
    return <LoadingState label="Loading conversation..." />;
  }

  return (
    <div className="space-y-5">
      {pendingToolCall && activeRun?.status === "waiting_for_approval" ? (
        <ToolApprovalModal
          toolCall={pendingToolCall}
          onApprove={handleApproveToolCall}
          onReject={handleRejectToolCall}
        />
      ) : null}

      <SectionHeading
        eyebrow="Chat"
        title={conversation?.title || "Conversation"}
        actions={
          <Button variant="secondary" onClick={() => setShowDocs((current) => !current)}>
            Docs
          </Button>
        }
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}
      {activeRun && !isTerminal(activeRun.status) ? (
        <Alert tone="info">
          {activeRun.status === "waiting_for_approval"
            ? "LearnPilot is waiting for your approval before it writes external calendar events."
            : `LearnPilot is working on your latest request. Current run status: ${activeRun.status}.`}
        </Alert>
      ) : null}
      {showDocs ? (
        <div className="flex justify-end">
          <Card className="w-full max-w-sm space-y-4 p-4">
            {documents.length === 0 ? (
              <p className="text-sm text-[var(--muted-foreground)]">No documents attached yet.</p>
            ) : (
              <div className="grid gap-3">
                {documents.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-2xl border border-[var(--border)] bg-white/60 px-4 py-3"
                  >
                    <p className="text-sm font-semibold">{item.document.filename}</p>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">{item.document.processing_status}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="mx-auto flex min-h-[calc(100vh-12rem)] w-full max-w-4xl flex-col gap-4">
          <div className="flex-1">
            <MessageTimeline messages={messages} />
          </div>
          <div className="sticky bottom-0 z-10 pb-2 pt-4">
            <ChatComposer onSend={handleSendMessage} onUpload={handleUploadDocument} />
          </div>
        </div>
        <div className="xl:sticky xl:top-6 xl:self-start">
          <div className="space-y-4">
            <SessionNotePanel note={sessionNote} />
            <ArtifactList
              artifacts={artifacts}
              onDownload={handleDownloadArtifact}
              onUploadToDrive={handleUploadArtifactToDrive}
              busyArtifactId={artifactActionId}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
