"use client";

import Link from "next/link";
import { startTransition, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AnalyzeControls } from "@/components/app/analyze-controls";
import { EventReviewCard } from "@/components/app/event-review-card";
import { NoteEditor } from "@/components/app/note-editor";
import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/ui/loading-state";
import { SectionHeading } from "@/components/ui/section-heading";
import { assistantApi, calendarApi, documentsApi, driveApi, notesApi } from "@/lib/api";
import type { ApiError, AssistantAction, DocumentDetail, DriveArchiveStatus } from "@/lib/types";
import { formatDateTime, formatFileSize, sentenceCase } from "@/lib/utils";

export default function DocumentDetailPage() {
  const params = useParams<{ documentId: string }>();
  const documentId = params.documentId;
  const { token } = useAuth();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [archiveStatus, setArchiveStatus] = useState<DriveArchiveStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveMessage, setArchiveMessage] = useState<string | null>(null);

  const loadDocument = useCallback(async () => {
    if (!token) {
      return;
    }

    const [detail, driveStatus] = await Promise.all([
      documentsApi.detail(token, documentId),
      driveApi.status(token, documentId),
    ]);
    startTransition(() => {
      setDocument(detail);
      setArchiveStatus(driveStatus);
    });
  }, [documentId, token]);

  useEffect(() => {
    if (!token) {
      return;
    }

    loadDocument()
      .then(() => {
        startTransition(() => {
          setLoading(false);
          setError(null);
        });
      })
      .catch((requestError: ApiError) => {
        startTransition(() => {
          setError(requestError);
          setLoading(false);
        });
      });
  }, [documentId, loadDocument, token]);

  async function handleAnalyze(payload: {
    requested_actions: AssistantAction[];
    archive_to_drive: boolean;
    save_notes: boolean;
  }) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to analyze documents." } satisfies ApiError;
    }

    await assistantApi.execute(token, {
      document_id: documentId,
      ...payload,
    });
    await loadDocument();
  }

  async function handleSaveNote(payload: {
    document_id: string;
    summary: string;
    key_points: string[];
    action_items: string[];
  }) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to save notes." } satisfies ApiError;
    }

    await notesApi.save(token, payload);
    await loadDocument();
  }

  async function handleCreateEvents(candidateEventIds: string[]) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to create events." } satisfies ApiError;
    }

    await calendarApi.createEvents(token, candidateEventIds);
    await loadDocument();
  }

  async function handleArchive() {
    if (!token) {
      return;
    }

    setArchiveLoading(true);
    setArchiveMessage(null);
    try {
      const status = await driveApi.archive(token, documentId);
      startTransition(() => {
        setArchiveStatus(status);
        setArchiveMessage("Document archived to Google Drive.");
      });
      await loadDocument();
    } catch (requestError) {
      setArchiveMessage((requestError as ApiError).message);
    } finally {
      setArchiveLoading(false);
    }
  }

  if (loading) {
    return <LoadingState label="Loading document details..." />;
  }

  if (!document) {
    return (
      <Alert tone="danger">
        {error?.message || "The requested document could not be loaded."}
      </Alert>
    );
  }

  const latestRun = document.analysis_runs[0] ?? null;

  return (
    <div className="space-y-8">
      <SectionHeading
        eyebrow="Document workspace"
        title={document.filename}
        description="Review extracted text, generated notes, candidate events, and archive status for this uploaded file."
        actions={
          <Link href="/app">
            <Button variant="secondary">Back to dashboard</Button>
          </Link>
        }
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="space-y-2">
          <p className="text-sm text-[var(--muted-foreground)]">Processing status</p>
          <Badge tone="brand">{sentenceCase(document.processing_status)}</Badge>
        </Card>
        <Card className="space-y-2">
          <p className="text-sm text-[var(--muted-foreground)]">File size</p>
          <p className="text-xl font-semibold">{formatFileSize(document.file_size)}</p>
        </Card>
        <Card className="space-y-2">
          <p className="text-sm text-[var(--muted-foreground)]">Latest analysis</p>
          <p className="text-xl font-semibold">{latestRun ? sentenceCase(latestRun.status) : "Not run yet"}</p>
        </Card>
        <Card className="space-y-2">
          <p className="text-sm text-[var(--muted-foreground)]">Drive archive</p>
          <p className="text-xl font-semibold">{archiveStatus?.archived ? "Archived" : "Not archived"}</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <AnalyzeControls document={document} onAnalyze={handleAnalyze} />
        <Card className="space-y-5">
          <div className="space-y-2">
            <CardTitle>Archive status</CardTitle>
            <CardDescription>
              Send the original PDF to your connected Google Drive folder when you are ready.
            </CardDescription>
          </div>

          <div className="rounded-2xl border border-[var(--border)] bg-white/70 p-4">
            <p className="text-sm font-semibold">
              {archiveStatus?.archived ? "This document is archived." : "This document has not been archived yet."}
            </p>
            <p className="mt-2 text-sm text-[var(--muted-foreground)]">
              File ID: {archiveStatus?.drive_file_id || "Not available"}
            </p>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              Folder ID: {archiveStatus?.drive_folder_id || "Not available"}
            </p>
          </div>

          {archiveMessage ? <p className="text-sm text-[var(--muted-foreground)]">{archiveMessage}</p> : null}

          <Button onClick={handleArchive} loading={archiveLoading}>
            Archive to Google Drive
          </Button>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="space-y-5">
          <div className="space-y-2">
            <CardTitle>Extracted text preview</CardTitle>
            <CardDescription>
              This is the text content LearnPilot extracted from the uploaded PDF.
            </CardDescription>
          </div>
          <div className="max-h-[30rem] overflow-auto rounded-[24px] border border-[var(--border)] bg-[var(--surface-strong)] p-5 text-sm leading-7 text-[var(--muted-foreground)]">
            {document.extracted_text || "No extractable text was found in this PDF."}
          </div>
        </Card>

        <Card className="space-y-5">
          <div className="space-y-2">
            <CardTitle>Latest analysis run</CardTitle>
            <CardDescription>
              LearnPilot keeps a compact history of what actions were requested and completed.
            </CardDescription>
          </div>
          {latestRun ? (
            <div className="space-y-4 rounded-[24px] border border-[var(--border)] bg-white/70 p-5">
              <div className="flex items-center justify-between gap-3">
                <Badge tone={latestRun.status === "completed" ? "success" : "danger"}>
                  {sentenceCase(latestRun.status)}
                </Badge>
                <span className="text-xs text-[var(--muted-foreground)]">
                  {formatDateTime(latestRun.created_at)}
                </span>
              </div>
              <div>
                <p className="text-sm font-semibold">Requested actions</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  {latestRun.requested_actions.length
                    ? latestRun.requested_actions.map(sentenceCase).join(", ")
                    : "None"}
                </p>
              </div>
              <div>
                <p className="text-sm font-semibold">Completed actions</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  {latestRun.completed_actions.length
                    ? latestRun.completed_actions.map(sentenceCase).join(", ")
                    : "None"}
                </p>
              </div>
              {latestRun.error_message ? (
                <Alert tone="danger">{latestRun.error_message}</Alert>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">
              No analysis run has been recorded for this document yet.
            </p>
          )}
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <NoteEditor note={document.note} documentId={document.id} onSave={handleSaveNote} />
        <EventReviewCard events={document.candidate_events} onCreateEvents={handleCreateEvents} />
      </div>
    </div>
  );
}
