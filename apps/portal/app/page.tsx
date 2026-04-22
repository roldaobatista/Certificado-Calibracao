import { buildPublicVerificationOverviewModel } from "@/src/home/public-verification-overview";
import { loadPublicCertificateCatalog } from "@/src/public-certificate-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const catalog = await loadPublicCertificateCatalog();
  const overview = buildPublicVerificationOverviewModel(catalog);

  return (
    <AppShell
      eyebrow="Portal - verificacao publica"
      title="Consulta segura com metadados minimos"
      description="A home do portal agora le o catalogo publico canonico para resumir autenticidade, reemissao e fail-closed sem expor dados sensiveis."
      aside={
        <>
          <div className="hero-stat">
            <span className="eyebrow">Leitura publica</span>
            <strong>{overview.featuredScenarioLabel}</strong>
            <StatusPill tone={overview.heroStatusTone} label={overview.heroStatusLabel} />
            <p>{overview.heroStatusDescription}</p>
          </div>
          <div className="hero-stat">
            <span className="eyebrow">Principio de exposicao</span>
            <strong>Somente o minimo necessario</strong>
            <p>Sem cliente final, sem resultado metrologico e sem hash completo em tela publica.</p>
          </div>
        </>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Resumo publico</span>
          <h2>Estado operacional do catalogo de verificacao</h2>
          <p>
            A vitrine publica agora mostra o estado do backend canonico antes mesmo de abrir um cenario especifico
            de verificacao.
          </p>
        </div>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Catalogo</span>
          <strong>{overview.sourceAvailable ? "Carga publica disponivel" : "Backend obrigatorio"}</strong>
          <p>
            {overview.sourceAvailable
              ? "Os cenarios publicos foram lidos diretamente do endpoint canonico do portal."
              : "Sem payload valido do backend, a home permanece em fail-closed e nao assume nenhum metadado."}
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Metadados expostos</span>
          <strong>{overview.authenticCount + overview.reissuedCount} cenario(s) com resposta publica</strong>
          <p>Somente autenticidade e reemissao carregam metadados publicos minimizados para a tela.</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Fail-closed</span>
          <strong>{overview.notFoundCount} cenario(s) sem dados publicos</strong>
          <p>O status nao localizado continua previsto como resposta segura quando faltam evidencias suficientes.</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Entradas</span>
          <h2>Cenarios publicos disponiveis</h2>
          <p>Use a pagina de verificacao para navegar pelos estados operacionais do QR sem abrir excecao de sigilo.</p>
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

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Portal autenticado</span>
          <h2>Entradas canonicamente previstas para o cliente</h2>
          <p>O portal tambem passa a expor o dashboard logado do cliente com carteira, certificados e vencimentos.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href="/dashboard?scenario=stable-portfolio"
          eyebrow="Dashboard"
          title="Carteira estavel"
          description="Abrir a visao do cliente quando nao ha vencimentos imediatos no recorte atual."
          statusTone="ok"
          statusLabel="Sem alertas"
          cta="Abrir dashboard"
        />
        <NavCard
          href="/dashboard?scenario=expiring-soon"
          eyebrow="Vencimentos"
          title="Equipamentos vencendo em breve"
          description="Abrir o dashboard com foco em vencimentos proximos e acao preventiva."
          statusTone="warn"
          statusLabel="Atencao"
          cta="Abrir dashboard"
        />
      </section>
    </AppShell>
  );
}
