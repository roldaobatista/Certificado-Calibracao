import { loadReviewSignatureCatalog } from "@/src/emission/review-signature-api";
import { buildReviewSignatureCatalogView } from "@/src/emission/review-signature-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export const dynamic = "force-dynamic";

function formatRole(role: string): string {
  switch (role) {
    case "admin":
      return "Administrador";
    case "quality_manager":
      return "Gestor da qualidade";
    case "signatory":
      return "Signatario";
    case "technical_reviewer":
      return "Revisor tecnico";
    case "technician":
      return "Tecnico";
    case "auditor_readonly":
      return "Auditor leitura";
    case "external_client":
      return "Cliente externo";
    default:
      return role;
  }
}

function mapReviewScenarioToPreviewScenario(reviewScenarioId: string): string {
  switch (reviewScenarioId) {
    case "signatory-mfa-blocked":
      return "type-c-blocked";
    default:
      return "type-b-ready";
  }
}

function mapReviewScenarioToQueueScenario(reviewScenarioId: string): string {
  switch (reviewScenarioId) {
    case "approved-ready":
      return "approved-ready";
    case "signatory-mfa-blocked":
      return "mfa-blocked";
    default:
      return "approved-ready";
  }
}

function mapReviewScenarioToServiceOrderScenario(reviewScenarioId: string): string {
  switch (reviewScenarioId) {
    case "reviewer-conflict":
    case "signatory-mfa-blocked":
      return "review-blocked";
    default:
      return "review-ready";
  }
}

export default async function ReviewSignaturePage(props: PageProps) {
  const catalog = await loadReviewSignatureCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - revisao e assinatura"
        title="Workflow indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico do backend. Em fail-closed, nenhuma atribuicao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o workflow de revisao e assinatura.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o workflow de aprovacao ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /emission/review-signature`. Sem resposta valida do backend,
              o web nao inventa atribuicoes de revisor e signatario para evitar drift de autorizacao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildReviewSignatureCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Emissao - revisao e assinatura"
      title={scenario.summary.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={scenario.summary.status === "ready" ? "ok" : "warn"}
            label={scenario.summary.status === "ready" ? "Workflow liberado" : "Workflow bloqueado"}
          />
          <p>
            {scenario.summary.reviewStatusLabel} · {scenario.summary.signatureStatusLabel}
          </p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Etapa</span>
          <strong>{scenario.summary.stageLabel}</strong>
          <p>{scenario.result.summary}</p>
          <div className="chip-list">
            <span className="chip">{scenario.summary.allowedActionsLabel}</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Revisao</span>
          <strong>{scenario.result.reviewStep.actorLabel}</strong>
          <p>{scenario.result.reviewStep.detail}</p>
          <div className="chip-list">
            {scenario.result.assignments.reviewer?.roles.map((role) => (
              <span className="chip" key={role}>
                {formatRole(role)}
              </span>
            )) ?? <span className="chip chip--warn">Sem atribuicao valida</span>}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Assinatura</span>
          <strong>{scenario.result.signatureStep.actorLabel}</strong>
          <p>{scenario.result.signatureStep.detail}</p>
          <div className="chip-list">
            {scenario.result.assignments.signatory?.roles.map((role) => (
              <span className="chip" key={role}>
                {formatRole(role)}
              </span>
            )) ?? <span className="chip chip--warn">Sem atribuicao valida</span>}
            {scenario.result.assignments.signatory ? (
              <span className={`chip${scenario.result.assignments.signatory.mfaEnabled ? "" : " chip--warn"}`}>
                {scenario.result.assignments.signatory.mfaEnabled ? "MFA ativo" : "MFA pendente"}
              </span>
            ) : null}
          </div>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.result.blockers.length === 0
              ? "Sem bloqueios ativos"
              : `${scenario.result.blockers.length} bloqueio(s) de autorizacao`}
          </strong>
          <ul>
            {scenario.result.blockers.length === 0 ? (
              <li>Segregacao de funcoes e elegibilidade estao consistentes para esta etapa.</li>
            ) : (
              scenario.result.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Sugestao de revisor</span>
          <strong>{scenario.result.suggestions.reviewer?.displayName ?? "Sem sugestao automatica"}</strong>
          <p>{scenario.result.suggestions.reviewer?.rationale ?? "Nenhum revisor elegivel disponivel no catalogo atual."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Sugestao de signatario</span>
          <strong>{scenario.result.suggestions.signatory?.displayName ?? "Sem sugestao automatica"}</strong>
          <p>
            {scenario.result.suggestions.signatory?.rationale ??
              "Nenhum signatario elegivel com MFA ativo foi encontrado no catalogo atual."}
          </p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Checks</span>
          <h2>RBAC basico e segregacao por gate</h2>
          <p>Os checks abaixo explicam por que o fluxo pode avancar, precisa reatribuir atores ou continua bloqueado.</p>
        </div>

        <ul className="check-list">
          {scenario.result.checks.map((check) => (
            <li key={check.id}>
              <div className="metric-row">
                <strong>{check.title}</strong>
                <StatusPill
                  tone={check.status === "passed" ? "ok" : "warn"}
                  label={check.status === "passed" ? "Passou" : "Falhou"}
                />
              </div>
              <p>{check.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Continuar a partir do workflow</h2>
          <p>Use as rotas abaixo para conferir a previa do certificado ou abrir a fila final de assinatura.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/service-order-review?scenario=${mapReviewScenarioToServiceOrderScenario(scenario.id)}`}
          eyebrow="OS"
          title="Abrir detalhe da OS"
          description="Contextualizar o workflow com linha do tempo, checklist e dados de execucao."
          cta="Abrir OS"
        />
        <NavCard
          href={`/emission/certificate-preview?scenario=${mapReviewScenarioToPreviewScenario(scenario.id)}`}
          eyebrow="Previa"
          title="Abrir previa do certificado"
          description="Revisar os campos que serao apresentados ao signatario antes da emissao."
          cta="Abrir previa"
        />
        <NavCard
          href={`/emission/signature-queue?scenario=${mapReviewScenarioToQueueScenario(scenario.id)}`}
          eyebrow="Fila"
          title="Abrir fila de assinatura"
          description="Conferir os itens prontos, em atencao ou bloqueados antes da assinatura final."
          cta="Abrir fila"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do workflow</h2>
          <p>Use os atalhos abaixo para revisar segregacao, MFA e elegibilidade sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/review-signature?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.description}
            statusTone={item.summary.status === "ready" ? "ok" : "warn"}
            statusLabel={item.summary.status === "ready" ? "Workflow liberado" : "Workflow bloqueado"}
            cta="Abrir workflow"
          />
        ))}
      </section>
    </AppShell>
  );
}
