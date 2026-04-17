import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import { AuthProvider } from "@/components/providers/auth-provider";
import "@/app/globals.css";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

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
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body
        style={{
          fontFamily: "var(--font-body), sans-serif",
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-heading), sans-serif",
            position: "absolute",
            opacity: 0,
            pointerEvents: "none",
          }}
        />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
