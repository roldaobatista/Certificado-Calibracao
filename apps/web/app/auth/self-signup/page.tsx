import { listSelfSignupScenarios, resolveSelfSignupScenario } from "@/src/auth/self-signup-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export default function SelfSignupPage(props: PageProps) {
  const scenario = resolveSelfSignupScenario(props.searchParams?.scenario);
  const scenarios = listSelfSignupScenarios();

  return (
    <AppShell
      eyebrow="Auth - PRD 13.11"
      title="Auto-cadastro com SSO e MFA visiveis"
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={scenario.viewModel.status === "ready" ? "ok" : "warn"}
            label={scenario.viewModel.status === "ready" ? "Fluxo liberado" : "Fluxo bloqueado"}
          />
          <p>
            O cliente web so materializa o checklist. A decisao regulatoria continua no backend e nos contratos compartilhados.
          </p>
        </div>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Estado atual</span>
          <h2>Metodos apresentados ao laboratorio</h2>
          <p>Todos os provedores obrigatorios aparecem lado a lado com a etapa de MFA para perfis privilegiados.</p>
        </div>
        <StatusPill
          tone={scenario.viewModel.showMfaStep ? "neutral" : "warn"}
          label={scenario.viewModel.showMfaStep ? "MFA em destaque" : "Sem MFA nesta rota"}
        />
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Disponiveis</span>
          <strong>{scenario.viewModel.visibleMethods.length} metodos visiveis</strong>
          <div className="chip-list">
            {scenario.viewModel.visibleMethods.map((method) => (
              <span className="chip" key={method}>
                {method}
              </span>
            ))}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Pendencias</span>
          <strong>
            {scenario.viewModel.missingMethods.length === 0
              ? "Nenhum provedor faltante"
              : `${scenario.viewModel.missingMethods.length} lacunas de habilitacao`}
          </strong>
          <div className="chip-list">
            {scenario.viewModel.missingMethods.length === 0 ? (
              <span className="chip">Stack de login completa</span>
            ) : (
              scenario.viewModel.missingMethods.map((method) => (
                <span className="chip chip--warn" key={method}>
                  {method}
                </span>
              ))
            )}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Risco regulatorio</span>
          <strong>{scenario.viewModel.showMfaStep ? "MFA mantido no fluxo" : "MFA nao aplicavel"}</strong>
          <p>
            Signatarios e administradores seguem com a etapa de MFA em destaque para impedir configuracao incompleta antes da operacao.
          </p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar contexto sem mexer em codigo</h2>
          <p>Use as rotas abaixo para validar o comportamento visual de cada estado-chave do onboarding de auth.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/auth/self-signup?scenario=${item.id}`}
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
