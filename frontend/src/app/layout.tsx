import type { Metadata } from "next";

import { AuthProvider } from "@/components/providers/auth-provider";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "LearnPilot",
  description:
    "A learning assistant web app for turning academic PDFs into structured notes, candidate deadlines, and cloud-ready study records.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        style={{
          fontFamily: "var(--font-body), sans-serif",
        }}
        suppressHydrationWarning
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
