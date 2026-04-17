"use client";

import Link from "next/link";
import { startTransition, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { conversationsApi } from "@/lib/api";
import type { ApiError, Conversation } from "@/lib/types";
import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, formatDateTime } from "@/lib/utils";

const navigation = [
  { href: "/app/chat", label: "Chat" },
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, logout } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [creating, setCreating] = useState(false);

  const loadConversations = useCallback(async () => {
    if (!token) {
      return;
    }
    const response = await conversationsApi.list(token);
    startTransition(() => {
      setConversations(response);
    });
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    loadConversations().catch(() => {
      startTransition(() => {
        setConversations([]);
      });
    });
  }, [loadConversations, pathname, token]);

  async function handleNewChat() {
    if (!token) {
      return;
    }
    setCreating(true);
    try {
      const emptyConversation = conversations.find(
        (conversation) => conversation.title === "New chat" && !conversation.last_message_at,
      );
      if (emptyConversation) {
        router.push(`/app/chat/${emptyConversation.id}`);
        return;
      }
      const created = await conversationsApi.create(token, {});
      startTransition(() => {
        setConversations((current) => [created, ...current]);
      });
      router.push(`/app/chat/${created.id}`);
    } catch (_error) {
      const _ignored = _error as ApiError;
    } finally {
      setCreating(false);
    }
  }

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <div className="page-shell">
      <div className="mx-auto grid min-h-screen max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:px-6">
        <aside className="surface-card hidden h-[calc(100vh-3rem)] flex-col gap-4 p-4 lg:flex">
          <Badge tone="brand" className="px-3 py-1.5 text-sm">
            LearnPilot
          </Badge>

          <nav className="grid gap-2">
            {navigation.map((item) => {
              const isNewChatEntry = item.href === "/app/chat";
              return (
                <div key={item.href}>
                  {isNewChatEntry ? (
                    <button
                      type="button"
                      onClick={handleNewChat}
                      className={cn(
                        "w-full rounded-lg px-2.5 py-1.5 text-left text-xs font-medium transition",
                        pathname.startsWith("/app/chat")
                          ? "bg-[var(--primary)] text-white"
                          : "text-[var(--muted-foreground)] hover:bg-white/80 hover:text-[var(--foreground)]",
                      )}
                    >
                      {creating ? "Creating..." : "New chat"}
                    </button>
                  ) : (
                    <Link
                      href={item.href}
                      className={cn(
                        "block rounded-lg px-2.5 py-1.5 text-xs font-medium transition",
                        isActive(item.href)
                          ? "bg-[var(--primary)] text-white"
                          : "text-[var(--muted-foreground)] hover:bg-white/80 hover:text-[var(--foreground)]",
                      )}
                    >
                      {item.label}
                    </Link>
                  )}
                </div>
              );
            })}
          </nav>

          <div className="min-h-0 flex-1 space-y-3 overflow-hidden">
            <p className="px-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--muted-foreground)]">
              History
            </p>
            <div className="grid max-h-full gap-2 overflow-y-auto pr-1">
              {conversations.length === 0 ? (
                <p className="rounded-xl border border-dashed border-[var(--border)] px-3 py-4 text-xs text-[var(--muted-foreground)]">
                  No conversations yet.
                </p>
              ) : (
                conversations.map((conversation) => (
                  <Link
                    key={conversation.id}
                    href={`/app/chat/${conversation.id}`}
                    className={cn(
                      "rounded-lg border px-3 py-2 transition",
                      pathname === `/app/chat/${conversation.id}`
                        ? "border-[var(--primary)] bg-[var(--accent-soft)]"
                        : "border-[var(--border)] bg-white/50 hover:bg-white/80",
                    )}
                  >
                    <p className="line-clamp-2 text-xs font-semibold">{conversation.title}</p>
                    <p className="mt-1 text-[11px] text-[var(--muted-foreground)]">
                      {conversation.last_message_at
                        ? formatDateTime(conversation.last_message_at)
                        : "Empty chat"}
                    </p>
                  </Link>
                ))
              )}
            </div>
          </div>

          <div className="mt-auto space-y-3">
            <Button variant="ghost" block onClick={logout}>
              Sign out
            </Button>
          </div>
        </aside>

        <div className="space-y-4">
          <header className="surface-card flex flex-col gap-3 p-4 lg:hidden">
            <div className="flex items-center gap-2">
              <Badge tone="brand" className="px-3 py-1.5 text-sm">
                LearnPilot
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              {navigation.map((item) => (
                item.href === "/app/chat" ? (
                  <button
                    key={item.href}
                    type="button"
                    onClick={handleNewChat}
                    className={cn(
                      "rounded-full px-2.5 py-1 text-xs",
                      pathname.startsWith("/app/chat")
                        ? "bg-[var(--primary)] text-white"
                        : "bg-white/70 text-[var(--muted-foreground)]",
                    )}
                  >
                    {creating ? "Creating..." : "New chat"}
                  </button>
                ) : (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "rounded-full px-2.5 py-1 text-xs",
                      isActive(item.href)
                        ? "bg-[var(--primary)] text-white"
                        : "bg-white/70 text-[var(--muted-foreground)]",
                    )}
                  >
                    {item.label}
                  </Link>
                )
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
