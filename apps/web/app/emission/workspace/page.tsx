import { loadEmissionWorkspaceCatalog } from "@/src/emission/emission-workspace-api";
import { buildEmissionWorkspaceCatalogView } from "@/src/emission/emission-workspace-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Workspace pronto";
    case "attention":
      return "Workspace com atencao";
    case "blocked":
      return "Workspace bloqueado";
    default:
      return status;
  }
}

function mapWorkspaceScenarioToPreviewScenario(
  workspaceScenarioId: string,
  dryRunScenarioId: string,
): string {
  if (dryRunScenarioId) {
    return dryRunScenarioId;
  }

  switch (workspaceScenarioId) {
    case "release-blocked":
      return "type-c-blocked";
    default:
      return "type-b-ready";
  }
}

function mapWorkspaceScenarioToQueueScenario(workspaceScenarioId: string): string {
  switch (workspaceScenarioId) {
    case "team-attention":
      return "attention-required";
    case "release-blocked":
      return "mfa-blocked";
    default:
      return "approved-ready";
  }
}

function mapWorkspaceScenarioToServiceOrderScenario(workspaceScenarioId: string): string {
  switch (workspaceScenarioId) {
    case "team-attention":
      return "history-pending";
    case "release-blocked":
      return "review-blocked";
    default:
      return "review-ready";
  }
}

function mapWorkspaceScenarioToRegistryScenario(workspaceScenarioId: string): string {
  switch (workspaceScenarioId) {
    case "team-attention":
      return "certificate-attention";
    case "release-blocked":
      return "registration-blocked";
    default:
      return "operational-ready";
  }
}

function mapWorkspaceScenarioToStandardScenario(workspaceScenarioId: string): string {
  switch (workspaceScenarioId) {
    case "team-attention":
      return "expiration-attention";
    case "release-blocked":
      return "expired-blocked";
    default:
      return "operational-ready";
  }
}

function mapWorkspaceScenarioToProcedureContext(workspaceScenarioId: string): {
  scenarioId: string;
  procedureId: string;
} {
  switch (workspaceScenarioId) {
    case "team-attention":
      return {
        scenarioId: "revision-attention",
        procedureId: "procedure-pt009-r02",
      };
    case "release-blocked":
      return {
        scenarioId: "obsolete-visible",
        procedureId: "procedure-pt005-r03",
      };
    default:
      return {
        scenarioId: "operational-ready",
        procedureId: "procedure-pt005-r04",
      };
  }
}

function mapWorkspaceScenarioToAuditTrailContext(workspaceScenarioId: string): {
  scenarioId: string;
  eventId: string;
} {
  switch (workspaceScenarioId) {
    case "team-attention":
      return {
        scenarioId: "reissue-attention",
        eventId: "audit-7",
      };
    case "release-blocked":
      return {
        scenarioId: "integrity-blocked",
        eventId: "audit-3",
      };
    default:
      return {
        scenarioId: "recent-emission",
        eventId: "audit-4",
      };
  }
}

function mapWorkspaceScenarioToNonconformityContext(workspaceScenarioId: string): {
  scenarioId: string;
  ncId: string;
} {
  switch (workspaceScenarioId) {
    case "team-attention":
      return {
        scenarioId: "open-attention",
        ncId: "nc-014",
      };
    case "release-blocked":
      return {
        scenarioId: "critical-response",
        ncId: "nc-015",
      };
    default:
      return {
        scenarioId: "resolved-history",
        ncId: "nc-011",
      };
  }
}

function mapWorkspaceScenarioToOrganizationSettingsContext(workspaceScenarioId: string): {
  scenarioId: string;
  sectionKey: string;
} {
  switch (workspaceScenarioId) {
    case "team-attention":
      return {
        scenarioId: "renewal-attention",
        sectionKey: "security",
      };
    case "release-blocked":
      return {
        scenarioId: "profile-change-blocked",
        sectionKey: "regulatory_profile",
      };
    default:
      return {
        scenarioId: "operational-ready",
        sectionKey: "regulatory_profile",
      };
  }
}

export default async function EmissionWorkspacePage(props: PageProps) {
  const catalog = await loadEmissionWorkspaceCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - workspace"
        title="Workspace indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico consolidado. Em fail-closed, nenhuma prontidao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o workspace operacional.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a consolidacao operacional ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /emission/workspace`. Sem resposta valida do backend, o
              web nao consolida auth, onboarding, equipe, dry-run e workflow por conta propria.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildEmissionWorkspaceCatalogView(catalog);
  const procedureContext = mapWorkspaceScenarioToProcedureContext(scenario.id);
  const auditTrailContext = mapWorkspaceScenarioToAuditTrailContext(scenario.id);
  const nonconformityContext = mapWorkspaceScenarioToNonconformityContext(scenario.id);
  const organizationSettingsContext = mapWorkspaceScenarioToOrganizationSettingsContext(scenario.id);

  return (
    <AppShell
      eyebrow="Emissao - workspace"
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
          <span className="eyebrow">Prontidao</span>
          <strong>{scenario.summary.readyModules} modulo(s) prontos</strong>
          <p>{scenario.summary.attentionModules} em atencao e {scenario.summary.blockedModules} bloqueado(s).</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Emissao final</span>
          <strong>{scenario.summary.readyToEmit ? "Pronta para emitir" : "Ainda nao pronta para emitir"}</strong>
          <p>
            {scenario.summary.readyToEmit
              ? "Todos os gates relevantes estao verdes para concluir a emissao."
              : "A operacao ainda precisa concluir as etapas restantes antes da emissao oficial."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima acao</span>
          <strong>{scenario.summary.recommendedAction}</strong>
          <p>Use os modulos abaixo para abrir exatamente a leitura canonica relacionada a cada gate.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Modulos</span>
          <h2>Entradas canonicas que sustentam a emissao</h2>
          <p>O workspace apenas consolida os sinais. Cada modulo continua com rota e leitura dedicadas no backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.modules.map((module) => (
          <NavCard
            key={module.key}
            href={module.href}
            eyebrow={module.title}
            title={statusLabel(module.status)}
            description={module.detail}
            statusTone={statusTone(module.status)}
            statusLabel={statusLabel(module.status)}
            cta="Abrir modulo"
          />
        ))}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Previa e assinatura</span>
          <h2>Conferir o certificado e a fila final</h2>
          <p>O workspace aponta para a previa integral e para a fila de assinatura coerentes com este cenario.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/emission/service-order-review?scenario=${mapWorkspaceScenarioToServiceOrderScenario(scenario.id)}`}
          eyebrow="OS"
          title="Abrir detalhe da OS"
          description="Revisar linha do tempo, checklist tecnico e acoes da OS atual."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir OS"
        />
        <NavCard
          href={`/emission/certificate-preview?scenario=${mapWorkspaceScenarioToPreviewScenario(scenario.id, scenario.references.dryRunScenarioId)}`}
          eyebrow="Certificado"
          title="Abrir previa integral"
          description="Revisar os campos que o operador precisa conferir antes da assinatura final."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir previa"
        />
        <NavCard
          href={`/emission/signature-queue?scenario=${mapWorkspaceScenarioToQueueScenario(scenario.id)}`}
          eyebrow="Assinatura"
          title="Abrir fila canonica"
          description="Inspecionar os itens pendentes e a tela final de assinatura antes da emissao."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir fila"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cadastros</span>
          <h2>Clientes e equipamentos que sustentam a operacao</h2>
          <p>O workspace tambem aponta para os cadastros canonicos usados pela emissao e pela revisao tecnica.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/registry/customers?scenario=${mapWorkspaceScenarioToRegistryScenario(scenario.id)}`}
          eyebrow="Clientes"
          title="Abrir lista de clientes"
          description="Conferir o recorte canonico de clientes ativos, em atencao ou bloqueados."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir clientes"
        />
        <NavCard
          href={`/registry/equipment?scenario=${mapWorkspaceScenarioToRegistryScenario(scenario.id)}`}
          eyebrow="Equipamentos"
          title="Abrir lista global de equipamentos"
          description="Validar cadastro minimo, vencimentos e relacionamento com clientes antes da emissao."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir equipamentos"
        />
        <NavCard
          href={`/registry/standards?scenario=${mapWorkspaceScenarioToStandardScenario(scenario.id)}`}
          eyebrow="Padroes"
          title="Abrir carteira de padroes"
          description="Conferir vencimentos, historico de calibracoes e elegibilidade dos padroes usados pela operacao."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir padroes"
        />
        <NavCard
          href={`/registry/procedures?scenario=${procedureContext.scenarioId}&procedure=${procedureContext.procedureId}`}
          eyebrow="Procedimentos"
          title="Abrir lista versionada"
          description="Conferir vigencia, revisoes ativas e procedimentos obsoletos que sustentam a operacao."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir procedimentos"
        />
        <NavCard
          href={`/quality/audit-trail?scenario=${auditTrailContext.scenarioId}&event=${auditTrailContext.eventId}`}
          eyebrow="Auditoria"
          title="Abrir trilha de auditoria"
          description="Conferir a cadeia append-only, reemissoes e integridade do recorte operacional."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir trilha"
        />
        <NavCard
          href={`/quality/nonconformities?scenario=${nonconformityContext.scenarioId}&nc=${nonconformityContext.ncId}`}
          eyebrow="NCs"
          title="Abrir nao conformidades"
          description="Conferir NCs abertas, criticas ou encerradas ligadas ao recorte operacional."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir NCs"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Governanca</span>
          <h2>Configuracoes estruturais da organizacao</h2>
          <p>O workspace tambem aponta para o catalogo canonico de configuracoes que sustenta perfil, numeracao e seguranca.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/settings/organization?scenario=${organizationSettingsContext.scenarioId}&section=${organizationSettingsContext.sectionKey}`}
          eyebrow="Configuracoes"
          title="Abrir organizacao"
          description="Revisar perfil regulatorio, numeracao, auth, notificacoes e LGPD do tenant ativo."
          statusTone={statusTone(scenario.summary.status)}
          statusLabel={statusLabel(scenario.summary.status)}
          cta="Abrir configuracoes"
        />
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.summary.blockers.length === 0
              ? "Nenhum bloqueio consolidado"
              : `${scenario.summary.blockers.length} bloqueio(s) consolidado(s)`}
          </strong>
          <ul>
            {scenario.summary.blockers.length === 0 ? (
              <li>O workspace nao encontrou gate critico bloqueando este cenario.</li>
            ) : (
              scenario.summary.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>
            {scenario.summary.warnings.length === 0
              ? "Sem warnings ativos"
              : `${scenario.summary.warnings.length} warning(s) operacional(is)`}
          </strong>
          <ul>
            {scenario.summary.warnings.length === 0 ? (
              <li>Nenhum warning complementar foi agregado neste cenario.</li>
            ) : (
              scenario.summary.warnings.map((warning) => <li key={warning}>{warning}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proximas acoes</span>
          <strong>{scenario.nextActions.length} passo(s) sugerido(s)</strong>
          <ul>
            {scenario.nextActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do workspace</h2>
          <p>Use os atalhos abaixo para revisar baseline, risco preventivo e bloqueio fail-closed sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/emission/workspace?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir workspace"
          />
        ))}
      </section>
    </AppShell>
  );
}
