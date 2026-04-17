import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { CredentialStatus, DocumentListItem, User } from "@/lib/types";

export function StatusCardGrid({
  user,
  credentials,
  documents,
}: {
  user: User | null;
  credentials: CredentialStatus | null;
  documents: DocumentListItem[];
}) {
  const analyzedCount = documents.filter((document) =>
    ["analyzed", "archived"].includes(document.processing_status),
  ).length;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card className="space-y-2">
        <p className="text-sm font-medium text-[var(--muted-foreground)]">Account</p>
        <p className="text-2xl font-semibold">{user?.full_name || user?.email || "Guest"}</p>
        <p className="text-sm text-[var(--muted-foreground)]">
          Your workspace is ready for uploads and analysis.
        </p>
      </Card>
      <Card className="space-y-2">
        <p className="text-sm font-medium text-[var(--muted-foreground)]">LLM credential</p>
        <div className="flex items-center gap-3">
          <p className="text-2xl font-semibold">
            {credentials?.llm_configured ? "Configured" : "Missing"}
          </p>
          <Badge tone={credentials?.llm_configured ? "success" : "warning"}>
            {credentials?.llm_provider || "OpenAI"}
          </Badge>
        </div>
        <p className="text-sm text-[var(--muted-foreground)]">
          Add your API key in Settings before running analysis.
        </p>
      </Card>
      <Card className="space-y-2">
        <p className="text-sm font-medium text-[var(--muted-foreground)]">Google connection</p>
        <p className="text-2xl font-semibold">
          {credentials?.google_connected ? "Connected" : "Pending"}
        </p>
        <p className="text-sm text-[var(--muted-foreground)]">
          {credentials?.google_account_email || "Connect your Google account to sync events and archive PDFs."}
        </p>
      </Card>
      <Card className="space-y-2">
        <p className="text-sm font-medium text-[var(--muted-foreground)]">Analyzed documents</p>
        <p className="text-2xl font-semibold">{analyzedCount}</p>
        <p className="text-sm text-[var(--muted-foreground)]">
          {documents.length} total uploaded document{documents.length === 1 ? "" : "s"}.
        </p>
      </Card>
    </div>
  );
}
