"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { LoadingState } from "@/components/ui/loading-state";
import { conversationsApi } from "@/lib/api";
import type { ApiError } from "@/lib/types";

export default function ChatLandingPage() {
  const router = useRouter();
  const { token } = useAuth();
  const startedRef = useRef(false);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (!token || startedRef.current) {
      return;
    }

    startedRef.current = true;

    conversationsApi
      .list(token)
      .then(async (conversations) => {
        const emptyConversation = conversations.find(
          (conversation) => conversation.title === "New chat" && !conversation.last_message_at,
        );

        if (emptyConversation) {
          router.replace(`/app/chat/${emptyConversation.id}`);
          return;
        }

        const created = await conversationsApi.create(token, {});
        router.replace(`/app/chat/${created.id}`);
      })
      .catch((requestError: ApiError) => {
        setError(requestError);
      });
  }, [router, token]);

  return (
    <div className="space-y-6">
      {error ? <Alert tone="danger">{error.message}</Alert> : null}
      <LoadingState label="Opening a new chat..." />
    </div>
  );
}
