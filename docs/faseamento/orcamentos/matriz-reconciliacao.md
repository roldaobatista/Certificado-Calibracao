---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: orcamentos
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/orcamentos/spec.md
  - docs/faseamento/orcamentos/plan.md
  - docs/faseamento/orcamentos/tasks.md
  - docs/adr/0083-orcamento-preco-resolvido-reconcilia-vo-preco-prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `orcamentos` (Fatia 2 / Ondas 2a–2f)

> **Pra quê:** provar, item por item, que cada US/INV da spec virou código real + teste.
> Formato R20 (ritual-orquestrador.md §3.7): SOMENTE §1 rastreabilidade US/INV↔código,
> §2 INV↔teste, §8 ata do P9. Path aninhado comercial `src/{domain,application}/comercial/
> orcamentos/` + `src/infrastructure/orcamentos/` (D-ORC-2). Frente comercial #5 da cadeia.
>
> **Escopo do fechamento:** Fatia 2 (Ondas 2a–2f) — núcleo de orçamentos (criar/itens/
> enviar/aprovar/recusar/cancelar/expirar + análise crítica cl. 7.1 + link público 1-clique
> + conversão em OS). **NÃO fecha o módulo inteiro:** `US-ORC-005` (Templates / `TemplateViewSet`
> — T-ORC-039) fica como pendência aberta rastreada; `US-ORC-003/006/010` são Wave B.

---

## 1. Rastreabilidade US/INV ↔ código

| US / entidade | ACs / decisões | INV | Arquivo de código (símbolo) | Status |
|---|---|---|---|---|
| US-ORC-001 criar < 5 min | AC-001-1/2/3 (carimba `PrecoResolvido`; rejeita tabela expirada; item imutável) | **INV-ORC-PRECO-001**, INV-026 | `src/application/comercial/orcamentos/criar_orcamento.py` · `itens.py` (`adicionar_item`/`editar_item`) · `src/infrastructure/orcamentos/views.py` (`OrcamentoViewSet.create`/`adicionar_item`) · `serializers.py` · `models.py` + migration `0001_initial.py` | ✅ (PDF/envio = GATE-ORC-PDF, frente de telas) |
| US-ORC-002 aprovar 1-clique (link público) | AC-002-1/2/3 (preview sem login; aceite rico WORM; converte em OS) | **INV-ORC-APROVACAO-WORM**, **INV-ORC-LINK-TOKEN** | `src/infrastructure/orcamentos/views_publicas.py` (`OrcamentoPublicoView`) · `serializers_publico.py` · `migration 0009_resolver_orc_publico.py` (SECURITY DEFINER) · `repositories.py` (`salvar_aprovacao`, `revogar_link`) | ✅ |
| US-ORC-004 impacto do desconto na comissão | AC-004-1 (recálculo server-side; comissão só `ver_margem`) | **INV-ORC-MARGEM-OFF** | `src/application/comercial/orcamentos/itens.py` (`_recompor_agregado`) · `src/infrastructure/orcamentos/serializers.py` (gate `pode_ver_margem`) | ✅ (bloqueio escalado de desconto = Wave B) |
| US-ORC-007 conversão em OS com atividades | AC-007-1/2 (envelope por item; item técnico→atividade, comercial→`ItemComercialOS`) | **INV-ORC-APROVADO-ENVELOPE**, **INV-ORC-EQUIP-ITEM** | `src/domain/comercial/orcamentos/transicoes.py` (`montar_envelope_orcamento_aprovado`, `traduzir_tipo_atividade_alvo`) · `src/infrastructure/ordens_servico/consumers/orcamento.py` (`handle_orcamento_aprovado`) | ✅ (origem_item via `sequencia` = GATE-ORC-ORIGEM-ITEM) |
| US-ORC-008 bloquear cancelamento de convertido | AC-008-1/2 (409 `OrcamentoConvertido`; estado terminal) | **INV-ORC-CONVERTIDO-TERMINAL** | `src/application/comercial/orcamentos/ciclo_vida.py` (`cancelar_orcamento`) · `src/domain/comercial/orcamentos/transicoes.py` (`TRANSICOES_VALIDAS`, `validar_transicao`) · migration `0004_constraints.py` (trigger estado terminal) | ✅ |
| US-ORC-009 análise crítica cl. 7.1 perfil-aware | AC-009-1..6 (matriz A/B/C/D; fail-closed A; WORM rico) | **INV-ORC-CL71-001**, **INV-ORC-ANALISE-WORM** | `src/domain/comercial/orcamentos/analise_critica.py` (`decidir_analise_critica`, `calcular_snapshot_hash_analise`) · `src/application/comercial/orcamentos/aprovacao.py` (`aprovar_orcamento`) · `src/infrastructure/orcamentos/views.py` (`aprovar`) · `analise_critica_ports.py` (`avaliar_itens_calibracao`, `resolver_perfil_e_suspensao`) | ✅ (2 portas — `rt_competencia`/`padrao` reconciliados D-ORC-5; emenda AC-009-1 P8) |
| Snapshot de preço (D-ORC-1 / ADR-0083) | item carimba `PrecoResolvido`, não VO `Preco` novo | **INV-ORC-PRECO-001**, INV-026 | `src/domain/comercial/orcamentos/entities.py` (`ItemOrcamento.preco_resolvido` frozen) · `src/domain/produtos_pecas_servicos/entities.py` (`PrecoResolvido`) | ✅ (ADR-0083 + emenda PRD P8) |
| Anonimização de cliente (LGPD) | propaga por estado (rascunho cancela / enviado expira / aprovado+ preserva) | **INV-ANON-001..004** | `src/infrastructure/orcamentos/consumers/cliente_anonimizado.py` · `src/application/comercial/orcamentos/ciclo_vida.py` (`anonimizar_cliente_em_orcamentos`) | ✅ (consumer dormente até `clientes` publicar = GATE-ANON-EVENTO-RECONCILIAR) |
| Expiração de orçamento | sweep idempotente por `orcamento_id` | **INV-ORC-EXP-001** | `src/infrastructure/orcamentos/views.py` (`expirar_vencidos`) | ✅ parcial (corte por timezone-tenant = GATE-ORC-EXPIRY-JOB, job procrastinate diferido) |
| US-ORC-005 Templates | AC-005-1/2 (CRUD + gate selo RBC) | — | `src/domain/comercial/orcamentos/entities.py` (`Template`) · `models.py` (`Template`) — **REST `TemplateViewSet` NÃO entregue** | 🔲 PENDENTE (T-ORC-039) |
| US-ORC-003/006/010 | versionar v2 / tracking leitura / cobrança gateway | — | — | ⏭️ Wave B (fora de escopo) |

---

## 2. INV ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (arquivo) |
|---|---|---|
| INV-ORC-PRECO-001 | `ItemOrcamento`+`PrecoResolvido` frozen; `VersaoOrcamento` WORM (D-ORC-8) | `tests/regressao/test_inv_orc_preco_001.py` (frozen + não-retroage) |
| INV-ORC-CL71-001 | domínio puro `decidir_analise_critica` (fail-closed A + indeterminado) + hook `orc-analise-perfil-check` | `tests/regressao/test_inv_orc_cl71.py` (UNHAPPY por perfil 422+WORM) + `tests/test_orcamentos_analise_critica.py` (matriz pura) |
| INV-ORC-CONVERTIDO-TERMINAL | `TRANSICOES_VALIDAS` (frozenset vazio) + trigger `orcamento_estado_terminal_trg` | `tests/test_orcamentos_schema.py` (drill trigger) + `tests/test_orcamentos_dominio.py` (frozenset vazio) |
| INV-ORC-APROVACAO-WORM | trigger `orcamento_aprovacao_anti_mutation_trg` (migration 0003) | `tests/test_orcamentos_schema.py` (UPDATE/DELETE → raise) |
| INV-ORC-LINK-TOKEN | partial unique `uq_orcamento_link_ativo` WHERE revogado IS NULL; `secrets.token_urlsafe(32)` | `tests/test_orcamentos_schema.py` (link único; 2º após revogar OK) + `tests/test_orcamentos_publico.py` (404 indistinguível) |
| INV-ORC-APROVADO-ENVELOPE | função pura `montar_envelope_orcamento_aprovado` + hook `orc-envelope-contrato-check` | `tests/regressao/test_inv_orc_envelope.py` (contrato produtor→consumidor + replay dedup + UNHAPPY) |
| INV-ORC-ANALISE-WORM | trigger `analise_critica_orcamento_anti_mutation_trg` + `snapshot_hash` ADR-0029 carimbado | `tests/test_orcamentos_schema.py` (UPDATE/DELETE → raise) + identidade hash em `test_inv_orc_cl71.py`/`test_orcamentos_analise_critica.py` |
| INV-ORC-EQUIP-ITEM | CHECK `ck_item_orc_bifurcacao` (migration 0004) + `ItemOrcamento.__post_init__` | `tests/test_orcamentos_schema.py` (drill CHECK as duas pontas) + `tests/test_orcamentos_dominio.py` |
| INV-ORC-MARGEM-OFF | allowlist `_ITEM_CAMPOS_PUBLICOS` + hook `orc-margem-off-check` | `tests/regressao/test_inv_orc_margem_off.py` (snapshot sem margem + allowlist) + `tests/test_orcamentos_publico.py` (E2E) |
| INV-ORC-EXP-001 | sweep filtra só `ENVIADO`→`EXPIRADO` (idempotente por estado) | `tests/test_orcamentos_fatia2.py` (`test_expirar_vencidos_idempotente`); timezone-tenant = GATE-ORC-EXPIRY-JOB |
| INV-TENANT-001..003 (transversal) | RLS v2 FORCE nas tabelas (migration 0002) + roles NOBYPASSRLS (0005) | `tests/test_orcamentos_schema.py` (RLS UNHAPPY cross-tenant) |
| INV-BUS-001 / IDEMP (transversal) | `@consumer_idempotente` (os_aberta/cliente_anonimizado/orcamento_aprovado) + Idempotency-Key nos POST | `tests/test_orcamentos_fatia2.py` (replay consumers + idempotência aprovar) |

---

## 8. P9 — ritual auditores roteados (INV-RITUAL-003) — VEREDITO FINAL

**8 auditores roteados** (qualidade · segurança · llm-correctness · idempotência ·
produto · performance · observabilidade · conformidade-lgpd OBRIGATÓRIO).
Supplychain N/A (sem dep nova). **Resultado: 8/8 PASS ZERO CRÍTICO/ALTO/MÉDIO
após conserto + 2ª passada escopada — INV-RITUAL-001 satisfeito.**

| Passada | Resultado |
|---|---|
| **1ª** | 7 PASS (segurança · llm · idempotência · produto · performance · observabilidade · conformidade-lgpd) + **1 MÉDIO**: QUALIDADE — INV-ORC-PRECO-001 (snapshot imutável, não retroage) SEM teste citando o ID (TST-004), embora a barreira exista no código (`ItemOrcamento`/`PrecoResolvido` frozen). **Verificação adversarial (R6) confirmou real** (grep: zero teste citando o ID; "não-retroage" não exercitado). |
| **conserto causa-raiz** | criado `tests/regressao/test_inv_orc_preco_001.py` (3 testes: item frozen → `FrozenInstanceError`; carimbo frozen; snapshot a 150,00 não muda quando fonte resolve 300,00). `setattr` usado p/ provar barreira de runtime (sem `type: ignore`). 3/3 verdes em PG real. |
| **2ª (escopada R5 — só QUALIDADE, restrita ao conserto)** | **QUALIDADE PASS** — MÉDIO resolvido na causa-raiz, zero novo mascaramento. |

**Achados BAIXO / GATE (lote pós-fechamento, não bloqueiam):**
- PRD AC-ORC-009-1 (4→2 predicates) + glossário `tipo_atividade_alvo` (sem `OUTRO`; `verificacao`) — **✅ emendados P8** (espelho ADR-0083).
- `repositories.revogar_link` filtra só por `id` (RLS FORCE cobre cross-tenant; defesa-em-profundidade Python ausente — registrar como follow-up).
- INV-ANON-004 (`anonimizacao_propagada` em `acessos_dados_cliente`) — consumer dormente; finalidade ainda não existe em `FinalidadeAcessoCliente` → anexar ao **GATE-ANON-EVENTO-RECONCILIAR** (débito gêmeo no consumer de `ordens_servico`).
- `views_publicas.py` log de perfil indeterminado sem `extra={tenant_id, correlation_id}` (endpoint pré-RLS; evento de auditoria correlacionado já emitido).
- `scripts/checa-tst-mecanico.sh`: regex de famílias cego a IDs INV multi-segmento/sufixo-textual (INV-ORC-*) — não pegou o MÉDIO automaticamente; registrar p/ dono do script.
- GATEs rastreados: GATE-ORC-RATELIMIT-PUBLICO · GATE-LGPD-RETENCAO-APROVACAO · GATE-ORC-PUB-PERF · GATE-ORC-PUB-FORENSE · GATE-ORC-EXPIRY-JOB · GATE-ORC-PADRAO · GATE-ORC-ITEMCOMERCIAL-DESCRICAO · GATE-ORC-CMC-PREENCHIDO · GATE-ORC-KMS-APROVADOR · GATE-OBS-ORC-METRICA-APROVACAO · GATE-ORC-PERF-APROVAR · GATE-ORC-TERMINOLOGIA-BCD · GATE-ORC-SAGA-DLQ.

**Pendência aberta (não-goal de fatia):** US-ORC-005 Templates (`TemplateViewSet` + gate selo RBC) = T-ORC-039.

**Lição registrada:** o gate mecânico TST-004 (`checa-tst-mecanico.sh`) estava CEGO à
família INV-ORC (regex não casa ID nomeado multi-segmento). Foi a auditoria humana-
substituta do auditor-qualidade que pegou a invariante de abertura sem teste — confirmação
de que o auditor LLM cobre o ângulo que o checador estático não alcança.
