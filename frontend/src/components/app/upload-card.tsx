"use client";

import type { ChangeEvent } from "react";
import { useRef, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ApiError, DocumentListItem } from "@/lib/types";

export function UploadCard({
  onUpload,
}: {
  onUpload: (file: File) => Promise<DocumentListItem>;
}) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    if (!selectedFile) {
      return;
    }

    setSelectedFileName(selectedFile.name);
    setLoading(true);
    setMessage(null);
    try {
      const uploaded = await onUpload(selectedFile);
      setMessage(`Uploaded ${uploaded.filename} successfully.`);
      setSelectedFileName(null);
      if (inputRef.current) {
        inputRef.current.value = "";
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
            {loading
              ? `Uploading ${selectedFileName ?? "your PDF"}...`
              : selectedFileName
                ? `${selectedFileName} selected`
                : "Click to choose a PDF"}
          </span>
          <span className="mt-2 text-sm text-[var(--muted-foreground)]">
            {loading
              ? "Your file is being sent to the backend right away."
              : "Choose a file and LearnPilot will start uploading it immediately."}
          </span>
          <input
            ref={inputRef}
            id="document-upload-input"
            type="file"
            className="hidden"
            accept="application/pdf"
            disabled={loading}
            onChange={handleFileChange}
          />
        </label>

        {message ? (
          <Alert tone={message.startsWith("Uploaded ") ? "success" : "danger"}>{message}</Alert>
        ) : null}
      </div>
    </Card>
  );
}
