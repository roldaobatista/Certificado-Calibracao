import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadQualityIndicatorCatalog } from "@/src/quality/quality-indicator-api";
import { buildQualityIndicatorCatalogView } from "@/src/quality/quality-indicator-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    indicator?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Dentro da meta";
    case "attention":
      return "Atencao preventiva";
    case "blocked":
      return "Deriva critica";
    default:
      return status;
  }
}

function mapIndicatorScenarioToQualityHubScenario(
  scenarioId: "baseline-ready" | "action-sla-attention" | "critical-drift",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "critical-drift":
      return "critical-response";
    case "baseline-ready":
      return "stable-baseline";
    case "action-sla-attention":
    default:
      return "operational-attention";
  }
}

export default async function QualityIndicatorsPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadQualityIndicatorCatalog({
    scenarioId: props.searchParams?.scenario,
    indicatorId: props.searchParams?.indicator,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Qualidade - indicadores"
          title="Modulo protegido por sessao"
          description="Os indicadores persistidos da V5 exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel de Qualidade para abrir o painel real do tenant.</p>
            </div>
          }
        >
          <section className="content-panel">
            <div className="button-row">
              <a className="button-primary" href="/auth/login">
                Fazer login
              </a>
            </div>
          </section>
        </AppShell>
      );
    }

    return (
      <AppShell
        eyebrow="Qualidade - indicadores"
        title="Painel de indicadores indisponivel"
        description="O back-office nao recebeu o payload canonico de indicadores da Qualidade. Em fail-closed, nenhuma tendencia ou meta local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o painel gerencial.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar indicadores ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/indicators`. Sem resposta valida, o web nao
              assume metas, tendencias ou snapshots mensais da Qualidade.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildQualityIndicatorCatalogView(catalog);
  const detail = scenario.detail;
  const selectedIndicator = scenario.selectedIndicator;

  return (
      <AppShell
        eyebrow="Qualidade - indicadores"
        title={scenario.summary.headline}
        description={
          authSession?.authenticated === true && !props.searchParams?.scenario
            ? `${scenario.description} Os numeros exibidos derivam do tenant persistido da V5.`
            : scenario.description
        }
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
          <span className="eyebrow">Janela consolidada</span>
          <strong>{scenario.summary.monthlyWindowLabel}</strong>
          <p>
            {scenario.summary.indicatorCount} indicador(es) no painel, {scenario.summary.attentionCount} em atencao e{" "}
            {scenario.summary.blockedCount} em deriva critica.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Indicador selecionado</span>
          <strong>{selectedIndicator.title}</strong>
          <p>{selectedIndicator.currentLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Meta e tendencia</span>
          <strong>{selectedIndicator.targetLabel}</strong>
          <p>{selectedIndicator.trendLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.indicators.map((item) => (
          <NavCard
            key={item.indicatorId}
            href={`/quality/indicators?scenario=${scenario.id}&indicator=${item.indicatorId}`}
            eyebrow={item.cadenceLabel}
            title={item.title}
            description={`${item.currentLabel} | ${item.targetLabel} | ${item.ownerLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir indicador"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Status</span>
          <strong>{detail.currentLabel}</strong>
          <p>{detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Owner e cadencia</span>
          <strong>{detail.ownerLabel}</strong>
          <p>{detail.cadenceLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Definicao</span>
          <strong>{detail.targetLabel}</strong>
          <p>{detail.measurementDefinitionLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Periodo</span>
          <strong>{detail.periodLabel}</strong>
          <p>{detail.trendLabel}</p>
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

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Snapshots mensais</span>
          <strong>{detail.snapshots.length} leitura(s)</strong>
          <ul>
            {detail.snapshots.map((item) => (
              <li key={`${item.monthLabel}-${item.valueLabel}`}>
                {item.monthLabel} | {item.valueLabel} | {statusLabel(item.status)}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Artefatos relacionados</span>
          <strong>{detail.relatedArtifacts.length} item(ns)</strong>
          <ul>
            {detail.relatedArtifacts.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Dossie minimo</span>
          <strong>Evidencia e pauta</strong>
          <p>{detail.evidenceLabel}</p>
          <p>{detail.managementReviewLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapIndicatorScenarioToQualityHubScenario(scenario.id)}&module=indicators`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado da Qualidade mantendo os indicadores como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.nonconformityScenarioId && detail.links.nonconformityId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${detail.links.nonconformityScenarioId}&nc=${detail.links.nonconformityId}`}
            eyebrow="NC"
            title="Abrir nao conformidade relacionada"
            description="Inspecionar a NC que sustenta o desvio ou a melhora deste indicador."
            cta="Abrir NC"
          />
        ) : null}
        {detail.links.complaintScenarioId && detail.links.complaintId ? (
          <NavCard
            href={`/quality/complaints?scenario=${detail.links.complaintScenarioId}&complaint=${detail.links.complaintId}`}
            eyebrow="Reclamacoes"
            title="Abrir reclamacao relacionada"
            description="Conferir a resposta ao cliente associada a este indicador."
            cta="Abrir reclamacao"
          />
        ) : null}
        {detail.links.riskRegisterScenarioId && detail.links.riskId ? (
          <NavCard
            href={`/quality/risk-register?scenario=${detail.links.riskRegisterScenarioId}&risk=${detail.links.riskId}`}
            eyebrow="Riscos"
            title="Abrir risco relacionado"
            description="Inspecionar o risco que ajuda a explicar a deriva deste indicador."
            cta="Abrir riscos"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/indicators?scenario=${item.id}&indicator=${item.selectedIndicator.indicatorId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir indicadores"
          />
        ))}
      </section>
    </AppShell>
  );
}
