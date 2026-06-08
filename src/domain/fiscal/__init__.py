"""Domínio puro da frente `fiscal/NFS-e` (Wave A — núcleo de emissão agnóstica).

Núcleo lógico da emissão de NFS-e de serviço (calibração/manutenção) via porta
AGNÓSTICA de país/fornecedor (`FiscalProvider` — ADR-0008 §1), com a trava
metrológica por perfil rodando no USE CASE (não no permission layer DRF —
coerência ADR-0073). Adapters reais (PlugNotas/Focus), B2 `store_xml`, A3/OCSP,
contingência, CC-e e cutover ficam DIFERIDOS (GATE-FIS-* pré-produção).

Decisões cravadas no `plan.md` (D-FIS-1..10):
  - D-FIS-1: VO agnóstico — campos BR (`chave_acesso_44`/`numero`) em `metadata`,
    nunca atributo nomeado; o VO NÃO valida formato BR.
  - D-FIS-3/4: máquina de estados PENDING→AUTHORIZED|REJECTED; AUTHORIZED→CANCELED
    (REJECTED/CANCELED terminais); cancelamento = transição + evento append-only.
  - D-FIS-5/6/7: trava de perfil PURA combina perfil (Tenant, server-side) +
    `Certificado.tipo_acreditacao` (snapshot M8); NUNCA reconsulta vigência do
    Tenant (INV-FIS-002). Perfil A pode emitir cert NAO_RBC (D-FIS-6).
  - D-FIS-8: `MockFiscalProvider` vive no domínio (determinístico, sem I/O); o
    circuit breaker `pybreaker` vive na infra (diferido).

Domínio NÃO importa Django (ADR-0007). Path raiz própria `src/.../fiscal/`
(domínio `financeiro`, NÃO sob `metrologia/` — ADR-0072 só normatiza metrologia;
TL-08).
"""
