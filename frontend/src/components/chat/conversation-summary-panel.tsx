"use client";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { AssistantRun, ConversationDocument } from "@/lib/types";
import { formatDateTime, sentenceCase } from "@/lib/utils";

export function ConversationSummaryPanel({
  documents,
  run,
}: {
  documents: ConversationDocument[];
  run: AssistantRun | null;
}) {
  return (
    <div className="grid gap-6">
      <Card className="space-y-4 p-4">
        <div className="space-y-1">
          <CardTitle>Attached documents</CardTitle>
          <CardDescription>Files that LearnPilot can reference in this conversation.</CardDescription>
        </div>
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
                <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                  {sentenceCase(item.document.processing_status)}
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="space-y-4 p-4">
        <div className="space-y-1">
          <CardTitle>Latest run</CardTitle>
          <CardDescription>The current assistant run state for this conversation.</CardDescription>
        </div>
        {run ? (
          <div className="rounded-2xl border border-[var(--border)] bg-white/60 px-4 py-4">
            <p className="text-sm font-semibold">{sentenceCase(run.status)}</p>
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              Updated {formatDateTime(run.updated_at)}
            </p>
            {run.error_message ? (
              <p className="mt-3 text-sm text-[var(--danger)]">{run.error_message}</p>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-[var(--muted-foreground)]">No assistant run has been started yet.</p>
        )}
      </Card>
    </div>
  );
}
