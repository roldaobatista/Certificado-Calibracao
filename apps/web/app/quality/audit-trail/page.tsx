import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadAuditTrailCatalog } from "@/src/quality/audit-trail-api";
import { buildAuditTrailCatalogView } from "@/src/quality/audit-trail-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    event?: string;
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
      return "Trilha integra";
    case "attention":
      return "Trilha sensivel";
    case "blocked":
      return "Trilha bloqueada";
    default:
      return status;
  }
}

function mapAuditTrailScenarioToQualityHubScenario(
  scenarioId: "recent-emission" | "reissue-attention" | "integrity-blocked",
): "stable-baseline" | "operational-attention" | "critical-response" {
  switch (scenarioId) {
    case "integrity-blocked":
      return "critical-response";
    case "reissue-attention":
      return "operational-attention";
    case "recent-emission":
    default:
      return "stable-baseline";
  }
}

function mapAuditTrailScenarioToComplaintContext(
  scenarioId: "recent-emission" | "reissue-attention" | "integrity-blocked",
): { scenarioId: "resolved-history" | "open-follow-up" | "critical-response"; complaintId: string } {
  switch (scenarioId) {
    case "integrity-blocked":
      return { scenarioId: "critical-response", complaintId: "recl-007" };
    case "reissue-attention":
      return { scenarioId: "critical-response", complaintId: "recl-007" };
    case "recent-emission":
    default:
      return { scenarioId: "resolved-history", complaintId: "recl-002" };
  }
}

export default async function AuditTrailPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadAuditTrailCatalog({
    scenarioId: props.searchParams?.scenario,
    eventId: props.searchParams?.event,
    itemId: props.searchParams?.item,
    cookieHeader,
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  if (!catalog && authSession?.authenticated === false && !props.searchParams?.scenario) {
    return (
      <AppShell
        eyebrow="Qualidade - trilha de auditoria"
        title="Trilha protegida por sessao"
        description="A trilha crítica persistida do tenant exige autenticacao antes da leitura."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Acesso atual</span>
            <strong>Login necessario</strong>
            <StatusPill tone="warn" label="RBAC ativo" />
            <p>Entre com um papel operacional para auditar os eventos críticos reais da emissão.</p>
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

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Qualidade - trilha de auditoria"
        title="Trilha de auditoria indisponivel"
        description="O back-office nao recebeu o payload canonico da trilha. Em fail-closed, nenhum evento local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a trilha de auditoria.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a trilha ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/audit-trail`. Sem resposta valida, o web nao
              assume integridade, criticidade ou reemissoes da cadeia.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildAuditTrailCatalogView(catalog);
  const selectedEvent = scenario.selectedEvent;
  const detail = scenario.detail;
  const complaintContext = mapAuditTrailScenarioToComplaintContext(scenario.id);

  return (
    <AppShell
      eyebrow="Qualidade - trilha de auditoria"
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
          <span className="eyebrow">Eventos</span>
          <strong>{scenario.summary.totalEvents} evento(s)</strong>
          <p>
            {scenario.summary.criticalEvents} critico(s), {scenario.summary.reissueEvents} de reemissao e{" "}
            {scenario.summary.integrityFailures} falha(s) de integridade.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Evento selecionado</span>
          <strong>{selectedEvent.actionLabel}</strong>
          <p>
            {selectedEvent.actorLabel} · {selectedEvent.entityLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Exportacao</span>
          <strong>{detail.exportLabel}</strong>
          <p>{detail.chainStatusLabel}</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Filtros aplicados</span>
          <h2>Janela e recorte canonico da trilha</h2>
          <p>Os chips abaixo resumem o mesmo recorte operacional entregue pelo backend para a trilha selecionada.</p>
        </div>

        <div className="chip-list">
          <span className="chip">{detail.selectedWindowLabel}</span>
          <span className="chip">{detail.selectedActorLabel}</span>
          <span className="chip">{detail.selectedEntityLabel}</span>
          <span className="chip">{detail.selectedActionLabel}</span>
        </div>
      </section>

      {detail.selectedEventContextFields.length > 0 ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Contexto do evento</span>
            <h2>Metadados relevantes da selecao atual</h2>
            <p>Quando a revisao tecnica registra decisao assistida, a trilha mostra o alinhamento e a justificativa associados ao evento.</p>
          </div>

          <div className="detail-grid">
            {detail.selectedEventContextFields.map((field) => (
              <article className="detail-card" key={field.label}>
                <span className="eyebrow">{field.label}</span>
                <strong>{field.value}</strong>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Eventos canonicos</span>
          <h2>Lista append-only do recorte selecionado</h2>
          <p>Os eventos abaixo permitem alternar o ponto focal da trilha sem sair do mesmo catalogo canonico.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.eventId}
            href={
              isPersistedMode && props.searchParams?.item
                ? `/quality/audit-trail?item=${props.searchParams.item}&event=${item.eventId}`
                : `/quality/audit-trail?scenario=${scenario.id}&event=${item.eventId}`
            }
            eyebrow={item.eventId === selectedEvent.eventId ? "Selecionado" : item.occurredAtLabel}
            title={item.actionLabel}
            description={`${item.actorLabel} · ${item.entityLabel} · hash ${item.hashLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir evento"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Cobertura</span>
          <strong>{detail.coveredActions.length} acao(oes)</strong>
          <ul>
            {detail.coveredActions.map((item) => (
              <li key={item}>{item}</li>
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

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas a esta cadeia</h2>
          <p>Use os atalhos abaixo para voltar ao fluxo operacional que compartilha a mesma trilha de auditoria.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapAuditTrailScenarioToQualityHubScenario(scenario.id)}&module=audit-trail`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado da Qualidade mantendo este recorte como ancora."
          cta="Abrir hub"
        />
        <NavCard
          href={`/quality/complaints?scenario=${complaintContext.scenarioId}&complaint=${complaintContext.complaintId}`}
          eyebrow="Reclamacoes"
          title="Abrir reclamacoes"
          description="Conferir a tratativa de cliente mais coerente com o recorte atual da trilha."
          cta="Abrir reclamacoes"
        />
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao consolidada"
            description="Voltar ao workspace que compartilha o mesmo recorte operacional da trilha."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={
              isPersistedMode
                ? `/emission/service-order-review?item=${detail.links.reviewItemId}`
                : `/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`
            }
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Inspecionar a OS canônica vinculada ao evento ou chain selecionados."
            cta="Abrir OS"
          />
        ) : null}
        {detail.links.dryRunScenarioId ? (
          <NavCard
            href={
              isPersistedMode && detail.links.reviewItemId
                ? `/emission/dry-run?item=${detail.links.reviewItemId}`
                : `/emission/dry-run?scenario=${detail.links.dryRunScenarioId}`
            }
            eyebrow="Dry-run"
            title="Abrir dry-run de emissao"
            description="Conferir o recorte de emissao que sustenta esta trilha de auditoria."
            cta="Abrir dry-run"
          />
        ) : null}
        <NavCard
          href={
            detail.status === "blocked"
              ? "/quality/nonconformities?scenario=critical-response&nc=nc-015"
              : detail.status === "attention"
                ? "/quality/nonconformities?scenario=open-attention&nc=nc-014"
                : "/quality/nonconformities?scenario=resolved-history&nc=nc-011"
          }
          eyebrow="NCs"
          title="Abrir nao conformidades"
          description="Conferir a NC canônica associada ao contexto atual da trilha."
          cta="Abrir NCs"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto da trilha</h2>
          <p>Use os cenarios abaixo para revisar emissao recente, reemissao controlada e divergencia de integridade sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={
              isPersistedMode && props.searchParams?.item
                ? `/quality/audit-trail?item=${props.searchParams.item}&event=${item.selectedEvent.eventId}`
                : `/quality/audit-trail?scenario=${item.id}&event=${item.selectedEvent.eventId}`
            }
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir trilha"
          />
        ))}
      </section>
    </AppShell>
  );
}
