import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadOnboardingCatalog } from "@/src/onboarding/onboarding-api";
import { buildOnboardingCatalogView } from "@/src/onboarding/onboarding-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export const dynamic = "force-dynamic";

export default async function OnboardingPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadOnboardingCatalog({
    scenarioId: props.searchParams?.scenario,
    cookieHeader,
  });
  const publicApiBaseUrl = resolvePublicApiBaseUrl();

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Onboarding - bootstrap real"
          title="Criar o tenant inicial"
          description="Sem sessao autenticada, o onboarding entra no modo bootstrap para criar organizacao, admin e estado inicial persistido."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Modo atual</span>
              <strong>Bootstrap sem sessao</strong>
              <StatusPill tone="warn" label="Criacao inicial" />
              <p>Depois do bootstrap, voce volta para o login com o tenant ja persistido.</p>
            </div>
          }
        >
          <section className="content-panel">
            <div className="section-copy">
              <span className="eyebrow">Primeiro passo</span>
              <h2>Provisionar organizacao e admin</h2>
              <p>Este formulario grava organizacao, usuario administrador e estado inicial do onboarding no banco.</p>
            </div>
            <form className="form-grid" action={`${publicApiBaseUrl}/onboarding/bootstrap`} method="post">
              <label className="field">
                <span>Slug do tenant</span>
                <input name="slug" placeholder="laboratorio-demo" required />
              </label>
              <label className="field">
                <span>Razao social</span>
                <input name="legalName" placeholder="Laboratorio Exemplo Ltda" required />
              </label>
              <label className="field">
                <span>Perfil regulatorio</span>
                <select name="regulatoryProfile" defaultValue="type_b">
                  <option value="type_b">type_b</option>
                  <option value="type_c">type_c</option>
                </select>
              </label>
              <label className="field">
                <span>Nome do admin</span>
                <input name="adminName" placeholder="Ana Responsavel" required />
              </label>
              <label className="field">
                <span>E-mail do admin</span>
                <input name="adminEmail" type="email" placeholder="admin@laboratorio.local" required />
              </label>
              <label className="field">
                <span>Senha inicial</span>
                <input name="password" type="password" minLength={8} required />
              </label>
              <input type="hidden" name="redirectTo" value="http://127.0.0.1:3002/auth/login?created=1" />
              <div className="button-row">
                <button className="button-primary" type="submit">
                  Criar tenant
                </button>
                <a className="button-secondary" href="/auth/login">
                  Ja tenho acesso
                </a>
              </div>
            </form>
          </section>
        </AppShell>
      );
    }

    return (
      <AppShell
        eyebrow="Onboarding - PRD 13.12"
        title="Onboarding indisponivel para revisao"
        description="O back-office nao recebeu a leitura canonica do backend. Em fail-closed, a pagina nao assume um resumo local."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem resumo canonico" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o estado operacional do onboarding.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a prontidao do onboarding ao backend</h2>
            <p>
              Esta pagina agora depende do endpoint canonico `GET /onboarding/readiness`. Sem carga valida do backend,
              a leitura da primeira emissao permanece bloqueada para evitar drift.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildOnboardingCatalogView(catalog);
  const checklist = scenario.checklist;

  return (
    <AppShell
      eyebrow="Onboarding - PRD 13.12"
      title="Prontidao objetiva para a primeira emissao"
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={scenario.summary.status === "ready" ? "ok" : "warn"}
            label={scenario.summary.status === "ready" ? "Emissao liberada" : "Emissao bloqueada"}
          />
          <p>{scenario.summary.timeTargetLabel} para o administrador inicial.</p>
        </div>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Resumo</span>
          <h2>{scenario.summary.title}</h2>
          <p>O wizard ja traduz os bloqueios tecnicos em passos legiveis para operacao de V1.</p>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Meta operacional</span>
          <strong>{scenario.summary.timeTargetLabel}</strong>
          <p>O recorte de V1 deixa explicito se o onboarding respeitou a janela de 1 hora prevista no PRD.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.summary.blockingSteps.length === 0
              ? "Sem bloqueios pendentes"
              : `${scenario.summary.blockingSteps.length} passos bloqueantes`}
          </strong>
          <ul>
            {scenario.summary.blockingSteps.length === 0 ? (
              <li>Configuracao minima atendida para seguir com a primeira emissao.</li>
            ) : (
              scenario.summary.blockingSteps.map((step: string) => <li key={step}>{step}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Leitura de V1</span>
          <strong>Fluxo pensado para operacao assistida</strong>
          <p>
            Esta tela agora materializa o resumo vindo do backend sem duplicar a regra de prontidao no cliente.
          </p>
        </article>
      </section>

      {checklist ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Wizard persistido</span>
            <h2>Atualizar prerequisitos no banco</h2>
            <p>
              Os campos abaixo escrevem o estado real do tenant autenticado em `POST /onboarding/readiness`.
            </p>
          </div>
          <form className="form-grid" action={`${publicApiBaseUrl}/onboarding/readiness`} method="post">
            <label className="toggle-field">
              <input
                defaultChecked={checklist.organizationProfileCompleted}
                name="organizationProfileCompleted"
                type="checkbox"
              />
              <span>Perfil da organizacao concluido</span>
            </label>
            <label className="toggle-field">
              <input
                defaultChecked={checklist.primarySignatoryReady}
                name="primarySignatoryReady"
                type="checkbox"
              />
              <span>Signatario principal liberado</span>
            </label>
            <label className="toggle-field">
              <input
                defaultChecked={checklist.certificateNumberingConfigured}
                name="certificateNumberingConfigured"
                type="checkbox"
              />
              <span>Numeracao de certificados configurada</span>
            </label>
            <label className="toggle-field">
              <input defaultChecked={checklist.scopeReviewCompleted} name="scopeReviewCompleted" type="checkbox" />
              <span>Revisao de escopo concluida</span>
            </label>
            <label className="toggle-field">
              <input defaultChecked={checklist.publicQrConfigured} name="publicQrConfigured" type="checkbox" />
              <span>QR publico configurado</span>
            </label>
            <input type="hidden" name="redirectTo" value="http://127.0.0.1:3002/onboarding" />
            <div className="button-row">
              <button className="button-primary" type="submit">
                Salvar onboarding
              </button>
              <a className="button-secondary" href="/auth/login">
                Trocar sessao
              </a>
            </div>
          </form>
        </section>
      ) : null}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Alternar entre pronto e bloqueado</h2>
          <p>Os links abaixo ajudam a validar a leitura operacional usando a catalogacao canonica do backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/onboarding?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.description}
            cta="Abrir cenario"
          />
        ))}
      </section>
    </AppShell>
  );
}

function resolvePublicApiBaseUrl() {
  return process.env.AFERE_PUBLIC_API_BASE_URL ?? process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
}
