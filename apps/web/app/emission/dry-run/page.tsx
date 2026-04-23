import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadEmissionDryRunCatalog } from "@/src/emission/emission-dry-run-api";
import { buildEmissionDryRunCatalogView } from "@/src/emission/emission-dry-run-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    item?: string;
  };
};

export const dynamic = "force-dynamic";

export default async function EmissionDryRunPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadEmissionDryRunCatalog({
    scenarioId: props.searchParams?.scenario,
    itemId: props.searchParams?.item,
    cookieHeader,
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  if (!catalog && authSession?.authenticated === false && !props.searchParams?.scenario) {
    return (
      <AppShell
        eyebrow="Emissao - dry-run"
        title="Dry-run protegido por sessao"
        description="O dry-run persistido do tenant exige autenticacao antes da leitura."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Acesso atual</span>
            <strong>Login necessario</strong>
            <StatusPill tone="warn" label="RBAC ativo" />
            <p>Entre com um papel operacional para revisar o pipeline real de emissao.</p>
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

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - dry-run"
        title="Dry-run indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico do backend. Em fail-closed, nenhum preview local foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o dry-run operacional.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a leitura operacional ao backend</h2>
            <p>
              A tela agora depende do endpoint canonico `GET /emission/dry-run`. Sem esse backend disponivel, a
              revisao fica bloqueada para evitar drift entre UI e dominio regulatorio.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildEmissionDryRunCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Emissao - dry-run"
      title={scenario.summary.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Leitura atual</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={scenario.summary.status === "ready" ? "ok" : "warn"}
            label={scenario.summary.status === "ready" ? "Emissao pronta" : "Emissao bloqueada"}
          />
          <p>
            {scenario.summary.passedChecks} checks verdes e {scenario.summary.failedChecks} checks falhos neste preview.
          </p>
        </div>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Sintese</span>
          <h2>{scenario.result.summary}</h2>
          <p>O dry-run junta os gates de V1 em uma leitura unica para revisao operacional antes da emissao oficial.</p>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Artefatos</span>
          <strong>{scenario.summary.templateLabel}</strong>
          <p>{scenario.summary.symbolLabel}</p>
          <div className="chip-list">
            {scenario.result.artifacts.certificateNumber ? (
              <span className="chip">{scenario.result.artifacts.certificateNumber}</span>
            ) : (
              <span className="chip chip--warn">Sem numero reservado</span>
            )}
            {scenario.result.artifacts.qrVerificationStatus ? (
              <span className="chip">{scenario.result.artifacts.qrVerificationStatus}</span>
            ) : (
              <span className="chip chip--warn">QR sem preview</span>
            )}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>
            {scenario.summary.blockers.length === 0
              ? "Nenhum bloqueio ativo"
              : `${scenario.summary.blockers.length} bloqueios operacionais`}
          </strong>
          <ul>
            {scenario.summary.blockers.length === 0 ? (
              <li>Todos os gates desta fatia estao verdes para seguir.</li>
            ) : (
              scenario.summary.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)
            )}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Warnings</span>
          <strong>
            {scenario.summary.warnings.length === 0
              ? "Sem warnings complementares"
              : `${scenario.summary.warnings.length} avisos de politica`}
          </strong>
          <ul>
            {scenario.summary.warnings.length === 0 ? (
              <li>Nenhuma observacao adicional precisa ser carregada para esta execucao.</li>
            ) : (
              scenario.summary.warnings.map((warning) => <li key={warning}>{warning}</li>)
            )}
          </ul>
        </article>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Checklist</span>
          <h2>Verificacao por gate</h2>
          <p>Os checks abaixo mostram exatamente onde o pipeline seco passa ou falha antes de tocar persistencia real.</p>
        </div>

        <ul className="check-list">
          {scenario.result.checks.map((check) => (
            <li key={check.id}>
              <div className="metric-row">
                <strong>{check.title}</strong>
                <StatusPill
                  tone={check.status === "passed" ? "ok" : "warn"}
                  label={check.status === "passed" ? "Passou" : "Falhou"}
                />
              </div>
              <p>{check.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Declaracao</span>
          <strong>Resumo tecnico</strong>
          <p>{scenario.result.artifacts.declarationSummary ?? "Declaracao indisponivel neste cenario."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">QR</span>
          <strong>Preview do endpoint publico</strong>
          <p>{scenario.result.artifacts.qrCodeUrl ?? "QR ainda nao pode ser gerado neste cenario."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Portal</span>
          <strong>Metadados minimos previstos</strong>
          {Object.keys(scenario.result.artifacts.publicPreview).length === 0 ? (
            <div className="empty-state">Sem recorte publico disponivel para este cenario.</div>
          ) : (
            <dl>
              {Object.entries(scenario.result.artifacts.publicPreview).map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Previa</span>
          <h2>Conferir a peca antes da assinatura</h2>
          <p>A pre-visualizacao canonica usa este mesmo cenario do dry-run para mostrar o certificado antes da assinatura.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode && props.searchParams?.item
              ? `/emission/certificate-preview?item=${props.searchParams.item}`
              : `/emission/certificate-preview?scenario=${scenario.id}`
          }
          eyebrow="Certificado"
          title="Abrir previa integral"
          description="Conferir cabecalho, identificacao, padroes, ambiente, resultados, decisao e rodape antes da assinatura."
          statusTone={scenario.result.status === "ready" ? "ok" : "warn"}
          statusLabel={scenario.result.status === "ready" ? "Previa pronta" : "Previa bloqueada"}
          cta="Abrir previa"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do dry-run</h2>
          <p>Esses atalhos ajudam a revisar o comportamento dos perfis A, B e C sem alterar o codigo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={
              isPersistedMode && props.searchParams?.item
                ? `/emission/dry-run?item=${props.searchParams.item}`
                : `/emission/dry-run?scenario=${item.id}`
            }
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.description}
            cta="Abrir dry-run"
          />
        ))}
      </section>
    </AppShell>
  );
}
