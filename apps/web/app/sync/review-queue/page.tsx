import { loadOfflineSyncCatalog } from "@/src/sync/offline-sync-api";
import { buildOfflineSyncCatalogView } from "@/src/sync/offline-sync-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    item?: string;
    conflict?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Sync pronto";
    case "attention":
      return "Triagem pendente";
    case "blocked":
      return "Sync bloqueado";
  }
}

function conflictStatusLabel(status: "resolved" | "open" | "escalated"): string {
  switch (status) {
    case "resolved":
      return "Resolvido";
    case "open":
      return "Aberto";
    case "escalated":
      return "Escalado";
  }
}

function outboxStatusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Pronto para upload";
    case "attention":
      return "Retido para triagem";
    case "blocked":
      return "Bloqueado";
  }
}

export default async function OfflineSyncReviewQueuePage(props: PageProps) {
  const catalog = await loadOfflineSyncCatalog({
    scenarioId: props.searchParams?.scenario,
    itemId: props.searchParams?.item,
    conflictId: props.searchParams?.conflict,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Sync - revisao humana"
        title="Fila de sync indisponivel"
        description="O back-office nao recebeu o payload canonico do sync offline. Em fail-closed, nenhuma decisao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a triagem humana do sync.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a fila de sync ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /sync/review-queue`. Sem resposta valida, a web nao
              inventa decisao humana, vencedor de conflito ou liberacao de emissao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildOfflineSyncCatalogView(catalog);
  const outboxItem = scenario.selectedOutboxItem;
  const conflict = scenario.selectedConflict;
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Sync - revisao humana"
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
          <strong>{scenario.summary.queuedItems} lote(s) na outbox</strong>
          <p>
            {scenario.summary.openConflictCount} conflito(s) aberto(s), {scenario.summary.escalatedConflictCount} em
            escala regulatoria e {scenario.summary.blockedWorkOrders} OS bloqueada(s).
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Outbox selecionada</span>
          <strong>{outboxItem.workOrderNumber}</strong>
          <p>
            {outboxItem.deviceLabel} · {outboxStatusLabel(outboxItem.status)}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Conflito selecionado</span>
          <strong>{conflict.class}</strong>
          <p>
            {conflictStatusLabel(conflict.status)} · {conflict.deadlineLabel}
          </p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.outboxItems.map((item) => (
          <NavCard
            key={item.itemId}
            href={`/sync/review-queue?scenario=${scenario.id}&item=${item.itemId}&conflict=${conflict.conflictId}`}
            eyebrow={item.itemId === outboxItem.itemId ? "Outbox ativa" : item.deviceLabel}
            title={item.workOrderNumber}
            description={`${item.eventCount} envelope(s) · ${item.networkLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={outboxStatusLabel(item.status)}
            cta="Abrir outbox"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Outbox offline</span>
          <h2>{outboxItem.workOrderNumber} no device</h2>
          <p>{outboxItem.nextActionLabel}</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Rede e storage</span>
            <strong>{outboxItem.networkLabel}</strong>
            <p>{outboxItem.storageLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Fila local</span>
            <strong>{outboxItem.eventCount} envelope(s)</strong>
            <p>
              {outboxItem.replayProtectedCount} com replay protection · ultima tentativa {outboxItem.lastAttemptLabel}
            </p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Bloqueios e avisos</span>
            <strong>{outboxItem.blockers.length} bloqueio(s)</strong>
            <p>{outboxItem.warnings.length} warning(s) associados ao lote local.</p>
          </article>
        </div>

        <ul className="check-list">
          {outboxItem.envelopes.map((event) => (
            <li key={event.eventId}>
              <div className="metric-row">
                <strong>
                  {event.aggregateLabel} · Lamport {event.lamport}
                </strong>
                <StatusPill tone={event.state === "uploaded" || event.state === "deduplicated" ? "ok" : "warn"} label={event.state} />
              </div>
              <p>
                {event.eventKind} · {event.payloadDigest} · replay protection{" "}
                {event.replayProtected ? "confirmada" : "ausente"}.
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="nav-grid">
        {scenario.conflicts.map((item) => (
          <NavCard
            key={item.conflictId}
            href={`/sync/review-queue?scenario=${scenario.id}&item=${outboxItem.itemId}&conflict=${item.conflictId}`}
            eyebrow={item.conflictId === conflict.conflictId ? "Conflito ativo" : item.class}
            title={item.workOrderNumber}
            description={`${item.summaryLabel} · ${item.responsibleLabel}`}
            statusTone={item.status === "resolved" ? "ok" : "warn"}
            statusLabel={conflictStatusLabel(item.status)}
            cta="Abrir conflito"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Decisao</span>
          <strong>{detail.recommendedDecisionLabel}</strong>
          <p>{detail.summary}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Responsavel e SLA</span>
          <strong>{detail.responsibleLabel}</strong>
          <p>
            {detail.queueSlaLabel} · prazo {detail.decisionDeadlineLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Emissao</span>
          <strong>{detail.blockedForEmission ? "Bloqueada por arquitetura" : "Sem bloqueio ativo"}</strong>
          <p>
            {detail.regulatorEscalationRequired
              ? "A decisao depende de interpretacao regulatoria antes de liberar qualquer emissao."
              : "A decisao pode ser concluida no back-office sem escala regulatoria obrigatoria."}
          </p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Opcoes de resolucao</span>
          <strong>{detail.resolutionOptions.filter((option) => option.allowed).length} opcao(oes) liberada(s)</strong>
          <ul>
            {detail.resolutionOptions.map((option) => (
              <li key={option.action}>
                {option.label}: {option.detail} {option.allowed ? "Liberada." : "Bloqueada."}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Auditoria</span>
          <strong>{detail.auditRequirements.length} requisito(s) de evidencia</strong>
          <ul>
            {detail.auditRequirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Justificativa modelo</span>
          <strong>{detail.title}</strong>
          <p>{detail.rationaleTemplate}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {detail.blockers.length === 0 ? <li>Sem bloqueios adicionais neste cenario.</li> : null}
            {detail.blockers.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{detail.warnings.length} warning(s)</strong>
          <ul>
            {detail.warnings.length === 0 ? <li>Sem warnings adicionais neste cenario.</li> : null}
            {detail.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Eventos vencedores</span>
          <strong>{detail.winningEventId ?? "Sem evento vencedor"}</strong>
          <p>{detail.losingEventId ? `Evento perdedor: ${detail.losingEventId}` : "Nenhum evento perdedor explicito neste cenario."}</p>
        </article>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
          eyebrow="Workspace"
          title="Abrir prontidao consolidada"
          description="Voltar ao recorte operacional que sobe o bloqueio de sync para a emissao."
          cta="Abrir workspace"
        />
        <NavCard
          href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}`}
          eyebrow="OS"
          title="Abrir revisao tecnica da OS"
          description="Conferir a OS bloqueada ou em atencao pelo conflito de sync."
          cta="Abrir OS"
        />
        <NavCard
          href={`/quality/audit-trail?scenario=${detail.links.auditTrailScenarioId}`}
          eyebrow="Auditoria"
          title="Abrir trilha de auditoria"
          description="Inspecionar a hash-chain e os eventos cruzados desta decisao de sync."
          cta="Abrir trilha"
        />
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/sync/review-queue?scenario=${item.id}&item=${item.selectedOutboxItem.itemId}&conflict=${item.selectedConflict.conflictId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir sync"
          />
        ))}
      </section>
    </AppShell>
  );
}
