"use client";

import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { Conversation } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function RecentConversationsCard({
  conversations,
}: {
  conversations: Conversation[];
}) {
  return (
    <Card className="space-y-4">
      <div className="space-y-2">
        <CardTitle>Recent conversations</CardTitle>
        <CardDescription>Jump back into the latest chat threads you have been working on.</CardDescription>
      </div>
      {conversations.length === 0 ? (
        <p className="text-sm text-[var(--muted-foreground)]">
          No conversations yet. Start a new chat to turn LearnPilot into your main workspace.
        </p>
      ) : (
        <div className="grid gap-3">
          {conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/app/chat/${conversation.id}`}
              className="rounded-2xl border border-[var(--border)] bg-white/60 px-4 py-3 transition hover:bg-white/80"
            >
              <p className="text-sm font-semibold">{conversation.title}</p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                {conversation.last_message_at
                  ? `Updated ${formatDateTime(conversation.last_message_at)}`
                  : "No messages yet"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
}
