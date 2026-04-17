"use client";

import { useParams, useRouter } from "next/navigation";
import { startTransition, useCallback, useEffect, useState } from "react";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ConversationList } from "@/components/chat/conversation-list";
import { ConversationSummaryPanel } from "@/components/chat/conversation-summary-panel";
import { MessageTimeline } from "@/components/chat/message-timeline";
import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { LoadingState } from "@/components/ui/loading-state";
import { SectionHeading } from "@/components/ui/section-heading";
import { conversationsApi, messagesApi, runsApi, workspaceApi } from "@/lib/api";
import type { ApiError, AssistantRun, Conversation, ConversationDetail, ConversationDocument, Message } from "@/lib/types";

function isTerminal(status: AssistantRun["status"]) {
  return status === "completed" || status === "failed";
}

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId;
  const router = useRouter();
  const { token } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<ConversationDocument[]>([]);
  const [activeRun, setActiveRun] = useState<AssistantRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingConversation, setCreatingConversation] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const loadConversationData = useCallback(async () => {
    if (!token) {
      return;
    }
    const [conversationList, detail, messageList, documentList] = await Promise.all([
      conversationsApi.list(token),
      conversationsApi.detail(token, conversationId),
      messagesApi.list(token, conversationId),
      workspaceApi.listDocuments(token, conversationId),
    ]);
    startTransition(() => {
      setConversations(conversationList);
      setConversation(detail);
      setMessages(messageList);
      setDocuments(documentList);
      setActiveRun(detail.latest_run);
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
        if (isTerminal(refreshedRun.status)) {
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

  async function handleCreateConversation() {
    if (!token) {
      return;
    }
    setCreatingConversation(true);
    try {
      const created = await conversationsApi.create(token, {});
      router.push(`/app/chat/${created.id}`);
    } catch (requestError) {
      setError(requestError as ApiError);
    } finally {
      setCreatingConversation(false);
    }
  }

  async function handleSendMessage(content: string) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to send a message." } satisfies ApiError;
    }
    const response = await messagesApi.create(token, conversationId, { content });
    startTransition(() => {
      setMessages((current) => [...current, response.message]);
      setActiveRun(response.assistant_run);
    });
    const refreshedConversations = await conversationsApi.list(token);
    startTransition(() => {
      setConversations(refreshedConversations);
    });
  }

  async function handleUploadDocument(file: File) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to upload a document." } satisfies ApiError;
    }
    await workspaceApi.uploadDocument(token, conversationId, file);
    await loadConversationData();
  }

  if (loading) {
    return <LoadingState label="Loading conversation..." />;
  }

  return (
    <div className="space-y-8">
      <SectionHeading
        eyebrow="Chat"
        title={conversation?.title || "Conversation"}
        description="Keep uploaded PDFs, assistant replies, and run status in one conversation-centric workflow."
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}
      {activeRun && !isTerminal(activeRun.status) ? (
        <Alert tone="info">LearnPilot is working on your latest request. Current run status: {activeRun.status}.</Alert>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_320px]">
        <ConversationList
          conversations={conversations}
          currentConversationId={conversationId}
          onCreate={handleCreateConversation}
          creating={creatingConversation}
        />

        <div className="space-y-6">
          <MessageTimeline messages={messages} />
          <ChatComposer onSend={handleSendMessage} onUpload={handleUploadDocument} />
        </div>

        <ConversationSummaryPanel documents={documents} run={activeRun} />
      </div>
    </div>
  );
}
