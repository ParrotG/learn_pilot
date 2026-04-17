import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type FieldProps = {
  label: string;
  hint?: string;
  error?: string | null;
};

export function InputField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="grid gap-2 text-sm font-medium text-[var(--foreground)]">
      <span>{label}</span>
      <input
        className={cn(
          "min-h-11 rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-sm outline-none transition",
          "placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--accent-soft)]",
          error && "border-[var(--danger)] focus:ring-red-100",
          className,
        )}
        {...props}
      />
      {error ? (
        <span className="text-xs text-[var(--danger)]">{error}</span>
      ) : hint ? (
        <span className="text-xs text-[var(--muted-foreground)]">{hint}</span>
      ) : null}
    </label>
  );
}

export function TextareaField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <label className="grid gap-2 text-sm font-medium text-[var(--foreground)]">
      <span>{label}</span>
      <textarea
        className={cn(
          "min-h-28 rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-3 text-sm outline-none transition",
          "placeholder:text-[var(--muted-foreground)] focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--accent-soft)]",
          error && "border-[var(--danger)] focus:ring-red-100",
          className,
        )}
        {...props}
      />
      {error ? (
        <span className="text-xs text-[var(--danger)]">{error}</span>
      ) : hint ? (
        <span className="text-xs text-[var(--muted-foreground)]">{hint}</span>
      ) : null}
    </label>
  );
}
