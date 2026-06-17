---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: caixa-tecnico
tipo: reviews-consolidado
relacionados:
  - docs/faseamento/caixa-tecnico/spec.md
  - docs/faseamento/caixa-tecnico/T-CT-000-investigacao.md
---

# Reviews consolidados P2 — frente `caixa-tecnico`

> 2 revisores (tech-lead + advogado LGPD; produto via Roldão já cravado em P0). Veredito geral:
> **APROVA COM CORREÇÕES** — todas incorporadas na `spec.md`. Nenhum REPROVA travante. Achados abaixo
> + onde foram cravados. (Consultor RBC não convocado — módulo transversal A/B/C/D sem gating
> metrológico; só retenção de PII de GPS varia, coberta pelo advogado.)

## tech-lead-saas-regulado — APROVA COM CORREÇÕES

| ID | Achado | Sev | Onde cravado |
|---|---|---|---|
| TL-CT-01 | Foto de recibo **NÃO** é `AnexoStoragePort` (esse é PDF, `salvar(pdf_bytes)`, sem validação de imagem). Molde correto = `equipamentos/services_foto_storage.py` (JPG/PNG + MIME + ≤5MB + EXIF strip). Hash sobre bytes **pós-strip** | ALTO | D-CT-4 + INV-CT-FOTO-DEDUP-001 |
| TL-CT-02 | Anti-duplicata: `tenant_id` 1ª coluna (RLS não escopa constraint — cicatriz TL-AGE-01); fronteira **storage idempotente global ≠ anti-fraude por tenant**; teste cross-tenant (fotos idênticas em tenants ≠ coexistem) | ALTO | D-CT-4 + INV-CT-FOTO-DEDUP-001 |
| TL-CT-03 | G6/PDF: **WeasyPrint existe** (`pyproject:35` + `equipamentos/services_etiqueta.py`). Não diferir por ferramenta — PDF é fatia leve Wave A; dado estruturado = fonte WORM, PDF = projeção on-demand | ALTO→resolve G6 | D-CT-8 |
| TL-CT-04 | G1/GPS: entidade na própria frente OK, mas porta **promovível a `shared`** (não "ou"); app-tecnico lê **a porta**, nunca a tabela; naming `ConsentimentoGpsColaborador` (colaborador-scoped) | MÉD→resolve G1 | D-CT-6 |
| TL-CT-05 | Trigger na **`despesa`** (corrige PRD "ON caixa_tecnico") `WHEN OLD.status='validada'` + block-delete **sempre** (fiscal 5a); reapresentação `rejeitada→pendente` NÃO dispara (teste obrigatório) | MÉD→confirma D-CT-3 | D-CT-3 + INV-CT-IMUT-001 |
| TL-CT-06 | `/sync/despesas-lote`: limite ≤20 itens + 413; **atomicidade per-item** (207-style, 1 foto ruim não trava o sync); dedup por item via `UNIQUE(tenant_id, client_offline_id)` (Idempotency-Key é do lote) | MÉD | D-CT-5 + INV-CT-IDEMP-001 |
| TL-CT-07 | `OSReferenciaPort`: declarar non-goal — despesa **não segue** cancelamento da OS (rastro histórico); checar c/ advogado se `os_id`→cliente expõe PII transitiva (UUID, provável não) | MÉD | D-CT-11 + §7 |
| TL-CT-08 | **Remover `AReembolsarPort`** (porta-stub que só publica = cerimônia sem contrato). `tenant-deve` = estado consultável + evento; contas-pagar faz **backfill por query** ao nascer (dinheiro não some no outbox) | MÉD | D-CT-8 + §6 |
| TL-CT-09 | Path **FLAT** confirmado (financeiro é flat: CR+fiscal; agenda aninhou só por espelhar `os`) | MÉD→confirma D-CT-1 | D-CT-1 |
| TL-CT-10 | Saldo derivado on-read **aprovado**; fechamento sob `pg_advisory_xact_lock` por `(tenant, tecnico)` (2 prestações concorrentes não congelam saldos divergentes) | MÉD→confirma D-CT-2 | D-CT-2 + INV-CT-PRESTACAO-001 |
| TL-CT-11 | `ACOES_CAIXA_TECNICO` **+ união em `ACOES_CANONICAS`** (senão `assert_acao_canonica` faz todo publish falhar — cicatriz TL-CR-11) | MÉD | D-CT-11 |
| TL-CT-12 | Perfil já auto-injetado no envelope por `publicar_evento`; módulo transversal **não gateia** → **sem coluna `perfil_no_evento`** nas tabelas | BAIXO | D-CT-10 |
| TL-CT-13 | `EventoAuditoriaCaixa` próprio só se GPS sensível não puder ir no payload geral; senão trilha via evento canônico WORM do bus | BAIXO | D-CT-10 |
| TL-CT-14 | EXIF da foto traz GPS → **strip remove**; GPS vem **só** do opt-in estruturado, nunca do EXIF (coerência LGPD) | BAIXO | D-CT-4/6 + INV-LGPD-CONSENT-001 |
| TL-CT-15 | Ordem de fatias: 1a domínio → 1b schema → 2 use cases/REST → 3a adapters → 3b eventos → 3c PDF → P8/P9 | BAIXO | §8 ação P3.5 |

**Limite de honestidade (escalar Roldão):** sync offline de fotos grandes é net-new sem molde → teste
de carga com falha de rede antes do 1º tenant pago; anti-duplicata é **bit-idêntica**, não semântica
(re-foto/crop passa) — non-goal §7.

## advogado-saas-regulado — minuta APROVA COM CORREÇÕES (consultiva, sem OAB)

| ID | Achado | Sev | Onde cravado |
|---|---|---|---|
| ADV-CT-01 | Base legal do GPS = **art. 7º IX (legítimo interesse + LIA da DPIA-02) + art. 7º V (apoio)**; opt-in = salvaguarda (art. 8º §5º/art. 18 §2º), **NÃO** base autônoma (consentimento de empregado é frágil, art. 8º §1º). A spec usava só V — corrigir | ALTO | D-CT-6 + INV-LGPD-CONSENT-001 |
| ADV-CT-02 | Retenção GPS de 5a viola **minimização (art. 6º III)** — 5a é lastro **fiscal** (foto+valor), GPS não é dado fiscal. GPS: **fechamento da prestação + 90d (máx 6–12m)**, desacoplado; foto+valor seguem 5a | ALTO | D-CT-6 |
| ADV-CT-03 | Foto de recibo carrega **PII de terceiros** (CPF na nota, placa); aviso de UI (molde AC-APP-006-5); EXIF strip antes de persistir; EXIF não vira 2º canal de GPS | MÉD-ALTO | D-CT-4 + §1 |
| ADV-CT-04 | `foto_hash` via **HMAC com chave do tenant** (ADR-0064), não SHA-256 global — crypto-shredding cobre o hash + impede correlação cross-tenant | MÉD | D-CT-4 + INV-CT-FOTO-DEDUP-001 |
| ADV-CT-05 | Revogabilidade OK (art. 8º §5º), mas falta **transparência (art. 9º)** — expor GPS da despesa no canal "Meus dados (LGPD)" (reuso US-ACS-012) | MÉD | D-CT-6 |
| ADV-CT-06 | Fronteira "caixa só lê o consentimento" correta, mas o **aviso ao titular** mora no termo de admissão/onboarding de RH (documento, não código); registro técnico colaborador-scoped + porta `shared` | ALTO | D-CT-6 + §1 |
| ADV-CT-07 | RAT-13: só corrigir o **apontador-PII** na spec agora (V→V+IX, retenção menor); entrada RAT completa só no **GATE-LGPD-RAT-CONSOLIDACAO** (respeitar congelamento R17) | MÉD | §8 ação P3.4 |
| ADV-CT-08 | Divergência interna (spec só V vs app-tecnico/RAT-13/T-CT-000 V+IX) — spec-as-source propagaria erro; INV-LGPD-CONSENT-001 **compartilhada** não pode ter 2 bases | MÉD/processo | D-CT-6 (sanado) |
| ADV-CT-09 | **GATE-CT-GPS-LGPD-OAB** (bloqueante de produção, molde GATE-AGE-JORNADA-TRABALHISTA): LIA assinada + termo de admissão c/ cláusula GPS + DPIA-02 aprovada | bloqueante prod | D-CT-13 + §8 ação P3.3 |

## Ações P3 (antes/durante plan/tasks) — ver spec §8

1. Corrigir **PRD** `caixa-tecnico/prd.md`: AC-CT-005-3 (trigger na `despesa`), AC-CT-002-5 (base V→**V+IX**),
   AC-CT-002-7 (retenção GPS própria curta).
2. **ADR curta** promovendo `ConsentimentoGpsPort`/entidade a `shared` (ou registrar promovível + diferir).
3. **GATE-CT-GPS-LGPD-OAB** em `gates-wave-a-consolidado.md` (🔴 OAB humano pré-produção).
4. `retencao-matriz.md`: linha própria do GPS da despesa **só no GATE-LGPD-RAT-CONSOLIDACAO** (R17).
5. Ordem de fatias 1a..3c + P8 + P9.

## Limites de subagente IA (escalonamento honesto)

- Base "legítimo interesse sobre empregado" + LIA + termo de admissão c/ cláusula GPS: advogado humano
  OAB antes do 1º técnico real (combina LGPD + Direito do Trabalho — vício de consentimento).
- Sync offline de fotos grandes (net-new): teste de carga com falha de rede antes do 1º tenant pago.
- Minutas escritas agora; revisão/assinatura humana só pré-produção (decisão Roldão —
  [[project_sem_contratacoes_externas_ate_producao]]).
