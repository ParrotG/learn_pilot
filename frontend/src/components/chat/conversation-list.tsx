"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { Conversation } from "@/lib/types";
import { cn, formatDateTime } from "@/lib/utils";

export function ConversationList({
  conversations,
  currentConversationId,
  onCreate,
  creating = false,
}: {
  conversations: Conversation[];
  currentConversationId?: string;
  onCreate: () => Promise<void>;
  creating?: boolean;
}) {
  return (
    <Card className="space-y-4 p-4">
      <div className="space-y-1">
        <CardTitle>Chats</CardTitle>
        <CardDescription>Start a fresh thread or continue an existing study conversation.</CardDescription>
      </div>

      <Button block onClick={onCreate} loading={creating}>
        New conversation
      </Button>

      <div className="grid gap-2">
        {conversations.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[var(--border)] px-4 py-5 text-sm text-[var(--muted-foreground)]">
            No conversations yet.
          </p>
        ) : (
          conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/app/chat/${conversation.id}`}
              className={cn(
                "rounded-2xl border px-4 py-3 transition",
                conversation.id === currentConversationId
                  ? "border-[var(--primary)] bg-[var(--accent-soft)]"
                  : "border-[var(--border)] bg-white/50 hover:border-[var(--border-strong)] hover:bg-white/70",
              )}
            >
              <p className="line-clamp-2 text-sm font-semibold">{conversation.title}</p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                {conversation.last_message_at
                  ? `Updated ${formatDateTime(conversation.last_message_at)}`
                  : "No messages yet"}
              </p>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}
