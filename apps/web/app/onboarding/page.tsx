import { listOnboardingScenarios, resolveOnboardingScenario } from "@/src/onboarding/onboarding-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export default function OnboardingPage(props: PageProps) {
  const scenario = resolveOnboardingScenario(props.searchParams?.scenario);
  const scenarios = listOnboardingScenarios();

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
              scenario.summary.blockingSteps.map((step) => <li key={step}>{step}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Leitura de V1</span>
          <strong>Fluxo pensado para operacao assistida</strong>
          <p>
            Esta tela ainda usa cenarios guiados, mas o layout ja esta pronto para receber respostas reais da API sem remodelar a UX.
          </p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Alternar entre pronto e bloqueado</h2>
          <p>Os links abaixo ajudam a validar o tom do produto antes de acoplar fetch e persistencia reais.</p>
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
