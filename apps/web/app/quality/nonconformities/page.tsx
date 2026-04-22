import { loadNonconformityCatalog } from "@/src/quality/nonconformity-api";
import { buildNonconformityCatalogView } from "@/src/quality/nonconformity-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    nc?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "NC encerrada";
    case "attention":
      return "NC em acompanhamento";
    case "blocked":
      return "NC critica";
    default:
      return status;
  }
}

function mapNonconformityScenarioToQualityHubScenario(
  scenarioId: "open-attention" | "critical-response" | "resolved-history",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "critical-response":
      return "critical-response";
    case "resolved-history":
      return "stable-baseline";
    case "open-attention":
    default:
      return "operational-attention";
  }
}

export default async function NonconformityPage(props: PageProps) {
  const catalog = await loadNonconformityCatalog({
    scenarioId: props.searchParams?.scenario,
    ncId: props.searchParams?.nc,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Qualidade - nao conformidades"
        title="Modulo de NC indisponivel"
        description="O back-office nao recebeu o payload canonico de nao conformidades. Em fail-closed, nenhuma NC local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o modulo de nao conformidades.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar NCs ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/nonconformities`. Sem resposta valida, o web nao
              assume severidade, responsavel ou prazo de nenhuma NC.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildNonconformityCatalogView(catalog);
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Qualidade - nao conformidades"
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
          <span className="eyebrow">Resumo</span>
          <strong>{scenario.summary.openCount} NC(s) aberta(s)</strong>
          <p>
            {scenario.summary.criticalCount} critica(s) e {scenario.summary.closedCount} encerrada(s) no recorte atual.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionada</span>
          <strong>{detail.title}</strong>
          <p>{detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Responsavel e prazo</span>
          <strong>{detail.ownerLabel}</strong>
          <p>
            aberta em {detail.openedAtLabel} · prazo {detail.dueAtLabel}
          </p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.ncId}
            href={`/quality/nonconformities?scenario=${scenario.id}&nc=${item.ncId}`}
            eyebrow={item.ncId}
            title={item.summary}
            description={`${item.originLabel} · ${item.severityLabel} · ${item.ownerLabel} · ${item.ageLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir NC"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Origem e severidade</span>
          <strong>{detail.originLabel}</strong>
          <p>{detail.severityLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Causa e contenção</span>
          <strong>{detail.rootCauseLabel}</strong>
          <p>{detail.containmentLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Acao corretiva</span>
          <strong>{detail.correctiveActionLabel}</strong>
          <p>{detail.evidenceLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
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

        <article className="detail-card">
          <span className="eyebrow">Evidencia</span>
          <strong>{detail.evidenceLabel}</strong>
          <p>Use os atalhos abaixo para voltar ao fluxo, trilha ou procedimento relacionados.</p>
        </article>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapNonconformityScenarioToQualityHubScenario(scenario.id)}&module=nonconformities`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir a visao consolidada da Qualidade mantendo a NC como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao consolidada"
            description="Voltar ao recorte operacional associado a esta NC."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.auditTrailScenarioId ? (
          <NavCard
            href={`/quality/audit-trail?scenario=${detail.links.auditTrailScenarioId}`}
            eyebrow="Auditoria"
            title="Abrir trilha de auditoria"
            description="Inspecionar a cadeia append-only relacionada a esta NC."
            cta="Abrir trilha"
          />
        ) : null}
        {detail.links.procedureScenarioId ? (
          <NavCard
            href={`/registry/procedures?scenario=${detail.links.procedureScenarioId}`}
            eyebrow="Procedimento"
            title="Abrir lista versionada"
            description="Conferir o procedimento ligado a esta NC."
            cta="Abrir procedimento"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Inspecionar a OS vinculada ao contexto desta NC."
            cta="Abrir OS"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/nonconformities?scenario=${item.id}&nc=${item.selectedNc.ncId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir NCs"
          />
        ))}
      </section>
    </AppShell>
  );
}
