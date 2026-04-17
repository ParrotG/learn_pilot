"use client";

import { useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { InputField } from "@/components/ui/input";
import type { ApiError, CredentialStatus } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function CredentialSettingsCard({
  credentialStatus,
  onSaveLlm,
  onGoogleConnect,
  onRefreshStatus,
}: {
  credentialStatus: CredentialStatus | null;
  onSaveLlm: (payload: { provider: string; api_key: string }) => Promise<void>;
  onGoogleConnect: () => Promise<{ authorization_url: string }>;
  onRefreshStatus: () => Promise<CredentialStatus | null>;
}) {
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "success" | "danger" | "info"; text: string } | null>(
    null,
  );

  async function handleSaveLlm() {
    if (!apiKey.trim()) {
      setFeedback({ tone: "danger", text: "Paste an OpenAI API key before saving it." });
      return;
    }

    setLoading(true);
    setFeedback(null);
    try {
      await onSaveLlm({ provider: "openai", api_key: apiKey });
      setApiKey("");
      setFeedback({
        tone: "success",
        text: "Your OpenAI API key was verified and saved successfully.",
      });
    } catch (error) {
      setFeedback({ tone: "danger", text: (error as ApiError).message });
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleConnect() {
    setGoogleLoading(true);
    setFeedback(null);

    try {
      const payload = await onGoogleConnect();

      const popup = window.open(
        payload.authorization_url,
        "learnpilot-google-oauth",
        "popup=yes,width=600,height=720",
      );

      if (!popup) {
        window.location.href = payload.authorization_url;
        setGoogleLoading(false);
        return;
      }

      let attempts = 0;
        const timer = window.setInterval(async () => {
          attempts += 1;
          const status = await onRefreshStatus();
          if (status?.google_connected || popup.closed || attempts > 120) {
            window.clearInterval(timer);
            if (!popup.closed) {
              popup.close();
            }
            if (status?.google_connected) {
              setFeedback({ tone: "success", text: "Google account connected successfully." });
            } else if (attempts > 120) {
              setFeedback({
                tone: "info",
                text: "Google connection is taking longer than expected. You can refresh status or try again.",
              });
            }
            setGoogleLoading(false);
          }
        }, 2000);
    } catch (error) {
      setFeedback({ tone: "danger", text: (error as ApiError).message });
      setGoogleLoading(false);
    }
  }

  return (
    <Card className="space-y-6">
      <div className="space-y-2">
        <CardTitle>Credentials and integrations</CardTitle>
        <CardDescription>
          LearnPilot keeps your study workflow personal: your own LLM key, your own Google account, your own files.
        </CardDescription>
      </div>

      <div className="grid gap-4 rounded-[24px] border border-[var(--border)] bg-white/70 p-5">
        <div className="space-y-1">
          <p className="text-sm font-semibold">OpenAI API key</p>
          <p className="text-sm text-[var(--muted-foreground)]">
            {credentialStatus?.llm_configured
              ? `Configured with provider ${credentialStatus.llm_provider ?? "openai"}.`
              : "No LLM key has been saved yet."}
          </p>
        </div>
        <InputField
          label={credentialStatus?.llm_configured ? "Replace API key" : "New API key"}
          type="password"
          placeholder="Paste your OpenAI API key"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          hint={
            credentialStatus?.llm_configured
              ? "Paste a new key here if you want to replace the current verified key."
              : "LearnPilot verifies the key before saving it to your account."
          }
        />
        <Button onClick={handleSaveLlm} loading={loading}>
          {credentialStatus?.llm_configured ? "Replace OpenAI key" : "Save OpenAI key"}
        </Button>
      </div>

      <div className="grid gap-4 rounded-[24px] border border-[var(--border)] bg-white/70 p-5">
        <div className="space-y-1">
          <p className="text-sm font-semibold">Google Calendar and Drive</p>
          <p className="text-sm text-[var(--muted-foreground)]">
            {credentialStatus?.google_connected
              ? `Connected as ${credentialStatus.google_account_email ?? "your Google account"}.`
              : "Google is not connected yet."}
          </p>
          {credentialStatus?.google_token_expiry ? (
            <p className="text-xs text-[var(--muted-foreground)]">
              Token expiry: {formatDateTime(credentialStatus.google_token_expiry)}
            </p>
          ) : null}
        </div>
        <Button onClick={handleGoogleConnect} loading={googleLoading}>
          {credentialStatus?.google_connected ? "Reconnect Google" : "Connect Google"}
        </Button>
      </div>

      {feedback ? <Alert tone={feedback.tone}>{feedback.text}</Alert> : null}
    </Card>
  );
}
