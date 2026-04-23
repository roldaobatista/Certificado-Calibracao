import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadNonconformingWorkCatalog } from "@/src/quality/nonconforming-work-api";
import { buildNonconformingWorkCatalogView } from "@/src/quality/nonconforming-work-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    case?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Historico arquivado";
    case "attention":
      return "Contencao ativa";
    case "blocked":
      return "Liberacao bloqueada";
    default:
      return status;
  }
}

function mapScenarioToQualityHubScenario(
  scenarioId: "contained-attention" | "release-blocked" | "archived-history",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "release-blocked":
      return "critical-response";
    case "archived-history":
      return "stable-baseline";
    case "contained-attention":
    default:
      return "operational-attention";
  }
}

export default async function NonconformingWorkPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadNonconformingWorkCatalog({
    scenarioId: props.searchParams?.scenario,
    caseId: props.searchParams?.case,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Qualidade - trabalho nao conforme"
          title="Modulo protegido por sessao"
          description="Os casos persistidos da V5 exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel de Qualidade para abrir os casos reais do tenant.</p>
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
        eyebrow="Qualidade - trabalho nao conforme"
        title="Modulo de trabalho nao conforme indisponivel"
        description="O back-office nao recebeu o payload canonico de trabalho nao conforme. Em fail-closed, nenhuma contencao, regra de liberacao ou historico local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o recorte de trabalho nao conforme.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o recorte de 7.10 ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/nonconforming-work`. Sem resposta valida, o web
              nao assume congelamento, suspensao preventiva ou liberacao de nenhum caso interno.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildNonconformingWorkCatalogView(catalog);
  const detail = scenario.detail;

  return (
      <AppShell
        eyebrow="Qualidade - trabalho nao conforme"
        title={scenario.summary.headline}
        description={
          authSession?.authenticated === true && !props.searchParams?.scenario
            ? `${scenario.description} Este modulo esta lendo a camada persistida da V5.`
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
          <span className="eyebrow">Casos abertos</span>
          <strong>{scenario.summary.openCaseCount}</strong>
          <p>{scenario.summary.blockedReleaseCount} liberacao(oes) bloqueada(s) no recorte atual.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Casos restaurados</span>
          <strong>{scenario.summary.restoredCount}</strong>
          <p>Historicos ja formalmente liberados e mantidos apenas para rastreabilidade.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Caso selecionado</span>
          <strong>{detail.title}</strong>
          <p>{detail.noticeLabel}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.caseId}
            href={`/quality/nonconforming-work?scenario=${scenario.id}&case=${item.caseId}`}
            eyebrow={item.caseId}
            title={item.titleLabel}
            description={`${item.affectedEntityLabel} · ${item.originLabel} · ${item.impactLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir caso"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Classificacao</span>
          <strong>{detail.classificationLabel}</strong>
          <p>{detail.originLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Entidade afetada</span>
          <strong>{detail.affectedEntityLabel}</strong>
          <p>{detail.containmentLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Regra de liberacao</span>
          <strong>Fail-closed</strong>
          <p>{detail.releaseRuleLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Evidencia</span>
          <strong>Dossie minimo</strong>
          <p>{detail.evidenceLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Retorno ao fluxo</span>
          <strong>Restauracao segura</strong>
          <p>{detail.restorationLabel}</p>
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
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/quality?scenario=${mapScenarioToQualityHubScenario(scenario.id)}&module=nonconforming-work`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado mantendo a contencao como ancora do recorte."
          cta="Abrir hub"
        />
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao operacional"
            description="Conferir o recorte operacional associado a este trabalho nao conforme."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.nonconformityScenarioId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${detail.links.nonconformityScenarioId}`}
            eyebrow="NC"
            title="Abrir nao conformidades"
            description="Voltar ao registro de NC que ancora a contencao deste caso."
            cta="Abrir NCs"
          />
        ) : null}
        {detail.links.complaintScenarioId && detail.links.complaintId ? (
          <NavCard
            href={`/quality/complaints?scenario=${detail.links.complaintScenarioId}&complaint=${detail.links.complaintId}`}
            eyebrow="Reclamacao"
            title="Abrir reclamacao vinculada"
            description="Conferir a resposta ao cliente dentro do mesmo recorte de contencao."
            cta="Abrir reclamacao"
          />
        ) : null}
        {detail.links.auditTrailScenarioId ? (
          <NavCard
            href={`/quality/audit-trail?scenario=${detail.links.auditTrailScenarioId}`}
            eyebrow="Auditoria"
            title="Abrir trilha de auditoria"
            description="Inspecionar a cadeia append-only vinculada a este caso."
            cta="Abrir trilha"
          />
        ) : null}
        {detail.links.qualityDocumentScenarioId && detail.links.documentId ? (
          <NavCard
            href={`/quality/documents?scenario=${detail.links.qualityDocumentScenarioId}&document=${detail.links.documentId}`}
            eyebrow="Documentos"
            title="Abrir documentos da qualidade"
            description="Conferir o documento SGQ usado como ancora desta contencao."
            cta="Abrir documentos"
          />
        ) : null}
        {detail.links.procedureScenarioId ? (
          <NavCard
            href={`/registry/procedures?scenario=${detail.links.procedureScenarioId}`}
            eyebrow="Procedimento"
            title="Abrir procedimentos"
            description="Conferir o contexto documental do procedimento afetado."
            cta="Abrir procedimento"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Inspecionar a OS associada a este caso interno."
            cta="Abrir OS"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/nonconforming-work?scenario=${item.id}&case=${item.selectedCase.caseId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir contencao"
          />
        ))}
      </section>
    </AppShell>
  );
}
