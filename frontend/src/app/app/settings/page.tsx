"use client";

import { startTransition, useCallback, useEffect, useState } from "react";

import { CredentialSettingsCard } from "@/components/app/credential-settings-card";
import { ProfileSettingsCard } from "@/components/app/profile-settings-card";
import { useAuth } from "@/components/providers/auth-provider";
import { Alert } from "@/components/ui/alert";
import { LoadingState } from "@/components/ui/loading-state";
import { SectionHeading } from "@/components/ui/section-heading";
import { credentialsApi } from "@/lib/api";
import type { ApiError, CredentialStatus } from "@/lib/types";

export default function SettingsPage() {
  const { token, user, refreshUser, updateProfile } = useAuth();
  const [credentialStatus, setCredentialStatus] = useState<CredentialStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const loadCredentialStatus = useCallback(async () => {
    if (!token) {
      return null;
    }

    const status = await credentialsApi.status(token);
    startTransition(() => {
      setCredentialStatus(status);
    });
    return status;
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }

    Promise.all([loadCredentialStatus(), refreshUser()])
      .then(() => {
        startTransition(() => {
          setLoading(false);
          setError(null);
        });
      })
      .catch((requestError: ApiError) => {
        startTransition(() => {
          setError(requestError);
          setLoading(false);
        });
      });
  }, [loadCredentialStatus, refreshUser, token]);

  async function handleSaveLlm(payload: { provider: string; api_key: string }) {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to save credentials." } satisfies ApiError;
    }
    const status = await credentialsApi.saveLlmKey(token, payload);
    startTransition(() => {
      setCredentialStatus(status);
    });
  }

  async function handleGoogleConnect() {
    if (!token) {
      throw { code: "unauthorized", message: "Sign in to connect Google." } satisfies ApiError;
    }

    return credentialsApi.googleConnect(token);
  }

  if (loading) {
    return <LoadingState label="Loading settings..." />;
  }

  return (
    <div className="space-y-8">
      <SectionHeading
        eyebrow="Settings"
        title="Account and integrations"
        description="Manage your profile, connect external services, and prepare LearnPilot for analysis and calendar sync."
      />

      {error ? <Alert tone="danger">{error.message}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <ProfileSettingsCard user={user} onSave={updateProfile} />
        <CredentialSettingsCard
          credentialStatus={credentialStatus}
          onSaveLlm={handleSaveLlm}
          onGoogleConnect={handleGoogleConnect}
          onRefreshStatus={loadCredentialStatus}
        />
      </div>
    </div>
  );
}
