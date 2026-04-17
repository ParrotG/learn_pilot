"use client";

import Link from "next/link";
import { startTransition, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { DocumentTable } from "@/components/app/document-table";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { NoteListCard } from "@/components/app/note-list-card";
import { SectionHeading } from "@/components/ui/section-heading";
import { StatusCardGrid } from "@/components/app/status-card-grid";
import { UploadCard } from "@/components/app/upload-card";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { credentialsApi, documentsApi, notesApi } from "@/lib/api";
import type { ApiError, CredentialStatus, DocumentListItem, Note } from "@/lib/types";

export default function DashboardPage() {
  const { token, user } = useAuth();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [credentialStatus, setCredentialStatus] = useState<CredentialStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!token) {
      return;
    }

    const [documentsResponse, notesResponse, credentialStatusResponse] = await Promise.all([
      documentsApi.list(token),
      notesApi.list(token),
      credentialsApi.status(token),
    ]);

    startTransition(() => {
      setDocuments(documentsResponse);
      setNotes(notesResponse);
      setCredentialStatus(credentialStatusResponse);
      setError(null);
      setLoading(false);
    });
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }

    loadDashboard()
      .catch((requestError: ApiError) => {
        startTransition(() => {
          setError(requestError);
          setLoading(false);
        });
      });
  }, [loadDashboard, token]);

  async function handleUpload(file: File) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to upload a document." } satisfies ApiError;
    }

    const uploaded = await documentsApi.upload(token, file);
    const refreshedDocuments = await documentsApi.list(token);
    startTransition(() => {
      setDocuments(refreshedDocuments);
    });
    return uploaded;
  }

  if (loading) {
    return <LoadingState label="Loading your dashboard..." />;
  }

  return (
    <div className="space-y-8">
      <SectionHeading
        eyebrow="Workspace"
        title={`Hello${user?.full_name ? `, ${user.full_name}` : ""}`}
        description="Upload a fresh course PDF, revisit previous analyses, or check whether your credentials are ready for the next run."
        actions={
          <Link href="/app/settings">
            <Button variant="secondary">Open settings</Button>
          </Link>
        }
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}

      <StatusCardGrid user={user} credentials={credentialStatus} documents={documents} />

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <UploadCard onUpload={handleUpload} />
        <NoteListCard notes={notes.slice(0, 4)} />
      </div>

      {documents.length > 0 ? (
        <DocumentTable documents={documents} />
      ) : (
        <EmptyState
          title="Your dashboard is ready for its first document"
          description="Upload a study PDF to create notes, extract deadlines, and build a cleaner academic workflow."
        />
      )}
    </div>
  );
}
