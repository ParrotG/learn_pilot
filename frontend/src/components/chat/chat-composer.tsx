"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
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
    <div className="surface-card space-y-2 p-2">
      <div className="relative">
        <textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Ask anything"
          className="min-h-28 w-full rounded-[1.75rem] border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-4 pr-28 text-sm outline-none transition placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--accent-soft)]"
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleUpload}
          />
          <Button
            variant="secondary"
            onClick={() => inputRef.current?.click()}
            loading={uploading}
            className="min-h-8 rounded-full px-3 py-1 text-xs"
          >
            +
          </Button>
          <Button
            onClick={handleSend}
            loading={sending}
            disabled={!content.trim()}
            className="min-h-8 rounded-full px-4 py-1 text-xs"
          >
            Send
          </Button>
        </div>
      </div>

      {message ? <p className="text-sm text-[var(--danger)]">{message}</p> : null}
    </div>
  );
}
