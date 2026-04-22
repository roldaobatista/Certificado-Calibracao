import { loadUserDirectoryCatalog } from "@/src/auth/user-directory-api";
import { buildUserDirectoryCatalogView } from "@/src/auth/user-directory-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

function formatRole(role: string): string {
  switch (role) {
    case "admin":
      return "Administrador";
    case "quality_manager":
      return "Gestor da qualidade";
    case "signatory":
      return "Signatario";
    case "technical_reviewer":
      return "Revisor tecnico";
    case "technician":
      return "Tecnico calibrador";
    case "auditor_readonly":
      return "Auditor leitura";
    case "external_client":
      return "Cliente externo";
    default:
      return role;
  }
}

function formatLifecycle(status: string): string {
  switch (status) {
    case "active":
      return "Ativo";
    case "invited":
      return "Convidado";
    case "suspended":
      return "Suspenso";
    default:
      return status;
  }
}

function formatCompetencyStatus(status: string): string {
  switch (status) {
    case "authorized":
      return "Autorizada";
    case "expiring":
      return "Expirando";
    case "expired":
      return "Expirada";
    default:
      return status;
  }
}

export const dynamic = "force-dynamic";

export default async function UserDirectoryPage(props: PageProps) {
  const catalog = await loadUserDirectoryCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Auth - usuarios e competencias"
        title="Diretorio indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico da equipe. Em fail-closed, nenhuma leitura local de usuarios foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o diretorio de usuarios.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar usuarios e competencias ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /auth/users`. Sem resposta valida do backend, o web nao
              assume lista local de usuarios ou competencias.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildUserDirectoryCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Auth - usuarios e competencias"
      title={scenario.label}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Organizacao</span>
          <strong>{scenario.summary.organizationName}</strong>
          <StatusPill
            tone={scenario.summary.status === "ready" ? "ok" : "warn"}
            label={scenario.summary.status === "ready" ? "Equipe saudavel" : "Equipe com atencao"}
          />
          <p>{scenario.summaryLabel}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Usuarios</span>
          <strong>{scenario.summary.activeUsers} ativo(s)</strong>
          <p>{scenario.summary.invitedUsers} convite(s) pendente(s) e {scenario.summary.suspendedUsers} suspenso(s).</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Competencias</span>
          <strong>{scenario.summary.expiringCompetencies} expirando</strong>
          <p>{scenario.summary.expiredCompetencies} vencida(s) no recorte canonico atual.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Uso em V1</span>
          <strong>Base para RBAC e assinatura</strong>
          <p>O diretorio mostra quem pode operar, revisar e assinar antes da emissao oficial.</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.users.map((user) => (
          <article className="nav-card" key={user.userId}>
            <span className="eyebrow">{formatLifecycle(user.status)}</span>
            <strong>{user.displayName}</strong>
            <p>{user.email}</p>
            <div className="chip-list">
              {user.roles.map((role) => (
                <span className="chip" key={role}>
                  {formatRole(role)}
                </span>
              ))}
            </div>
            <div className="chip-list">
              <span className="chip">{user.deviceCount} dispositivo(s)</span>
              {user.teamName ? <span className="chip">{user.teamName}</span> : null}
            </div>
            <div className="chip-list">
              {user.competencies.length === 0 ? (
                <span className="chip chip--warn">Sem competencia operacional</span>
              ) : (
                user.competencies.map((competency) => (
                  <span
                    className={`chip${competency.status === "authorized" ? "" : " chip--warn"}`}
                    key={`${user.userId}-${competency.instrumentType}-${competency.roleLabel}`}
                  >
                    {competency.instrumentType} · {formatCompetencyStatus(competency.status)}
                  </span>
                ))
              )}
            </div>
          </article>
        ))}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o estado da equipe</h2>
          <p>Use os cenarios abaixo para revisar convites, suspensoes e vencimento de competencias sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/auth/users?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={item.summary.status === "ready" ? "ok" : "warn"}
            statusLabel={item.summary.status === "ready" ? "Equipe saudavel" : "Equipe com atencao"}
            cta="Abrir diretorio"
          />
        ))}
      </section>
    </AppShell>
  );
}
