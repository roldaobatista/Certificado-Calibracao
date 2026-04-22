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

export default async function StandardDetailPage(props: PageProps) {
  const catalog = await loadStandardRegistryCatalog({
    scenarioId: props.searchParams?.scenario,
    standardId: props.searchParams?.standard,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Cadastros - detalhe do padrao"
        title="Detalhe do padrao indisponivel"
        description="O back-office nao recebeu o payload canonico do padrao selecionado. Em fail-closed, nenhum detalhe local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o detalhe do padrao.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar detalhe do padrao ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /registry/standards`. Sem resposta valida, o web nao assume
              historico, uso recente ou elegibilidade do padrao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildStandardRegistryCatalogView(catalog);
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Cadastros - detalhe do padrao"
      title={detail.title}
      description={detail.noticeLabel}
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
          <span className="eyebrow">Fabricante e modelo</span>
          <strong>{detail.manufacturerLabel}</strong>
          <p>
            {detail.modelLabel} · {detail.serialNumberLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Grandeza e classe</span>
          <strong>{detail.nominalValueLabel}</strong>
          <p>
            {detail.classLabel} · {detail.usageRangeLabel}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Incerteza</span>
          <strong>{detail.uncertaintyLabel}</strong>
          <p>{detail.correctionFactorLabel}</p>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Historico</span>
          <h2>Calibracoes registradas do padrao</h2>
          <p>As entradas abaixo resumem a cadeia recente de calibracoes que sustenta o uso auditavel deste item.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Calibracoes</span>
            <strong>{detail.history.length} registro(s)</strong>
            <ul>
              {detail.history.map((entry) => (
                <li key={`${entry.certificateLabel}-${entry.validUntilLabel}`}>
                  {entry.calibratedAtLabel} · {entry.laboratoryLabel} · {entry.certificateLabel} · validade {entry.validUntilLabel}
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Uso recente em OS</span>
            <strong>{detail.recentWorkOrders.length} OS relacionada(s)</strong>
            <ul>
              {detail.recentWorkOrders.map((entry) => (
                <li key={`${entry.workOrderNumber}-${entry.usedAtLabel}`}>
                  {entry.workOrderNumber} · usado em {entry.usedAtLabel}
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

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas ao padrao</h2>
          <p>Use os atalhos abaixo para continuar a partir do mesmo contexto canonico do detalhe selecionado.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={`/registry/standards?scenario=${scenario.id}&standard=${detail.standardId}`}
          eyebrow="Padroes"
          title="Abrir lista da carteira"
          description="Voltar ao painel de vencimentos e aos demais padroes do mesmo recorte."
          cta="Abrir padroes"
        />
        {detail.links.registryScenarioId && detail.links.selectedEquipmentId ? (
          <NavCard
            href={`/registry/equipment?scenario=${detail.links.registryScenarioId}&equipment=${detail.links.selectedEquipmentId}`}
            eyebrow="Equipamento"
            title="Abrir lista global de equipamentos"
            description="Conferir o equipamento vinculado a este padrao no mesmo recorte operacional."
            cta="Abrir equipamento"
          />
        ) : null}
        {detail.links.serviceOrderScenarioId && detail.links.reviewItemId ? (
          <NavCard
            href={`/emission/service-order-review?scenario=${detail.links.serviceOrderScenarioId}&item=${detail.links.reviewItemId}`}
            eyebrow="OS"
            title="Abrir revisao tecnica da OS"
            description="Inspecionar a OS recente que reutiliza este padrao no fluxo de emissao."
            cta="Abrir OS"
          />
        ) : null}
        {detail.links.dryRunScenarioId ? (
          <NavCard
            href={`/emission/dry-run?scenario=${detail.links.dryRunScenarioId}`}
            eyebrow="Dry-run"
            title="Abrir dry-run de emissao"
            description="Conferir o recorte de emissao que depende do mesmo padrao selecionado."
            cta="Abrir dry-run"
          />
        ) : null}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do padrao</h2>
          <p>Use os cenarios abaixo para revisar baseline, atencao por vencimento e bloqueio por expiracao sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/registry/standard-detail?scenario=${item.id}&standard=${item.selectedStandard.standardId}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir padrao"
          />
        ))}
      </section>
    </AppShell>
  );
}
