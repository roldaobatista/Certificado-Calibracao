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
  const catalog = await loadOnboardingCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
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
