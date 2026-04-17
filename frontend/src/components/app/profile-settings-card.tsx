"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { InputField } from "@/components/ui/input";
import type { ApiError, User } from "@/lib/types";

export function ProfileSettingsCard({
  user,
  onSave,
}: {
  user: User | null;
  onSave: (payload: { full_name?: string | null }) => Promise<unknown>;
}) {
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setFullName(user?.full_name ?? "");
  }, [user]);

  async function handleSave() {
    setLoading(true);
    setMessage(null);
    try {
      await onSave({ full_name: fullName || null });
      setMessage("Profile updated successfully.");
    } catch (error) {
      setMessage((error as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Profile</CardTitle>
        <CardDescription>
          Keep your display name up to date so your dashboard feels personal and presentation-ready.
        </CardDescription>
      </div>

      <InputField label="Email address" value={user?.email ?? ""} disabled />
      <InputField
        label="Display name"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        placeholder="How should LearnPilot address you?"
      />

      {message ? <p className="text-sm text-[var(--muted-foreground)]">{message}</p> : null}

      <Button onClick={handleSave} loading={loading}>
        Save profile
      </Button>
    </Card>
  );
}
