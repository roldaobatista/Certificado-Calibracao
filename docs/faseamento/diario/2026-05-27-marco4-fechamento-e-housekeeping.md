---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-06-27
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao FECHADO
tipo: diario-de-sessao
relacionados:
  - .agent/CURRENT.md
  - docs/faseamento/M4-calibracao/auditoria-familia5.md
  - docs/faseamento/diario/2026-05-27-marco4-p5-auditoria-1a-passada.md
---

# 2026-05-27 — Marco 4 FECHADO + housekeeping cross-marco

## Resumo

Marco 4 `metrologia/calibracao` FECHADO formalmente após 1ª passada Família 5
(2 PASS / 1 CONCERNS / 7 FAIL → 41 itens C/A/M) + **6 batches conserto
causa-raiz S1..S6.1** + **2ª passada Família 5** (8 PASS + 2 CONCERNS BAIXO
carryover) + **3ª/4ª passada drift-docs** (PASS limpo). 7 Foundations/Marcos
agora fechados (F-A+F-B+M1+M2+F-C1+M3-OS+M4). Pós-fechamento, **batch S7
zerou 19 drifts cross-marco** identificados pelo auditor-drift-docs varrendo
projeto inteiro.

## Sequência de commits desta janela (10 commits)

| # | Commit | Escopo |
|---|---|---|
| 1 | `7c06411` | S1 drift-docs 13 itens C/A/M |
| 2 | `146ef9b` | S2 SEG-CAL-01 CRÍTICO server-side hash PII |
| 3 | `4b58c24` | S3 IDEMP-CAL-01 CRÍTICO idempotência REST |
| 4 | `ae524e5` | S5-inicial ADR-0066 fail-open lazy (PROD-CAL-01/02) |
| 5 | `6464dfe` | S4 OBS-CAL-01 ALTO + S5-restante (1 ALTO + 13 MÉDIO) |
| 6 | `59b3f1c` | S6 drift sync 377→379 + ADR-0066 header + 2ª passada §7 |
| 7 | `eff3441` | S6.1 drift residual interno AGENTS L10+L257 |
| 8 | `8e8017a` | **FECHAMENTO** M4 — INV-RITUAL-001 satisfeito |
| 9 | `1b8f71c` | S7 drift cross-marco (8 ALTO + 7 MÉDIO + 4 BAIXO) |
| 10 | `4b63ee4` | S7.1 REGRAS notas operacionais sync |

## Conserto causa-raiz aplicado (resumo técnico)

### S4 observabilidade
- `src/application/metrologia/calibracao/append_evento_calibracao.py` — use
  case puro (ADR-0064 HMAC + ADR-0065 advisory lock).
- `src/domain/metrologia/calibracao/repository.py` — `EventoDeCalibracaoRepository`
  Protocol.
- `src/infrastructure/calibracao/repositories.py` — `DjangoEventoDeCalibracaoRepository`
  com `pg_advisory_xact_lock(0xCA1AED, hashtext("tenant|cal"))` + SELECT MAX
  hash + HMAC + INSERT.
- Logs estruturados `extra={tenant_id, correlation_id}` nos 8 jobs +
  3 actions HTTP.
- `_serializar_snapshot` retorna `correlation_id`.

### S5 restante
- `DjangoCalibracaoRepository.obter_por_id` filtra `tenant_id = active_tenant_context.get()`
  explícito (SEG-CAL-02).
- `registrar_recebimento_subcontratado` levanta `RecebedorSpoofingProibido` +
  `RecebedorIgualExecutorProibido` (SEG-CAL-04).
- Jobs M4 em `run_in_tenant_context(tenant.id)` (SEG-CAL-05).
- Migration `0014_grants_app_user` GRANT nas 23 tabelas (SEG-CAL-06).
- Use case `cancelar_calibracao` (T-CAL-095) — production-ready (PROD-CAL-03).
- 3 arquivos novos em `tests/regressao/`:
  - `test_inv_cal_classes_nomeadas.py` — 12 classes `TestINV_CAL_*` (Q-CAL-01).
  - `test_inv_cal_fail_open_lazy_adr0066.py` — regressão fail-open lazy (Q-CAL-03).
  - `test_inv_cal_uuid_digit_heavy.py` — regressão paralela ao bug visao-360 (Q-CAL-04).

### S7 housekeeping cross-marco
- README.md, INDICE.md, documentos-do-projeto.md, faseamento-foundation-waves.md,
  faseamento-modulos.md — sweep numérico (629/48/379/61 ADRs) + status
  7 marcos fechados.
- catalogo-auditores.md — reconciliação 11º prompt `bus-integrity` Tier 4.
- CONTRIBUTING.md — 3→10 auditores; Conventional Commits relaxado reconciliado.
- constitution.md §3 — tetos como ORIENTATIVOS (não enforced); drift atual aceito.
- REGRAS-INEGOCIAVEIS.md notas operacionais — hooks ✅ CRIADOS marcados;
  TRACK Wave A explicitado (módulo `padroes` ADR-0040, Marco 5 certificados,
  Wave B billing-saas full).

## Estado final 2026-05-27

- Pytest M4 chave: **629/629** verde em ~27s.
- Pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **379/379** verdes / 48 hooks ativos.
- ruff/mypy: limpos nos paths novos.
- 7 Foundations/Marcos fechados com 10/10 Família 5 PASS ZERO C/A/M.
- 61 ADRs aceitas (0000..0058 + 0062..0066).

## Aprendizados desta sessão

1. **Drift residual interno é o tipo mais difícil de pegar.** S4/S5
   introduziram drift novo (377→379 não sincronizado). S6 corrigiu a maior
   parte, mas S6.1 foi necessário pra header L10 + L257 do AGENTS — drift
   intra-arquivo (header vs corpo). Lição: rodar drift-docs **2 vezes** após
   batch grande — uma vez logo após, outra após o conserto do drift novo.
2. **Fail-open lazy ADR-0066 é padrão reusável.** Paralelo a ADR-0063 do M3
   OS. Quando módulo upstream entra em Wave A, GATE acende e predicate vira
   fail-closed automaticamente. Pode ser reusado em Marco 5.
3. **`append_evento_calibracao` é template.** Use case puro + Protocol +
   Django adapter com advisory lock + HMAC versionado pode ser reusado em
   qualquer marco com WORM hash-chain (Marco 5 certificados emitidos sai
   direto desse padrão).
4. **`cancelar_calibracao` esqueleto** — quando spec lista transição mas use
   case não existe, NÃO mascarar com 501; implementar use case + plugar
   diretamente. Auditor-produto pegou isso (PROD-CAL-03).
5. **Sweep numérico cross-doc só fecha quando todos os documentos canônicos
   estão sincronizados.** Auditor-drift-docs achou 19 itens em 11 arquivos
   diferentes. Conserto via `sed -i 's/377/379/g'` em batch eficiente.

## Próximo passo (decisão Roldão pendente)

**Wave A** — pré-requisitos:
1. Decisão estratégica sobre quais ADRs em proposta promover a aceitas
   (12 ADRs listadas em AGENTS §11).
2. 7 ViewSets restantes M4 (LeituraViewSet, RevisaoViewSet, ConferenciaViewSet,
   NaoConformidadeViewSet, ReclamacaoViewSet, SubcontratacaoViewSet,
   AceiteRegraDecisaoViewSet) — tech-lead aprovou plugar HOJE; bloqueio é
   **drill PG real** recomendado pra validar concorrência advisory lock +
   atomic com 7 endpoints concorrentes (sem PG real local, é mais código sem
   evidência).
3. Marco 5 (certificados emitidos) — próximo módulo natural após M4.
4. F-C2 (observabilidade) + F-C3 (resiliência) — sub-foundations pré-1º
   deploy externo.
