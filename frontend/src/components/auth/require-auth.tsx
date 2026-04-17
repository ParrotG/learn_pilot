"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoadingState } from "@/components/ui/loading-state";
import { useAuth } from "@/components/providers/auth-provider";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "unauthenticated") {
      const nextUrl = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${nextUrl}`);
    }
  }, [pathname, router, status]);

  if (status === "loading") {
    return <LoadingState label="Restoring your workspace..." />;
  }

  if (status !== "authenticated") {
    return <LoadingState label="Redirecting to sign in..." />;
  }

  return <>{children}</>;
}
