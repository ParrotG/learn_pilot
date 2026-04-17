"use client";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { SessionNote } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { MarkdownContent } from "./markdown-content";

export function SessionNotePanel({ note }: { note: SessionNote | null }) {
  return (
    <Card className="space-y-5 p-5">
      <div className="space-y-2">
        <CardTitle>{note?.title || "Session note"}</CardTitle>
        <CardDescription>
          {note ? `Updated ${formatDateTime(note.updated_at)}` : "The assistant will create a note here when needed."}
        </CardDescription>
      </div>

      {note ? (
        <div className="rounded-[1.75rem] border border-[var(--border)] bg-white/70 p-4">
          <MarkdownContent content={note.current_markdown} compact />
        </div>
      ) : (
        <div className="rounded-[1.75rem] border border-dashed border-[var(--border)] px-4 py-6 text-sm text-[var(--muted-foreground)]">
          No session note yet.
        </div>
      )}
    </Card>
  );
}
