import { cookies } from "next/headers";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadSelfSignupCatalog } from "@/src/auth/self-signup-api";
import { loadUserDirectoryCatalog } from "@/src/auth/user-directory-api";
import { loadEmissionDryRunCatalog } from "@/src/emission/emission-dry-run-api";
import { loadEmissionWorkspaceCatalog } from "@/src/emission/emission-workspace-api";
import { loadReviewSignatureCatalog } from "@/src/emission/review-signature-api";
import { loadServiceOrderReviewCatalog } from "@/src/emission/service-order-review-api";
import { loadSignatureQueueCatalog } from "@/src/emission/signature-queue-api";
import { buildOperationsOverviewModel } from "@/src/home/operations-overview";
import { loadOnboardingCatalog } from "@/src/onboarding/onboarding-api";
import { loadQualityHubCatalog } from "@/src/quality/quality-hub-api";
import { loadOfflineSyncCatalog } from "@/src/sync/offline-sync-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const [
    emissionWorkspaceCatalog,
    selfSignupCatalog,
    onboardingCatalog,
    emissionCatalog,
    serviceOrderReviewCatalog,
    reviewSignatureCatalog,
    signatureQueueCatalog,
    offlineSyncCatalog,
    qualityHubCatalog,
    userDirectoryCatalog,
  ] = await Promise.all([
    loadEmissionWorkspaceCatalog({ cookieHeader }),
    loadSelfSignupCatalog(),
    loadOnboardingCatalog({ cookieHeader }),
    loadEmissionDryRunCatalog(),
    loadServiceOrderReviewCatalog(),
    loadReviewSignatureCatalog(),
    loadSignatureQueueCatalog(),
    loadOfflineSyncCatalog(),
    loadQualityHubCatalog(),
    loadUserDirectoryCatalog({ cookieHeader }),
  ]);

  const overview = buildOperationsOverviewModel({
    emissionWorkspaceCatalog,
    selfSignupCatalog,
    onboardingCatalog,
    emissionCatalog,
    serviceOrderReviewCatalog,
    reviewSignatureCatalog,
    signatureQueueCatalog,
    offlineSyncCatalog,
    qualityHubCatalog,
    userDirectoryCatalog,
  });
  const availableSources = overview.cards.filter((card) => card.statusLabel !== "Sem carga canonica").length;
  const totalSources = overview.cards.length;

  return (
    <AppShell
      eyebrow="V1 + V2 inicial"
      title="Backoffice regulado para emissao, sync offline e hub da qualidade"
      description="A home agora consolida workspace, auth, equipe, onboarding, dry-run, OS, workflow, fila de assinatura, triagem humana do sync offline e hub da Qualidade para mostrar a prontidao operacional antes da emissao."
      aside={
        <>
          <div className="hero-stat">
            <span className="eyebrow">Leitura canonica</span>
            <strong>{availableSources}/{totalSources} fluxos conectados ao backend</strong>
            <StatusPill tone={overview.heroStatusTone} label={overview.heroStatusLabel} />
            <p>{overview.heroStatusDescription}</p>
          </div>
          <div className="hero-stat">
            <span className="eyebrow">Fonte de verdade</span>
            <strong>Apps web lidas a partir do `apps/api`</strong>
            <p>
              Quando uma carga canonica falha, a home acusa a lacuna e preserva o comportamento fail-closed em vez
              de inventar preview local.
            </p>
          </div>
        </>
      }
    >
      {!authSession?.authenticated ? (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Sessao</span>
            <h2>Entrar para liberar as rotas protegidas de V1</h2>
            <p>
              A home continua lendo os catalogos publicos, mas onboarding, diretorio e workspace reais so aparecem com cookie valido.
            </p>
          </div>
          <div className="button-row">
            <a className="button-primary" href="/auth/login">
              Fazer login
            </a>
            <a className="button-secondary" href="/onboarding">
              Criar tenant
            </a>
          </div>
        </section>
      ) : (
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Sessao ativa</span>
            <h2>{authSession.user.organizationName}</h2>
            <p>
              {authSession.user.displayName} autenticado com {authSession.user.roles.length} papel(is) para o tenant atual.
            </p>
          </div>
          <form
            action={`${resolvePublicApiBaseUrl()}/auth/logout`}
            className="inline-form"
            method="post"
          >
            <input type="hidden" name="redirectTo" value="http://127.0.0.1:3002/auth/login" />
            <button className="button-secondary" type="submit">
              Encerrar sessao
            </button>
          </form>
        </section>
      )}

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Painel operacional</span>
          <h2>Prontidao consolidada antes da emissao</h2>
          <p>
            O resumo abaixo mostra quais fluxos estao liberados, quais exigem atencao e quais dependem de reconexao
            com o backend canonico.
          </p>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Conectividade</span>
          <strong>{availableSources === totalSources ? "Todas as leituras online" : "Leitura parcial do backend"}</strong>
          <p>
            {availableSources === totalSources
              ? "Todas as rotas operacionais responderam com payload valido."
              : "Uma ou mais rotas nao responderam com carga canonica valida."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Fluxos prontos</span>
          <strong>{overview.readyCount} fluxo(s) liberado(s)</strong>
          <p>Workspace, auth, equipe, onboarding, dry-run, OS, workflow, fila de assinatura, sync e Qualidade sao avaliados lado a lado para evitar drift entre telas.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Fluxos com atencao</span>
          <strong>{overview.blockedCount} fluxo(s) bloqueado(s)</strong>
          <p>Qualquer bloqueio ou falta de carga canonica sobe para a home como sinal operacional imediato.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Entradas</span>
          <h2>Rotas iniciais de operacao</h2>
          <p>As paginas abaixo abrem diretamente no cenario selecionado pelo catalogo canonico de cada fluxo.</p>
        </div>
      </section>

      <section className="nav-grid">
        {overview.cards.map((card) => (
          <NavCard
            key={card.href}
            href={card.href}
            eyebrow={card.eyebrow}
            title={card.title}
            description={card.description}
            statusTone={card.statusTone}
            statusLabel={card.statusLabel}
            cta={card.cta}
          />
        ))}
      </section>
    </AppShell>
  );
}

function resolvePublicApiBaseUrl() {
  return process.env.AFERE_PUBLIC_API_BASE_URL ?? process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
}
