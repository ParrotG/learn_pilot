"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ApiError, DocumentListItem } from "@/lib/types";

export function UploadCard({
  onUpload,
}: {
  onUpload: (file: File) => Promise<DocumentListItem>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleUpload() {
    if (!file) {
      setMessage("Choose a PDF before uploading.");
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const uploaded = await onUpload(file);
      setMessage(`Uploaded ${uploaded.filename} successfully.`);
      setFile(null);
      const input = document.getElementById("document-upload-input") as HTMLInputElement | null;
      if (input) {
        input.value = "";
      }
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[var(--primary)] via-[var(--accent)] to-transparent" />
      <div className="space-y-4">
        <div className="space-y-2">
          <CardTitle>Upload a study PDF</CardTitle>
          <CardDescription>
            LearnPilot works best with text-based syllabi, assignment briefs, lecture notes, and announcements.
          </CardDescription>
        </div>

        <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-[24px] border border-dashed border-[var(--border-strong)] bg-white/60 p-6 text-center transition hover:border-[var(--primary)] hover:bg-white/75">
          <span className="text-sm font-semibold">
            {file ? file.name : "Click to choose a PDF"}
          </span>
          <span className="mt-2 text-sm text-[var(--muted-foreground)]">
            A local file is stored on the backend and prepared for analysis.
          </span>
          <input
            id="document-upload-input"
            type="file"
            className="hidden"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        {message ? <p className="text-sm text-[var(--muted-foreground)]">{message}</p> : null}

        <Button onClick={handleUpload} loading={loading}>
          Upload document
        </Button>
      </div>
    </Card>
  );
}
