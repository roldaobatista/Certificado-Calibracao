import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export default function HomePage() {
  return (
    <AppShell
      eyebrow="Portal - verificacao publica"
      title="Consulta segura com metadados minimos"
      description="O portal publico foi preparado para materializar o recorte seguro do QR: autenticidade, reemissao e fail-closed sem expor dados sensiveis."
      aside={
        <>
          <div className="hero-stat">
            <span className="eyebrow">Principio de exposicao</span>
            <strong>Somente o minimo necessario</strong>
            <p>Sem cliente final, sem resultado metrologico e sem hash completo em tela publica.</p>
          </div>
          <div className="hero-stat">
            <span className="eyebrow">Estado do fluxo</span>
            <StatusPill tone="neutral" label="Pronto para V1/V4" />
            <p>As telas ja cobrem autenticidade, reemissao e nao localizado em um mesmo padrao visual.</p>
          </div>
        </>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Entradas</span>
          <h2>Cenarios publicos disponiveis</h2>
          <p>Use a pagina de verificacao para navegar pelos estados operacionais do QR sem abrir excecao de sigilo.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href="/verify?scenario=authentic"
          eyebrow="Autenticidade"
          title="Certificado autentico"
          description="Recorte minimo de dados para um certificado valido que segue ativo."
          cta="Verificar"
        />
        <NavCard
          href="/verify?scenario=reissued"
          eyebrow="Rastreabilidade"
          title="Certificado reemitido"
          description="Mostra o relacionamento com a revisao mais recente sem quebrar a cadeia historica."
          cta="Verificar"
        />
        <NavCard
          href="/verify?scenario=not-found"
          eyebrow="Fail-closed"
          title="Nao localizado"
          description="Resposta vazia e segura quando o portal nao encontra evidencias publicas suficientes."
          cta="Verificar"
        />
      </section>
    </AppShell>
  );
}
