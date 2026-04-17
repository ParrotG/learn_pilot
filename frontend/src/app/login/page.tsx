import { Suspense } from "react";

import { PublicOnly } from "@/components/auth/public-only";
import { AuthForm } from "@/components/auth/auth-form";
import { LoadingState } from "@/components/ui/loading-state";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="page-shell flex min-h-screen items-center justify-center px-4 py-10"><LoadingState label="Preparing sign-in..." /></div>}>
      <PublicOnly>
        <div className="page-shell flex min-h-screen items-center justify-center px-4 py-10">
          <AuthForm mode="login" />
        </div>
      </PublicOnly>
    </Suspense>
  );
}
