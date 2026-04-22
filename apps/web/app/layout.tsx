import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Afere Backoffice",
  description: "Back-office operacional do Afere para auth, onboarding e emissao controlada.",
};

export default function RootLayout(props: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{props.children}</body>
    </html>
  );
}
