import { Suspense } from "react";

import { PublicOnly } from "@/components/auth/public-only";
import { AuthForm } from "@/components/auth/auth-form";
import { LoadingState } from "@/components/ui/loading-state";

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="page-shell flex min-h-screen items-center justify-center px-4 py-10"><LoadingState label="Preparing registration..." /></div>}>
      <PublicOnly>
        <div className="page-shell flex min-h-screen items-center justify-center px-4 py-10">
          <AuthForm mode="register" />
        </div>
      </PublicOnly>
    </Suspense>
  );
}
