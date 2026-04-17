"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { TextareaField } from "@/components/ui/input";
import type { ApiError, Note } from "@/lib/types";

function listToTextarea(items: string[]) {
  return items.join("\n");
}

function textareaToList(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function NoteEditor({
  note,
  documentId,
  onSave,
}: {
  note: Note | null;
  documentId: string;
  onSave: (payload: {
    document_id: string;
    summary: string;
    key_points: string[];
    action_items: string[];
  }) => Promise<void>;
}) {
  const [summary, setSummary] = useState(note?.summary ?? "");
  const [keyPoints, setKeyPoints] = useState(listToTextarea(note?.key_points ?? []));
  const [actionItems, setActionItems] = useState(listToTextarea(note?.action_items ?? []));
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setSummary(note?.summary ?? "");
    setKeyPoints(listToTextarea(note?.key_points ?? []));
    setActionItems(listToTextarea(note?.action_items ?? []));
  }, [note]);

  async function handleSave() {
    setLoading(true);
    setMessage(null);
    try {
      await onSave({
        document_id: documentId,
        summary,
        key_points: textareaToList(keyPoints),
        action_items: textareaToList(actionItems),
      });
      setMessage("The note was saved successfully.");
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Structured note</CardTitle>
        <CardDescription>
          Edit and save the note that LearnPilot keeps for this document.
        </CardDescription>
      </div>

      <TextareaField
        label="Summary"
        placeholder="Write a concise summary of the document."
        value={summary}
        onChange={(event) => setSummary(event.target.value)}
      />

      <TextareaField
        label="Key points"
        hint="One point per line."
        placeholder="Important concept one&#10;Important concept two"
        value={keyPoints}
        onChange={(event) => setKeyPoints(event.target.value)}
      />

      <TextareaField
        label="Action items"
        hint="One action per line."
        placeholder="Review section 3&#10;Submit the assignment"
        value={actionItems}
        onChange={(event) => setActionItems(event.target.value)}
      />

      {message ? <p className="text-sm text-[var(--muted-foreground)]">{message}</p> : null}

      <Button onClick={handleSave} loading={loading}>
        Save note
      </Button>
    </Card>
  );
}
