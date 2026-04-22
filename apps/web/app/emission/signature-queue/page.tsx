import { loadSignatureQueueCatalog } from "@/src/emission/signature-queue-api";
import { buildSignatureQueueCatalogView } from "@/src/emission/signature-queue-scenarios";
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
      return "Fila pronta";
    case "attention":
      return "Fila com atencao";
    case "blocked":
      return "Fila bloqueada";
    default:
      return status;
  }
}

function itemStatusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Pronto para assinar";
    case "attention":
      return "Conferir antes de assinar";
    case "blocked":
      return "Assinatura bloqueada";
    default:
      return status;
  }
}

function mapQueueScenarioToWorkspaceScenario(queueScenarioId: string): string {
  switch (queueScenarioId) {
    case "attention-required":
      return "team-attention";
    case "mfa-blocked":
      return "release-blocked";
    default:
      return "baseline-ready";
  }
}

function mapQueueScenarioToServiceOrderScenario(queueScenarioId: string): string {
  switch (queueScenarioId) {
    case "attention-required":
      return "history-pending";
    case "mfa-blocked":
      return "review-blocked";
    default:
      return "review-ready";
  }
}

function describeItemValidations(item: {
  validations: Array<{ status: "passed" | "warning" | "failed" }>;
}): string {
  const passed = item.validations.filter((validation) => validation.status === "passed").length;
  const warnings = item.validations.filter((validation) => validation.status === "warning").length;
  const failed = item.validations.filter((validation) => validation.status === "failed").length;

  return `${passed} check(s) verdes, ${warnings} warning(s) e ${failed} falha(s).`;
}

function requirementStatusLabel(status: "configured" | "missing"): string {
  return status === "configured" ? "Configurado" : "Pendente";
}

export default async function SignatureQueuePage(props: PageProps) {
  const catalog = await loadSignatureQueueCatalog({
    scenarioId: props.searchParams?.scenario,
    itemId: props.searchParams?.item,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - fila de assinatura"
        title="Fila indisponivel para assinatura"
        description="O back-office nao recebeu o payload canonico da fila. Em fail-closed, nenhum item foi considerado apto a assinar localmente."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a fila e a assinatura final.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a fila canônica ao backend</h2>
            <p>
              Esta pagina depende do endpoint `GET /emission/signature-queue`. Sem resposta valida, o web nao inventa
              itens assinaveis, pre-validacoes ou estado de re-autenticacao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildSignatureQueueCatalogView(catalog);
  const selectedItem = scenario.selectedItem;

  return (
    <AppShell
      eyebrow="Emissao - fila de assinatura"
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
          <span className="eyebrow">Pendencias</span>
          <strong>{scenario.summary.pendingCount} item(ns) na fila</strong>
          <p>
            {scenario.summary.batchReadyCount} pronto(s) para lote e pendencia mais antiga em{" "}
            {scenario.summary.oldestPendingLabel}.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Item selecionado</span>
          <strong>{selectedItem.workOrderNumber}</strong>
          <p>
            {selectedItem.customerName} · {selectedItem.equipmentLabel}
          </p>
          <div className="chip-list">
            <span className="chip">{selectedItem.instrumentType}</span>
            <span className="chip">{selectedItem.waitingSinceLabel}</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Assinatura final</span>
          <strong>{scenario.approval.canSign ? "Liberada para re-autenticacao" : "Mantida bloqueada"}</strong>
          <p>{scenario.approval.actionLabel}</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Fila</span>
          <h2>Itens pendentes de assinatura</h2>
          <p>Os itens abaixo refletem a leitura canônica da fila, com seleção do item ativo pela querystring.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.itemId}
            href={`/emission/signature-queue?scenario=${scenario.id}&item=${item.itemId}`}
            eyebrow={item.itemId === selectedItem.itemId ? "Selecionado" : "Pendente"}
            title={item.workOrderNumber}
            description={`${item.customerName} · ${item.waitingSinceLabel}. ${describeItemValidations(item)}`}
            statusTone={statusTone(item.status)}
            statusLabel={itemStatusLabel(item.status)}
            cta="Abrir assinatura"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Painel final</span>
          <h2>Tela de assinatura e re-autenticacao</h2>
          <p>O painel abaixo resume o item selecionado, o hash do documento e os fatores exigidos antes da emissao.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Declaracao</span>
            <strong>{scenario.approval.signatoryDisplayName}</strong>
            <p>{scenario.approval.statement}</p>
            <div className="chip-list">
              <span className="chip">{scenario.approval.authorizationLabel}</span>
              <span className="chip">{scenario.approval.documentHash}</span>
            </div>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Re-autenticacao</span>
            <strong>
              {scenario.approval.authRequirements.filter((requirement) => requirement.status === "configured").length}/
              {scenario.approval.authRequirements.length} fator(es) configurado(s)
            </strong>
            <ul>
              {scenario.approval.authRequirements.map((requirement) => (
                <li key={requirement.factor}>
                  {requirement.label}: {requirementStatusLabel(requirement.status)}. {requirement.detail}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Previa compacta</span>
            <strong>{selectedItem.certificateNumber ?? "Numeracao ainda indisponivel"}</strong>
            <dl>
              {scenario.approval.compactPreview.map((field) => (
                <div key={`${scenario.approval.itemId}-${field.label}`}>
                  <dt>{field.label}</dt>
                  <dd>{field.value}</dd>
                </div>
              ))}
            </dl>
          </article>
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Pre-validacoes</span>
          <h2>Checks do item selecionado</h2>
          <p>Os checks abaixo explicam por que o item pode seguir, exige conferencia final ou permanece bloqueado.</p>
        </div>

        <ul className="check-list">
          {selectedItem.validations.map((validation) => (
            <li key={`${selectedItem.itemId}-${validation.label}`}>
              <div className="metric-row">
                <strong>{validation.label}</strong>
                <StatusPill
                  tone={validation.status === "passed" ? "ok" : "warn"}
                  label={
                    validation.status === "passed"
                      ? "Passou"
                      : validation.status === "warning"
                        ? "Warning"
                        : "Falhou"
                  }
                />
              </div>
              <p>{validation.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.approval.blockers.length === 0
              ? "Nenhum bloqueio ativo"
              : `${scenario.approval.blockers.length} bloqueio(s) antes da assinatura`}
          </strong>
          <ul>
            {scenario.approval.blockers.length === 0 ? (
              <li>Este item nao possui bloqueios adicionais na tela final.</li>
            ) : (
              scenario.approval.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>
            {scenario.approval.warnings.length === 0
              ? "Sem warnings ativos"
              : `${scenario.approval.warnings.length} warning(s) a revisar`}
          </strong>
          <ul>
            {scenario.approval.warnings.length === 0 ? (
              <li>Nao ha observacoes adicionais para este item da fila.</li>
            ) : (
              scenario.approval.warnings.map((warning) => <li key={warning}>{warning}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Acao recomendada</span>
          <strong>{scenario.summary.recommendedAction}</strong>
          <p>O backend canonico mantem a assinatura fail-closed sempre que um gate critico falha.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas ao item selecionado</h2>
          <p>Use os atalhos abaixo para voltar aos sinais canônicos que sustentam a assinatura final.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/service-order-review?scenario=${mapQueueScenarioToServiceOrderScenario(scenario.id)}`}
          eyebrow="OS"
          title="Abrir detalhe da OS"
          description="Voltar ao detalhe canonico da OS que originou a fila de assinatura."
          cta="Abrir OS"
        />
        <NavCard
          href={`/emission/certificate-preview?scenario=${selectedItem.previewScenarioId}`}
          eyebrow="Previa"
          title="Abrir previa integral"
          description="Revisar a peca completa do certificado antes da assinatura final."
          cta="Abrir previa"
        />
        <NavCard
          href={`/emission/review-signature?scenario=${selectedItem.reviewSignatureScenarioId}`}
          eyebrow="Workflow"
          title="Abrir revisao e assinatura"
          description="Voltar ao workflow canônico que liberou ou bloqueou este item."
          cta="Abrir workflow"
        />
        <NavCard
          href={`/emission/workspace?scenario=${mapQueueScenarioToWorkspaceScenario(scenario.id)}`}
          eyebrow="Workspace"
          title="Abrir prontidao consolidada"
          description="Conferir o estado operacional agregado antes de concluir a emissao."
          cta="Abrir workspace"
        />
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/signature-queue?scenario=${item.id}&item=${item.selectedItem.itemId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir fila"
          />
        ))}
      </section>
    </AppShell>
  );
}
