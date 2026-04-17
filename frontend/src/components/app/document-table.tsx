"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { conversationsApi } from "@/lib/api";
import type { DocumentListItem } from "@/lib/types";
import { formatDate, formatFileSize, sentenceCase } from "@/lib/utils";

export function DocumentTable({ documents }: { documents: DocumentListItem[] }) {
  const router = useRouter();
  const { token } = useAuth();
  const [openingId, setOpeningId] = useState<string | null>(null);

  async function handleOpenInChat(documentId: string) {
    if (!token) {
      return;
    }
    setOpeningId(documentId);
    try {
      const conversation = await conversationsApi.create(token, {
        initial_document_ids: [documentId],
      });
      router.push(`/app/chat/${conversation.id}`);
    } finally {
      startTransition(() => {
        setOpeningId(null);
      });
    }
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-[var(--border)] px-6 py-5">
        <CardTitle>Recent documents</CardTitle>
        <CardDescription className="mt-2">
          Open any document in chat to continue working with its content and attachments.
        </CardDescription>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead className="bg-white/60 text-[var(--muted-foreground)]">
            <tr>
              <th className="px-6 py-4 font-medium">Document</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Size</th>
              <th className="px-6 py-4 font-medium">Uploaded</th>
              <th className="px-6 py-4 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id} className="border-t border-[var(--border)] bg-white/40">
                <td className="px-6 py-4">
                  <p className="font-semibold text-[var(--foreground)]">{document.filename}</p>
                </td>
                <td className="px-6 py-4">
                  <Badge
                    tone={
                      document.processing_status === "analyzed"
                        ? "success"
                        : document.processing_status === "analysis_failed"
                          ? "danger"
                          : document.processing_status === "archived"
                            ? "brand"
                            : "warning"
                    }
                  >
                    {sentenceCase(document.processing_status)}
                  </Badge>
                </td>
                <td className="px-6 py-4 text-[var(--muted-foreground)]">
                  {formatFileSize(document.file_size)}
                </td>
                <td className="px-6 py-4 text-[var(--muted-foreground)]">
                  {formatDate(document.created_at)}
                </td>
                <td className="px-6 py-4">
                  <Button
                    variant="secondary"
                    className="min-h-8 rounded-full px-3 py-1 text-xs"
                    onClick={() => handleOpenInChat(document.id)}
                    loading={openingId === document.id}
                  >
                    Open in chat
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
