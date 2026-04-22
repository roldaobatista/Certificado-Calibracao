import { loadComplaintCatalog } from "@/src/quality/complaint-registry-api";
import { buildComplaintCatalogView } from "@/src/quality/complaint-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    complaint?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Reclamacao encerrada";
    case "attention":
      return "Resposta em andamento";
    case "blocked":
      return "Resposta critica";
    default:
      return status;
  }
}

function actionLabel(status: "complete" | "pending" | "blocked"): string {
  switch (status) {
    case "complete":
      return "Concluido";
    case "pending":
      return "Pendente";
    case "blocked":
      return "Bloqueado";
    default:
      return status;
  }
}

function mapComplaintScenarioToQualityHubScenario(
  scenarioId: "open-follow-up" | "critical-response" | "resolved-history",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "critical-response":
      return "critical-response";
    case "resolved-history":
      return "stable-baseline";
    case "open-follow-up":
    default:
      return "operational-attention";
  }
}

export default async function ComplaintPage(props: PageProps) {
  const catalog = await loadComplaintCatalog({
    scenarioId: props.searchParams?.scenario,
    complaintId: props.searchParams?.complaint,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Qualidade - reclamacoes"
        title="Modulo de reclamacoes indisponivel"
        description="O back-office nao recebeu o payload canonico de reclamacoes. Em fail-closed, nenhuma resposta, prazo ou reemissao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o modulo de reclamacoes.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar reclamacoes ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/complaints`. Sem resposta valida, o web nao
              assume relato, prazo de resposta, vinculo a NC ou gatilho de reemissao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildComplaintCatalogView(catalog);
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Qualidade - reclamacoes"
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
          <strong>{scenario.summary.openCount} reclamacao(oes) aberta(s)</strong>
          <p>
            {scenario.summary.overdueCount} vencida(s), {scenario.summary.reissuePendingCount} com reemissao pendente
            e {scenario.summary.resolvedLast30d} resolvida(s) no recorte.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionada</span>
          <strong>{detail.title}</strong>
          <p>{detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Prazo de resposta</span>
          <strong>{detail.responseDeadlineLabel}</strong>
          <p>
            {detail.ownerLabel} · canal {detail.channelLabel}
          </p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.complaintId}
            href={`/quality/complaints?scenario=${scenario.id}&complaint=${item.complaintId}`}
            eyebrow={item.complaintId}
            title={item.summary}
            description={`${item.customerName} · ${item.channelLabel} · ${item.severityLabel} · ${item.ownerLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir reclamacao"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Cliente e canal</span>
          <strong>{detail.customerName}</strong>
          <p>
            {detail.channelLabel} · recebida em {detail.receivedAtLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Relato</span>
          <strong>Contexto do cliente</strong>
          <p>{detail.narrative}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">NC e reemissao</span>
          <strong>{detail.linkedNonconformityLabel}</strong>
          <p>{detail.reissueReasonLabel ? `Motivo de reemissao sugerido: ${detail.reissueReasonLabel}.` : "Sem gatilho de reemissao formal neste recorte."}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Checklist de acoes</span>
          <strong>{detail.actions.length} etapa(s)</strong>
          <ul>
            {detail.actions.map((item) => (
              <li key={item.key}>
                {item.label} · {actionLabel(item.status)} · {item.detail}
              </li>
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

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Evidencia</span>
          <h2>Dossie minimo da tratativa</h2>
          <p>{detail.evidenceLabel}</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapComplaintScenarioToQualityHubScenario(scenario.id)}&module=complaints`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado da Qualidade mantendo a reclamacao como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir workspace operacional"
            description="Voltar ao recorte operacional associado a esta reclamacao."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.auditTrailScenarioId ? (
          <NavCard
            href={`/quality/audit-trail?scenario=${detail.links.auditTrailScenarioId}`}
            eyebrow="Auditoria"
            title="Abrir trilha de auditoria"
            description="Inspecionar a cadeia append-only relacionada a esta reclamacao."
            cta="Abrir trilha"
          />
        ) : null}
        {detail.links.nonconformityScenarioId && detail.links.nonconformityId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${detail.links.nonconformityScenarioId}&nc=${detail.links.nonconformityId}`}
            eyebrow="NC"
            title="Abrir nao conformidade"
            description="Conferir a NC vinculada a esta reclamacao."
            cta="Abrir NC"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Inspecionar a OS vinculada ao contexto desta reclamacao."
            cta="Abrir OS"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/complaints?scenario=${item.id}&complaint=${item.selectedComplaint.complaintId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir reclamacoes"
          />
        ))}
      </section>
    </AppShell>
  );
}
