import { loadProcedureRegistryCatalog } from "@/src/registry/procedure-registry-api";
import { buildProcedureRegistryCatalogView } from "@/src/registry/procedure-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    procedure?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Procedimento vigente";
    case "attention":
      return "Procedimento em atencao";
    case "blocked":
      return "Procedimento obsoleto";
    default:
      return status;
  }
}

export default async function ProcedureRegistryPage(props: PageProps) {
  const catalog = await loadProcedureRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    procedureId: props.searchParams?.procedure,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Cadastros - procedimentos"
        title="Lista de procedimentos indisponivel"
        description="O back-office nao recebeu o payload canonico de procedimentos. Em fail-closed, nenhuma revisao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a carteira de procedimentos.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar procedimentos ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/procedures`. Sem resposta valida, o web nao
              assume vigencia, revisao ou obsolescencia dos procedimentos.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildProcedureRegistryCatalogView(catalog);
  const detail = scenario.detail;
  const selectedProcedure = scenario.selectedProcedure;

  return (
    <AppShell
      eyebrow="Cadastros - procedimentos"
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
          <span className="eyebrow">Vigentes</span>
          <strong>{scenario.summary.activeCount} procedimento(s)</strong>
          <p>{scenario.summary.attentionCount} em atencao e {scenario.summary.obsoleteCount} obsoleto(s).</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{selectedProcedure.code} rev.{selectedProcedure.revisionLabel}</strong>
          <p>{selectedProcedure.title}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Vigencia</span>
          <strong>{selectedProcedure.effectiveSinceLabel}</strong>
          <p>{selectedProcedure.effectiveUntilLabel ?? "Sem encerramento registrado"}</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista versionada</span>
          <h2>Procedimentos vigentes e obsoletos</h2>
          <p>A lista abaixo abre o detalhe do procedimento selecionado no mesmo catalogo canonico.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.procedureId}
            href={`/registry/procedures?scenario=${scenario.id}&procedure=${item.procedureId}`}
            eyebrow={item.procedureId === selectedProcedure.procedureId ? "Selecionado" : item.code}
            title={`${item.title} · rev.${item.revisionLabel}`}
            description={`${item.typeLabel} · ${item.lifecycleLabel} · ${item.usageLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir procedimento"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe do procedimento</span>
          <h2>{detail.title}</h2>
          <p>O painel abaixo resume escopo, ambiente, politica de curva e documentos relacionados do item selecionado.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Escopo</span>
            <strong>{detail.noticeLabel}</strong>
            <p>{detail.scopeLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Ambiente e curva</span>
            <strong>{detail.environmentRangeLabel}</strong>
            <p>{detail.curvePolicyLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Padrões e aprovacao</span>
            <strong>{detail.standardsPolicyLabel}</strong>
            <p>{detail.approvalLabel}</p>
          </article>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Documentos relacionados</span>
          <strong>{detail.relatedDocuments.length} item(ns)</strong>
          <ul>
            {detail.relatedDocuments.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {detail.blockers.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {detail.blockers.length === 0 ? <li>Sem bloqueios adicionais neste cenario.</li> : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{detail.warnings.length} warning(s)</strong>
          <ul>
            {detail.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {detail.warnings.length === 0 ? <li>Sem warnings adicionais neste cenario.</li> : null}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas ao procedimento</h2>
          <p>Use os atalhos abaixo para voltar ao contexto operacional que reutiliza o procedimento selecionado.</p>
        </div>
      </section>

      <section className="nav-grid">
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao consolidada"
            description="Voltar ao workspace que compartilha o mesmo contexto operacional do procedimento."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Conferir a OS canônica que reaproveita este procedimento."
            cta="Abrir OS"
          />
        ) : null}
        {detail.links.dryRunScenarioId ? (
          <NavCard
            href={`/emission/dry-run?scenario=${detail.links.dryRunScenarioId}`}
            eyebrow="Dry-run"
            title="Abrir dry-run de emissao"
            description="Inspecionar o recorte de emissao que usa o mesmo procedimento selecionado."
            cta="Abrir dry-run"
          />
        ) : null}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto da carteira</h2>
          <p>Use os cenarios abaixo para revisar baseline, revisao preventiva e consulta de revisoes obsoletas sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/registry/procedures?scenario=${item.id}&procedure=${item.selectedProcedure.procedureId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir procedimentos"
          />
        ))}
      </section>
    </AppShell>
  );
}
