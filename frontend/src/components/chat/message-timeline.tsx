"use client";

import { Card } from "@/components/ui/card";
import type { Message } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { MarkdownContent } from "./markdown-content";

function toneForRole(role: Message["role"]) {
  if (role === "assistant") {
    return "bg-white/80";
  }
  if (role === "system") {
    return "bg-[var(--surface-muted)]";
  }
  return "bg-[var(--accent-soft)]";
}

export function MessageTimeline({
  messages,
}: {
  messages: Message[];
}) {
  return (
    <Card className="space-y-4 p-4">
      {messages.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-[var(--border)] px-4 py-6 text-sm text-[var(--muted-foreground)]">
          This conversation is empty. Upload a document or send the first message to begin.
        </p>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`rounded-3xl border border-[var(--border)] p-4 ${toneForRole(message.role)}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
                {message.role}
              </p>
              <p className="text-xs text-[var(--muted-foreground)]">{formatDateTime(message.created_at)}</p>
            </div>
            {message.role === "user" ? (
              <p className="whitespace-pre-wrap text-sm leading-7">{message.content_markdown}</p>
            ) : (
              <MarkdownContent content={message.content_markdown} />
            )}
            {message.attachments.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {message.attachments.map((attachment) => (
                  <span
                    key={`${message.id}-${attachment.id}`}
                    className="rounded-full border border-[var(--border)] bg-white/70 px-3 py-1 text-xs text-[var(--muted-foreground)]"
                  >
                    {attachment.filename}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))
      )}
    </Card>
  );
}
