import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth-session-api";
import { loadPortalCertificateCatalog } from "@/src/portal-certificate-api";
import { buildPortalCertificateCatalogView } from "@/src/portal-certificate-scenarios";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

type PageProps = {
  searchParams?: {
    scenario?: string;
    certificate?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Visualizador pronto";
    case "attention":
      return "Reemissao rastreada";
    case "blocked":
      return "Viewer bloqueado";
    default:
      return status;
  }
}

export default async function PortalCertificatePage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const isPersistedMode = !props.searchParams?.scenario;
  const catalog = await loadPortalCertificateCatalog({
    scenarioId: props.searchParams?.scenario,
    certificateId: props.searchParams?.certificate,
    cookieHeader,
  });

  if (isPersistedMode && authSession?.authenticated === false) {
    return (
      <AppShell
        eyebrow="Portal - certificado"
        title="Viewer protegido por sessao"
        description="O viewer autenticado do certificado exige uma sessao valida do cliente antes de carregar a publicacao."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Acesso atual</span>
            <strong>Login necessario</strong>
            <StatusPill tone="warn" label="Sessao ausente" />
            <p>Entre com um usuario `external_client` para abrir os certificados reais do portal.</p>
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
        eyebrow="Portal - certificado"
        title="Visualizador indisponivel"
        description="O portal nao recebeu o payload canonico do certificado. Em fail-closed, nenhuma previa local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar o visualizador do certificado.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar o certificado ao backend</h2>
            <p>
              Esta pagina depende do endpoint canonico `GET /portal/certificate`. Sem resposta valida, o portal nao
              assume hash, assinatura, acoes ou previa integral do documento.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildPortalCertificateCatalogView(catalog);
  const detail = scenario.detail;

  return (
    <AppShell
      eyebrow="Portal - certificado"
      title={detail.title}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Certificado ativo</span>
          <strong>{scenario.selectedCertificate.certificateNumber}</strong>
          <StatusPill tone={statusTone(detail.status)} label={statusLabel(detail.status)} />
          <p>{detail.recommendedAction}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Hash</span>
          <strong>{detail.hashLabel}</strong>
          <p>{detail.signatureLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Viewer</span>
          <strong>{statusLabel(detail.status)}</strong>
          <p>{detail.viewerLabel}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Link publico</span>
          <strong>{detail.publicLinkLabel}</strong>
          <p>Use o QR ou o link acima para verificacao publica minimizada por terceiros.</p>
        </article>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.certificateId}
            href={
              isPersistedMode
                ? `/certificate?certificate=${item.certificateId}`
                : `/certificate?scenario=${scenario.id}&certificate=${item.certificateId}`
            }
            eyebrow={item.certificateId === detail.certificateId ? "Selecionado" : item.issuedAtLabel}
            title={item.certificateNumber}
            description={`${item.equipmentLabel} / ${item.statusLabel}`}
            statusTone={statusTone(item.status)}
            statusLabel={item.statusLabel}
            cta="Abrir certificado"
          />
        ))}
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Metadados</span>
          <h2>Resumo autenticado do certificado</h2>
          <p>Os campos abaixo representam o recorte autenticado exposto pelo viewer, separado da verificacao publica.</p>
        </div>

        <div className="detail-grid">
          {detail.metadataFields.map((field) => (
            <article className="detail-card" key={`${detail.certificateId}-${field.label}`}>
              <span className="eyebrow">{field.label}</span>
              <strong>{field.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Acoes previstas</span>
          <h2>Download, compartilhamento e impressao</h2>
          <p>As acoes abaixo representam o estado canonico do viewer, mesmo quando o arquivo integral ainda estiver bloqueado.</p>
        </div>
      </section>

      <section className="nav-grid">
        {detail.actions.map((action) => (
          <article className="nav-card" key={`${detail.certificateId}-${action.key}`}>
            <span className="eyebrow">{action.key}</span>
            <strong>{action.label}</strong>
            <p>{statusLabel(action.status)}</p>
          </article>
        ))}
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Como verificar</span>
          <strong>{detail.verificationSteps.length} passo(s)</strong>
          <ul>
            {detail.verificationSteps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios</span>
          <strong>{detail.blockers.length} bloqueio(s)</strong>
          <ul>
            {detail.blockers.length === 0 ? (
              <li>Sem bloqueios adicionais neste certificado.</li>
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
              <li>Sem warnings adicionais neste certificado.</li>
            ) : (
              detail.warnings.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Navegar entre certificado, equipamento e dashboard</h2>
          <p>Os atalhos abaixo preservam o contexto canonico entre o viewer autenticado e os demais recortes do portal.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={isPersistedMode ? detail.publicLinkLabel : `/verify?scenario=${detail.publicVerifyScenarioId}`}
          eyebrow="Publico"
          title="Abrir verificacao minimizada"
          description="Conferir a autenticidade publica do mesmo certificado."
          cta="Abrir verificacao"
        />
        <NavCard
          href={
            isPersistedMode
              ? `/equipment?equipment=${detail.equipmentId}`
              : `/equipment?scenario=${detail.equipmentScenarioId}&equipment=${detail.equipmentId}`
          }
          eyebrow="Equipamento"
          title="Voltar ao item do cliente"
          description="Retomar o equipamento associado a este certificado no mesmo recorte."
          cta="Abrir equipamento"
        />
        <NavCard
          href={isPersistedMode ? "/dashboard" : `/dashboard?scenario=${detail.dashboardScenarioId}`}
          eyebrow="Dashboard"
          title="Voltar ao resumo do cliente"
          description="Retomar o dashboard com o mesmo contexto canonico."
          cta="Abrir dashboard"
        />
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto do viewer</h2>
          <p>Use os cenarios abaixo para revisar certificado valido, reemissao rastreada e visualizacao bloqueada.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={
              isPersistedMode
                ? `/certificate?certificate=${item.selectedCertificate.certificateId}`
                : `/certificate?scenario=${item.id}&certificate=${item.selectedCertificate.certificateId}`
            }
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir viewer"
          />
        ))}
      </section>
    </AppShell>
  );
}
