"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { TextareaField } from "@/components/ui/input";
import type { ApiError } from "@/lib/types";

export function ChatComposer({
  onSend,
  onUpload,
}: {
  onSend: (content: string) => Promise<void>;
  onUpload: (file: File) => Promise<void>;
}) {
  const [content, setContent] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  async function handleSend() {
    const trimmed = content.trim();
    if (!trimmed) {
      return;
    }
    setSending(true);
    setMessage(null);
    try {
      await onSend(trimmed);
      setContent("");
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setSending(false);
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setUploading(true);
    setMessage(null);
    try {
      await onUpload(file);
      event.target.value = "";
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="surface-card space-y-4 p-4">
      <TextareaField
        label="Message"
        placeholder="Ask LearnPilot to summarize, explain, or help you work through the attached documents."
        value={content}
        onChange={(event) => setContent(event.target.value)}
        className="min-h-32"
      />

      {message ? <p className="text-sm text-[var(--danger)]">{message}</p> : null}

      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={handleUpload}
        />
        <Button variant="secondary" onClick={() => inputRef.current?.click()} loading={uploading}>
          Upload PDF
        </Button>
        <Button onClick={handleSend} loading={sending} disabled={!content.trim()}>
          Send message
        </Button>
      </div>
    </div>
  );
}
