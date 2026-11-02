import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./workspace.css";
import "./mobile.css";
import "./colorful-dark.css";
import "./reliability.css";
import "./themes.css";
import {THEME_BOOTSTRAP,THEME_CANVAS} from "@/lib/theme";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  manifest: "/manifest.webmanifest",
  title: "FINN — A clearer view of your portfolio",
  description:
    "Evidence-first investment intelligence. Know what changed, understand why it matters, and follow the source.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head><meta name="theme-color" content={THEME_CANVAS.dark}/><script dangerouslySetInnerHTML={{__html:THEME_BOOTSTRAP}}/></head>
      <body>{children}</body>
    </html>
  );
}
