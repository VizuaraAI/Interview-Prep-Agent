import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ML Engineer Interview Prep",
  description: "Prepare for your ML Engineer interview with AI-powered guidance",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
