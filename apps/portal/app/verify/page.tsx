import { loadPublicCertificateCatalog } from "@/src/public-certificate-api";
import { buildPublicCertificateCatalogView } from "@/src/public-certificate-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    certificate?: string;
    token?: string;
  };
};

export const dynamic = "force-dynamic";

export default async function VerifyPage(props: PageProps) {
  const isPersistedMode = !props.searchParams?.scenario;
  const catalog = await loadPublicCertificateCatalog({
    scenarioId: props.searchParams?.scenario,
    certificateId: props.searchParams?.certificate,
    token: props.searchParams?.token,
  });

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Portal - PRD 13.17"
        title="Verificacao publica indisponivel"
        description="O portal nao recebeu o payload canonico do backend. Em fail-closed, nenhum metadado publico foi assumido."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem resposta canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a verificacao publica.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o portal ao backend</h2>
            <p>
              Esta pagina agora depende do endpoint canonico `GET /portal/verify`. Sem resposta valida do backend,
              o portal nao monta preview local para evitar drift e leakage acidental.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildPublicCertificateCatalogView(catalog);

  return (
    <AppShell
      eyebrow="Portal - PRD 13.17"
      title={scenario.page.title}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Leitura atual</span>
          <strong>{scenario.label}</strong>
          <StatusPill
            tone={
              scenario.page.status === "authentic"
                ? "ok"
                : scenario.page.status === "reissued"
                  ? "neutral"
                  : "warn"
            }
            label={
              scenario.page.status === "authentic"
                ? "Certificado valido"
                : scenario.page.status === "reissued"
                  ? "Reemissao rastreada"
                  : "Sem dados publicos"
            }
          />
          <p>O portal agora traduz apenas o payload publico canonico vindo do backend.</p>
        </div>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Metadados publicos</span>
          <h2>Resposta publica e minimizada</h2>
          <p>Somente campos autorizados entram na tela. Todo o resto permanece fora do portal por desenho arquitetural.</p>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Status</span>
          <strong>{scenario.page.title}</strong>
          <p>
            {scenario.page.status === "not_found"
              ? "Nenhum dado publico e exposto quando a verificacao nao encontra evidencias suficientes."
              : "O portal preserva um recorte enxuto de metadados para autenticidade e rastreabilidade."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Campos exibidos</span>
          {Object.keys(scenario.page.publicMetadata).length === 0 ? (
            <div className="empty-state">Nenhum metadado publico disponivel para este cenario.</div>
          ) : (
            <dl>
              {Object.entries(scenario.page.publicMetadata).map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}
        </article>

        <article className="detail-card">
          <span className="eyebrow">Guardrail</span>
          <strong>Sem leakage lateral</strong>
          <p>
            Cliente final, endereco, resultado metrologico, token publico e hash completo continuam fora desta experiencia publica.
          </p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o estado da verificacao</h2>
          <p>Esses links ajudam a validar o portal usando o catalogo canonico de verificacao publica.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={
              isPersistedMode && props.searchParams?.certificate && props.searchParams?.token
                ? `/verify?certificate=${encodeURIComponent(props.searchParams.certificate)}&token=${encodeURIComponent(props.searchParams.token)}`
                : `/verify?scenario=${item.id}`
            }
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.description}
            cta="Abrir cenario"
          />
        ))}
      </section>
    </AppShell>
  );
}
