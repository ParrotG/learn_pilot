import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("surface-card p-6", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLHeadingElement>>) {
  return (
    <h2 className={cn("text-lg font-semibold tracking-tight", className)} {...props}>
      {children}
    </h2>
  );
}

export function CardDescription({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLParagraphElement>>) {
  return (
    <p className={cn("text-sm leading-6 text-[var(--muted-foreground)]", className)} {...props}>
      {children}
    </p>
  );
}
