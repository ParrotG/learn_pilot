"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ApiError, AssistantAction, DocumentDetail } from "@/lib/types";

const actions: Array<{ value: AssistantAction; label: string; description: string }> = [
  {
    value: "summarize",
    label: "Summarize",
    description: "Generate a concise document summary.",
  },
  {
    value: "extract_key_points",
    label: "Key points",
    description: "Extract the most important study points.",
  },
  {
    value: "extract_schedule_events",
    label: "Schedule events",
    description: "Find candidate deadlines or class events.",
  },
  {
    value: "save_notes",
    label: "Save notes",
    description: "Persist the generated note to your dashboard.",
  },
];

export function AnalyzeControls({
  document,
  onAnalyze,
}: {
  document: DocumentDetail;
  onAnalyze: (payload: {
    requested_actions: AssistantAction[];
    archive_to_drive: boolean;
    save_notes: boolean;
  }) => Promise<void>;
}) {
  const [selectedActions, setSelectedActions] = useState<AssistantAction[]>([
    "summarize",
    "extract_key_points",
    "extract_schedule_events",
    "save_notes",
  ]);
  const [archiveToDrive, setArchiveToDrive] = useState(false);
  const [saveNotes, setSaveNotes] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function toggleAction(action: AssistantAction) {
    setSelectedActions((current) =>
      current.includes(action) ? current.filter((item) => item !== action) : [...current, action],
    );
  }

  async function handleAnalyze() {
    setLoading(true);
    setMessage(null);

    try {
      await onAnalyze({
        requested_actions: selectedActions,
        archive_to_drive: archiveToDrive,
        save_notes: saveNotes,
      });
      setMessage("Analysis completed successfully.");
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Run document analysis</CardTitle>
        <CardDescription>
          Choose what LearnPilot should do with <span className="font-semibold">{document.filename}</span>.
        </CardDescription>
      </div>

      <div className="grid gap-3">
        {actions.map((action) => (
          <label
            key={action.value}
            className="flex items-start gap-3 rounded-2xl border border-[var(--border)] bg-white/70 p-4"
          >
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 accent-[var(--primary)]"
              checked={selectedActions.includes(action.value)}
              onChange={() => toggleAction(action.value)}
            />
            <div>
              <p className="text-sm font-semibold">{action.label}</p>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">{action.description}</p>
            </div>
          </label>
        ))}
      </div>

      <label className="flex items-start gap-3 rounded-2xl border border-[var(--border)] bg-white/70 p-4">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 accent-[var(--primary)]"
          checked={archiveToDrive}
          onChange={(event) => setArchiveToDrive(event.target.checked)}
        />
        <div>
          <p className="text-sm font-semibold">Archive the original PDF to Google Drive</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            If your Google account is connected, LearnPilot can archive this file during analysis.
          </p>
        </div>
      </label>

      <label className="flex items-start gap-3 rounded-2xl border border-[var(--border)] bg-white/70 p-4">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 accent-[var(--primary)]"
          checked={saveNotes}
          onChange={(event) => setSaveNotes(event.target.checked)}
        />
        <div>
          <p className="text-sm font-semibold">Persist generated notes</p>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Keep the generated note available in your dashboard and document detail view.
          </p>
        </div>
      </label>

      {message ? <p className="text-sm text-[var(--muted-foreground)]">{message}</p> : null}

      <Button onClick={handleAnalyze} loading={loading}>
        Analyze now
      </Button>
    </Card>
  );
}
