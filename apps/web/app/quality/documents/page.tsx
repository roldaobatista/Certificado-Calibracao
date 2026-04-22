import { loadQualityDocumentCatalog } from "@/src/quality/quality-document-api";
import { buildQualityDocumentCatalogView } from "@/src/quality/quality-document-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    document?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Documentacao estavel";
    case "attention":
      return "Revisao em andamento";
    case "blocked":
      return "Uso bloqueado";
    default:
      return status;
  }
}

function mapDocumentScenarioToQualityHubScenario(
  scenarioId: "operational-ready" | "revision-attention" | "obsolete-blocked",
): "operational-attention" | "critical-response" | "stable-baseline" {
  switch (scenarioId) {
    case "obsolete-blocked":
      return "critical-response";
    case "operational-ready":
      return "stable-baseline";
    case "revision-attention":
    default:
      return "operational-attention";
  }
}

export default async function QualityDocumentsPage(props: PageProps) {
  const catalog = await loadQualityDocumentCatalog({
    scenarioId: props.searchParams?.scenario,
    documentId: props.searchParams?.document,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Qualidade - documentos"
        title="Modulo documental indisponivel"
        description="O back-office nao recebeu o payload canonico de documentos da Qualidade. Em fail-closed, nenhuma vigencia ou revisao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o modulo documental.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar documentos ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality/documents`. Sem resposta valida, o web nao assume
              vigencia, revisao ou obsolescencia de MQ, PG, PT, IT e FR.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildQualityDocumentCatalogView(catalog);
  const detail = scenario.detail;
  const selectedDocument = scenario.selectedDocument;

  return (
    <AppShell
      eyebrow="Qualidade - documentos"
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
          <span className="eyebrow">Documentos vigentes</span>
          <strong>{scenario.summary.activeCount} documento(s)</strong>
          <p>{scenario.summary.attentionCount} em revisao e {scenario.summary.obsoleteCount} obsoleto(s) no acervo.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{selectedDocument.code} rev.{selectedDocument.revisionLabel}</strong>
          <p>{selectedDocument.title}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Vigencia</span>
          <strong>{selectedDocument.effectiveSinceLabel}</strong>
          <p>{selectedDocument.effectiveUntilLabel ?? "Sem encerramento registrado"}</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.documentId}
            href={`/quality/documents?scenario=${scenario.id}&document=${item.documentId}`}
            eyebrow={item.code}
            title={`${item.title} · rev.${item.revisionLabel}`}
            description={`${item.categoryLabel} · ${item.lifecycleLabel} · ${item.ownerLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir documento"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Classificacao</span>
          <strong>{detail.categoryLabel}</strong>
          <p>{detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Aprovacao</span>
          <strong>{detail.ownerLabel}</strong>
          <p>{detail.approvalLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Distribuicao</span>
          <strong>Consulta controlada</strong>
          <p>{detail.distributionLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Escopo</span>
          <strong>Aplicacao do documento</strong>
          <p>{detail.scopeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Politica de revisao</span>
          <strong>Cadencia e gatilhos</strong>
          <p>{detail.revisionPolicyLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Evidencia</span>
          <strong>Dossie minimo</strong>
          <p>{detail.evidenceLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
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
          href={`/quality?scenario=${mapDocumentScenarioToQualityHubScenario(scenario.id)}&module=documents`}
          eyebrow="Hub"
          title="Voltar ao hub da qualidade"
          description="Reabrir o panorama consolidado da Qualidade mantendo o recorte documental como ancora."
          cta="Abrir hub"
        />
        {detail.links.organizationSettingsScenarioId ? (
          <NavCard
            href={`/settings/organization?scenario=${detail.links.organizationSettingsScenarioId}`}
            eyebrow="Configuracoes"
            title="Abrir configuracoes da organizacao"
            description="Conferir o contexto regulatorio e de governanca associado ao documento selecionado."
            cta="Abrir configuracoes"
          />
        ) : null}
        {detail.links.procedureScenarioId && detail.links.procedureId ? (
          <NavCard
            href={`/registry/procedures?scenario=${detail.links.procedureScenarioId}&procedure=${detail.links.procedureId}`}
            eyebrow="Procedimentos"
            title="Abrir procedimento relacionado"
            description="Inspecionar o cadastro tecnico vinculado a este documento."
            cta="Abrir procedimento"
          />
        ) : null}
        {detail.links.riskRegisterScenarioId && detail.links.riskId ? (
          <NavCard
            href={`/quality/risk-register?scenario=${detail.links.riskRegisterScenarioId}&risk=${detail.links.riskId}`}
            eyebrow="Riscos"
            title="Abrir risco relacionado"
            description="Conferir a matriz de riscos ou declaracoes associadas ao documento selecionado."
            cta="Abrir riscos"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality/documents?scenario=${item.id}&document=${item.selectedDocument.documentId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir documentos"
          />
        ))}
      </section>
    </AppShell>
  );
}
