import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

export function Badge({
  children,
  className,
  tone = "neutral",
  ...props
}: PropsWithChildren<
  HTMLAttributes<HTMLSpanElement> & {
    tone?: "neutral" | "success" | "warning" | "danger" | "brand";
  }
>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide",
        tone === "neutral" &&
          "border-[var(--border)] bg-white/70 text-[var(--muted-foreground)]",
        tone === "success" &&
          "border-emerald-200 bg-emerald-50 text-emerald-700",
        tone === "warning" &&
          "border-amber-200 bg-amber-50 text-amber-700",
        tone === "danger" &&
          "border-rose-200 bg-rose-50 text-rose-700",
        tone === "brand" &&
          "border-[var(--primary)]/20 bg-[var(--accent-soft)] text-[var(--primary)]",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
