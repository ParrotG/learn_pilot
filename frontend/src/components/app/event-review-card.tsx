"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import type { ApiError, CandidateEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function EventReviewCard({
  events,
  onCreateEvents,
}: {
  events: CandidateEvent[];
  onCreateEvents: (candidateEventIds: string[]) => Promise<void>;
}) {
  const pendingEvents = useMemo(
    () => events.filter((event) => event.status === "pending"),
    [events],
  );
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleSelection(id: string) {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  async function handleCreateEvents() {
    setLoading(true);
    setMessage(null);
    try {
      await onCreateEvents(selectedIds);
      setSelectedIds([]);
      setMessage("Approved events were sent to Google Calendar.");
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Candidate calendar events</CardTitle>
        <CardDescription>
          Review extracted schedule items before writing them to Google Calendar.
        </CardDescription>
      </div>

      <div className="grid gap-4">
        {events.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">
            No candidate events have been extracted for this document yet.
          </p>
        ) : (
          events.map((event) => (
            <label
              key={event.id}
              className="grid gap-3 rounded-2xl border border-[var(--border)] bg-white/70 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  {event.status === "pending" ? (
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 accent-[var(--primary)]"
                      checked={selectedIds.includes(event.id)}
                      onChange={() => toggleSelection(event.id)}
                    />
                  ) : null}
                  <div className="space-y-1">
                    <p className="text-sm font-semibold">{event.title}</p>
                    <p className="text-sm text-[var(--muted-foreground)]">
                      {formatDateTime(event.start_time)}
                      {event.end_time ? ` → ${formatDateTime(event.end_time)}` : ""}
                    </p>
                  </div>
                </div>
                <Badge
                  tone={
                    event.status === "synced"
                      ? "success"
                      : event.status === "failed"
                        ? "danger"
                        : event.status === "approved"
                          ? "brand"
                          : "warning"
                  }
                >
                  {event.status}
                </Badge>
              </div>
              {event.description ? (
                <p className="text-sm text-[var(--muted-foreground)]">{event.description}</p>
              ) : null}
              {event.location ? (
                <p className="text-sm text-[var(--muted-foreground)]">Location: {event.location}</p>
              ) : null}
              {event.source_excerpt ? (
                <p className="rounded-2xl bg-[var(--surface-muted)] px-3 py-2 text-sm text-[var(--muted-foreground)]">
                  Source excerpt: {event.source_excerpt}
                </p>
              ) : null}
              {event.error_message ? (
                <p className="text-sm text-[var(--danger)]">{event.error_message}</p>
              ) : null}
            </label>
          ))
        )}
      </div>

      {message ? <p className="text-sm text-[var(--muted-foreground)]">{message}</p> : null}

      <Button
        onClick={handleCreateEvents}
        loading={loading}
        disabled={pendingEvents.length === 0 || selectedIds.length === 0}
      >
        Create selected calendar events
      </Button>
    </Card>
  );
}
