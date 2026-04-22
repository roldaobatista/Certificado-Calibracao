import { loadSelfSignupCatalog } from "@/src/auth/self-signup-api";
import { loadUserDirectoryCatalog } from "@/src/auth/user-directory-api";
import { loadEmissionDryRunCatalog } from "@/src/emission/emission-dry-run-api";
import { loadEmissionWorkspaceCatalog } from "@/src/emission/emission-workspace-api";
import { loadReviewSignatureCatalog } from "@/src/emission/review-signature-api";
import { loadServiceOrderReviewCatalog } from "@/src/emission/service-order-review-api";
import { loadSignatureQueueCatalog } from "@/src/emission/signature-queue-api";
import { buildOperationsOverviewModel } from "@/src/home/operations-overview";
import { loadOnboardingCatalog } from "@/src/onboarding/onboarding-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [
    emissionWorkspaceCatalog,
    selfSignupCatalog,
    onboardingCatalog,
    emissionCatalog,
    serviceOrderReviewCatalog,
    reviewSignatureCatalog,
    signatureQueueCatalog,
    userDirectoryCatalog,
  ] = await Promise.all([
    loadEmissionWorkspaceCatalog(),
    loadSelfSignupCatalog(),
    loadOnboardingCatalog(),
    loadEmissionDryRunCatalog(),
    loadServiceOrderReviewCatalog(),
    loadReviewSignatureCatalog(),
    loadSignatureQueueCatalog(),
    loadUserDirectoryCatalog(),
  ]);

  const overview = buildOperationsOverviewModel({
    emissionWorkspaceCatalog,
    selfSignupCatalog,
    onboardingCatalog,
    emissionCatalog,
    serviceOrderReviewCatalog,
    reviewSignatureCatalog,
    signatureQueueCatalog,
    userDirectoryCatalog,
  });
  const availableSources = overview.cards.filter((card) => card.statusLabel !== "Sem carga canonica").length;
  const totalSources = overview.cards.length;

  return (
    <AppShell
      eyebrow="V1 - emissao controlada"
      title="Backoffice regulado para workspace, OS, auth, equipe e assinatura"
      description="A home agora consolida o workspace canonico de emissao junto com auth, equipe, onboarding, dry-run, OS, workflow e fila de assinatura para mostrar a prontidao operacional antes da emissao."
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
          <p>Workspace, auth, equipe, onboarding, dry-run, OS, workflow e fila de assinatura sao avaliados lado a lado para evitar drift entre telas.</p>
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
