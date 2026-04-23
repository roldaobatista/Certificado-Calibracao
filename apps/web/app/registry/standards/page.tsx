import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadStandardRegistryCatalog } from "@/src/registry/standard-registry-api";
import { buildStandardRegistryCatalogView } from "@/src/registry/standard-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const WEB_BASE_URL = "http://127.0.0.1:3002";

type PageProps = {
  searchParams?: {
    scenario?: string;
    standard?: string;
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
      return "Padrao pronto";
    case "attention":
      return "Padrao em atencao";
    case "blocked":
      return "Padrao bloqueado";
    default:
      return status;
  }
}

export default async function StandardRegistryPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadStandardRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    standardId: props.searchParams?.standard,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Cadastros - padroes"
          title="Carteira protegida por sessao"
          description="Os padroes persistidos do tenant exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir, cadastrar e arquivar padroes reais.</p>
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
        eyebrow="Cadastros - padroes"
        title="Lista de padroes indisponivel"
        description="O back-office nao recebeu o payload canonico de padroes. Em fail-closed, nenhuma reserva ou vencimento local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a carteira de padroes.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar padroes ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/standards`. Sem resposta valida, o web nao assume
              validade, historico ou elegibilidade do padrao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildStandardRegistryCatalogView(catalog);
  const selectedStandard = scenario.selectedStandard;
  const search = props.searchParams?.q?.trim().toLowerCase() ?? "";
  const statusFilter = props.searchParams?.status?.trim() ?? "";
  const filteredItems = scenario.items.filter((item) => {
    const matchesQuery =
      search.length === 0 ||
      item.kindLabel.toLowerCase().includes(search) ||
      item.certificateLabel.toLowerCase().includes(search) ||
      item.sourceLabel.toLowerCase().includes(search);
    const matchesStatus = statusFilter.length === 0 || item.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  return (
    <AppShell
      eyebrow="Cadastros - padroes"
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
          <span className="eyebrow">Carteira</span>
          <strong>{scenario.summary.activeCount} padrao(es) ativo(s)</strong>
          <p>
            {scenario.summary.expiringSoonCount} em atencao e {scenario.summary.expiredCount} bloqueado(s) no recorte
            atual.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{scenario.detail.title}</strong>
          <p>{scenario.detail.noticeLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Origem</span>
          <strong>{selectedStandard.sourceLabel}</strong>
          <p>{selectedStandard.certificateLabel}</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Filtros</span>
          <h2>Buscar por origem, certificado ou status</h2>
          <p>Os filtros abaixo atuam sobre a carteira real de padroes carregada do backend.</p>
        </div>
        <form className="form-grid" action="/registry/standards" method="get">
          {props.searchParams?.scenario ? (
            <input type="hidden" name="scenario" value={props.searchParams.scenario} />
          ) : null}
          <label className="field">
            <span>Buscar</span>
            <input defaultValue={props.searchParams?.q ?? ""} name="q" placeholder="RBC, 1234/25/081..." />
          </label>
          <label className="field">
            <span>Status</span>
            <select defaultValue={statusFilter} name="status">
              <option value="">Todos</option>
              <option value="ready">Pronto</option>
              <option value="attention">Em atencao</option>
              <option value="blocked">Bloqueado</option>
            </select>
          </label>
          <div className="button-row">
            <button className="button-primary" type="submit">
              Aplicar filtro
            </button>
            <a className="button-secondary" href={props.searchParams?.scenario ? `/registry/standards?scenario=${props.searchParams.scenario}` : "/registry/standards"}>
              Limpar
            </a>
          </div>
        </form>
      </section>

      {isPersistedMode ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Novo padrao</span>
            <h2>Cadastrar padrao com validade e faixa aplicavel</h2>
            <p>O formulario abaixo grava um padrao real na carteira V2 e devolve o operador para esta lista.</p>
          </div>

          <form className="form-grid" action={`${API_BASE_URL}/registry/standards/manage`} method="post">
            <input type="hidden" name="action" value="save" />
            <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/standards`} />

            <label className="field">
              <span>Codigo</span>
              <input name="code" placeholder="PESO-050" required />
            </label>
            <label className="field">
              <span>Titulo</span>
              <input name="title" placeholder="Peso padrao 50 kg" required />
            </label>
            <label className="field">
              <span>Tipo</span>
              <input name="kindLabel" placeholder="Peso" required />
            </label>
            <label className="field">
              <span>Classe nominal</span>
              <input name="nominalClassLabel" placeholder="50 kg · M1" required />
            </label>
            <label className="field">
              <span>Origem</span>
              <input name="sourceLabel" placeholder="RBC-5050" required />
            </label>
            <label className="field">
              <span>Certificado</span>
              <input name="certificateLabel" placeholder="5050/26/001" required />
            </label>
            <label className="field">
              <span>Fabricante</span>
              <input name="manufacturerLabel" placeholder="Coelmatic" required />
            </label>
            <label className="field">
              <span>Modelo</span>
              <input name="modelLabel" placeholder="M50K" required />
            </label>
            <label className="field">
              <span>Serie</span>
              <input name="serialNumberLabel" placeholder="50K-001" required />
            </label>
            <label className="field">
              <span>Valor nominal</span>
              <input name="nominalValueLabel" placeholder="50,000 kg" required />
            </label>
            <label className="field">
              <span>Classe</span>
              <input name="classLabel" placeholder="M1" required />
            </label>
            <label className="field">
              <span>Faixa de uso</span>
              <input name="usageRangeLabel" placeholder="0 kg ate 50 kg" required />
            </label>
            <label className="field">
              <span>Valor de medicao</span>
              <input defaultValue="50" name="measurementValue" step="0.001" type="number" />
            </label>
            <label className="field">
              <span>Faixa minima</span>
              <input defaultValue="0" name="applicableRangeMin" step="0.001" type="number" />
            </label>
            <label className="field">
              <span>Faixa maxima</span>
              <input defaultValue="50" name="applicableRangeMax" step="0.001" type="number" />
            </label>
            <label className="field">
              <span>Incerteza</span>
              <input name="uncertaintyLabel" placeholder="+/- 0,020 kg" required />
            </label>
            <label className="field">
              <span>Fator de correcao</span>
              <input name="correctionFactorLabel" placeholder="+0,001 kg" required />
            </label>
            <label className="field">
              <span>Validade do certificado</span>
              <input name="certificateValidUntilUtc" type="date" />
            </label>
            <label className="toggle-field">
              <input defaultChecked name="hasValidCertificate" type="checkbox" />
              <span>Certificado valido</span>
            </label>

            <div className="button-row">
              <button className="button-primary" type="submit">
                Salvar padrao
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista canonica</span>
          <h2>Padroes e auxiliares monitorados</h2>
          <p>A lista abaixo abre o detalhe do padrao com o mesmo cenario canonico usado pelo backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {filteredItems.map((item) => (
          <article className="nav-card" key={item.standardId}>
            <span className="eyebrow">{item.standardId === selectedStandard.standardId ? "Selecionado" : "Padrao"}</span>
            <strong>{item.standardId.replace("standard-", "").toUpperCase()} · {item.nominalClassLabel}</strong>
            <p>{item.kindLabel} · {item.sourceLabel} · validade {item.validUntilLabel}</p>
            <div className="button-row">
              <a
                className="button-primary"
                href={
                  isPersistedMode
                    ? `/registry/standard-detail?standard=${item.standardId}`
                    : `/registry/standard-detail?scenario=${scenario.id}&standard=${item.standardId}`
                }
              >
                Abrir detalhe
              </a>
              {isPersistedMode ? (
                <form className="inline-form" action={`${API_BASE_URL}/registry/standards/manage`} method="post">
                  <input
                    type="hidden"
                    name="action"
                    value={item.status === "blocked" ? "restore" : "archive"}
                  />
                  <input type="hidden" name="standardId" value={item.standardId} />
                  <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/standards`} />
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
        <div className="empty-state">Nenhum padrao corresponde aos filtros aplicados.</div>
      ) : null}

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Painel de vencimentos</span>
          <h2>Resumo preventivo da carteira</h2>
          <p>O painel abaixo traduz o horizonte de vencimento que a operacao precisa acompanhar antes da proxima OS.</p>
        </div>

        <div className="detail-grid">
          {scenario.summary.expirationPanel.map((marker) => (
            <article className="detail-card" key={marker.standardId}>
              <span className="eyebrow">{marker.label}</span>
              <strong>{marker.dueInLabel}</strong>
              <StatusPill tone={statusTone(marker.status)} label={statusLabel(marker.status)} />
            </article>
          ))}
        </div>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Continuar a partir do padrao</h2>
          <p>Os atalhos abaixo mantem a navegacao coerente entre padrao, equipamento, OS e dry-run.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode
              ? `/registry/standard-detail?standard=${selectedStandard.standardId}`
              : `/registry/standard-detail?scenario=${scenario.id}&standard=${selectedStandard.standardId}`
          }
          eyebrow="Padrao"
          title="Abrir detalhe do padrao"
          description="Conferir historico de calibracoes, OS recentes e bloqueios do item selecionado."
          cta="Abrir detalhe"
        />
        {scenario.detail.links.registryScenarioId && scenario.detail.links.selectedEquipmentId ? (
          <NavCard
            href={
              isPersistedMode
                ? `/registry/equipment?equipment=${scenario.detail.links.selectedEquipmentId}`
                : `/registry/equipment?scenario=${scenario.detail.links.registryScenarioId}&equipment=${scenario.detail.links.selectedEquipmentId}`
            }
            eyebrow="Equipamento"
            title="Abrir lista global de equipamentos"
            description="Ir para o equipamento que usa este padrao no mesmo recorte operacional."
            cta="Abrir equipamento"
          />
        ) : null}
      </section>

      {!isPersistedMode ? (
        <>
          <section className="section-header">
            <div className="section-copy">
              <span className="eyebrow">Cenarios</span>
              <h2>Trocar o contexto da carteira</h2>
              <p>Use os cenarios abaixo para revisar baseline, vencimento iminente e bloqueio por expiracao sem alterar codigo.</p>
            </div>
          </section>

          <section className="nav-grid">
            {scenarios.map((item) => (
              <NavCard
                key={item.id}
                href={`/registry/standards?scenario=${item.id}&standard=${item.selectedStandard.standardId}`}
                eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
                title={item.label}
                description={item.summaryLabel}
                statusTone={statusTone(item.summary.status)}
                statusLabel={statusLabel(item.summary.status)}
                cta="Abrir padroes"
              />
            ))}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
