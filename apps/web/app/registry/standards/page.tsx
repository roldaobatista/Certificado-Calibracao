import { loadStandardRegistryCatalog } from "@/src/registry/standard-registry-api";
import { buildStandardRegistryCatalogView } from "@/src/registry/standard-registry-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    standard?: string;
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
  const catalog = await loadStandardRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    standardId: props.searchParams?.standard,
  });

  if (!catalog) {
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

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Lista canonica</span>
          <h2>Padroes e auxiliares monitorados</h2>
          <p>A lista abaixo abre o detalhe do padrao com o mesmo cenario canonico usado pelo backend.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.standardId}
            href={`/registry/standard-detail?scenario=${scenario.id}&standard=${item.standardId}`}
            eyebrow={item.standardId === selectedStandard.standardId ? "Selecionado" : "Padrao"}
            title={`${item.standardId.replace("standard-", "").toUpperCase()} · ${item.nominalClassLabel}`}
            description={`${item.kindLabel} · ${item.sourceLabel} · validade ${item.validUntilLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={statusLabel(item.status)}
            cta="Abrir detalhe"
          />
        ))}
      </section>

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
          href={`/registry/standard-detail?scenario=${scenario.id}&standard=${selectedStandard.standardId}`}
          eyebrow="Padrao"
          title="Abrir detalhe do padrao"
          description="Conferir historico de calibracoes, OS recentes e bloqueios do item selecionado."
          cta="Abrir detalhe"
        />
        {scenario.detail.links.registryScenarioId && scenario.detail.links.selectedEquipmentId ? (
          <NavCard
            href={`/registry/equipment?scenario=${scenario.detail.links.registryScenarioId}&equipment=${scenario.detail.links.selectedEquipmentId}`}
            eyebrow="Equipamento"
            title="Abrir lista global de equipamentos"
            description="Ir para o equipamento que usa este padrao no mesmo recorte operacional."
            cta="Abrir equipamento"
          />
        ) : null}
        {scenario.detail.links.serviceOrderScenarioId && scenario.detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${scenario.detail.links.serviceOrderScenarioId}&item=${scenario.detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Voltar para a OS canônica associada ao uso recente do padrao selecionado."
            cta="Abrir OS"
          />
        ) : null}
      </section>

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
    </AppShell>
  );
}
