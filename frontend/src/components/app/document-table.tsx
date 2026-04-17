"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { DocumentListItem } from "@/lib/types";
import { formatDate, formatFileSize, sentenceCase } from "@/lib/utils";

export function DocumentTable({ documents }: { documents: DocumentListItem[] }) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-[var(--border)] px-6 py-5">
        <CardTitle>Recent documents</CardTitle>
        <CardDescription className="mt-2">
          Open any document to review extracted text, notes, candidate events, and archive status.
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
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id} className="border-t border-[var(--border)] bg-white/40">
                <td className="px-6 py-4">
                  <Link
                    href={`/app/documents/${document.id}`}
                    className="font-semibold text-[var(--primary)] hover:underline"
                  >
                    {document.filename}
                  </Link>
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
