---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: precificacao
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/precificacao/spec.md
  - docs/faseamento/precificacao/plan.md
  - docs/faseamento/precificacao/tasks.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `precificacao` (núcleo Wave A PARCIAL)

> **Pra quê:** provar, item por item, que cada US/INV da spec virou código real + teste.
> Formato R20 (ritual-orquestrador.md §3.7 — auditoria de cerimônia 2026-06-12):
> SOMENTE §1 rastreabilidade US/INV↔código, §2 INV↔teste, §8 ata do P9.
> Path achatado `src/{domain,application,infrastructure}/precificacao/` (D-PRC-1).
> Frente #3 da cadeia de preço.

---

## 1. Rastreabilidade US/INV ↔ código

| US / entidade | ACs / decisões | INV | Arquivo de código (símbolo) | Status |
|---|---|---|---|---|
| US-PRC-001 regra por item (PRECO_FIXO + MARGEM_ALVO) | AC-PRC-001-1/2/3 (publicar WORM; anti-retroativa; revogar+recriar) | **INV-PRC-COSTPLUS-STUB**, **INV-PRC-REGRA-IMUTAVEL**, **INV-PRC-REGRA-SEM-SOBREPOSICAO** | `src/domain/precificacao/enums.py` (`ModoFormacaoPreco`) · `src/domain/precificacao/entities.py` (`RegraFormacaoPreco`) · `src/domain/precificacao/transicoes.py` (`validar_vigencia_nao_retroativa`) · `src/application/precificacao/regra.py` (`publicar_regra`, `revogar_regra`) · `src/infrastructure/precificacao/models.py` (`RegraFormacaoPreco`) · migrations `0001_initial.py` + `0003_triggers_worm.py` + `0004_exclusions.py` | ✅ |
| US-PRC-002 mínimo + sugerido (estimado via custo manual) | AC-PRC-002-1/2/3 (fórmulas canônicas; mínimo ESTIMADO; determinismo bit-a-bit) | **INV-PRC-MINIMO-BLOQUEIO**, **INV-PRC-CUSTO-EXPLICITO** | `src/domain/precificacao/transicoes.py` (`calcular_precos`, `_calcular_item`) · `src/domain/precificacao/value_objects.py` (`Percentual`, `CalculoPrecoResultado`) · `src/domain/precificacao/erros.py` (`PrecoMinimoViolado`, `ParametrosInviaveis`) | ✅ |
| US-PRC-003 impacto do desconto (motor POR CESTA, <200ms p95) | AC-PRC-003-1/2/3 (semáforo; motor stateless; bloqueio mínimo duro) | **INV-PRC-MINIMO-BLOQUEIO**, **INV-026** (motor não persiste) | `src/domain/precificacao/transicoes.py` (`calcular_precos`) · `src/application/precificacao/calculo.py` (`calcular_precos`, `CalcularPrecosInput`, `ItemCestaInput`) · `src/infrastructure/precificacao/views.py` (`CalculoPrecoView`) | ✅ |
| US-PRC-004 aprovação por faixa | AC-PRC-004-1/2/3/4 (faixas contíguas; fingerprint; one-shot; decisor≠solicitante) | **INV-PRC-APROVACAO-ONE-SHOT**, **INV-PRC-APROVACAO-INDEPENDENTE**, **INV-PRC-FAIXAS-CONTIGUAS** | `src/domain/precificacao/entities.py` (`FaixaAprovacaoDesconto`, `PedidoAprovacaoDesconto`) · `src/domain/precificacao/transicoes.py` (`validar_faixas_contiguas`, `fingerprint_calculo`, `validar_decisor_independente`, `alcada_para_pct`) · `src/application/precificacao/aprovacao.py` (`solicitar_aprovacao`, `decidir_aprovacao`) · `src/application/precificacao/configuracao.py` (`configurar_faixas`, `seed_faixas_default`) · migrations `0003_triggers_worm.py` (trigger one-shot) | ✅ |
| US-PRC-005 multi-tabela (cliente-específico > padrão) | AC-PRC-005-1 (vínculo em tabela própria; fallback por item) | — | `src/domain/precificacao/entities.py` (`VinculoTabelaPrecoCliente`) · `src/infrastructure/precificacao/models.py` (`VinculoTabelaPrecoCliente`) · `src/infrastructure/precificacao/views.py` (`_resolver_preco_com_fallback`) | ✅ |
| US-PRC-006 simulações (deslocamento + imposto + parcelamento + comissão prevista) | AC-PRC-006-1 (motor agrega componentes na cesta) | — | `src/domain/precificacao/transicoes.py` (`calcular_precos`) · `src/application/precificacao/calculo.py` (`calcular_precos`) · `src/infrastructure/precificacao/views.py` (`_aliquota_imposto_fn`) · `src/domain/precificacao/entities.py` (`ParametrosPrecificacaoTenant`) | ✅ |
| US-PRC-007 alerta margem (semáforo expõe `sem_regra_formacao`) | AC-PRC-007-1/2 (semáforo RBAC; `abaixo_margem_minima` no resultado) | **INV-PRC-MARGEM-RBAC**, **INV-PRC-SEGREDO-LOG** | `src/domain/precificacao/enums.py` (`Semaforo`) · `src/domain/precificacao/value_objects.py` (`CalculoPrecoResultado.sem_regra_formacao`) · `src/infrastructure/precificacao/serializers.py` (`filtrar_visao_margem`) | ✅ |
| US-PRC-008 histórico praticado (contrato minimizado do evento) | (contrato ADV-PRC-04 — materialização diferida) | — | `src/infrastructure/precificacao/views.py` (`_publicar_evento_precificacao`) — evento `Precificacao.PrecoPraticado` MINIMIZADO (item_id, cliente_ref, orcamento_ref, preco_final, desconto_pct, fechado_em; sem margem_realizada) | ✅ (contrato apenas; GATE-PRC-HISTORICO-ORCAMENTOS) |
| `CalculoPreco` transiente (D-PRC-9) | Motor não persiste; consumidor carimba snapshot | **INV-026** | `src/domain/precificacao/transicoes.py` (sem import Django ORM) · `src/domain/precificacao/value_objects.py` (`CalculoPrecoResultado` frozen) | ✅ |
| Porta `CustoProvider` + stub | D-PRC-5/6 — stub retorna `CustoIndisponivel` EXPLÍCITO | **INV-PRC-COSTPLUS-STUB**, **INV-PRC-CUSTO-EXPLICITO** | `src/domain/precificacao/portas.py` (`CustoProvider`, `StubCustoProvider`) | ✅ |
| Predicate ABAC `alcada_cobre` | TL-PRC-11 / D-PRC-3 — registrado via `register_predicate` | **INV-PRC-APROVACAO-INDEPENDENTE** | `src/infrastructure/precificacao/apps.py` (`alcada_cobre`, `register_predicate`) | ✅ |
| Justificativa hash+par (D-PRC-15) | ADV-PRC-01 — WORM leva hash; cru em tabela-par mutável | **INV-PRC-JUSTIFICATIVA-HASH** | `src/infrastructure/precificacao/views.py` (`_hash_justificativa`, `_salvar_justificativa`) · `src/infrastructure/precificacao/models.py` (`JustificativaDecisaoDesconto`) | ✅ |
| Eventos `Precificacao.*` hashificados | ADV-PRC-03 — payload hashificado POR EVENTO; valores de Parâmetros/Faixas NUNCA em claro | **INV-PRC-JUSTIFICATIVA-HASH**, **INV-PRC-SEGREDO-LOG** | `src/infrastructure/precificacao/views.py` (`_publicar_evento_precificacao`) | ✅ |

---

## 2. INV ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste nomeado (arquivo:classe) | Cobertura E2E adicional |
|---|---|---|---|
| INV-PRC-COSTPLUS-STUB | domínio fail-closed (`publicar_regra` consulta `CustoProvider`; COST_PLUS sob stub → 422 `CustoRealIndisponivel`) + hook `prc-costplus-stub-check` | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_COSTPLUS_STUB` | `tests/test_precificacao_fatia2_e2e.py` (publicar COST_PLUS sob stub → 422) |
| INV-PRC-REGRA-IMUTAVEL | triggers WORM Padrão B: `regra_formacao_preco_worm_trg` + `regra_formacao_preco_block_delete_trg` (migration `0003_triggers_worm.py`) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_REGRA_IMUTAVEL` | `tests/test_precificacao_schema_fatia1b.py` (UPDATE direto → trigger raise) |
| INV-PRC-REGRA-SEM-SOBREPOSICAO | exclusion `btree_gist` `excl_prc_regra_vigencia` `(tenant, item) WHERE revogado_em IS NULL` (migration `0004_exclusions.py`) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_REGRA_SEM_SOBREPOSICAO` | `tests/test_precificacao_schema_fatia1b.py` (overlap RAISE + revogada libera) |
| INV-PRC-APROVACAO-ONE-SHOT | UPDATE escopado em `status='SOLICITADO'` + trigger `pedido_aprovacao_one_shot_trg` (migration `0003_triggers_worm.py`) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_APROVACAO_ONE_SHOT` | `tests/test_precificacao_schema_fatia1b.py` (2ª decisão → raise) |
| INV-PRC-APROVACAO-INDEPENDENTE | `validar_decisor_independente` (domínio) + CHECK `decisor_id != solicitante_id` (migration `0001_initial.py`) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_APROVACAO_INDEPENDENTE` | `tests/test_precificacao_fatia2_e2e.py` (decisor==solicitante → recusa) |
| INV-PRC-MINIMO-BLOQUEIO | `_calcular_item` levanta `PrecoMinimoViolado` 422 quando mínimo calculável (domínio) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_MINIMO_BLOQUEIO` | `tests/test_precificacao_dominio.py` (mínimo violado → bloqueio) |
| INV-PRC-CUSTO-EXPLICITO | `StubCustoProvider` retorna `CustoIndisponivel` tipado (nunca 0 silencioso) | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_CUSTO_EXPLICITO` | `tests/test_precificacao_dominio.py` (stub → `CustoIndisponivel`) |
| INV-PRC-MARGEM-RBAC | `filtrar_visao_margem()` choke-point em TODOS os serializers + hook `prc-margem-rbac-check` | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_MARGEM_RBAC` | `tests/test_precificacao_fatia2_e2e.py` (vazamento margem por endpoint não-calculadora → ausente sem `ver_margem`) |
| INV-PRC-SEGREDO-LOG | `_falha()` em `views.py` nunca inclui custo/margem; eventos Parâmetros/Faixas são refs-only | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_SEGREDO_LOG` | `tests/test_precificacao_fatia2_e2e.py` |
| INV-PRC-JUSTIFICATIVA-HASH | `_hash_justificativa` + `_salvar_justificativa` + hook `prc-evento-pii-hash-check` | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_JUSTIFICATIVA_HASH` | `tests/test_precificacao_fatia2_e2e.py` |
| INV-PRC-FAIXAS-CONTIGUAS | `validar_faixas_contiguas` (domínio) + replace-all atômico no use case | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_PRC_FAIXAS_CONTIGUAS` | `tests/test_precificacao_dominio.py` (faixas com buraco → `FaixasDescontoInvalidas`) |
| INV-026 (herdada) | `transicoes.py` sem import Django ORM (motor puro); `CalculoPrecoResultado` frozen | `tests/regressao/test_inv_prc_classes_nomeadas.py:TestINV_026_MOTOR_NAO_PERSISTE` | `tests/test_precificacao_dominio.py` (cortesia 100% não estoura; frozen) |
| INV-TENANT-001..003 (transversal) | RLS v2 FORCE nas 7 tabelas (migrations `0002_rls_policies.py`) | `tests/test_precificacao_schema_fatia1b.py` (RLS UNHAPPY cross-tenant ×7) | — |
| IDEMP-001 (transversal) | Idempotency-Key em solicitar/decidir/publicar/configurar; `calcular` SEM key (leitura computada) | `tests/test_precificacao_fatia2_e2e.py` | — |

---

## 8. P9 — ritual auditores roteados (INV-RITUAL-003)

> **Placeholder — preenchido no P9 (T-PRC-061).**
>
> Auditores roteados: qualidade · segurança · llm-correctness · idempotência ·
> conformidade-lgpd (PII em eventos/justificativa/RAT) · produto (6 essenciais
> sempre) + performance (motor+porta+cesta — N+1/200ms) + observabilidade
> (views financeiras + segredo em log). Supplychain N/A (núcleo sem dep nova).
> Drift-docs FORA do fechamento (ritual R7).
>
> Verificação adversarial de TODO MÉDIO+ antes do mutirão (ritual R6);
> 2ª passada escopada (ritual R5). Meta: zero CRÍTICO/ALTO/MÉDIO (INV-RITUAL-001).
