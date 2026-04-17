"use client";

import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ExportArtifact } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function RecentExportsCard({ artifacts }: { artifacts: ExportArtifact[] }) {
  return (
    <Card className="space-y-4 p-5">
      <div className="space-y-2">
        <CardTitle>Recent exports</CardTitle>
        <CardDescription>Recently generated note files and their Drive upload status.</CardDescription>
      </div>

      {artifacts.length === 0 ? (
        <p className="text-sm text-[var(--muted-foreground)]">No exported note files yet.</p>
      ) : (
        <div className="space-y-3">
          {artifacts.map((artifact) => (
            <Link
              key={artifact.id}
              href={`/app/chat/${artifact.conversation_id}`}
              className="block rounded-2xl border border-[var(--border)] bg-white/70 px-4 py-3 transition hover:border-[var(--primary)] hover:bg-white"
            >
              <p className="truncate text-sm font-semibold">{artifact.filename}</p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                {artifact.target_format.toUpperCase()} · {artifact.status} · {formatDateTime(artifact.created_at)}
              </p>
              {artifact.drive_file_id ? (
                <p className="mt-1 text-xs text-[var(--muted-foreground)]">Uploaded to Google Drive</p>
              ) : null}
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
}
