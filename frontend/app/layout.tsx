import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./workspace.css";
import "./mobile.css";
import "./colorful-dark.css";
import "./reliability.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#050507",
};

export const metadata: Metadata = {
  title: "FINN — A clearer view of your portfolio",
  description:
    "Evidence-first investment intelligence. Know what changed, understand why it matters, and follow the source.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
