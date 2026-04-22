import { loadSelfSignupCatalog } from "@/src/auth/self-signup-api";
import { loadEmissionDryRunCatalog } from "@/src/emission/emission-dry-run-api";
import { buildOperationsOverviewModel } from "@/src/home/operations-overview";
import { loadOnboardingCatalog } from "@/src/onboarding/onboarding-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [selfSignupCatalog, onboardingCatalog, emissionCatalog] = await Promise.all([
    loadSelfSignupCatalog(),
    loadOnboardingCatalog(),
    loadEmissionDryRunCatalog(),
  ]);

  const overview = buildOperationsOverviewModel({
    selfSignupCatalog,
    onboardingCatalog,
    emissionCatalog,
  });
  const availableSources = overview.cards.filter((card) => card.statusLabel !== "Sem carga canonica").length;

  return (
    <AppShell
      eyebrow="V1 - emissao controlada"
      title="Backoffice regulado para onboarding e auth"
      description="A home agora consolida as leituras canonicas de auth, onboarding e dry-run para mostrar a prontidao operacional antes da primeira emissao."
      aside={
        <>
          <div className="hero-stat">
            <span className="eyebrow">Leitura canonica</span>
            <strong>{availableSources}/3 fluxos conectados ao backend</strong>
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
          <strong>{availableSources === 3 ? "Todas as leituras online" : "Leitura parcial do backend"}</strong>
          <p>
            {availableSources === 3
              ? "As tres rotas operacionais responderam com payload valido."
              : "Uma ou mais rotas nao responderam com carga canonica valida."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Fluxos prontos</span>
          <strong>{overview.readyCount} fluxo(s) liberado(s)</strong>
          <p>Auth, onboarding e dry-run sao avaliados lado a lado para evitar drift entre telas.</p>
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
