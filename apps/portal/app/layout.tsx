import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Afere Portal",
  description: "Portal publico de verificacao minima e autenticidade de certificados do Afere.",
};

export default function RootLayout(props: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{props.children}</body>
    </html>
  );
}
