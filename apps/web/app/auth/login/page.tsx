import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { AppShell, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    created?: string;
  };
};

export const dynamic = "force-dynamic";

export default async function LoginPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const publicApiBaseUrl = resolvePublicApiBaseUrl();
  const created = props.searchParams?.created === "1";

  return (
    <AppShell
      eyebrow="Auth real - V1"
      title={authSession?.authenticated ? "Sessao ativa no back-office" : "Entrar no back-office regulado"}
      description={
        authSession?.authenticated
          ? "A sessao persistida ja esta valida. Voce pode seguir para onboarding, equipe e workspace."
          : "O login usa sessao persistida no backend com cookie HTTP-only para sustentar RBAC e paginas protegidas."
      }
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Estado atual</span>
          <strong>
            {authSession?.authenticated ? authSession.user.organizationName : "Sessao ainda nao autenticada"}
          </strong>
          <StatusPill
            tone={authSession?.authenticated ? "ok" : "warn"}
            label={authSession?.authenticated ? "Sessao persistida" : "Login necessario"}
          />
          <p>
            {authSession?.authenticated
              ? `${authSession.user.displayName} (${authSession.user.email})`
              : "Use as credenciais seed ou crie um novo tenant em /onboarding."}
          </p>
        </div>
      }
    >
      {created ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Bootstrap concluido</span>
            <h2>Tenant criado com sucesso</h2>
            <p>O onboarding inicial foi persistido. Agora entre com o admin que acabou de ser criado.</p>
          </div>
        </section>
      ) : null}

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Credencial seed</span>
          <strong>`admin@afere.local`</strong>
          <p>Senha seed: `Afere@2026!` para validar a fundacao V1 local.</p>
        </article>
        <article className="detail-card">
          <span className="eyebrow">Tenant novo</span>
          <strong>Bootstrap via onboarding</strong>
          <p>Se preferir, crie um tenant novo em `/onboarding` antes de entrar.</p>
        </article>
        <article className="detail-card">
          <span className="eyebrow">RBAC</span>
          <strong>Sessao HTTP-only</strong>
          <p>As rotas protegidas deixam de responder sem cookie valido, mesmo com a UI no ar.</p>
        </article>
      </section>

      {authSession?.authenticated ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Sessao aberta</span>
            <h2>Continuar com o tenant autenticado</h2>
            <p>Voce ja pode seguir para a home, revisar o onboarding persistido ou encerrar a sessao atual.</p>
          </div>
          <div className="button-row">
            <a className="button-primary" href="/">
              Ir para a home
            </a>
            <a className="button-secondary" href="/onboarding">
              Abrir onboarding
            </a>
          </div>
          <form action={`${publicApiBaseUrl}/auth/logout`} method="post" className="inline-form">
            <input type="hidden" name="redirectTo" value="http://127.0.0.1:3002/auth/login" />
            <button className="button-secondary" type="submit">
              Encerrar sessao
            </button>
          </form>
        </section>
      ) : (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Entrar</span>
            <h2>Login persistido no backend</h2>
            <p>O formulario abaixo posta direto no `apps/api`, grava o cookie e redireciona de volta para o web.</p>
          </div>
          <form className="form-grid" action={`${publicApiBaseUrl}/auth/login`} method="post">
            <label className="field">
              <span>E-mail</span>
              <input defaultValue="admin@afere.local" name="email" type="email" required />
            </label>
            <label className="field">
              <span>Senha</span>
              <input defaultValue="Afere@2026!" name="password" type="password" required />
            </label>
            <input type="hidden" name="redirectTo" value="http://127.0.0.1:3002/" />
            <div className="button-row">
              <button className="button-primary" type="submit">
                Entrar no back-office
              </button>
              <a className="button-secondary" href="/onboarding">
                Criar novo tenant
              </a>
            </div>
          </form>
        </section>
      )}
    </AppShell>
  );
}

function resolvePublicApiBaseUrl() {
  return process.env.AFERE_PUBLIC_API_BASE_URL ?? process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
}
