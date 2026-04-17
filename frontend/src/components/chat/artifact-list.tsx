"use client";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ExportArtifact } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ArtifactList({
  artifacts,
  onDownload,
  onUploadToDrive,
  busyArtifactId,
}: {
  artifacts: ExportArtifact[];
  onDownload: (artifact: ExportArtifact) => Promise<void>;
  onUploadToDrive: (artifact: ExportArtifact) => Promise<void>;
  busyArtifactId?: string | null;
}) {
  return (
    <Card className="space-y-5 p-5">
      <div className="space-y-2">
        <CardTitle>Artifacts</CardTitle>
        <CardDescription>
          Exported note files appear here and can be uploaded to Google Drive after approval.
        </CardDescription>
      </div>

      {artifacts.length === 0 ? (
        <div className="rounded-[1.75rem] border border-dashed border-[var(--border)] px-4 py-6 text-sm text-[var(--muted-foreground)]">
          No export artifacts yet.
        </div>
      ) : (
        <div className="space-y-3">
          {artifacts.map((artifact) => (
            <div
              key={artifact.id}
              className="rounded-[1.75rem] border border-[var(--border)] bg-white/70 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{artifact.filename}</p>
                  <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                    {artifact.target_format.toUpperCase()} · {artifact.status} · {formatDateTime(artifact.created_at)}
                  </p>
                  {artifact.drive_file_id ? (
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">Uploaded to Google Drive</p>
                  ) : null}
                  {artifact.error_message ? (
                    <p className="mt-2 text-xs text-[var(--danger)]">{artifact.error_message}</p>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {artifact.status === "completed" || artifact.status === "uploaded" ? (
                    <Button
                      variant="secondary"
                      className="min-h-9 px-3 py-1.5 text-xs"
                      onClick={() => onDownload(artifact)}
                      loading={busyArtifactId === artifact.id}
                    >
                      Download
                    </Button>
                  ) : null}
                  {artifact.status === "completed" && !artifact.drive_file_id ? (
                    <Button
                      className="min-h-9 px-3 py-1.5 text-xs"
                      onClick={() => onUploadToDrive(artifact)}
                      loading={busyArtifactId === artifact.id}
                    >
                      Upload to Drive
                    </Button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
