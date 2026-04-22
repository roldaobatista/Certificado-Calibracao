import { loadServiceOrderReviewCatalog } from "@/src/emission/service-order-review-api";
import { buildServiceOrderReviewCatalogView } from "@/src/emission/service-order-review-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    item?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Revisao pronta";
    case "attention":
      return "Revisao em atencao";
    case "blocked":
      return "Revisao bloqueada";
    default:
      return status;
  }
}

function itemStatusLabel(
  status: "in_execution" | "awaiting_review" | "awaiting_signature" | "emitted" | "blocked",
): string {
  switch (status) {
    case "in_execution":
      return "Em execucao";
    case "awaiting_review":
      return "Aguardando revisao";
    case "awaiting_signature":
      return "Aguardando assinatura";
    case "emitted":
      return "Emitida";
    case "blocked":
      return "Bloqueada";
    default:
      return status;
  }
}

function timelineLabel(status: "complete" | "current" | "pending"): string {
  switch (status) {
    case "complete":
      return "Concluida";
    case "current":
      return "Atual";
    case "pending":
      return "Pendente";
    default:
      return status;
  }
}

function actionLabel(
  action: "return_to_technician" | "approve_review" | "open_preview" | "open_signature_queue",
): string {
  switch (action) {
    case "return_to_technician":
      return "Devolver ao tecnico";
    case "approve_review":
      return "Aprovar revisao";
    case "open_preview":
      return "Abrir previa";
    case "open_signature_queue":
      return "Abrir fila de assinatura";
    default:
      return action;
  }
}

export default async function ServiceOrderReviewPage(props: PageProps) {
  const catalog = await loadServiceOrderReviewCatalog({
    scenarioId: props.searchParams?.scenario,
    itemId: props.searchParams?.item,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - OS e revisao tecnica"
        title="OS indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico da lista e do detalhe da OS. Em fail-closed, nenhuma aprovacao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a lista e a revisao canônica da OS.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a OS canônica ao backend</h2>
            <p>
              Esta pagina depende do endpoint `GET /emission/service-order-review`. Sem resposta valida, o web nao
              inventa linha do tempo, checklist tecnico ou acoes de aprovacao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildServiceOrderReviewCatalogView(catalog);
  const selectedItem = scenario.selectedItem;

  return (
    <AppShell
      eyebrow="Emissao - OS e revisao tecnica"
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
          <span className="eyebrow">Lista</span>
          <strong>{scenario.summary.totalCount} OS no painel</strong>
          <p>
            {scenario.summary.awaitingReviewCount} aguardando revisao, {scenario.summary.awaitingSignatureCount} aguardando assinatura.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">OS selecionada</span>
          <strong>{selectedItem.workOrderNumber}</strong>
          <p>
            {selectedItem.customerName} · {selectedItem.equipmentLabel}
          </p>
          <div className="chip-list">
            <span className="chip">{selectedItem.technicianName}</span>
            <span className="chip">{selectedItem.updatedAtLabel}</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Status da revisao</span>
          <strong>{statusLabel(scenario.detail.status)}</strong>
          <p>{scenario.detail.statusLine}</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Ordens de servico</span>
          <h2>Lista canonica do back-office</h2>
          <p>As OS abaixo refletem a leitura canônica de lista e permitem alternar o detalhe da revisão pela querystring.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.itemId}
            href={`/emission/service-order-review?scenario=${scenario.id}&item=${item.itemId}`}
            eyebrow={item.itemId === selectedItem.itemId ? "Selecionada" : "OS"}
            title={item.workOrderNumber}
            description={`${item.customerName} · ${item.technicianName} · atualizada ${item.updatedAtLabel}`}
            statusTone={statusTone(item.status === "blocked" ? "blocked" : item.status === "awaiting_review" ? scenario.detail.status : "ready")}
            statusLabel={itemStatusLabel(item.status)}
            cta="Abrir detalhe"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe da OS</span>
          <h2>{scenario.detail.title}</h2>
          <p>O painel abaixo resume linha do tempo, dados de execução e o checklist que sustentam a revisão técnica.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Linha do tempo</span>
            <strong>{scenario.detail.statusLine}</strong>
            <ul>
              {scenario.detail.timeline.map((step) => (
                <li key={step.key}>
                  {step.label}: {step.timestampLabel} ({timelineLabel(step.status)})
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Dados da execucao</span>
            <strong>{scenario.detail.procedureLabel}</strong>
            <ul>
              <li>Padroes: {scenario.detail.standardsLabel}</li>
              <li>Ambiente: {scenario.detail.environmentLabel}</li>
              <li>Pontos da curva: {scenario.detail.curvePointsLabel}</li>
              <li>Evidencias: {scenario.detail.evidenceLabel}</li>
              <li>Incerteza: {scenario.detail.uncertaintyLabel}</li>
              <li>Conformidade: {scenario.detail.conformityLabel}</li>
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Responsabilidades</span>
            <strong>{scenario.detail.assignedReviewerLabel}</strong>
            <p>{scenario.detail.statusLine}</p>
            <div className="chip-list">
              <span className="chip">Executor: {scenario.detail.executorLabel}</span>
              <span className="chip">Revisor: {scenario.detail.assignedReviewerLabel}</span>
            </div>
          </article>
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Metricas</span>
          <h2>Resumo tecnico da execucao</h2>
          <p>Essas metricas ajudam a contextualizar a analise do revisor sem substituir a leitura integral da previa.</p>
        </div>

        <div className="detail-grid">
          {scenario.detail.metrics.map((metric) => (
            <article className="detail-card" key={metric.label}>
              <span className="eyebrow">{metric.label}</span>
              <strong>{metric.value}</strong>
              <StatusPill
                tone={metric.tone === "ok" ? "ok" : metric.tone === "warn" ? "warn" : "neutral"}
                label={metric.tone === "ok" ? "OK" : metric.tone === "warn" ? "Atencao" : "Info"}
              />
            </article>
          ))}
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Checklist</span>
          <h2>Checklist de revisao tecnica</h2>
          <p>O checklist abaixo explica por que a OS pode ser aprovada, exige atencao complementar ou segue bloqueada.</p>
        </div>

        <ul className="check-list">
          {scenario.detail.checklist.map((item) => (
            <li key={`${scenario.detail.itemId}-${item.label}`}>
              <div className="metric-row">
                <strong>{item.label}</strong>
                <StatusPill
                  tone={item.status === "passed" ? "ok" : "warn"}
                  label={item.status === "passed" ? "Passou" : item.status === "pending" ? "Pendente" : "Falhou"}
                />
              </div>
              <p>{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Comentario de revisao</span>
          <strong>{scenario.detail.commentDraft.length > 0 ? "Rascunho disponivel" : "Sem comentario registrado"}</strong>
          <p>{scenario.detail.commentDraft || "Nenhum comentario de revisao foi registrado para esta OS neste cenario."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Acoes disponiveis</span>
          <strong>{scenario.detail.allowedActions.length} acao(oes) mapeada(s)</strong>
          <div className="chip-list">
            {scenario.detail.allowedActions.map((action) => (
              <span className="chip" key={action}>
                {actionLabel(action)}
              </span>
            ))}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios e warnings</span>
          <strong>
            {scenario.detail.blockers.length} bloqueio(s) · {scenario.detail.warnings.length} warning(s)
          </strong>
          <ul>
            {scenario.detail.blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
            {scenario.detail.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
            {scenario.detail.blockers.length === 0 && scenario.detail.warnings.length === 0 ? (
              <li>Sem bloqueios ou warnings adicionais neste cenario.</li>
            ) : null}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas a esta OS</h2>
          <p>Use as rotas abaixo para voltar aos sinais canônicos que sustentam esta revisão.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/workspace?scenario=${scenario.detail.links.workspaceScenarioId}`}
          eyebrow="Workspace"
          title="Abrir prontidao consolidada"
          description="Voltar ao workspace operacional agregado desta OS."
          cta="Abrir workspace"
        />
        {scenario.detail.links.previewScenarioId ? (
          <NavCard
            href={`/emission/certificate-preview?scenario=${scenario.detail.links.previewScenarioId}`}
            eyebrow="Previa"
            title="Abrir previa do certificado"
            description="Conferir a peca canônica derivada desta mesma OS."
            cta="Abrir previa"
          />
        ) : null}
        {scenario.detail.links.reviewSignatureScenarioId ? (
          <NavCard
            href={`/emission/review-signature?scenario=${scenario.detail.links.reviewSignatureScenarioId}`}
            eyebrow="Workflow"
            title="Abrir workflow de revisao"
            description="Inspecionar os checks de segregacao e elegibilidade do fluxo."
            cta="Abrir workflow"
          />
        ) : null}
        {scenario.detail.links.signatureQueueScenarioId ? (
          <NavCard
            href={`/emission/signature-queue?scenario=${scenario.detail.links.signatureQueueScenarioId}`}
            eyebrow="Fila"
            title="Abrir fila de assinatura"
            description="Seguir para a etapa final da emissao quando a OS ja estiver aprovada."
            cta="Abrir fila"
          />
        ) : null}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto da OS</h2>
          <p>Os cenarios abaixo permitem revisar baseline, atencao complementar e bloqueio sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/service-order-review?scenario=${item.id}&item=${item.selectedItem.itemId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir OS"
          />
        ))}
      </section>
    </AppShell>
  );
}
