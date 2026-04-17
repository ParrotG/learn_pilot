import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

export function Alert({
  children,
  className,
  tone = "info",
  ...props
}: PropsWithChildren<
  HTMLAttributes<HTMLDivElement> & { tone?: "info" | "success" | "warning" | "danger" }
>) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3 text-sm leading-6",
        tone === "info" && "border-slate-200 bg-white/70 text-[var(--foreground)]",
        tone === "success" && "border-emerald-200 bg-emerald-50 text-emerald-800",
        tone === "warning" && "border-amber-200 bg-amber-50 text-amber-800",
        tone === "danger" && "border-rose-200 bg-rose-50 text-rose-800",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
