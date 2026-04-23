import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
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

export default async function CustomerDetailPage(props: PageProps) {
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
          eyebrow="Cadastros - detalhe do cliente"
          title="Detalhe protegido por sessao"
          description="O detalhe persistido do cliente exige autenticacao antes da leitura."
          aside={
            <div className="hero-stat">
              <span className="eyebrow">Acesso atual</span>
              <strong>Login necessario</strong>
              <StatusPill tone="warn" label="RBAC ativo" />
              <p>Entre com um papel autorizado para abrir o cadastro real do tenant.</p>
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
        eyebrow="Cadastros - detalhe do cliente"
        title="Detalhe do cliente indisponivel"
        description="O back-office nao recebeu o payload canonico do cliente selecionado. Em fail-closed, nenhum detalhe local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o detalhe do cliente.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar detalhe do cliente ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/customers`. Sem resposta valida, o web nao assume
              dados, contatos, enderecos, anexos ou historico do cliente.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildCustomerRegistryCatalogView(catalog);
  const detail = scenario.detail;
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  return (
    <AppShell
      eyebrow="Cadastros - detalhe do cliente"
      title={detail.title}
      description={detail.statusLine}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill tone={statusTone(detail.status)} label={statusLabel(detail.status)} />
          <p>{scenario.summary.recommendedAction}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Conta</span>
          <strong>{detail.accountOwnerLabel}</strong>
          <p>{detail.contractLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Condicoes especiais</span>
          <strong>{detail.specialConditionsLabel}</strong>
          <p>O recorte abaixo traduz o cadastro operacional em abas e leituras canonicas reutilizaveis.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Abas previstas</span>
          <strong>{detail.tabs.length} grupos</strong>
          <div className="chip-list">
            {detail.tabs.map((tab) => (
              <span className="chip" key={tab.key}>
                {tab.label}
                {tab.countLabel ? ` · ${tab.countLabel}` : ""}
              </span>
            ))}
          </div>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Dados</span>
          <h2>Contato, endereco e contexto operacional</h2>
          <p>As secoes abaixo resumem o detalhe do cliente em leitura canonica e auditavel.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Contatos</span>
            <strong>{detail.contacts.length} contato(s)</strong>
            <ul>
              {detail.contacts.map((contact) => (
                <li key={`${detail.customerId}-${contact.email}`}>
                  {contact.name} · {contact.roleLabel} · {contact.email}
                  {contact.phoneLabel ? ` · ${contact.phoneLabel}` : ""}
                  {contact.primary ? " · principal" : ""}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Enderecos</span>
            <strong>{detail.addresses.length} endereco(s)</strong>
            <ul>
              {detail.addresses.map((address) => (
                <li key={`${detail.customerId}-${address.label}`}>
                  {address.label}: {address.line1} · {address.cityStateLabel} · {address.postalCodeLabel}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Bloqueios e warnings</span>
            <strong>
              {detail.blockers.length} bloqueio(s) · {detail.warnings.length} warning(s)
            </strong>
            <ul>
              {detail.blockers.map((item) => (
                <li key={item}>{item}</li>
              ))}
              {detail.warnings.map((item) => (
                <li key={item}>{item}</li>
              ))}
              {detail.blockers.length === 0 && detail.warnings.length === 0 ? <li>Sem ressalvas adicionais.</li> : null}
            </ul>
          </article>
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Relacionamentos</span>
          <h2>Equipamentos, certificados, anexos e historico</h2>
          <p>Esses grupos ligam o cadastro do cliente a equipamentos, documentos e eventos que sustentam a emissao.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Equipamentos</span>
            <strong>{detail.equipmentHighlights.length} destaque(s)</strong>
            <ul>
              {detail.equipmentHighlights.map((item) => (
                <li key={item.equipmentId}>
                  {item.code} · {item.tagCode} · {item.typeModelLabel} · {item.nextDueLabel}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Certificados</span>
            <strong>{detail.certificateHighlights.length} registro(s)</strong>
            <ul>
              {detail.certificateHighlights.map((item) => (
                <li key={`${item.certificateNumber}-${item.workOrderNumber}`}>
                  {item.certificateNumber} · {item.workOrderNumber} · {item.statusLabel}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Anexos e historico</span>
            <strong>{detail.attachments.length + detail.history.length} entrada(s)</strong>
            <ul>
              {detail.attachments.map((item) => (
                <li key={item.label}>
                  {item.label} · {item.statusLabel}
                </li>
              ))}
              {detail.history.map((item) => (
                <li key={`${item.label}-${item.timestampLabel}`}>
                  {item.label} · {item.timestampLabel}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas ao cliente</h2>
          <p>Use os atalhos abaixo para continuar a partir do cadastro sem perder o contexto canonico.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode
              ? `/registry/equipment${detail.links.selectedEquipmentId ? `?equipment=${detail.links.selectedEquipmentId}` : ""}`
              : `/registry/equipment?scenario=${detail.links.equipmentScenarioId}&equipment=${detail.links.selectedEquipmentId ?? ""}`
          }
          eyebrow="Equipamentos"
          title="Abrir lista global de equipamentos"
          description="Conferir os equipamentos vinculados ao cliente dentro do mesmo recorte operacional."
          cta="Abrir equipamentos"
        />
      </section>

      {!isPersistedMode ? (
        <>
          <section className="section-header">
            <div className="section-copy">
              <span className="eyebrow">Cenarios</span>
              <h2>Trocar o contexto do cliente</h2>
              <p>Use os cenarios abaixo para revisar baseline, atencao de vencimento e bloqueio cadastral sem alterar codigo.</p>
            </div>
          </section>

          <section className="nav-grid">
            {scenarios.map((item) => (
              <NavCard
                key={item.id}
                href={`/registry/customer-detail?scenario=${item.id}&customer=${item.selectedCustomer.customerId}`}
                eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
                title={item.label}
                description={item.summaryLabel}
                statusTone={statusTone(item.summary.status)}
                statusLabel={statusLabel(item.summary.status)}
                cta="Abrir cliente"
              />
            ))}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
