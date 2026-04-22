import { loadCertificatePreviewCatalog } from "@/src/emission/certificate-preview-api";
import { buildCertificatePreviewCatalogView } from "@/src/emission/certificate-preview-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export const dynamic = "force-dynamic";

function mapPreviewScenarioToWorkspaceScenario(previewScenarioId: string): string {
  switch (previewScenarioId) {
    case "type-c-blocked":
      return "release-blocked";
    case "type-b-ready":
      return "baseline-ready";
    case "type-a-suppressed":
      return "baseline-ready";
    default:
      return "baseline-ready";
  }
}

function mapPreviewScenarioToQueueScenario(previewScenarioId: string): string {
  switch (previewScenarioId) {
    case "type-a-suppressed":
      return "attention-required";
    case "type-c-blocked":
      return "mfa-blocked";
    default:
      return "approved-ready";
  }
}

function renderTemplateLabel(templateId: string): string {
  switch (templateId) {
    case "template-a":
      return "Template A";
    case "template-b":
      return "Template B";
    case "template-c":
      return "Template C";
    default:
      return templateId;
  }
}

function renderSymbolLabel(symbolPolicy: string): string {
  switch (symbolPolicy) {
    case "allowed":
      return "Simbolo permitido";
    case "suppressed":
      return "Simbolo suprimido";
    case "blocked":
      return "Simbolo bloqueado";
    default:
      return symbolPolicy;
  }
}

export default async function CertificatePreviewPage(props: PageProps) {
  const catalog = await loadCertificatePreviewCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - previa do certificado"
        title="Previa indisponivel para conferencia"
        description="O back-office nao recebeu o payload canonico da previa. Em fail-closed, nenhum espelho local do certificado foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a previa operacional.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a previa ao backend canonico</h2>
            <p>
              Esta pagina depende do endpoint `GET /emission/certificate-preview`. Sem carga valida, o web nao tenta
              reconstruir o certificado a partir de fragmentos locais.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildCertificatePreviewCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Emissao - previa do certificado"
      title={scenario.result.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={scenario.result.status === "ready" ? "ok" : "warn"}
            label={scenario.result.status === "ready" ? "Previa pronta" : "Previa bloqueada"}
          />
          <p>{scenario.returnStepLabel}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Template</span>
          <strong>{renderTemplateLabel(scenario.result.templateId)}</strong>
          <p>{renderSymbolLabel(scenario.result.symbolPolicy)}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Certificado</span>
          <strong>{scenario.result.certificateNumber ?? "Numeracao ainda indisponivel"}</strong>
          <p>{scenario.result.qrCodeUrl ?? "QR ainda nao pode ser exibido neste cenario."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Correcao guiada</span>
          <strong>{scenario.returnStepLabel}</strong>
          <p>
            Quando a previa estiver bloqueada, o backend sugere o menor passo do wizard relacionado ao primeiro gate
            falho.
          </p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Previa integral</span>
          <h2>Campos que o operador deve conferir antes da assinatura</h2>
          <p>
            As secoes abaixo espelham o payload canonico da previa, sem edicao livre e sem assumir renderizacao final
            em PDF/A.
          </p>
        </div>

        <div className="detail-grid">
          {scenario.result.sections.map((section) => (
            <article className="detail-card" key={section.key}>
              <span className="eyebrow">{section.title}</span>
              <strong>{section.fields[0]?.value}</strong>
              <dl>
                {section.fields.map((field) => (
                  <div key={`${section.key}-${field.label}`}>
                    <dt>{field.label}</dt>
                    <dd>{field.value}</dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.result.blockers.length === 0
              ? "Nenhum bloqueio ativo"
              : `${scenario.result.blockers.length} bloqueio(s) antes da assinatura`}
          </strong>
          <ul>
            {scenario.result.blockers.length === 0 ? (
              <li>A previa pode seguir para conferencia final do operador.</li>
            ) : (
              scenario.result.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>
            {scenario.result.warnings.length === 0
              ? "Sem warnings ativos"
              : `${scenario.result.warnings.length} aviso(s) de politica`}
          </strong>
          <ul>
            {scenario.result.warnings.length === 0 ? (
              <li>Nao ha observacoes adicionais para este cenario.</li>
            ) : (
              scenario.result.warnings.map((warning) => <li key={warning}>{warning}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Navegacao</span>
          <strong>Rotas relacionadas</strong>
          <div className="chip-list">
            <span className="chip">Dry-run</span>
            <span className="chip">Workspace</span>
            <span className="chip">Workflow</span>
            <span className="chip">Fila</span>
          </div>
          <p>Use os atalhos abaixo para voltar aos gates canônicos que alimentam a previa.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Trocar o contexto da previa</h2>
          <p>Os cenarios abaixo permitem revisar a peca antes da assinatura sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/dry-run?scenario=${scenario.id}`}
          eyebrow="Dry-run"
          title="Abrir pipeline seco"
          description="Revisar os checks técnicos que alimentam esta previa."
          cta="Abrir dry-run"
        />
        <NavCard
          href={`/emission/workspace?scenario=${mapPreviewScenarioToWorkspaceScenario(scenario.id)}`}
          eyebrow="Workspace"
          title="Abrir prontidao consolidada"
          description="Voltar ao workspace canonico para revisar os modulos operacionais."
          cta="Abrir workspace"
        />
        <NavCard
          href={`/emission/signature-queue?scenario=${mapPreviewScenarioToQueueScenario(scenario.id)}`}
          eyebrow="Fila"
          title="Abrir fila de assinatura"
          description="Seguir para a fila canônica e revisar a tela final de assinatura."
          cta="Abrir fila"
        />
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/certificate-preview?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={item.result.status === "ready" ? "ok" : "warn"}
            statusLabel={item.result.status === "ready" ? "Previa pronta" : "Previa bloqueada"}
            cta="Abrir previa"
          />
        ))}
      </section>
    </AppShell>
  );
}
