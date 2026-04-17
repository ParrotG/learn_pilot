"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ApiError, ToolCall } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ToolApprovalModal({
  toolCall,
  onApprove,
  onReject,
}: {
  toolCall: ToolCall;
  onApprove: (comment?: string) => Promise<void>;
  onReject: (comment?: string) => Promise<void>;
}) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAction(action: "approve" | "reject") {
    setLoading(action);
    setError(null);
    try {
      if (action === "approve") {
        await onApprove();
      } else {
        await onReject();
      }
    } catch (requestError) {
      setError((requestError as ApiError).message);
    } finally {
      setLoading(null);
    }
  }

  const targetFormat = typeof toolCall.arguments_json.target_format === "string"
    ? toolCall.arguments_json.target_format.toUpperCase()
    : null;
  const artifactFilename = typeof toolCall.arguments_json.filename === "string"
    ? toolCall.arguments_json.filename
    : null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 px-4 py-6">
      <Card className="max-h-[85vh] w-full max-w-2xl space-y-5 overflow-y-auto p-6">
        <div className="space-y-2">
          <CardTitle>
            {toolCall.tool_name === "create_calendar_event"
              ? "Approve calendar write"
              : toolCall.tool_name === "export_note_with_pandoc"
                ? "Approve note export"
                : "Approve Drive upload"}
          </CardTitle>
          <CardDescription>
            {toolCall.tool_name === "create_calendar_event"
              ? "LearnPilot wants to create these events in your Google Calendar."
              : toolCall.tool_name === "export_note_with_pandoc"
                ? "LearnPilot wants to export the current session note to a local file."
                : "LearnPilot wants to upload an exported artifact to your Google Drive workspace folder."}
          </CardDescription>
        </div>

        {toolCall.tool_name === "create_calendar_event" ? (
          <div className="grid gap-4">
            {toolCall.candidate_events.map((event) => (
              <div key={event.id} className="rounded-2xl border border-[var(--border)] bg-white/70 p-4">
                <p className="text-sm font-semibold">{event.title}</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  {formatDateTime(event.start_time)}
                  {event.end_time ? ` → ${formatDateTime(event.end_time)}` : ""}
                </p>
                {event.description ? (
                  <p className="mt-3 text-sm text-[var(--muted-foreground)]">{event.description}</p>
                ) : null}
                {event.location ? (
                  <p className="mt-2 text-sm text-[var(--muted-foreground)]">Location: {event.location}</p>
                ) : null}
                {event.source_excerpt ? (
                  <p className="mt-3 rounded-2xl bg-[var(--surface-muted)] px-3 py-2 text-sm text-[var(--muted-foreground)]">
                    Source excerpt: {event.source_excerpt}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-[var(--border)] bg-white/70 p-4 text-sm text-[var(--muted-foreground)]">
            {toolCall.tool_name === "export_note_with_pandoc" ? (
              <>
                <p className="font-semibold text-[var(--foreground)]">Target format: {targetFormat ?? "Unknown"}</p>
                <p className="mt-2">The exported file will be created inside the backend export directory.</p>
              </>
            ) : (
              <>
                <p className="font-semibold text-[var(--foreground)]">
                  Artifact: {artifactFilename ?? "Selected export artifact"}
                </p>
                <p className="mt-2">The file will be uploaded to the LearnPilot-managed folder in Google Drive.</p>
              </>
            )}
          </div>
        )}

        {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

        <div className="flex items-center justify-end gap-3">
          <Button
            variant="secondary"
            onClick={() => handleAction("reject")}
            loading={loading === "reject"}
          >
            Reject
          </Button>
          <Button onClick={() => handleAction("approve")} loading={loading === "approve"}>
            Approve all
          </Button>
        </div>
      </Card>
    </div>
  );
}
