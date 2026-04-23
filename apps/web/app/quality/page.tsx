import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadQualityHubCatalog } from "@/src/quality/quality-hub-api";
import { buildQualityHubCatalogView } from "@/src/quality/quality-hub-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    module?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Qualidade estavel";
    case "attention":
      return "Qualidade com atencao";
    case "blocked":
      return "Qualidade bloqueada";
    default:
      return status;
  }
}

function moduleStatusLabel(
  status: "ready" | "attention" | "blocked",
  availability: "implemented" | "planned",
): string {
  if (availability === "planned") {
    return status === "blocked" ? "Planejado com risco" : "Planejado";
  }

  switch (status) {
    case "ready":
      return "Modulo ativo";
    case "attention":
      return "Modulo com atencao";
    case "blocked":
      return "Modulo bloqueado";
    default:
      return status;
  }
}

export default async function QualityHubPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadQualityHubCatalog({
    scenarioId: props.searchParams?.scenario,
    moduleKey: props.searchParams?.module,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Qualidade - hub"
          title="Hub protegido por sessao"
          description="A leitura persistida da V5 exige autenticacao antes de consolidar Qualidade e governanca reais."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel de Qualidade para abrir o hub persistido do tenant.</p>
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
        eyebrow="Qualidade - hub"
        title="Hub de Qualidade indisponivel"
        description="O back-office nao recebeu o payload canonico do hub de Qualidade. Em fail-closed, o web nao assume backlog, indicadores ou priorizacao local."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o hub da Qualidade.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o hub ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /quality`. Sem resposta valida, o web nao inventa
              consolidacao de NC, trilha, reclamacoes, riscos ou analise critica.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildQualityHubCatalogView(catalog);
  const selectedModule = scenario.selectedModule;

  return (
    <AppShell
      eyebrow="Qualidade - hub"
      title={`Qualidade · ${scenario.summary.organizationName}`}
      description={
        authSession?.authenticated === true && !props.searchParams?.scenario
          ? `${scenario.description} Este painel esta lendo a V5 persistida do tenant autenticado.`
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
          <span className="eyebrow">NC abertas</span>
          <strong>{scenario.summary.openNonconformities}</strong>
          <p>{scenario.summary.overdueActions} acao(oes) vencendo no recorte atual.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Auditoria e revisao</span>
          <strong>{scenario.summary.auditProgramCount} ciclo(s) no programa</strong>
          <p>Proxima analise critica: {scenario.summary.nextManagementReviewLabel}.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Reclamacoes e riscos</span>
          <strong>{scenario.summary.complaintCount} reclamacao(oes)</strong>
          <p>{scenario.summary.activeRiskCount} risco(s) ativo(s) monitorado(s) neste recorte.</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Implementacao</span>
          <strong>{scenario.summary.implementedModuleCount} modulo(s) ativos</strong>
          <p>{scenario.summary.plannedModuleCount} area(s) continuam planejadas e visiveis como backlog regulado.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Modulo selecionado</span>
          <strong>{selectedModule.title}</strong>
          <p>{selectedModule.metricLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Resumo do hub</span>
          <strong>{scenario.summaryLabel}</strong>
          <p>O hub consolida leituras canonicas ja existentes e explicita gaps sem simular fluxos transacionais.</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.modules.map((module) => (
          <NavCard
            key={module.key}
            href={`/quality?scenario=${scenario.id}&module=${module.key}`}
            eyebrow={module.availability === "implemented" ? "Implementado" : "Planejado"}
            title={module.title}
            description={`${module.metricLabel} · ${module.summary}`}
            statusTone={statusTone(module.status)}
            statusLabel={moduleStatusLabel(module.status, module.availability)}
            cta={module.availability === "implemented" ? "Inspecionar" : "Ver gap"}
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Escopo normativo</span>
          <strong>{selectedModule.clauseLabel}</strong>
          <p>{selectedModule.summary}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Disponibilidade</span>
          <strong>{selectedModule.availability === "implemented" ? "Leitura ativa" : "Area planejada"}</strong>
          <p>{selectedModule.nextStepLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Acao imediata</span>
          <strong>{selectedModule.metricLabel}</strong>
          <p>
            {selectedModule.availability === "implemented"
              ? "Use o acesso rapido abaixo para abrir a leitura dedicada sem perder o contexto do hub."
              : "O hub explicita o gap atual, mas nao inventa payload transacional enquanto a area nao existir."}
          </p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{selectedModule.blockers.length} bloqueio(s)</strong>
          <ul>
            {selectedModule.blockers.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {selectedModule.blockers.length === 0 ? <li>Sem bloqueios adicionais neste modulo.</li> : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{selectedModule.warnings.length} warning(s)</strong>
          <ul>
            {selectedModule.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {selectedModule.warnings.length === 0 ? <li>Sem warnings adicionais neste modulo.</li> : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Backlog honesto</span>
          <strong>{scenario.summary.plannedModuleCount} area(s) ainda planejada(s)</strong>
          <p>O hub deixa os gaps visiveis para evitar que a operacao dependa de memoria efemera ou planilhas soltas.</p>
        </article>
      </section>

      <section className="nav-grid">
        {selectedModule.href ? (
          <NavCard
            href={selectedModule.href}
            eyebrow="Modulo dedicado"
            title={`Abrir ${selectedModule.title.toLowerCase()}`}
            description="Ir para a leitura canonica dedicada preservando o contexto do hub."
            cta={selectedModule.ctaLabel}
          />
        ) : null}
        {scenario.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${scenario.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir workspace operacional"
            description="Voltar ao recorte operacional que compartilha o mesmo contexto da Qualidade."
            cta="Abrir workspace"
          />
        ) : null}
        {scenario.links.organizationSettingsScenarioId ? (
          <NavCard
            href={`/settings/organization?scenario=${scenario.links.organizationSettingsScenarioId}`}
            eyebrow="Configuracoes"
            title="Abrir configuracoes da organizacao"
            description="Conferir identidade, perfil regulatorio, seguranca e governanca do mesmo recorte."
            cta="Abrir configuracoes"
          />
        ) : null}
        {scenario.links.auditTrailScenarioId ? (
          <NavCard
            href={`/quality/audit-trail?scenario=${scenario.links.auditTrailScenarioId}`}
            eyebrow="Auditoria"
            title="Abrir trilha de auditoria"
            description="Inspecionar a cadeia append-only ligada ao recorte atual."
            cta="Abrir trilha"
          />
        ) : null}
        {scenario.links.nonconformityScenarioId ? (
          <NavCard
            href={`/quality/nonconformities?scenario=${scenario.links.nonconformityScenarioId}`}
            eyebrow="NC"
            title="Abrir nao conformidades"
            description="Conferir a NC ou o historico da qualidade que sustenta este recorte."
            cta="Abrir NCs"
          />
        ) : null}
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/quality?scenario=${item.id}&module=${item.selectedModule.key}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir hub"
          />
        ))}
      </section>
    </AppShell>
  );
}
