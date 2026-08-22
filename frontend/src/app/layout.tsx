import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrustWipe — Certificate Verification",
  description: "Independently verify secure data-erasure certificates",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
