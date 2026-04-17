import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { Note } from "@/lib/types";

export function NoteListCard({ notes }: { notes: Note[] }) {
  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Recent notes</CardTitle>
        <CardDescription>
          LearnPilot stores structured notes so you can revisit the most useful study outputs later.
        </CardDescription>
      </div>

      <div className="grid gap-4">
        {notes.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">
            No notes have been saved yet. Run document analysis to populate this section.
          </p>
        ) : (
          notes.map((note) => (
            <Link
              key={note.id}
              href={`/app/documents/${note.document_id}`}
              className="rounded-2xl border border-[var(--border)] bg-white/70 p-4 transition hover:border-[var(--primary)]"
            >
              <p className="text-sm font-semibold">Document {note.document_id.slice(0, 8)}</p>
              <p className="mt-2 line-clamp-3 text-sm leading-6 text-[var(--muted-foreground)]">
                {note.summary}
              </p>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}
