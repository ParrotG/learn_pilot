"use client";

import { useRouter } from "next/navigation";
import { startTransition, useCallback, useEffect, useState } from "react";

import { ConversationList } from "@/components/chat/conversation-list";
import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { SectionHeading } from "@/components/ui/section-heading";
import { conversationsApi } from "@/lib/api";
import type { ApiError, Conversation } from "@/lib/types";

export default function ChatLandingPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const loadConversations = useCallback(async () => {
    if (!token) {
      return;
    }
    const response = await conversationsApi.list(token);
    startTransition(() => {
      setConversations(response);
      setError(null);
      setLoading(false);
    });
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    loadConversations().catch((requestError: ApiError) => {
      startTransition(() => {
        setError(requestError);
        setLoading(false);
      });
    });
  }, [loadConversations, token]);

  async function handleCreateConversation() {
    if (!token) {
      return;
    }
    setCreating(true);
    try {
      const created = await conversationsApi.create(token, {});
      router.push(`/app/chat/${created.id}`);
    } catch (requestError) {
      setError(requestError as ApiError);
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return <LoadingState label="Loading chat workspace..." />;
  }

  return (
    <div className="space-y-8">
      <SectionHeading
        eyebrow="Chat"
        title="Conversation workspace"
        description="Use LearnPilot as your main workspace for uploaded course documents and assistant replies."
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <ConversationList
          conversations={conversations}
          onCreate={handleCreateConversation}
          creating={creating}
        />
        <EmptyState
          title="Choose a conversation or start a new one"
          description="Upload a PDF inside a chat thread, ask LearnPilot to summarize it, and keep the whole interaction in one persistent workspace."
        />
      </div>
    </div>
  );
}
