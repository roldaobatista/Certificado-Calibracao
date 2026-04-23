import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadInternalAuditCatalog } from "@/src/quality/internal-audit-api";
import { buildInternalAuditCatalogView } from "@/src/quality/internal-audit-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    cycle?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Programa controlado";
    case "attention":
      return "Follow-up em aberto";
    case "blocked":
      return "Escalacao extraordinaria";
    default:
      return status;
  }
}

function mapInternalAuditScenarioToQualityHubScenario(
  scenarioId:
    | "program-on-track"
    | "follow-up-attention"
    | "extraordinary-escalation",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "extraordinary-escalation":
      return "critical-response";
    case "program-on-track":
      return "stable-baseline";
    case "follow-up-attention":
    default:
      return "operational-attention";
  }
}

export default async function InternalAuditPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadInternalAuditCatalog({
    scenarioId: props.searchParams?.scenario,
    cycleId: props.searchParams?.cycle,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Qualidade - auditoria interna"
          title="Modulo protegido por sessao"
          description="A auditoria interna persistida da V5 exige autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel de Qualidade para abrir os ciclos reais do tenant.</p>
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
        eyebrow="Qualidade - auditoria interna"
        title="Modulo de auditoria interna indisponivel"
        description="O back-office nao recebeu o payload canonico do programa de auditoria interna. Em fail-closed, nenhum ciclo ou achado local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o programa de auditoria interna.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar auditoria interna ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/internal-audit`. Sem resposta valida, o web nao
              assume ciclos, checklist ou achados do programa anual.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildInternalAuditCatalogView(catalog);
  const detail = scenario.detail;
  const selectedCycle = scenario.selectedCycle;

  return (
      <AppShell
        eyebrow="Qualidade - auditoria interna"
        title={scenario.summary.headline}
        description={
          authSession?.authenticated === true && !props.searchParams?.scenario
            ? `${scenario.description} O programa exibido vem da base persistida da V5.`
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
          <span className="eyebrow">Programa</span>
          <strong>{scenario.summary.programLabel}</strong>
          <p>
            {scenario.summary.plannedCycleCount} ciclo(s) planejado(s), {scenario.summary.completedCycleCount} concluido(s) e{" "}
            {scenario.summary.openFindingCount} achado(s) em aberto.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Ciclo selecionado</span>
          <strong>{selectedCycle.cycleLabel}</strong>
          <p>{selectedCycle.scopeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Janela</span>
          <strong>{selectedCycle.windowLabel}</strong>
          <p>{selectedCycle.findingsLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.cycles.map((cycle) => (
          <NavCard
            key={cycle.cycleId}
            href={`/quality/internal-audit?scenario=${scenario.id}&cycle=${cycle.cycleId}`}
            eyebrow={cycle.windowLabel}
            title={cycle.cycleLabel}
            description={`${cycle.scopeLabel} | ${cycle.auditorLabel}`}
            statusTone={statusTone(cycle.status)}
            statusLabel={cycle.statusLabel}
            cta="Abrir ciclo"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Status</span>
          <strong>{detail.noticeLabel}</strong>
          <p>{detail.reportLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Auditoria</span>
          <strong>{detail.auditorLabel}</strong>
          <p>Auditados: {detail.auditeeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Periodo e escopo</span>
          <strong>{detail.periodLabel}</strong>
          <p>{detail.scopeLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Checklist aplicado</span>
          <strong>{detail.checklist.length} item(ns)</strong>
          <ul>
            {detail.checklist.map((item) => (
              <li key={item.key}>
                {item.requirementLabel} | {item.evidenceLabel} | {statusLabel(item.status)}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Achados</span>
          <strong>{detail.findings.length} item(ns)</strong>
          <ul>
            {detail.findings.map((item) => (
              <li key={item.findingId}>
                {item.title} | {item.severityLabel} | {item.ownerLabel} | {item.dueDateLabel}
                {item.nonconformityId ? ` | ${item.nonconformityId}` : ""}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima leitura</span>
          <strong>Follow-up minimo</strong>
          <p>{detail.nextReviewLabel}</p>
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
          <strong>Dossie minimo</strong>
          <p>{detail.evidenceLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapInternalAuditScenarioToQualityHubScenario(scenario.id)}&module=internal-audit`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado mantendo a auditoria interna como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.nonconformityScenarioId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${detail.links.nonconformityScenarioId}`}
            eyebrow="NC"
            title="Abrir nao conformidades relacionadas"
            description="Inspecionar o follow-up das NCs geradas ou ancoradas por este ciclo."
            cta="Abrir NCs"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/internal-audit?scenario=${item.id}&cycle=${item.selectedCycle.cycleId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir auditoria"
          />
        ))}
      </section>
    </AppShell>
  );
}
