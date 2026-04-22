import { loadEquipmentRegistryCatalog } from "@/src/registry/equipment-registry-api";
import { buildEquipmentRegistryCatalogView } from "@/src/registry/equipment-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    equipment?: string;
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
  const catalog = await loadEquipmentRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    equipmentId: props.searchParams?.equipment,
  });

  if (!catalog) {
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

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.equipmentId}
            href={`/registry/equipment?scenario=${scenario.id}&equipment=${item.equipmentId}`}
            eyebrow={item.equipmentId === selectedEquipment.equipmentId ? "Selecionado" : "Equipamento"}
            title={`${item.code} · ${item.tagCode}`}
            description={`${item.customerName} · ${item.typeModelLabel} · prox. ${item.nextCalibrationLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir item"
          />
        ))}
      </section>

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
            <span className="eyebrow">Padroes e OS</span>
            <strong>{scenario.detail.standardSetLabel}</strong>
            <p>{scenario.detail.lastServiceOrderLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Proxima calibracao</span>
            <strong>{scenario.detail.nextCalibrationLabel}</strong>
            <p>O estado abaixo continua fail-closed quando o cadastro minimo ou a janela operacional exigem acao.</p>
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
          <p>{selectedEquipment.lastCalibrationLabel} foi a ultima calibracao registrada no recorte canonico atual.</p>
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
          href={`/registry/customer-detail?scenario=${scenario.detail.links.customerScenarioId}&customer=${scenario.detail.links.customerId}`}
          eyebrow="Cliente"
          title="Abrir detalhe do cliente"
          description="Voltar ao cadastro do cliente vinculado ao equipamento selecionado."
          cta="Abrir cliente"
        />
        <NavCard
          href={`/registry/standard-detail?scenario=${mapEquipmentScenarioToStandardScenario(scenario.id)}&standard=${mapEquipmentToStandardId(selectedEquipment.equipmentId)}`}
          eyebrow="Padroes"
          title="Abrir detalhe do padrao"
          description="Conferir o padrao canonico mais relevante para o equipamento selecionado neste recorte."
          cta="Abrir padrao"
        />
        {scenario.detail.links.serviceOrderScenarioId && scenario.detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${scenario.detail.links.serviceOrderScenarioId}&item=${scenario.detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Conferir a OS canonica relacionada ao ultimo uso operacional do equipamento."
            cta="Abrir OS"
          />
        ) : null}
        {scenario.detail.links.dryRunScenarioId ? (
          <NavCard
            href={`/emission/dry-run?scenario=${scenario.detail.links.dryRunScenarioId}`}
            eyebrow="Dry-run"
            title="Abrir dry-run de emissao"
            description="Inspecionar o recorte de emissao que reaproveita o equipamento selecionado."
            cta="Abrir dry-run"
          />
        ) : null}
      </section>

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
    </AppShell>
  );
}
