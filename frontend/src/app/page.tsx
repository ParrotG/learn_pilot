import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const featureCards = [
  {
    title: "Upload study PDFs",
    description:
      "Bring in syllabi, assignment briefs, lecture notes, and announcements without leaving the browser.",
  },
  {
    title: "Generate useful notes",
    description:
      "Turn long academic documents into concise summaries, key points, and action-oriented study notes.",
  },
  {
    title: "Review deadlines before syncing",
    description:
      "Extract candidate schedule events, review them carefully, and then push the approved ones to Google Calendar.",
  },
];

export default function HomePage() {
  return (
    <div className="page-shell">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 lg:px-6">
        <header className="surface-card flex items-center justify-between gap-4 px-5 py-4">
          <div className="flex items-center gap-3">
            <Badge tone="brand">LearnPilot</Badge>
            <p className="text-sm text-[var(--muted-foreground)]">
              Learning Assistant-as-a-Service for academic workflows
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button>Create account</Button>
            </Link>
          </div>
        </header>

        <main className="grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1.2fr_0.8fr] lg:py-20">
          <section className="space-y-8">
            <Badge tone="brand">Built for students who want clarity fast</Badge>
            <div className="space-y-6">
              <h1
                className="max-w-4xl text-5xl font-semibold tracking-tight text-balance md:text-6xl"
                style={{ fontFamily: "var(--font-heading), sans-serif" }}
              >
                Transform course PDFs into structured notes, action items, and reviewable deadlines.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-[var(--muted-foreground)]">
                I built LearnPilot to help students move from “I need to read all of this later” to a clear, organized workspace with generated notes, candidate calendar events, and optional cloud archiving.
              </p>
            </div>
            <div className="flex flex-wrap gap-4">
              <Link href="/register">
                <Button className="px-6 py-3 text-base">Start with LearnPilot</Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" className="px-6 py-3 text-base">
                  Return to your dashboard
                </Button>
              </Link>
            </div>
          </section>

          <section className="grid gap-5">
            {featureCards.map((feature) => (
              <Card key={feature.title} className="relative overflow-hidden p-6">
                <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-[var(--accent-soft)] blur-2xl" />
                <div className="relative space-y-3">
                  <p
                    className="text-2xl font-semibold"
                    style={{ fontFamily: "var(--font-heading), sans-serif" }}
                  >
                    {feature.title}
                  </p>
                  <p className="text-sm leading-7 text-[var(--muted-foreground)]">
                    {feature.description}
                  </p>
                </div>
              </Card>
            ))}
          </section>
        </main>
      </div>
    </div>
  );
}
