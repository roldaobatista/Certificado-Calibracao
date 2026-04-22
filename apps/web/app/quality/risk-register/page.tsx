import { loadRiskRegisterCatalog } from "@/src/quality/risk-register-api";
import { buildRiskRegisterCatalogView } from "@/src/quality/risk-register-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    risk?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Monitoramento estavel";
    case "attention":
      return "Acompanhamento em curso";
    case "blocked":
      return "Escalacao critica";
    default:
      return status;
  }
}

function declarationStatusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Declaracao vigente";
    case "attention":
      return "Conflito declarado";
    case "blocked":
      return "Rodada pendente";
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

function mapRiskScenarioToQualityHubScenario(
  scenarioId: "annual-declarations" | "commercial-pressure" | "stable-monitoring",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "commercial-pressure":
      return "critical-response";
    case "stable-monitoring":
      return "stable-baseline";
    case "annual-declarations":
    default:
      return "operational-attention";
  }
}

export default async function RiskRegisterPage(props: PageProps) {
  const catalog = await loadRiskRegisterCatalog({
    scenarioId: props.searchParams?.scenario,
    riskId: props.searchParams?.risk,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Qualidade - imparcialidade e riscos"
        title="Modulo de imparcialidade e riscos indisponivel"
        description="O back-office nao recebeu o payload canonico de declaracoes e matriz de riscos. Em fail-closed, nenhuma mitigacao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o modulo de imparcialidade e riscos.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar riscos ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/risk-register`. Sem resposta valida, o web nao
              assume declaracoes de conflito, matriz de riscos ou exportacao para analise critica.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildRiskRegisterCatalogView(catalog);
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Qualidade - imparcialidade e riscos"
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
          <span className="eyebrow">Declaracoes</span>
          <strong>{scenario.summary.declarationCount} declaracao(oes)</strong>
          <p>
            {scenario.summary.pendingDeclarationCount} pendente(s) e {scenario.summary.conflictDeclarationCount} com
            conflito relatado no recorte.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Matriz de riscos</span>
          <strong>{scenario.summary.activeRiskCount} risco(s) ativo(s)</strong>
          <p>{scenario.summary.highImpactRiskCount} classificado(s) com impacto alto.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Risco selecionado</span>
          <strong>{detail.title}</strong>
          <p>{detail.noticeLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Declaracoes de conflito</span>
          <strong>{scenario.declarations.length} item(ns)</strong>
          <ul>
            {scenario.declarations.map((item) => (
              <li key={item.declarationId}>
                {item.actorName} · {item.dateLabel} · {declarationStatusLabel(item.status)} · {item.summary} ·{" "}
                {item.documentLabel}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Classificacao</span>
          <strong>{detail.categoryLabel}</strong>
          <p>
            Probabilidade {detail.probabilityLabel} · Impacto {detail.impactLabel} · Responsavel {detail.ownerLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Revisao</span>
          <strong>{detail.lastReviewedAtLabel}</strong>
          <p>Cadencia: {detail.reviewCadenceLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.risks.map((item) => (
          <NavCard
            key={item.riskId}
            href={`/quality/risk-register?scenario=${scenario.id}&risk=${item.riskId}`}
            eyebrow={item.categoryLabel}
            title={item.title}
            description={`Prob ${item.probabilityLabel} · Imp ${item.impactLabel} · ${item.ownerLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={item.statusLabel}
            cta="Abrir risco"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Descricao</span>
          <strong>Contexto do risco</strong>
          <p>{detail.description}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Mitigacao</span>
          <strong>Plano vigente</strong>
          <p>{detail.mitigationPlanLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Vinculo declaratorio</span>
          <strong>Declaracoes e alocacao</strong>
          <p>{detail.linkedDeclarationLabel}</p>
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
          <span className="eyebrow">Evidencia e exportacao</span>
          <h2>Dossie minimo de imparcialidade</h2>
          <p>{detail.evidenceLabel}</p>
          <p>{detail.managementReviewLabel}</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapRiskScenarioToQualityHubScenario(scenario.id)}&module=risk-impartiality`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado da Qualidade mantendo o risco como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.organizationSettingsScenarioId ? (
          <NavCard
            href={`/settings/organization?scenario=${detail.links.organizationSettingsScenarioId}`}
            eyebrow="Configuracoes"
            title="Abrir configuracoes da organizacao"
            description="Conferir governanca e contexto regulatorio associados a este risco."
            cta="Abrir configuracoes"
          />
        ) : null}
        {detail.links.complaintScenarioId && detail.links.complaintId ? (
          <NavCard
            href={`/quality/complaints?scenario=${detail.links.complaintScenarioId}&complaint=${detail.links.complaintId}`}
            eyebrow="Reclamacoes"
            title="Abrir reclamacao relacionada"
            description="Inspecionar a tratativa de cliente ligada ao risco selecionado."
            cta="Abrir reclamacao"
          />
        ) : null}
        {detail.links.nonconformityScenarioId && detail.links.nonconformityId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${detail.links.nonconformityScenarioId}&nc=${detail.links.nonconformityId}`}
            eyebrow="NC"
            title="Abrir nao conformidade relacionada"
            description="Conferir a NC vinculada ao mesmo recorte critico deste risco."
            cta="Abrir NC"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/risk-register?scenario=${item.id}&risk=${item.selectedRisk.riskId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir riscos"
          />
        ))}
      </section>
    </AppShell>
  );
}
