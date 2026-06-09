---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
status: draft
diataxis: reference
audiencia: [agente, auditor, advogado, tech-lead, consultor-rbc]
frente: fiscal-nfse
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/fiscal-nfse/plan.md
  - docs/faseamento/fiscal-nfse/tasks.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
  - docs/adr/0008-fiscal-pluggable.md
---

# Matriz de reconciliação — frente `fiscal/NFS-e` (núcleo de emissão)

> Fecha o ritual antes do P9 (auditores). Cruza US↔AC↔INV↔ADR↔hook↔código + INV↔teste
> + GATEs + pendências. Núcleo agnóstico (porta + mock + domínio + use cases + REST +
> P7), adapters reais/B2/contrato/A3/contingência diferidos (GATE-FIS-*).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US (PRD) | AC cobertos no núcleo | INV | ADR | Hook | Código |
|----------|----------------------|-----|-----|------|--------|
| US-FIS-001 emitir | AC-1 (happy mock) / AC-4 (cross-tenant) / AC-5 (idempotência) / AC-8 (perfil incompatível 403) / AC-9 (perfil D declaração, `tipo_servico=calibracao`) / **AC-10 (perfil A + NAO_RBC, D-FIS-6)** | INV-FIS-001/002/005/006/009 | ADR-0008/0067/0073 | `fiscal-perfil-server-side-check` · `fiscal-provider-import-fronteira-check` | `application/fiscal/emitir_nfse.py` · `infrastructure/fiscal/views.py` (`emitir`) · `domain/fiscal/perfil_documento.py` · `vinculo_metrologico.py` |
| US-FIS-003 cancelar | AC-1 (happy <24h) / AC-2 (prazo expirado 422) / AC-3 (cross-tenant 404) | INV-FIS-004/006 | ADR-0029/0064 | `audit-immutability-check` | `application/fiscal/cancelar_nfse.py` · `views.py` (`cancelar`, advisory lock) |
| US-FIS-001 consulta | resolve PENDING→AUTHORIZED/REJECTED | INV-FIS-004 | — | — | `application/fiscal/consultar_status_nfse.py` · `views.py` (`consultar`) |
| US-FIS-007 evento→título | **publica** `fiscal.nfse_emitida` (outbox); consumer `contas-receber` diferido | INV-FIS-CR-001 (reusada) | ADR-0033 | — | `views.py` (`_publicar_evento_fiscal`) · `acoes_canonicas.ACOES_FISCAL` |
| (anti-uso-indevido) | descrição B/C/D sem qualificador acreditado | INV-FIS-007 | ADR-0075 | `fiscal-anti-rbc-em-descricao` | hook + validador render (diferido) |
| (retenção) | NFS-e+XML zona B 5a | INV-FIS-008 | ADR-0021 | trigger block-delete | `migrations/0003` · `retencao-matriz.md` |

## 2. INV-FIS-* ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Classe `TestINV_FIS_*` | Enforcement real |
|-----|------------------------|------------------|
| INV-FIS-001 | `TestINV_FIS_001` | `documento_metrologico_obrigatorio_por_perfil` (use case) + hook perfil-server-side |
| INV-FIS-002 | `TestINV_FIS_002` | `vinculo_metrologico.ler_tipo_acreditacao` (server-side) + use case usa snapshot |
| INV-FIS-003 | `TestINV_FIS_003` | Protocol `FiscalProvider` + hook provider-import-fronteira |
| INV-FIS-004 | `TestINV_FIS_004` (PG) | trigger WORM `nota_fiscal_servico_worm_check` |
| INV-FIS-005 | `TestINV_FIS_005` + `test_unique_negocio_e_integrity` (PG) | UNIQUE `uq_nfse_origem_versao` + `obter_por_origem` + Idempotency-Key |
| INV-FIS-006 | `TestINV_FIS_006` (PG) | RLS pattern v2 (migration 0002) |
| INV-FIS-007 | `TestINV_FIS_007` | hook `fiscal-anti-rbc-em-descricao` (render runtime diferido) |
| INV-FIS-008 | `TestINV_FIS_008` (PG) | trigger `nota_fiscal_servico_block_delete` + matriz retenção |
| INV-FIS-009 | `TestINV_FIS_009` | entidade sem PII clara + `sanitizar_payload_audit` no evento |

## 3. Hooks novos da frente (camada A pré-commit)

| Hook | INV | Casos `_test-runner` |
|------|-----|----------------------|
| `fiscal-perfil-server-side-check` | INV-FIS-001 | FPS1..FPS6 (6) |
| `fiscal-provider-import-fronteira-check` | INV-FIS-003 | FPI1..FPI5 (5) |
| `fiscal-anti-rbc-em-descricao` | INV-FIS-007 | FAR1..FAR5 (5) |

Total +16 casos (527→543). Testados contra arquivos REAIS sem falso-positivo.

## 4. Entregas por fatia

| Fatia | Tasks | Commit | Verificação |
|-------|-------|--------|-------------|
| 1a domínio puro | T-FIS-010..015 | `e9a01a5` | 32 testes puros + ruff/mypy |
| 1b schema PG | T-FIS-020..023 | `06c96cb` | 8 testes PG + drill 11/11 |
| 2 use cases + REST | T-FIS-030..033 | `668dd04` | 12 E2E + Django check 0 |
| 3 P7 (REGRAS+hooks+matrizes) | T-FIS-040..043 | `d8a97b8` | 543/543 _test-runner + 10 INV |
| P8 (reconciliação+emendas) | T-FIS-050 | (este) | emenda ADR-0008/PRD |

## 5. GATEs do módulo (pré-produção — não bloqueiam fechamento)

GATE-FIS-PLUGNOTAS-REAL · GATE-FIS-FOCUS-REAL · GATE-FIS-B2-XML ·
GATE-FIS-SMOKE-TRIMESTRAL · GATE-FIS-CONTRATO (14 cláusulas — minuta escrita,
assinatura pré-produção) · GATE-FIS-CIRCUIT-BREAKER · GATE-FIS-A3-OCSP.

## 6. Pendências (não bloqueiam fechamento do núcleo)

- **Adapters reais + B2 + contrato + A3/OCSP + contingência/CC-e/inutilização/devolução/
  cutover** — diferidos com seam pronto (porta agnóstica + `store_xml` stub).
- **Consumer `contas-receber`** — evento `fiscal.nfse_emitida` já publicado no outbox;
  criação do título é frente própria depois (INV-FIS-CR-001).
- **Validação de render impresso INV-FIS-007** — runtime na frente PDF/template (hoje só
  hook estático + caller fornece descrição).
- **`amount` de orçamentos** — input do caller até `orcamentos` existir.

## 7. Veredito de reconciliação

Núcleo **completo e verificado**: 6 US/AC do núcleo cobertos, 9 INV-FIS com teste
nomeado + hook/trigger/RLS, 3 hooks verdes, 62 testes fiscais verdes (32+8+12+10),
`_test-runner` 543/543, ruff/mypy limpos, makemigrations limpo, Django check 0,
contagens sincronizadas (70/543/80/148). Emendas ADR-0008 + PRD cravadas.
**Pronto para P9** (auditores roteados).

## 8. P9 — ritual auditores roteados (INV-RITUAL-003)

A rotear (risco da frente): **seguranca** (perfil server-side L6 + cross-tenant +
WORM) · **conformidade-lgpd** (PII do tomador em 2 regimes INV-FIS-009 + retenção
zona B) · **supplychain** (porta agnóstica + deps futuras plugnotas/focus/pybreaker) ·
**idempotencia** (2 camadas INV-FIS-005) · **llm-correctness** (docstrings/`Any`) ·
**produto** (AC binários núcleo vs diferido). *(Preenchido no fechamento P9.)*
