"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { InputField } from "@/components/ui/input";
import type { ApiError } from "@/lib/types";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, register } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isRegister = mode === "register";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (isRegister) {
        await register({
          email,
          password,
          full_name: fullName || null,
        });
        await login({ email, password });
      } else {
        await login({ email, password });
      }

      setSuccess(isRegister ? "Account created successfully." : "Signed in successfully.");
      router.replace(searchParams.get("next") || "/app");
    } catch (requestError) {
      setError(requestError as ApiError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="mx-auto max-w-lg p-8">
      <div className="space-y-2">
        <CardTitle className="text-2xl">
          {isRegister ? "Create your LearnPilot workspace" : "Welcome back"}
        </CardTitle>
        <CardDescription>
          {isRegister
            ? "Set up your account to upload study PDFs, generate notes, and sync important deadlines."
            : "Sign in to continue working with your documents, notes, and schedule suggestions."}
        </CardDescription>
      </div>

      <form className="mt-8 grid gap-5" onSubmit={handleSubmit}>
        {error ? <Alert tone="danger">{error.message}</Alert> : null}
        {success ? <Alert tone="success">{success}</Alert> : null}

        {isRegister ? (
          <InputField
            label="Full name"
            placeholder="How should LearnPilot address you?"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
        ) : null}

        <InputField
          label="Email address"
          type="email"
          placeholder="student@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />

        <InputField
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <Button type="submit" loading={loading} block>
          {isRegister ? "Create account" : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-[var(--muted-foreground)]">
        {isRegister ? "Already have an account?" : "New to LearnPilot?"}{" "}
        <Link
          href={isRegister ? "/login" : "/register"}
          className="font-semibold text-[var(--primary)]"
        >
          {isRegister ? "Sign in here" : "Create one now"}
        </Link>
      </p>
    </Card>
  );
}
