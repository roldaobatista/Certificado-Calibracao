import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth-session-api";
import { AppShell, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_PUBLIC_API_BASE_URL ?? process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const PORTAL_BASE_URL = "http://127.0.0.1:3003";

export const dynamic = "force-dynamic";

export default async function PortalLoginPage() {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });

  return (
    <AppShell
      eyebrow="Portal - acesso do cliente"
      title={authSession?.authenticated ? "Sessao ativa no portal" : "Entrar no portal do cliente"}
      description={
        authSession?.authenticated
          ? "A sessao persistida ja esta ativa. O portal autenticado passa a ler apenas a carteira vinculada ao cliente logado."
          : "O portal usa a mesma sessao HTTP-only do backend, mas restringe o acesso a usuarios com papel external_client."
      }
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Estado atual</span>
          <strong>{authSession?.authenticated ? authSession.user.displayName : "Login necessario"}</strong>
          <StatusPill
            tone={authSession?.authenticated ? "ok" : "warn"}
            label={authSession?.authenticated ? "Sessao persistida" : "Portal bloqueado"}
          />
          <p>
            {authSession?.authenticated
              ? `${authSession.user.email} · ${authSession.user.organizationName}`
              : "Use um usuario externo do cliente para abrir dashboard, equipamentos e certificados."}
          </p>
        </div>
      }
    >
      {authSession?.authenticated ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Sessao aberta</span>
            <h2>Continuar no portal autenticado</h2>
            <p>Voce ja pode seguir para a carteira do cliente e para os certificados publicados.</p>
          </div>
          <div className="button-row">
            <a className="button-primary" href="/dashboard">
              Abrir dashboard
            </a>
            <form action={`${API_BASE_URL}/auth/logout`} method="post" className="inline-form">
              <input type="hidden" name="redirectTo" value={`${PORTAL_BASE_URL}/auth/login`} />
              <button className="button-secondary" type="submit">
                Encerrar sessao
              </button>
            </form>
          </div>
        </section>
      ) : (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Credencial seed</span>
            <h2>Login do cliente externo</h2>
            <p>O formulario abaixo grava o cookie de sessao no backend e redireciona de volta para o portal.</p>
          </div>
          <form className="form-grid" action={`${API_BASE_URL}/auth/login`} method="post">
            <label className="field">
              <span>E-mail</span>
              <input defaultValue="marcia@paodoce.com.br" name="email" type="email" required />
            </label>
            <label className="field">
              <span>Senha</span>
              <input defaultValue="Afere@2026!" name="password" type="password" required />
            </label>
            <input type="hidden" name="redirectTo" value={`${PORTAL_BASE_URL}/dashboard`} />
            <div className="button-row">
              <button className="button-primary" type="submit">
                Entrar no portal
              </button>
            </div>
          </form>
        </section>
      )}
    </AppShell>
  );
}
