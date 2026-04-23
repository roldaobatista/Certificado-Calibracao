import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadOrganizationSettingsCatalog } from "@/src/settings/organization-settings-api";
import { buildOrganizationSettingsCatalogView } from "@/src/settings/organization-settings-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    section?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Configurada";
    case "attention":
      return "Em atencao";
    case "blocked":
      return "Bloqueada";
    default:
      return status;
  }
}

export default async function OrganizationSettingsPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadOrganizationSettingsCatalog({
    scenarioId: props.searchParams?.scenario,
    sectionKey: props.searchParams?.section,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Configuracoes - organizacao"
          title="Configuracoes protegidas por sessao"
          description="A governanca regulatoria persistida da V5 exige autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir o perfil regulatorio real do tenant.</p>
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
        eyebrow="Configuracoes - organizacao"
        title="Configuracoes indisponiveis para revisao"
        description="O back-office nao recebeu o payload canonico da organizacao. Em fail-closed, nenhuma configuracao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar as configuracoes da organizacao.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar as configuracoes ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /settings/organization`. Sem resposta valida, o web nao
              assume perfil, numeracao, seguranca ou LGPD da organizacao ativa.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildOrganizationSettingsCatalogView(catalog);
  const detail = scenario.detail;

  return (
      <AppShell
        eyebrow="Configuracoes - organizacao"
        title={scenario.summary.organizationName}
        description={
          authSession?.authenticated === true && !props.searchParams?.scenario
            ? `${scenario.description} A pagina esta exibindo a governanca persistida da V5.`
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
          <span className="eyebrow">Perfil atual</span>
          <strong>{scenario.summary.profileLabel}</strong>
          <p>{scenario.summary.accreditationLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Codigo e plano</span>
          <strong>{scenario.summary.organizationCode}</strong>
          <p>{scenario.summary.planLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Secoes</span>
          <strong>{scenario.summary.configuredSections} configurada(s)</strong>
          <p>
            {scenario.summary.attentionSections} em atencao e {scenario.summary.blockedSections} bloqueada(s).
          </p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Secoes configuraveis</span>
          <h2>Trocar o foco da leitura canonicamente tipada</h2>
          <p>As secoes abaixo usam a mesma carga canonica do backend e permitem revisar a governanca por querystring.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.sections.map((section) => (
          <NavCard
            key={section.key}
            href={`/settings/organization?scenario=${scenario.id}&section=${section.key}`}
            eyebrow={section.key === scenario.selectedSectionKey ? "Selecionada" : section.ownerLabel}
            title={section.title}
            description={`${section.detail} / ${section.lastUpdatedLabel}`}
            statusTone={statusTone(section.status)}
            statusLabel={statusLabel(section.status)}
            cta={section.actionLabel}
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Secao ativa</span>
          <strong>{detail.title}</strong>
          <p>{detail.summary}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Ultima revisao</span>
          <strong>{detail.lastReviewedLabel}</strong>
          <p>{detail.reviewModeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Evidencia</span>
          <strong>{statusLabel(detail.status)}</strong>
          <p>{detail.evidenceLabel}</p>
        </article>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Checklist</span>
          <strong>{detail.checklistItems.length} item(ns)</strong>
          <ul>
            {detail.checklistItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {detail.blockers.length === 0 ? (
              <li>Sem bloqueios adicionais nesta secao.</li>
            ) : (
              detail.blockers.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{detail.warnings.length} warning(s)</strong>
          <ul>
            {detail.warnings.length === 0 ? (
              <li>Sem warnings adicionais nesta secao.</li>
            ) : (
              detail.warnings.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Abrir os modulos relacionados a esta secao</h2>
          <p>Os links abaixo mantem o contexto canonico entre configuracoes, onboarding, auth, workspace e qualidade.</p>
        </div>
      </section>

      <section className="nav-grid">
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao consolidada"
            description="Voltar ao recorte operacional que compartilha esta configuracao."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.onboardingScenarioId ? (
          <NavCard
            href={`/onboarding?scenario=${detail.links.onboardingScenarioId}`}
            eyebrow="Onboarding"
            title="Abrir prontidao da organizacao"
            description="Revisar os passos do onboarding relacionados a esta secao."
            cta="Abrir onboarding"
          />
        ) : null}
        {detail.links.selfSignupScenarioId ? (
          <NavCard
            href={`/auth/self-signup?scenario=${detail.links.selfSignupScenarioId}`}
            eyebrow="Auth"
            title="Abrir auto-cadastro"
            description="Conferir o recorte canonico de providers e MFA que sustenta esta secao."
            cta="Abrir auth"
          />
        ) : null}
        {detail.links.userDirectoryScenarioId ? (
          <NavCard
            href={`/auth/users?scenario=${detail.links.userDirectoryScenarioId}`}
            eyebrow="Equipe"
            title="Abrir usuarios e competencias"
            description="Inspecionar a equipe e as competencias relacionadas a esta governanca."
            cta="Abrir equipe"
          />
        ) : null}
        {detail.links.auditTrailScenarioId ? (
          <NavCard
            href={`/quality/audit-trail?scenario=${detail.links.auditTrailScenarioId}`}
            eyebrow="Auditoria"
            title="Abrir trilha de auditoria"
            description="Conferir o registro append-only relacionado a esta secao."
            cta="Abrir trilha"
          />
        ) : null}
        {detail.links.standardScenarioId ? (
          <NavCard
            href={`/registry/standards?scenario=${detail.links.standardScenarioId}`}
            eyebrow="Padroes"
            title="Abrir carteira de padroes"
            description="Conferir os padroes relacionados ao perfil regulatorio atual."
            cta="Abrir padroes"
          />
        ) : null}
        {detail.links.procedureScenarioId ? (
          <NavCard
            href={`/registry/procedures?scenario=${detail.links.procedureScenarioId}`}
            eyebrow="Procedimentos"
            title="Abrir lista versionada"
            description="Revisar o procedimento documental ligado a esta secao."
            cta="Abrir procedimentos"
          />
        ) : null}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto das configuracoes</h2>
          <p>Use os cenarios abaixo para revisar baseline, renovacao preventiva e bloqueio de mudanca sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/settings/organization?scenario=${item.id}&section=${item.selectedSection.key}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir configuracoes"
          />
        ))}
      </section>
    </AppShell>
  );
}
