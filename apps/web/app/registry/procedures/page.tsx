import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadProcedureRegistryCatalog } from "@/src/registry/procedure-registry-api";
import { buildProcedureRegistryCatalogView } from "@/src/registry/procedure-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const WEB_BASE_URL = "http://127.0.0.1:3002";

type PageProps = {
  searchParams?: {
    scenario?: string;
    procedure?: string;
    q?: string;
    status?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Procedimento vigente";
    case "attention":
      return "Procedimento em atencao";
    case "blocked":
      return "Procedimento obsoleto";
    default:
      return status;
  }
}

export default async function ProcedureRegistryPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadProcedureRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    procedureId: props.searchParams?.procedure,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Cadastros - procedimentos"
          title="Carteira protegida por sessao"
          description="Os procedimentos persistidos do tenant exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir, cadastrar e arquivar revisoes reais.</p>
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
        eyebrow="Cadastros - procedimentos"
        title="Lista de procedimentos indisponivel"
        description="O back-office nao recebeu o payload canonico de procedimentos. Em fail-closed, nenhuma revisao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a carteira de procedimentos.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar procedimentos ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/procedures`. Sem resposta valida, o web nao
              assume vigencia, revisao ou obsolescencia dos procedimentos.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildProcedureRegistryCatalogView(catalog);
  const detail = scenario.detail;
  const selectedProcedure = scenario.selectedProcedure;
  const search = props.searchParams?.q?.trim().toLowerCase() ?? "";
  const statusFilter = props.searchParams?.status?.trim() ?? "";
  const filteredItems = scenario.items.filter((item) => {
    const matchesQuery =
      search.length === 0 ||
      item.code.toLowerCase().includes(search) ||
      item.title.toLowerCase().includes(search) ||
      item.typeLabel.toLowerCase().includes(search);
    const matchesStatus = statusFilter.length === 0 || item.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  return (
    <AppShell
      eyebrow="Cadastros - procedimentos"
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
          <span className="eyebrow">Vigentes</span>
          <strong>{scenario.summary.activeCount} procedimento(s)</strong>
          <p>{scenario.summary.attentionCount} em atencao e {scenario.summary.obsoleteCount} obsoleto(s).</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{selectedProcedure.code} rev.{selectedProcedure.revisionLabel}</strong>
          <p>{selectedProcedure.title}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Vigencia</span>
          <strong>{selectedProcedure.effectiveSinceLabel}</strong>
          <p>{selectedProcedure.effectiveUntilLabel ?? "Sem encerramento registrado"}</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Filtros</span>
          <h2>Buscar revisoes por codigo, titulo ou status</h2>
          <p>Os filtros abaixo refinam a carteira persistida sem abandonar o contexto atual.</p>
        </div>
        <form className="form-grid" action="/registry/procedures" method="get">
          {props.searchParams?.scenario ? (
            <input type="hidden" name="scenario" value={props.searchParams.scenario} />
          ) : null}
          <label className="field">
            <span>Buscar</span>
            <input defaultValue={props.searchParams?.q ?? ""} name="q" placeholder="PT-005, plataforma..." />
          </label>
          <label className="field">
            <span>Status</span>
            <select defaultValue={statusFilter} name="status">
              <option value="">Todos</option>
              <option value="ready">Vigente</option>
              <option value="attention">Em atencao</option>
              <option value="blocked">Obsoleto</option>
            </select>
          </label>
          <div className="button-row">
            <button className="button-primary" type="submit">
              Aplicar filtro
            </button>
            <a className="button-secondary" href={props.searchParams?.scenario ? `/registry/procedures?scenario=${props.searchParams.scenario}` : "/registry/procedures"}>
              Limpar
            </a>
          </div>
        </form>
      </section>

      {isPersistedMode ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Nova revisao</span>
            <h2>Cadastrar procedimento versionado</h2>
            <p>Use um documento por linha ou separado por virgula para preencher a lista de referencias relacionadas.</p>
          </div>

          <form className="form-grid" action={`${API_BASE_URL}/registry/procedures/manage`} method="post">
            <input type="hidden" name="action" value="save" />
            <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/procedures`} />

            <label className="field">
              <span>Codigo</span>
              <input name="code" placeholder="PT-050" required />
            </label>
            <label className="field">
              <span>Titulo</span>
              <input name="title" placeholder="Calibracao de plataforma pesada" required />
            </label>
            <label className="field">
              <span>Tipo</span>
              <input name="typeLabel" placeholder="NAWI pesada" required />
            </label>
            <label className="field">
              <span>Revisao</span>
              <input name="revisionLabel" placeholder="01" required />
            </label>
            <label className="field">
              <span>Inicio de vigencia</span>
              <input name="effectiveSinceUtc" required type="date" />
            </label>
            <label className="field">
              <span>Fim de vigencia</span>
              <input name="effectiveUntilUtc" type="date" />
            </label>
            <label className="field">
              <span>Ciclo de vida</span>
              <input defaultValue="Vigente" name="lifecycleLabel" required />
            </label>
            <label className="field">
              <span>Uso</span>
              <input name="usageLabel" placeholder="Campo controlado" required />
            </label>
            <label className="field">
              <span>Escopo</span>
              <input name="scopeLabel" placeholder="Balancas plataforma ate 500 kg." required />
            </label>
            <label className="field">
              <span>Ambiente</span>
              <input name="environmentRangeLabel" placeholder="Temp 18C-26C" required />
            </label>
            <label className="field">
              <span>Politica de curva</span>
              <input name="curvePolicyLabel" placeholder="5 pontos com subida e descida" required />
            </label>
            <label className="field">
              <span>Politica de padroes</span>
              <input name="standardsPolicyLabel" placeholder="Padrao de massa M1 vigente" required />
            </label>
            <label className="field">
              <span>Aprovacao</span>
              <input name="approvalLabel" placeholder="Aprovado por Ana Administradora" required />
            </label>
            <label className="field">
              <span>Documentos relacionados</span>
              <textarea defaultValue={"IT-050\nFR-050"} name="relatedDocuments" />
            </label>

            <div className="button-row">
              <button className="button-primary" type="submit">
                Salvar procedimento
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista versionada</span>
          <h2>Procedimentos vigentes e obsoletos</h2>
          <p>A lista abaixo abre o detalhe do procedimento selecionado no mesmo catalogo canonico.</p>
        </div>
      </section>

      <section className="nav-grid">
        {filteredItems.map((item) => (
          <article className="nav-card" key={item.procedureId}>
            <span className="eyebrow">{item.procedureId === selectedProcedure.procedureId ? "Selecionado" : item.code}</span>
            <strong>{item.title} · rev.{item.revisionLabel}</strong>
            <p>{item.typeLabel} · {item.lifecycleLabel} · {item.usageLabel}</p>
            <div className="button-row">
              <a
                className="button-primary"
                href={
                  isPersistedMode
                    ? `/registry/procedures?procedure=${item.procedureId}`
                    : `/registry/procedures?scenario=${scenario.id}&procedure=${item.procedureId}`
                }
              >
                Abrir procedimento
              </a>
              {isPersistedMode ? (
                <form className="inline-form" action={`${API_BASE_URL}/registry/procedures/manage`} method="post">
                  <input
                    type="hidden"
                    name="action"
                    value={item.status === "blocked" ? "restore" : "archive"}
                  />
                  <input type="hidden" name="procedureId" value={item.procedureId} />
                  <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/procedures`} />
                  <button className="button-secondary" type="submit">
                    {item.status === "blocked" ? "Restaurar" : "Arquivar"}
                  </button>
                </form>
              ) : null}
            </div>
          </article>
        ))}
      </section>

      {filteredItems.length === 0 ? (
        <div className="empty-state">Nenhum procedimento corresponde aos filtros aplicados.</div>
      ) : null}

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe do procedimento</span>
          <h2>{detail.title}</h2>
          <p>O painel abaixo resume escopo, ambiente, politica de curva e documentos relacionados do item selecionado.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Escopo</span>
            <strong>{detail.noticeLabel}</strong>
            <p>{detail.scopeLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Ambiente e curva</span>
            <strong>{detail.environmentRangeLabel}</strong>
            <p>{detail.curvePolicyLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Padroes e aprovacao</span>
            <strong>{detail.standardsPolicyLabel}</strong>
            <p>{detail.approvalLabel}</p>
          </article>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Documentos relacionados</span>
          <strong>{detail.relatedDocuments.length} item(ns)</strong>
          <ul>
            {detail.relatedDocuments.map((item) => (
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
          <h2>Rotas relacionadas ao procedimento</h2>
          <p>Use os atalhos abaixo para voltar ao contexto operacional que reutiliza o procedimento selecionado.</p>
        </div>
      </section>

      <section className="nav-grid">
        {detail.links.workspaceScenarioId ? (
          <NavCard
            href={`/emission/workspace?scenario=${detail.links.workspaceScenarioId}`}
            eyebrow="Workspace"
            title="Abrir prontidao consolidada"
            description="Voltar ao workspace que compartilha o mesmo contexto operacional do procedimento."
            cta="Abrir workspace"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Conferir a OS canonica que reaproveita este procedimento."
            cta="Abrir OS"
          />
        ) : null}
        {detail.links.dryRunScenarioId ? (
          <NavCard
            href={`/emission/dry-run?scenario=${detail.links.dryRunScenarioId}`}
            eyebrow="Dry-run"
            title="Abrir dry-run de emissao"
            description="Inspecionar o recorte de emissao que usa o mesmo procedimento selecionado."
            cta="Abrir dry-run"
          />
        ) : null}
      </section>

      {!isPersistedMode ? (
        <>
          <section className="section-header">
            <div className="section-copy">
              <span className="eyebrow">Cenarios</span>
              <h2>Trocar o contexto da carteira</h2>
              <p>Use os cenarios abaixo para revisar baseline, revisao preventiva e consulta de revisoes obsoletas sem alterar codigo.</p>
            </div>
          </section>

          <section className="nav-grid">
            {scenarios.map((item) => (
              <NavCard
                key={item.id}
                href={`/registry/procedures?scenario=${item.id}&procedure=${item.selectedProcedure.procedureId}`}
                eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
                title={item.label}
                description={item.summaryLabel}
                statusTone={statusTone(item.summary.status)}
                statusLabel={statusLabel(item.summary.status)}
                cta="Abrir procedimentos"
              />
            ))}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
