import { loadPortalDashboardCatalog } from "@/src/portal-dashboard-api";
import { buildPortalDashboardCatalogView } from "@/src/portal-dashboard-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
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
      return "Carteira estavel";
    case "attention":
      return "Vencimentos proximos";
    case "blocked":
      return "Acao imediata";
    default:
      return status;
  }
}

export default async function DashboardPage(props: PageProps) {
  const catalog = await loadPortalDashboardCatalog({ scenarioId: props.searchParams?.scenario });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Portal - dashboard do cliente"
        title="Dashboard indisponivel"
        description="O portal nao recebeu o payload canonico do dashboard. Em fail-closed, nenhuma carteira local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o dashboard do cliente.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o dashboard ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /portal/dashboard`. Sem resposta valida, o portal nao
              assume equipamentos, certificados ou vencimentos do cliente.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildPortalDashboardCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Portal - dashboard do cliente"
      title={scenario.summary.clientName}
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
          <strong>{scenario.summary.equipmentCount} ativo(s)</strong>
          <p>Carteira atual acompanhada pelo laboratorio {scenario.summary.organizationName}.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Certificados</span>
          <strong>{scenario.summary.certificateCount} emitido(s)</strong>
          <p>Os certificados recentes abaixo permanecem vinculados ao recorte canonico do cliente.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Vencimentos</span>
          <strong>
            {scenario.summary.overdueCount > 0
              ? `${scenario.summary.overdueCount} vencido(s)`
              : `${scenario.summary.expiringSoonCount} vencendo em breve`}
          </strong>
          <p>{scenario.summary.recommendedAction}</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atencao programatica</span>
          <h2>Equipamentos que pedem acompanhamento</h2>
          <p>O dashboard resume os equipamentos com vencimento proximo ou ja vencidos no recorte selecionado.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.expiringEquipments.length === 0 ? (
          <article className="nav-card">
            <span className="eyebrow">Sem alertas</span>
            <strong>Carteira sem vencimentos proximos</strong>
            <p>O recorte atual nao tem equipamentos em atencao para os proximos 30 dias.</p>
          </article>
        ) : (
          scenario.expiringEquipments.map((item) => (
            <NavCard
              key={item.equipmentId}
              href={`/equipment?scenario=${scenario.id}&equipment=${item.equipmentId}`}
              eyebrow={item.tag}
              title={item.description}
              description={`${item.locationLabel} / prox. ${item.dueAtLabel}`}
              statusTone={statusTone(item.status)}
              statusLabel={statusLabel(item.status)}
              cta="Abrir equipamento"
            />
          ))
        )}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Certificados recentes</span>
          <h2>Abrir a verificacao publica do item selecionado</h2>
          <p>Os atalhos abaixo reutilizam a pagina publica canonica para conferir autenticidade ou reemissao.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.recentCertificates.map((item) => (
          <NavCard
            key={item.certificateId}
            href={`/certificate?scenario=${mapVerifyScenarioToCertificateScenario(item.verifyScenarioId)}&certificate=${item.certificateId}`}
            eyebrow={item.certificateNumber}
            title={item.equipmentLabel}
            description={`${item.issuedAtLabel} / ${item.statusLabel}`}
            statusTone={item.verifyScenarioId === "authentic" ? "ok" : "warn"}
            statusLabel={item.statusLabel}
            cta="Abrir certificado"
          />
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{scenario.summary.blockers.length} bloqueio(s)</strong>
          <ul>
            {scenario.summary.blockers.length === 0 ? (
              <li>Sem bloqueios adicionais neste recorte do cliente.</li>
            ) : (
              scenario.summary.blockers.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>{scenario.summary.warnings.length} warning(s)</strong>
          <ul>
            {scenario.summary.warnings.length === 0 ? (
              <li>Sem warnings adicionais neste recorte do cliente.</li>
            ) : (
              scenario.summary.warnings.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Origem</span>
          <strong>Catalogo canonico do portal</strong>
          <p>O dashboard apenas traduz a carteira entregue pelo backend, sem consolidacao local paralela.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do dashboard</h2>
          <p>Use os cenarios abaixo para revisar estabilidade, vencimentos proximos e carteira vencida sem alterar codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/dashboard?scenario=${item.id}`}
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir dashboard"
          />
        ))}
      </section>
    </AppShell>
  );
}
