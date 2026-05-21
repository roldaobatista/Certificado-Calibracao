---
owner: advogado-saas-regulado (consultivo — NÃO substitui OAB)
revisado-em: 2026-05-20
status: stable
---

# Review advogado — US-CLI-006 (T-CLI-114..120)

Veredito: **AJUSTAR** (7 BLOQ absorvidos).

## A1 — termset PII sensível
**AJUSTAR.** Lista art. 5º II LGPD é taxativa. **FALTAM**: racial/étnico, sindical, filosófica, ideologia, saúde reprodutiva. **FALSOS POSITIVOS FATAIS**: `pt/pl/vot/trans/gen` em ERP metrológico bloqueiam clientes legítimos. Trocar substring→word-boundary `\b` + termos ≥5 chars.

## A2 — SLA 15 dias + resposta TEMÁTICA — **BLOQ-1**
Res. CD/ANPD 2/2022 art. 11 exige resposta **temática fundamentada**, não só ack 200. `payload_resposta_titular` precisa schema por tipo (`acesso`/`eliminacao`/`correcao`/etc).

## A3 — flag `anonimizado_em`
**PROSSEGUIR.** Sem timestamp = defeito art. 37. Adicionar `anonimizado_em` + `anonimizado_motivo` enum (`LGPD_ART16_I/II/III`).

## A4 — efeito revogação — **BLOQ-2**
LGPD art. 8º §5º + art. 9º §3º: revogação cessa SÓ tratamento baseado em CONSENTIMENTO; outras bases subsistem. Helper `cliente_base_legal_aplicavel(cliente, finalidade)` precisa mapa `finalidade × bases_aceitas` cravado em `INV-CLI-002`.

## A5 — `qt_titulares_estimada`
**AJUSTAR.** `Cliente.count()` superestima. Helper recebe `cliente_ids: list[UUID]` OU `escopo: Literal["registro_unico"|"subconjunto_filtrado"|"base_inteira"]`. Default = `registro_unico`.

## A6 — idade <18 em EDICAO
**AJUSTAR.** NG-CLI-12 vale CREATE+UPDATE. Adicionar CHECK constraint `data_nascimento <= now() - interval '18 years'`.

## A7 — PII sensível legado
**NÃO-GOAL Marco 1.** Wave A: management `auditar_pii_sensivel_legado` advisory mode.

## BLOQs adicionais

- **BLOQ-4**: `motivo_recusa` + `base_legal_recusa` no modelo (art. 18 §4º recusa fundamentada).
- **BLOQ-5**: `payload_resposta_titular` (PII pro titular legítimo) NÃO passa pelo sanitizador padrão; `payload_auditoria` separado, sanitizado.
- **BLOQ-6**: idempotência via `causation_id` (não date-bucket — bloqueia titular legítimo refazendo pedido).
- **BLOQ-7**: `OperacaoTratamentoCliente.payload` precisa `base_legal` + `finalidade_negocial` (art. 37 inventário).

## Limites OAB

Minuta consultiva. Pré-1º tenant externo: consulta pontual (2-4h) com advogado licenciado pra:
- Termset PII sensível final.
- Templates de `payload_resposta` por tipo.
- Mapa finalidade×base-legal.
- Texto de recusa fundamentada.
