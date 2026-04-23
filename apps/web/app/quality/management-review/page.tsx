import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadManagementReviewCatalog } from "@/src/quality/management-review-api";
import { buildManagementReviewCatalogView } from "@/src/quality/management-review-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    meeting?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Ata arquivada";
    case "attention":
      return "Pauta em preparo";
    case "blocked":
      return "Extraordinaria bloqueante";
    default:
      return status;
  }
}

function mapManagementReviewScenarioToQualityHubScenario(
  scenarioId: "ordinary-ready" | "agenda-attention" | "extraordinary-response",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "extraordinary-response":
      return "critical-response";
    case "ordinary-ready":
      return "stable-baseline";
    case "agenda-attention":
    default:
      return "operational-attention";
  }
}

export default async function ManagementReviewPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadManagementReviewCatalog({
    scenarioId: props.searchParams?.scenario,
    meetingId: props.searchParams?.meeting,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Qualidade - analise critica"
          title="Modulo protegido por sessao"
          description="A analise critica persistida da V5 exige autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel de Qualidade para abrir as reunioes reais do tenant.</p>
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
        eyebrow="Qualidade - analise critica"
        title="Modulo de analise critica indisponivel"
        description="O back-office nao recebeu o payload canonico da analise critica. Em fail-closed, nenhuma pauta, entrada automatica ou deliberação local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a analise critica.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar analise critica ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/management-review`. Sem resposta valida, o web
              nao assume pauta, entradas automaticas ou deliberacoes da direcao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildManagementReviewCatalogView(catalog);
  const detail = scenario.detail;
  const selectedMeeting = scenario.selectedMeeting;

  return (
      <AppShell
        eyebrow="Qualidade - analise critica"
        title={scenario.summary.headline}
        description={
          authSession?.authenticated === true && !props.searchParams?.scenario
            ? `${scenario.description} A reuniao exibida vem da camada persistida da V5.`
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
          <span className="eyebrow">Proxima reuniao</span>
          <strong>{scenario.summary.nextMeetingLabel}</strong>
          <p>
            {scenario.summary.agendaCount} item(ns) de pauta, {scenario.summary.automaticInputCount} entrada(s)
            automatica(s) e {scenario.summary.openDecisionCount} decisao(oes) em aberto.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Reuniao selecionada</span>
          <strong>{selectedMeeting.titleLabel}</strong>
          <p>{selectedMeeting.outcomeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Presidencia</span>
          <strong>{detail.chairLabel}</strong>
          <p>{detail.attendeesLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.meetings.map((meeting) => (
          <NavCard
            key={meeting.meetingId}
            href={`/quality/management-review?scenario=${scenario.id}&meeting=${meeting.meetingId}`}
            eyebrow={meeting.dateLabel}
            title={meeting.titleLabel}
            description={meeting.outcomeLabel}
            statusTone={statusTone(meeting.status)}
            statusLabel={statusLabel(meeting.status)}
            cta="Abrir reuniao"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Ata</span>
          <strong>{detail.ataLabel}</strong>
          <p>{detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Periodo</span>
          <strong>{detail.periodLabel}</strong>
          <p>Proxima referencia: {detail.nextMeetingLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Evidencia</span>
          <strong>Dossie minimo</strong>
          <p>{detail.evidenceLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Pauta padrao</span>
          <strong>{detail.agendaItems.length} item(ns)</strong>
          <ul>
            {detail.agendaItems.map((item) => (
              <li key={item.key}>
                {item.label} | {statusLabel(item.status)}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Deliberacoes</span>
          <strong>{detail.decisions.length} item(ns)</strong>
          <ul>
            {detail.decisions.map((item) => (
              <li key={item.key}>
                {item.label} | {item.ownerLabel} | {item.dueDateLabel} | {statusLabel(item.status)}
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
      </section>

      <section className="detail-grid">
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
          <span className="eyebrow">Entradas automaticas</span>
          <strong>{detail.automaticInputs.length} item(ns)</strong>
          <p>Os cards abaixo reabrem os modulos de origem que sustentam a pauta desta reuniao.</p>
        </article>
      </section>

      <section className="nav-grid">
        {detail.automaticInputs.map((item) => (
          <NavCard
            key={item.key}
            href={item.href ?? "/quality"}
            eyebrow={item.sourceLabel}
            title={item.label}
            description={item.valueLabel}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta={item.href ? "Abrir origem" : "Ver contexto"}
          />
        ))}
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapManagementReviewScenarioToQualityHubScenario(scenario.id)}&module=management-review`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado mantendo a analise critica como ancora do recorte."
          cta="Abrir hub"
        />
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/management-review?scenario=${item.id}&meeting=${item.selectedMeeting.meetingId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir analise critica"
          />
        ))}
      </section>
    </AppShell>
  );
}
