import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadCustomerRegistryCatalog } from "@/src/registry/customer-registry-api";
import { loadEquipmentRegistryCatalog } from "@/src/registry/equipment-registry-api";
import { buildEquipmentRegistryCatalogView } from "@/src/registry/equipment-registry-scenarios";
import { loadProcedureRegistryCatalog } from "@/src/registry/procedure-registry-api";
import { loadStandardRegistryCatalog } from "@/src/registry/standard-registry-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const WEB_BASE_URL = "http://127.0.0.1:3002";

type PageProps = {
  searchParams?: {
    scenario?: string;
    equipment?: string;
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
      return "Equipamento pronto";
    case "attention":
      return "Equipamento em atencao";
    case "blocked":
      return "Equipamento bloqueado";
    default:
      return status;
  }
}

function mapEquipmentScenarioToStandardScenario(equipmentScenarioId: string): string {
  switch (equipmentScenarioId) {
    case "certificate-attention":
      return "expiration-attention";
    case "registration-blocked":
      return "expired-blocked";
    default:
      return "operational-ready";
  }
}

function mapEquipmentToStandardId(equipmentId: string): string {
  switch (equipmentId) {
    case "equipment-002":
      return "standard-002";
    case "equipment-003":
      return "standard-005";
    case "equipment-004":
      return "standard-010";
    default:
      return "standard-001";
  }
}

export default async function EquipmentRegistryPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadEquipmentRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    equipmentId: props.searchParams?.equipment,
    cookieHeader,
  });

  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;
  const [customerCatalog, standardCatalog, procedureCatalog] = isPersistedMode
    ? await Promise.all([
        loadCustomerRegistryCatalog({ cookieHeader }),
        loadStandardRegistryCatalog({ cookieHeader }),
        loadProcedureRegistryCatalog({ cookieHeader }),
      ])
    : [null, null, null];

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Cadastros - equipamentos"
          title="Lista protegida por sessao"
          description="Os equipamentos persistidos do tenant exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir, cadastrar e arquivar equipamentos reais.</p>
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
        eyebrow="Cadastros - equipamentos"
        title="Lista global de equipamentos indisponivel"
        description="O back-office nao recebeu o payload canonico de equipamentos. Em fail-closed, nenhum item local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a lista global de equipamentos.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar equipamentos ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/equipment`. Sem resposta valida, o web nao assume
              cliente vinculado, status cadastral ou vencimento do equipamento.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildEquipmentRegistryCatalogView(catalog);
  const selectedEquipment = scenario.selectedEquipment;
  const search = props.searchParams?.q?.trim().toLowerCase() ?? "";
  const statusFilter = props.searchParams?.status?.trim() ?? "";
  const filteredItems = scenario.items.filter((item) => {
    const matchesQuery =
      search.length === 0 ||
      item.code.toLowerCase().includes(search) ||
      item.tagCode.toLowerCase().includes(search) ||
      item.customerName.toLowerCase().includes(search);
    const matchesStatus = statusFilter.length === 0 || item.status === statusFilter;
    return matchesQuery && matchesStatus;
  });

  const customerOptions = customerCatalog?.scenarios[0]?.customers ?? [];
  const standardOptions = standardCatalog?.scenarios[0]?.items ?? [];
  const procedureOptions = procedureCatalog?.scenarios[0]?.items ?? [];

  return (
    <AppShell
      eyebrow="Cadastros - equipamentos"
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
          <span className="eyebrow">Equipamentos</span>
          <strong>{scenario.summary.totalEquipment} item(ns)</strong>
          <p>
            {scenario.summary.readyCount} pronto(s), {scenario.summary.attentionCount} em atencao e{" "}
            {scenario.summary.blockedCount} bloqueado(s).
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{selectedEquipment.code}</strong>
          <p>
            {selectedEquipment.customerName} · {selectedEquipment.typeModelLabel}
          </p>
          <div className="chip-list">
            <span className="chip">{selectedEquipment.tagCode}</span>
            <span className="chip">{selectedEquipment.serialNumber}</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Cadastro</span>
          <strong>{selectedEquipment.registrationStatusLabel}</strong>
          <p>{scenario.detail.statusLine}</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Filtros</span>
          <h2>Buscar por codigo, tag, cliente ou status</h2>
          <p>Os filtros abaixo atuam sobre a lista real de equipamentos carregada do backend.</p>
        </div>
        <form className="form-grid" action="/registry/equipment" method="get">
          {props.searchParams?.scenario ? (
            <input type="hidden" name="scenario" value={props.searchParams.scenario} />
          ) : null}
          <label className="field">
            <span>Buscar</span>
            <input defaultValue={props.searchParams?.q ?? ""} name="q" placeholder="EQ-050, BAL-007, Lab. Acme" />
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
            <a className="button-secondary" href={props.searchParams?.scenario ? `/registry/equipment?scenario=${props.searchParams.scenario}` : "/registry/equipment"}>
              Limpar
            </a>
          </div>
        </form>
      </section>

      {isPersistedMode ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Novo equipamento</span>
            <h2>Cadastrar equipamento com vinculos obrigatorios</h2>
            <p>V2.5 exige cliente, procedimento, padrao principal e endereco minimo antes da operacao.</p>
          </div>

          <form className="form-grid" action={`${API_BASE_URL}/registry/equipment/manage`} method="post">
            <input type="hidden" name="action" value="save" />
            <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/equipment`} />

            <label className="field">
              <span>Cliente</span>
              <select name="customerId" required>
                <option value="">Selecione</option>
                {customerOptions.map((customer) => (
                  <option key={customer.customerId} value={customer.customerId}>
                    {customer.tradeName}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Procedimento</span>
              <select name="procedureId" required>
                <option value="">Selecione</option>
                {procedureOptions.map((procedure) => (
                  <option key={procedure.procedureId} value={procedure.procedureId}>
                    {procedure.code} rev.{procedure.revisionLabel}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Padrao principal</span>
              <select name="primaryStandardId" required>
                <option value="">Selecione</option>
                {standardOptions.map((standard) => (
                  <option key={standard.standardId} value={standard.standardId}>
                    {standard.standardId} · {standard.nominalClassLabel}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Codigo</span>
              <input name="code" placeholder="EQ-050" required />
            </label>
            <label className="field">
              <span>Tag</span>
              <input name="tagCode" placeholder="PLAT-050" required />
            </label>
            <label className="field">
              <span>Serie</span>
              <input name="serialNumber" placeholder="SN-050" required />
            </label>
            <label className="field">
              <span>Tipo/modelo</span>
              <input name="typeModelLabel" placeholder="Balanca plataforma 500 kg" required />
            </label>
            <label className="field">
              <span>Capacidade/classe</span>
              <input name="capacityClassLabel" placeholder="500 kg · 0,1 kg · III" required />
            </label>
            <label className="field">
              <span>Tipo metrologico</span>
              <select defaultValue="" name="instrumentKind">
                <option value="">Nao informar</option>
                <option value="nawi">NAWI/IPNA</option>
                <option value="analytical_balance">Balanca analitica</option>
                <option value="precision_balance">Balanca de precisao</option>
                <option value="platform_scale">Balanca plataforma</option>
                <option value="vehicle_scale">Balanca rodoviaria</option>
              </select>
            </label>
            <label className="field">
              <span>Unidade canonica</span>
              <input name="measurementUnit" placeholder="kg" />
            </label>
            <label className="field">
              <span>Capacidade maxima</span>
              <input name="maximumCapacityValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Capacidade minima</span>
              <input name="minimumCapacityValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Divisao real d</span>
              <input name="readabilityValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Divisao de verificacao e</span>
              <input name="verificationScaleIntervalValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Classe normativa</span>
              <select defaultValue="" name="normativeClass">
                <option value="">Nao informar</option>
                <option value="i">Classe I</option>
                <option value="ii">Classe II</option>
                <option value="iii">Classe III</option>
                <option value="iiii">Classe IIII</option>
              </select>
            </label>
            <label className="field">
              <span>Carga minima</span>
              <input name="minimumLoadValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Faixa efetiva minima</span>
              <input name="effectiveRangeMinValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Faixa efetiva maxima</span>
              <input name="effectiveRangeMaxValue" step="0.000001" type="number" />
            </label>
            <label className="field">
              <span>Padroes de apoio</span>
              <input name="supportingStandardCodes" placeholder="PESO-001, PESO-002" />
            </label>
            <label className="field">
              <span>Endereco</span>
              <input name="addressLine1" placeholder="Rua da Calibracao, 500" required />
            </label>
            <label className="field">
              <span>Cidade</span>
              <input name="addressCity" placeholder="Cuiaba" required />
            </label>
            <label className="field">
              <span>Estado</span>
              <input name="addressState" placeholder="MT" required />
            </label>
            <label className="field">
              <span>CEP</span>
              <input name="addressPostalCode" placeholder="78000-500" />
            </label>
            <label className="field">
              <span>Pais</span>
              <input defaultValue="Brasil" name="addressCountry" required />
            </label>
            <label className="field">
              <span>Condicoes do local</span>
              <input name="addressConditionsLabel" placeholder="Area coberta" />
            </label>
            <label className="field">
              <span>Ultima calibracao</span>
              <input name="lastCalibrationAtUtc" type="date" />
            </label>
            <label className="field">
              <span>Proxima calibracao</span>
              <input name="nextCalibrationAtUtc" type="date" />
            </label>

            <div className="button-row">
              <button className="button-primary" type="submit">
                Salvar equipamento
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="nav-grid">
        {filteredItems.map((item) => (
          <article className="nav-card" key={item.equipmentId}>
            <span className="eyebrow">{item.equipmentId === selectedEquipment.equipmentId ? "Selecionado" : "Equipamento"}</span>
            <strong>
              {item.code} · {item.tagCode}
            </strong>
            <p>{item.customerName} · {item.typeModelLabel} · prox. {item.nextCalibrationLabel}</p>
            <div className="button-row">
              <a
                className="button-primary"
                href={
                  isPersistedMode
                    ? `/registry/equipment?equipment=${item.equipmentId}`
                    : `/registry/equipment?scenario=${scenario.id}&equipment=${item.equipmentId}`
                }
              >
                Abrir item
              </a>
              {isPersistedMode ? (
                <form className="inline-form" action={`${API_BASE_URL}/registry/equipment/manage`} method="post">
                  <input
                    type="hidden"
                    name="action"
                    value={item.status === "blocked" ? "restore" : "archive"}
                  />
                  <input type="hidden" name="equipmentId" value={item.equipmentId} />
                  <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/equipment`} />
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
        <div className="empty-state">Nenhum equipamento corresponde aos filtros aplicados.</div>
      ) : null}

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe do equipamento</span>
          <h2>{scenario.detail.title}</h2>
          <p>O painel abaixo resume cliente vinculado, endereco, padroes e ultimo uso operacional do item selecionado.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Cliente vinculado</span>
            <strong>{scenario.detail.customerLabel}</strong>
            <p>{scenario.detail.addressLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Padroes e procedimento</span>
            <strong>{scenario.detail.standardSetLabel}</strong>
            <p>{scenario.detail.lastServiceOrderLabel}</p>
          </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima calibracao</span>
          <strong>{scenario.detail.nextCalibrationLabel}</strong>
          <p>O estado abaixo continua fail-closed quando o cadastro minimo ou a janela operacional exigem acao.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Perfil metrologico</span>
          <strong>{scenario.detail.metrologySummaryLabel ?? "Perfil metrologico canonico pendente."}</strong>
          <p>Essa camada prepara `Max`, `d`, `e` e classe normativa para a engine real.</p>
        </article>
      </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{scenario.detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {scenario.detail.blockers.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {scenario.detail.blockers.length === 0 ? <li>Sem bloqueios adicionais neste cenario.</li> : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{scenario.detail.warnings.length} warning(s)</strong>
          <ul>
            {scenario.detail.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
            {scenario.detail.warnings.length === 0 ? <li>Sem warnings adicionais neste cenario.</li> : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Capacidade</span>
          <strong>{selectedEquipment.capacityClassLabel}</strong>
          <p>{selectedEquipment.lastCalibrationLabel} foi a ultima calibracao registrada no recorte atual.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas ao equipamento</h2>
          <p>Use os atalhos abaixo para voltar ao cliente, a OS ou ao dry-run que compartilham o mesmo contexto.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode
              ? `/registry/customer-detail?customer=${scenario.detail.links.customerId}`
              : `/registry/customer-detail?scenario=${scenario.detail.links.customerScenarioId}&customer=${scenario.detail.links.customerId}`
          }
          eyebrow="Cliente"
          title="Abrir detalhe do cliente"
          description="Voltar ao cadastro do cliente vinculado ao equipamento selecionado."
          cta="Abrir cliente"
        />
        <NavCard
          href={
            isPersistedMode
              ? "/registry/standards"
              : `/registry/standard-detail?scenario=${mapEquipmentScenarioToStandardScenario(scenario.id)}&standard=${mapEquipmentToStandardId(selectedEquipment.equipmentId)}`
          }
          eyebrow="Padroes"
          title="Abrir detalhe do padrao"
          description={
            isPersistedMode
              ? "Abrir a carteira persistida de padroes para localizar o item principal vinculado."
              : "Conferir o padrao canonico mais relevante para o equipamento selecionado neste recorte."
          }
          cta="Abrir padrao"
        />
      </section>

      {!isPersistedMode ? (
        <>
          <section className="section-header">
            <div className="section-copy">
              <span className="eyebrow">Cenarios</span>
              <h2>Trocar o contexto da lista global</h2>
              <p>Use os cenarios abaixo para revisar baseline, atencao de vencimento e bloqueio cadastral sem alterar codigo.</p>
            </div>
          </section>

          <section className="nav-grid">
            {scenarios.map((item) => (
              <NavCard
                key={item.id}
                href={`/registry/equipment?scenario=${item.id}&equipment=${item.selectedEquipment.equipmentId}`}
                eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
                title={item.label}
                description={item.summaryLabel}
                statusTone={statusTone(item.summary.status)}
                statusLabel={statusLabel(item.summary.status)}
                cta="Abrir equipamentos"
              />
            ))}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
