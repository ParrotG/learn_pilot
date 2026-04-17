"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { LoadingState } from "@/components/ui/loading-state";
import { useAuth } from "@/components/providers/auth-provider";

export function PublicOnly({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "authenticated") {
      router.replace(searchParams.get("next") || "/app");
    }
  }, [router, searchParams, status]);

  if (status === "loading") {
    return <LoadingState label="Checking your session..." />;
  }

  if (status === "authenticated") {
    return <LoadingState label="Opening your dashboard..." />;
  }

  return <>{children}</>;
}
