import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell(props: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">{props.eyebrow}</span>
          <h1>{props.title}</h1>
          <p>{props.description}</p>
        </div>
        <div className="hero-aside">{props.aside}</div>
      </section>
      {props.children}
    </main>
  );
}

export function StatusPill(props: {
  tone: "ok" | "warn" | "neutral";
  label: string;
}) {
  return <span className={`status-pill status-pill--${props.tone}`}>{props.label}</span>;
}

export function NavCard(props: {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
  cta: string;
}) {
  return (
    <Link className="nav-card" href={props.href}>
      <span className="eyebrow">{props.eyebrow}</span>
      <strong>{props.title}</strong>
      <p>{props.description}</p>
      <span className="nav-card__cta">{props.cta}</span>
    </Link>
  );
}
