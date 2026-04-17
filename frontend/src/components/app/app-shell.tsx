"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/app", label: "Dashboard" },
  { href: "/app/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="page-shell">
      <div className="mx-auto grid min-h-screen max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-6">
        <aside className="surface-card hidden h-fit flex-col gap-8 p-6 lg:flex">
          <div className="space-y-5">
            <div className="space-y-3">
              <Badge tone="brand">LearnPilot</Badge>
              <div>
                <p className="text-2xl font-semibold tracking-tight">Study faster. Miss less.</p>
                <p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">
                  Turn course PDFs into notes, candidate deadlines, and cloud-ready study records.
                </p>
              </div>
            </div>
            <div className="rounded-3xl bg-[var(--surface-muted)] p-4">
              <p className="text-sm font-semibold">{user?.full_name || user?.email}</p>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">{user?.email}</p>
            </div>
          </div>

          <nav className="grid gap-2">
            {navigation.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-2xl px-4 py-3 text-sm font-medium transition",
                    active
                      ? "bg-[var(--primary)] text-[var(--primary-contrast)]"
                      : "text-[var(--muted-foreground)] hover:bg-white/80 hover:text-[var(--foreground)]",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto space-y-3">
            <div className="rounded-3xl border border-[var(--border)] bg-white/75 p-4 text-sm text-[var(--muted-foreground)]">
              Start on the dashboard to upload a new PDF or revisit your latest analysis.
            </div>
            <Button variant="ghost" block onClick={logout}>
              Sign out
            </Button>
          </div>
        </aside>

        <div className="space-y-4">
          <header className="surface-card flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between lg:hidden">
            <div>
              <p className="text-lg font-semibold">LearnPilot</p>
              <p className="text-sm text-[var(--muted-foreground)]">
                {user?.full_name || user?.email}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-full px-4 py-2 text-sm",
                    pathname === item.href
                      ? "bg-[var(--primary)] text-[var(--primary-contrast)]"
                      : "bg-white/70 text-[var(--muted-foreground)]",
                  )}
                >
                  {item.label}
                </Link>
              ))}
              <Button variant="ghost" onClick={logout}>
                Sign out
              </Button>
            </div>
          </header>

          <main>{children}</main>
        </div>
      </div>
    </div>
  );
}
