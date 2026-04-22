import { loadCustomerRegistryCatalog } from "@/src/registry/customer-registry-api";
import { buildCustomerRegistryCatalogView } from "@/src/registry/customer-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    customer?: string;
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
  const catalog = await loadCustomerRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    customerId: props.searchParams?.customer,
  });

  if (!catalog) {
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
          <p>{scenario.summary.dueSoonCount} vencimento(s) proximo(s) no cenário selecionado.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Certificados</span>
          <strong>{scenario.summary.certificatesThisMonth} no mes</strong>
          <p>Use o detalhe do cliente para entender contatos, enderecos, anexos e certificados relacionados.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista canonica</span>
          <h2>Clientes ativos e recortes de cadastro</h2>
          <p>A lista abaixo abre o detalhe do cliente com o mesmo cenario canonico usado pelo backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.customers.map((customer) => (
          <NavCard
            key={customer.customerId}
            href={`/registry/customer-detail?scenario=${scenario.id}&customer=${customer.customerId}`}
            eyebrow={customer.customerId === scenario.selectedCustomer.customerId ? "Selecionado" : "Cliente"}
            title={customer.tradeName}
            description={`${customer.documentLabel} · ${customer.segmentLabel} · ${customer.equipmentCount} equipamento(s)`}
            statusTone={statusTone(customer.status)}
            statusLabel={statusLabel(customer.status)}
            cta="Abrir detalhe"
          />
        ))}
      </section>

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
          href={`/registry/customer-detail?scenario=${scenario.id}&customer=${scenario.selectedCustomer.customerId}`}
          eyebrow="Cliente"
          title="Abrir detalhe do cliente"
          description="Conferir dados, contatos, enderecos, equipamentos, certificados e historico do cadastro selecionado."
          cta="Abrir detalhe"
        />
        <NavCard
          href={`/registry/equipment?scenario=${scenario.detail.links.equipmentScenarioId}&equipment=${scenario.detail.links.selectedEquipmentId ?? ""}`}
          eyebrow="Equipamentos"
          title="Abrir lista global de equipamentos"
          description="Ir para o recorte global de equipamentos coerente com o cliente e o cenario selecionados."
          cta="Abrir equipamentos"
        />
        {scenario.detail.links.serviceOrderScenarioId && scenario.detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${scenario.detail.links.serviceOrderScenarioId}&item=${scenario.detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Voltar para a OS canonica que sustenta o certificado ou a pendencia do cliente selecionado."
            cta="Abrir OS"
          />
        ) : null}
      </section>

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
    </AppShell>
  );
}
