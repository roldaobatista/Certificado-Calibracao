import { loadPortalEquipmentCatalog } from "@/src/portal-equipment-api";
import { buildPortalEquipmentCatalogView } from "@/src/portal-equipment-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    equipment?: string;
  };
};

export const dynamic = "force-dynamic";

function mapVerifyScenarioToCertificateScenario(verifyScenarioId: "authentic" | "reissued" | "not-found"): string {
  switch (verifyScenarioId) {
    case "reissued":
      return "reissued-history";
    case "not-found":
      return "download-blocked";
    default:
      return "current-valid";
  }
}

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Equipamento estavel";
    case "attention":
      return "Vencimento proximo";
    case "blocked":
      return "Equipamento vencido";
    default:
      return status;
  }
}

export default async function PortalEquipmentPage(props: PageProps) {
  const catalog = await loadPortalEquipmentCatalog({
    scenarioId: props.searchParams?.scenario,
    equipmentId: props.searchParams?.equipment,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Portal - meus equipamentos"
        title="Carteira de equipamentos indisponivel"
        description="O portal nao recebeu o payload canonico da carteira do cliente. Em fail-closed, nenhum equipamento local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a carteira do cliente.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a carteira ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /portal/equipment`. Sem resposta valida, o portal nao
              assume lista, vencimentos ou historico de certificados do cliente.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildPortalEquipmentCatalogView(catalog);
  const selectedEquipment = scenario.selectedEquipment;
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Portal - meus equipamentos"
      title={scenario.summary.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Equipamento ativo</span>
          <strong>{selectedEquipment.tag}</strong>
          <StatusPill tone={statusTone(detail.status)} label={statusLabel(detail.status)} />
          <p>{detail.recommendedAction}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Carteira</span>
          <strong>{scenario.summary.equipmentCount} item(ns)</strong>
          <p>
            {scenario.summary.attentionCount} em atencao e {scenario.summary.blockedCount} bloqueado(s) no recorte.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Selecionado</span>
          <strong>{selectedEquipment.description}</strong>
          <p>{selectedEquipment.locationLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Proxima calibracao</span>
          <strong>{selectedEquipment.nextDueLabel}</strong>
          <p>Ultima calibracao em {selectedEquipment.lastCalibrationLabel}.</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.equipmentId}
            href={`/equipment?scenario=${scenario.id}&equipment=${item.equipmentId}`}
            eyebrow={item.equipmentId === selectedEquipment.equipmentId ? "Selecionado" : item.tag}
            title={item.description}
            description={`${item.locationLabel} / prox. ${item.nextDueLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir item"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe do equipamento</span>
          <h2>{detail.title}</h2>
          <p>O painel abaixo resume fabricante, modelo, serie, local e o historico recente de certificados do item.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Fabricante e modelo</span>
            <strong>{detail.manufacturerLabel}</strong>
            <p>{detail.modelLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Serie e capacidade</span>
            <strong>{detail.serialLabel}</strong>
            <p>{detail.capacityClassLabel}</p>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Local</span>
            <strong>{detail.locationLabel}</strong>
            <p>{detail.recommendedAction}</p>
          </article>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {detail.blockers.length === 0 ? (
              <li>Sem bloqueios adicionais para o equipamento selecionado.</li>
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
              <li>Sem warnings adicionais para o equipamento selecionado.</li>
            ) : (
              detail.warnings.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Origem</span>
          <strong>Catalogo canonico do portal</strong>
          <p>O detalhe reutiliza apenas a carga do backend, sem consolidacao local paralela.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Historico de certificados</span>
          <h2>Abrir a verificacao publica do certificado correspondente</h2>
          <p>Enquanto o visualizador autenticado nao existe, o portal reutiliza a verificacao publica canonica por certificado.</p>
        </div>
      </section>

      <section className="nav-grid">
        {detail.certificateHistory.map((item) => (
          <NavCard
            key={item.certificateId}
            href={`/certificate?scenario=${mapVerifyScenarioToCertificateScenario(item.verifyScenarioId)}&certificate=${item.certificateId}`}
            eyebrow={item.issuedAtLabel}
            title={item.certificateNumber}
            description={`${item.resultLabel} / U ${item.uncertaintyLabel}`}
            statusTone={item.verifyScenarioId === "authentic" ? "ok" : "warn"}
            statusLabel={item.resultLabel}
            cta="Abrir certificado"
          />
        ))}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Voltar ao dashboard do cliente</h2>
          <p>Use os atalhos abaixo para retomar o contexto do dashboard ou trocar o recorte da carteira.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/dashboard?scenario=${scenario.id}`}
          eyebrow="Dashboard"
          title="Abrir resumo do cliente"
          description="Voltar ao dashboard com o mesmo recorte canonico da carteira."
          cta="Abrir dashboard"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto da carteira</h2>
          <p>Use os cenarios abaixo para revisar estabilidade, vencimentos proximos e item vencido sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/equipment?scenario=${item.id}&equipment=${item.selectedEquipment.equipmentId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir carteira"
          />
        ))}
      </section>
    </AppShell>
  );
}
