"use client";

import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "ghost" | "danger";
    loading?: boolean;
    block?: boolean;
  }
>;

export function Button({
  children,
  className,
  variant = "primary",
  loading = false,
  block = false,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border px-4 py-2 text-sm font-semibold transition duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--primary)]",
        block && "w-full",
        variant === "primary" &&
          "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-contrast)] shadow-lg shadow-emerald-900/15 hover:bg-[var(--primary-strong)]",
        variant === "secondary" &&
          "border-[var(--border-strong)] bg-[var(--surface-strong)] text-[var(--foreground)] hover:border-[var(--primary)] hover:text-[var(--primary)]",
        variant === "ghost" &&
          "border-transparent bg-transparent text-[var(--muted-foreground)] hover:bg-white/60 hover:text-[var(--foreground)]",
        variant === "danger" &&
          "border-[var(--danger)] bg-[var(--danger)] text-white hover:opacity-90",
        (disabled || loading) && "cursor-not-allowed opacity-60",
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          <span>Working…</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
