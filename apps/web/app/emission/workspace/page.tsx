import { loadEmissionWorkspaceCatalog } from "@/src/emission/emission-workspace-api";
import { buildEmissionWorkspaceCatalogView } from "@/src/emission/emission-workspace-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Workspace pronto";
    case "attention":
      return "Workspace com atencao";
    case "blocked":
      return "Workspace bloqueado";
    default:
      return status;
  }
}

function mapWorkspaceScenarioToPreviewScenario(
  workspaceScenarioId: string,
  dryRunScenarioId: string,
): string {
  if (dryRunScenarioId) {
    return dryRunScenarioId;
  }

  switch (workspaceScenarioId) {
    case "release-blocked":
      return "type-c-blocked";
    default:
      return "type-b-ready";
  }
}

function mapWorkspaceScenarioToQueueScenario(workspaceScenarioId: string): string {
  switch (workspaceScenarioId) {
    case "team-attention":
      return "attention-required";
    case "release-blocked":
      return "mfa-blocked";
    default:
      return "approved-ready";
  }
}

export default async function EmissionWorkspacePage(props: PageProps) {
  const catalog = await loadEmissionWorkspaceCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - workspace"
        title="Workspace indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico consolidado. Em fail-closed, nenhuma prontidao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o workspace operacional.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a consolidacao operacional ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /emission/workspace`. Sem resposta valida do backend, o
              web nao consolida auth, onboarding, equipe, dry-run e workflow por conta propria.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildEmissionWorkspaceCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Emissao - workspace"
      title={scenario.summary.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill tone={statusTone(scenario.summary.status)} label={statusLabel(scenario.summary.status)} />
          <p>{scenario.summary.recommendedAction}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Prontidao</span>
          <strong>{scenario.summary.readyModules} modulo(s) prontos</strong>
          <p>{scenario.summary.attentionModules} em atencao e {scenario.summary.blockedModules} bloqueado(s).</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Emissao final</span>
          <strong>{scenario.summary.readyToEmit ? "Pronta para emitir" : "Ainda nao pronta para emitir"}</strong>
          <p>
            {scenario.summary.readyToEmit
              ? "Todos os gates relevantes estao verdes para concluir a emissao."
              : "A operacao ainda precisa concluir as etapas restantes antes da emissao oficial."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima acao</span>
          <strong>{scenario.summary.recommendedAction}</strong>
          <p>Use os modulos abaixo para abrir exatamente a leitura canonica relacionada a cada gate.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Modulos</span>
          <h2>Entradas canonicas que sustentam a emissao</h2>
          <p>O workspace apenas consolida os sinais. Cada modulo continua com rota e leitura dedicadas no backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.modules.map((module) => (
          <NavCard
            key={module.key}
            href={module.href}
            eyebrow={module.title}
            title={statusLabel(module.status)}
            description={module.detail}
            statusTone={statusTone(module.status)}
            statusLabel={statusLabel(module.status)}
            cta="Abrir modulo"
          />
        ))}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Previa e assinatura</span>
          <h2>Conferir o certificado e a fila final</h2>
          <p>O workspace aponta para a previa integral e para a fila de assinatura coerentes com este cenario.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/certificate-preview?scenario=${mapWorkspaceScenarioToPreviewScenario(scenario.id, scenario.references.dryRunScenarioId)}`}
          eyebrow="Certificado"
          title="Abrir previa integral"
          description="Revisar os campos que o operador precisa conferir antes da assinatura final."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir previa"
        />
        <NavCard
          href={`/emission/signature-queue?scenario=${mapWorkspaceScenarioToQueueScenario(scenario.id)}`}
          eyebrow="Assinatura"
          title="Abrir fila canonica"
          description="Inspecionar os itens pendentes e a tela final de assinatura antes da emissao."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir fila"
        />
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.summary.blockers.length === 0
              ? "Nenhum bloqueio consolidado"
              : `${scenario.summary.blockers.length} bloqueio(s) consolidado(s)`}
          </strong>
          <ul>
            {scenario.summary.blockers.length === 0 ? (
              <li>O workspace nao encontrou gate critico bloqueando este cenario.</li>
            ) : (
              scenario.summary.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>
            {scenario.summary.warnings.length === 0
              ? "Sem warnings ativos"
              : `${scenario.summary.warnings.length} warning(s) operacional(is)`}
          </strong>
          <ul>
            {scenario.summary.warnings.length === 0 ? (
              <li>Nenhum warning complementar foi agregado neste cenario.</li>
            ) : (
              scenario.summary.warnings.map((warning) => <li key={warning}>{warning}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proximas acoes</span>
          <strong>{scenario.nextActions.length} passo(s) sugerido(s)</strong>
          <ul>
            {scenario.nextActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do workspace</h2>
          <p>Use os atalhos abaixo para revisar baseline, risco preventivo e bloqueio fail-closed sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/workspace?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir workspace"
          />
        ))}
      </section>
    </AppShell>
  );
}
