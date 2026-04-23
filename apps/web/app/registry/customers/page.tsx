import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadCustomerRegistryCatalog } from "@/src/registry/customer-registry-api";
import { buildCustomerRegistryCatalogView } from "@/src/registry/customer-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const WEB_BASE_URL = "http://127.0.0.1:3002";

type PageProps = {
  searchParams?: {
    scenario?: string;
    customer?: string;
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
      return "Cadastro pronto";
    case "attention":
      return "Cadastro em atencao";
    case "blocked":
      return "Cadastro bloqueado";
    default:
      return status;
  }
}

export default async function CustomerRegistryPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadCustomerRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    customerId: props.searchParams?.customer,
    cookieHeader,
  });

  if (!catalog) {
    if (authSession?.authenticated === false && !props.searchParams?.scenario) {
      return (
        <AppShell
          eyebrow="Cadastros - clientes"
          title="Lista protegida por sessao"
          description="Os clientes persistidos do tenant exigem autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir, criar e arquivar clientes reais.</p>
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
        eyebrow="Cadastros - clientes"
        title="Lista de clientes indisponivel"
        description="O back-office nao recebeu o payload canonico de clientes. Em fail-closed, nenhum cadastro local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a lista de clientes.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar clientes ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/customers`. Sem resposta valida, o web nao assume
              cliente, detalhe ou contagem de equipamentos.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildCustomerRegistryCatalogView(catalog);
  const search = props.searchParams?.q?.trim().toLowerCase() ?? "";
  const statusFilter = props.searchParams?.status?.trim() ?? "";
  const filteredCustomers = scenario.customers.filter((customer) => {
    const matchesQuery =
      search.length === 0 ||
      customer.tradeName.toLowerCase().includes(search) ||
      customer.legalName.toLowerCase().includes(search) ||
      customer.documentLabel.toLowerCase().includes(search);
    const matchesStatus = statusFilter.length === 0 || customer.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  return (
    <AppShell
      eyebrow="Cadastros - clientes"
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
          <span className="eyebrow">Clientes</span>
          <strong>{scenario.summary.activeCustomers} ativo(s)</strong>
          <p>
            {scenario.summary.attentionCustomers} em atencao e {scenario.summary.blockedCustomers} bloqueado(s) no
            recorte atual.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Equipamentos</span>
          <strong>{scenario.summary.totalEquipment} item(ns) vinculados</strong>
          <p>{scenario.summary.dueSoonCount} vencimento(s) proximo(s) no recorte selecionado.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">V2.2 e V2.6</span>
          <strong>Cadastro, busca e arquivo</strong>
          <p>O painel abaixo usa os dados persistidos do tenant para criar, filtrar e arquivar clientes reais.</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Filtros</span>
          <h2>Buscar cliente por nome, documento ou status</h2>
          <p>Os filtros abaixo refinam o catalogo atual sem sair do contexto carregado do backend.</p>
        </div>
        <form className="form-grid" action="/registry/customers" method="get">
          {props.searchParams?.scenario ? (
            <input type="hidden" name="scenario" value={props.searchParams.scenario} />
          ) : null}
          <label className="field">
            <span>Buscar</span>
            <input defaultValue={props.searchParams?.q ?? ""} name="q" placeholder="Cliente, CNPJ..." />
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
            <a className="button-secondary" href={props.searchParams?.scenario ? `/registry/customers?scenario=${props.searchParams.scenario}` : "/registry/customers"}>
              Limpar
            </a>
          </div>
        </form>
      </section>

      {isPersistedMode ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Novo cliente</span>
            <h2>Cadastrar cliente com contato e endereco principal</h2>
            <p>O formulario abaixo grava diretamente no backend V2 e retorna para a lista persistida.</p>
          </div>

          <form className="form-grid" action={`${API_BASE_URL}/registry/customers/manage`} method="post">
            <input type="hidden" name="action" value="save" />
            <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/customers`} />

            <label className="field">
              <span>Razao social</span>
              <input name="legalName" placeholder="Cliente Campo Ltda." required />
            </label>
            <label className="field">
              <span>Nome fantasia</span>
              <input name="tradeName" placeholder="Cliente Campo" required />
            </label>
            <label className="field">
              <span>Documento</span>
              <input name="documentLabel" placeholder="55.555.555/0001-55" required />
            </label>
            <label className="field">
              <span>Segmento</span>
              <input name="segmentLabel" placeholder="Industria" required />
            </label>
            <label className="field">
              <span>Responsavel da conta</span>
              <input name="accountOwnerName" placeholder="Marta Operacoes" required />
            </label>
            <label className="field">
              <span>E-mail do responsavel</span>
              <input name="accountOwnerEmail" placeholder="marta@cliente.com.br" required type="email" />
            </label>
            <label className="field">
              <span>Contato principal</span>
              <input name="contactName" placeholder="Marta Operacoes" required />
            </label>
            <label className="field">
              <span>Papel do contato</span>
              <input name="contactRoleLabel" placeholder="Coordenadora" required />
            </label>
            <label className="field">
              <span>E-mail do contato</span>
              <input name="contactEmail" placeholder="marta@cliente.com.br" required type="email" />
            </label>
            <label className="field">
              <span>Telefone do contato</span>
              <input name="contactPhoneLabel" placeholder="(65) 99999-5050" />
            </label>
            <label className="field">
              <span>Contrato</span>
              <input name="contractLabel" placeholder="Contrato vigente ate 12/2026" required />
            </label>
            <label className="field">
              <span>Condicoes especiais</span>
              <input name="specialConditionsLabel" placeholder="Atendimento em janela noturna" required />
            </label>
            <label className="field">
              <span>Endereco</span>
              <input name="addressLine1" placeholder="Distrito Industrial, 505" required />
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
              <input name="addressPostalCode" placeholder="78010-505" />
            </label>
            <label className="field">
              <span>Pais</span>
              <input defaultValue="Brasil" name="addressCountry" required />
            </label>
            <label className="field">
              <span>Condicoes do local</span>
              <input name="addressConditionsLabel" placeholder="Acesso controlado" />
            </label>
            <div className="button-row">
              <button className="button-primary" type="submit">
                Salvar cliente
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista canonica</span>
          <h2>Clientes ativos e recortes de cadastro</h2>
          <p>A lista abaixo abre o detalhe do cliente com o mesmo cenario canonico usado pelo backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {filteredCustomers.map((customer) => (
          <article className="nav-card" key={customer.customerId}>
            <span className="eyebrow">{customer.customerId === scenario.selectedCustomer.customerId ? "Selecionado" : "Cliente"}</span>
            <strong>{customer.tradeName}</strong>
            <p>{customer.documentLabel} · {customer.segmentLabel}</p>
            <div className="chip-list">
              <span className="chip">{customer.equipmentCount} equipamento(s)</span>
              <span className="chip">{statusLabel(customer.status)}</span>
            </div>
            <div className="button-row">
              <a
                className="button-primary"
                href={
                  isPersistedMode
                    ? `/registry/customer-detail?customer=${customer.customerId}`
                    : `/registry/customer-detail?scenario=${scenario.id}&customer=${customer.customerId}`
                }
              >
                Abrir detalhe
              </a>
              {isPersistedMode ? (
                <form className="inline-form" action={`${API_BASE_URL}/registry/customers/manage`} method="post">
                  <input
                    type="hidden"
                    name="action"
                    value={customer.status === "blocked" ? "restore" : "archive"}
                  />
                  <input type="hidden" name="customerId" value={customer.customerId} />
                  <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/registry/customers`} />
                  <button className="button-secondary" type="submit">
                    {customer.status === "blocked" ? "Restaurar" : "Arquivar"}
                  </button>
                </form>
              ) : null}
            </div>
          </article>
        ))}
      </section>

      {filteredCustomers.length === 0 ? (
        <div className="empty-state">Nenhum cliente corresponde aos filtros aplicados.</div>
      ) : null}

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Cliente selecionado</span>
          <strong>{scenario.selectedCustomer.legalName}</strong>
          <p>{scenario.selectedCustomer.documentLabel}</p>
          <div className="chip-list">
            <span className="chip">{scenario.selectedCustomer.segmentLabel}</span>
            <span className="chip">{scenario.selectedCustomer.equipmentCount} equipamento(s)</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima calibracao</span>
          <strong>{scenario.selectedCustomer.nextDueLabel}</strong>
          <p>Esta leitura resume o proximo ponto de atencao cadastral ligado ao cliente selecionado.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Atalhos</span>
          <strong>Clientes, equipamentos e emissao</strong>
          <div className="chip-list">
            <span className="chip">Detalhe do cliente</span>
            <span className="chip">Lista global de equipamentos</span>
            <span className="chip">OS e dry-run relacionados</span>
          </div>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Continuar a partir do cadastro</h2>
          <p>Os atalhos abaixo mantem a navegacao coerente entre cliente, equipamento e emissao.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode
              ? `/registry/customer-detail?customer=${scenario.selectedCustomer.customerId}`
              : `/registry/customer-detail?scenario=${scenario.id}&customer=${scenario.selectedCustomer.customerId}`
          }
          eyebrow="Cliente"
          title="Abrir detalhe do cliente"
          description="Conferir dados, contatos, enderecos, equipamentos, certificados e historico do cadastro selecionado."
          cta="Abrir detalhe"
        />
        <NavCard
          href={
            isPersistedMode
              ? `/registry/equipment${scenario.detail.links.selectedEquipmentId ? `?equipment=${scenario.detail.links.selectedEquipmentId}` : ""}`
              : `/registry/equipment?scenario=${scenario.detail.links.equipmentScenarioId}&equipment=${scenario.detail.links.selectedEquipmentId ?? ""}`
          }
          eyebrow="Equipamentos"
          title="Abrir lista global de equipamentos"
          description="Ir para o recorte global de equipamentos coerente com o cliente e o cenario selecionados."
          cta="Abrir equipamentos"
        />
      </section>

      {!isPersistedMode ? (
        <>
          <section className="section-header">
            <div className="section-copy">
              <span className="eyebrow">Cenarios</span>
              <h2>Trocar o contexto do cadastro</h2>
              <p>Use os cenarios abaixo para revisar baseline, vencimento proximo e bloqueio cadastral sem alterar codigo.</p>
            </div>
          </section>

          <section className="nav-grid">
            {scenarios.map((item) => (
              <NavCard
                key={item.id}
                href={`/registry/customers?scenario=${item.id}&customer=${item.selectedCustomer.customerId}`}
                eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
                title={item.label}
                description={item.summaryLabel}
                statusTone={statusTone(item.summary.status)}
                statusLabel={statusLabel(item.summary.status)}
                cta="Abrir clientes"
              />
            ))}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
