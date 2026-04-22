import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

export default function HomePage() {
  return (
    <AppShell
      eyebrow="V1 - emissao controlada"
      title="Backoffice regulado para onboarding e auth"
      description="Esta fatia transforma o web-ui em uma app real de back-office, com telas iniciais para auto-cadastro, onboarding e leitura operacional dos bloqueios duros antes da primeira emissao."
      aside={
        <>
          <div className="hero-stat">
            <span className="eyebrow">Foco imediato</span>
            <strong>Operacao Tipo B/C em ambiente controlado</strong>
            <p>Sem puxar regra normativa para o cliente e com linguagem pronta para V1.</p>
          </div>
          <div className="hero-stat">
            <span className="eyebrow">Estado do fluxo</span>
            <StatusPill tone="neutral" label="Scaffold funcional de UI" />
            <p>Telas preparadas para conectar com tRPC assim que os endpoints de dominio forem expostos.</p>
          </div>
        </>
      }
    >
      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Entradas</span>
          <h2>Rotas iniciais de operacao</h2>
          <p>As paginas abaixo cobrem os estados mais sensiveis do V1 e ja usam os view models canonicos do repositorio.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href="/auth/self-signup?scenario=signatory-ready"
          eyebrow="Auth"
          title="Checklist de auto-cadastro"
          description="Visualiza provedores habilitados, bloqueios por ausencia de SSO e o passo mandatorio de MFA."
          cta="Abrir auth"
        />
        <NavCard
          href="/onboarding?scenario=ready"
          eyebrow="Onboarding"
          title="Prontidao da primeira emissao"
          description="Mostra se a primeira emissao pode seguir ou se escopo, QR e numeracao ainda bloqueiam a operacao."
          cta="Abrir onboarding"
        />
        <NavCard
          href="/emission/dry-run?scenario=type-b-ready"
          eyebrow="Emissao"
          title="Dry-run consolidado"
          description="Encadeia os gates tecnicos de V1 em um preview unico antes da emissao oficial."
          cta="Abrir dry-run"
        />
      </section>
    </AppShell>
  );
}
