import {
  listPublicCertificateScenarios,
  resolvePublicCertificateScenario,
} from "@/src/public-certificate-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
  };
};

export default function VerifyPage(props: PageProps) {
  const scenario = resolvePublicCertificateScenario(props.searchParams?.scenario);
  const scenarios = listPublicCertificateScenarios();

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
          <p>O modelo da pagina e montado a partir do contrato compartilhado, sem depender de import entre apps.</p>
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
          <p>Esses links ajudam a validar o portal antes da conexao com o endpoint real de verificacao por QR.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={`/verify?scenario=${item.id}`}
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
