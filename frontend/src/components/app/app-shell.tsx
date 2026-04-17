"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/app", label: "Dashboard" },
  { href: "/app/chat", label: "Chat" },
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
            <div className="min-w-0 rounded-3xl bg-[var(--surface-muted)] p-4">
              <p className="break-words text-sm font-semibold">{user?.full_name || user?.email}</p>
              <p className="mt-1 break-all text-sm text-[var(--muted-foreground)]">{user?.email}</p>
            </div>
          </div>

          <nav className="grid gap-2">
            {navigation.map((item) => {
              const active =
                item.href === "/app" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-2xl px-4 py-3 text-sm font-medium transition",
                    active
                      ? "bg-[var(--primary)] text-white"
                      : "text-[var(--muted-foreground)] hover:bg-white/80 hover:text-[var(--foreground)]",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto space-y-3">
            <Button variant="ghost" block onClick={logout}>
              Sign out
            </Button>
          </div>
        </aside>

        <div className="space-y-4">
          <header className="surface-card flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between lg:hidden">
            <div>
              <p className="text-lg font-semibold">LearnPilot</p>
              <p className="break-words text-sm text-[var(--muted-foreground)]">
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
                    (item.href === "/app" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`))
                      ? "bg-[var(--primary)] text-white"
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
