export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center gap-3 text-sm text-[var(--muted-foreground)]">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border-strong)] border-t-[var(--primary)]" />
      <span>{label}</span>
    </div>
  );
}
