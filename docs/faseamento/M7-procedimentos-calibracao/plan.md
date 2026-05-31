---
owner: roldao
revisado-em: 2026-05-31
status: stable
fase: M7-procedimentos-calibracao
dominio: metrologia
modulo: procedimentos-calibracao
ritual: plan
versao: 1
depende-de:
  - docs/faseamento/M7-procedimentos-calibracao/spec.md (v2)
  - docs/faseamento/M7-procedimentos-calibracao/reviews-consolidado.md
  - docs/faseamento/M6-escopos-cmc/ (molde-espelho — entregue/auditado 6/6 PASS)
---

# Plan — M7 `metrologia/procedimentos-calibracao` (3º módulo Wave A)

> Deriva da spec v2 + `reviews-consolidado.md` (RBC + tech-lead APROVA COM
> CORREÇÕES — D-PROC-1..6 + C-1..4). Molde-espelho: M6 `escopos-cmc`. Path
> aninhado `src/{domain,application,infrastructure}/metrologia/procedimentos_calibracao/`
> (ADR-0072). **Nenhuma ADR nova.** Pronto para `/tasks`.

## 1. Arquitetura (molde M6, com as divergências D1..D5 do reviews)

- **Domínio puro** (`domain/metrologia/procedimentos_calibracao/`): enums,
  entities (snapshots frozen), repository Protocols, máquina de estados,
  invariantes puras. NÃO importa Django (ADR-0007).
- **Peça compartilhada** (D-PROC-6): extrair `faixa_contida` + `avaliar_contencao`
  de `domain/metrologia/escopos_cmc/cobertura.py:32-54` → novo
  `domain/metrologia/faixa_cobertura.py`. `escopos_cmc/cobertura.py` re-exporta
  (`from ...faixa_cobertura import faixa_contida, avaliar_contencao`) — zero
  mudança de assinatura/comportamento. **Suíte M6 reverde idêntica** (gate
  anti-regressão antes de mergear). NÃO mover `cmc_*`/`u_*` (M7 não tem).
- **Application** (`application/.../procedimentos_calibracao/`): use cases puros
  (Input frozen + Protocol) + porta `AnexoStoragePort` (Protocol).
- **Infra** (`infrastructure/metrologia/procedimentos_calibracao/`): models
  tipados, migrations irmãs, repositories, `query_service.vigente_em()`
  (**função de módulo**, não singleton — C-3), mappers, serializers, views, urls,
  adapter `AnexoStorage` (B2/filesystem), drill, management command.
- **Wire-in** (Fatia 3): 2ª porta `CoberturaProcedimentoPort` injetada em
  `configurar_calibracao` (3º parâmetro, default fail-open lazy), DEPOIS do
  portão de escopo, só RBC, 1ª falha interrompe.

## 2. Modelo de dados — `ProcedimentoCalibracao` (colunas TIPADAS, não JSONField)

| Campo | Tipo | Nota |
|-------|------|------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK | RLS v2 |
| `codigo` | varchar | identidade do doc controlado (cl. 8.3) |
| `titulo` | varchar | |
| `grandeza` | varchar (slug) | UMA por código (D-PROC-2) |
| `faixa_min/max` | Decimal | faixa contígua única no MVP |
| `unidade` | varchar | vocabulário `value_objects.py` |
| `metodo_norma` | varchar | NIT-DICLA / ABNT / OIML |
| `tipo_metodo` | varchar enum | NORMALIZADO/NAO_NORMALIZADO/MODIFICADO (cl. 7.2.2) |
| `registro_validacao_id` | UUID NULL | evidência validação (fail-open lazy) |
| `numero_revisao` | varchar | "Rev. 03" — cl. 8.3.2c |
| `aprovado_em` | timestamptz NULL | ato de aprovação (cl. 8.3.1) |
| `aprovado_por_id` | UUID NULL | + `aprovado_por_nome_snapshot` |
| `anexo_pdf_storage_key` | varchar | chave opaca |
| `anexo_pdf_sha256` | varchar | sha256 server-side (C-2) |
| `versao` | int | contador interno |
| `vigente_a_partir` | timestamptz | |
| `estado` | varchar enum | RASCUNHO/PUBLICADO/REVOGADO |
| `vigencia_inicio/fim` | timestamptz | ADR-0030 |
| `revogado_em` / `motivo_revogacao` | timestamptz / varchar | one-shot ADR-0031 |
| `revision` | int | CAS |
| `correlation_id` | UUID | molde M5/M6 |

**Constraints chave:**
- UNIQUE documental `(tenant_id, codigo, versao)` (INV-PROC-002).
- UNIQUE PARCIAL não-overlap `(tenant_id, codigo, grandeza, faixa_min, faixa_max)
  WHERE estado='PUBLICADO' AND vigencia_fim IS NULL AND revogado_em IS NULL`
  (INV-PROC-008 / D-PROC-3).
- CHECK vigência ADR-0030 (INV-VIG-001..004); CHECK `cmc`? n/a.
- índice parcial de resolução `WHERE estado='PUBLICADO' AND revogado_em IS NULL`.

## 3. Máquina de estados (D2 — diferente do M6)

`RASCUNHO` (editável) → `PUBLICADO` (vigente, WORM Padrão B) → `REVOGADO`
(terminal). Só `PUBLICADO` + vigente entra em `vigente_em()`. Revisão de PUBLICADO
= INSERT nova `versao` (não transição). `validar_motivo_revogacao` ≥10 chars.

## 4. INV-PROC-001..010 → enforcement → teste → hook

| INV | Enforcement | Teste (TST-004) | Hook |
|-----|-------------|------------------|------|
| 001 | `vigente_em` só PUBLICADO+vigente+contém faixa | `TestINV_PROC_001` PG | — |
| 002 | UNIQUE `(tenant,codigo,versao)` migration | `TestINV_PROC_002` + schema | migration-metrology-classifier |
| 003 | trigger WORM Padrão B (UPDATE campo técnico/DELETE de PUBLICADO) | `TestINV_PROC_003` PG | — |
| 004 | porta `vigente_em` fail-CLOSED + wire-in 412 | `TestINV_PROC_004` PG | **proc-vigente-fail-closed-check** (molde M6 escopo-cobre) |
| 005 | preenche `procedimento_versao_snapshot` (já existe M4) imutável | `TestINV_PROC_005` | — |
| 006 | `__post_init__` tz-aware + `vigente_em` | `TestINV_PROC_006` | — |
| 007 | `anexo_pdf_sha256` recalculado server-side; WORM | `TestINV_PROC_007` | — |
| 008 | advisory lock + UNIQUE parcial não-overlap | `TestINV_PROC_008` PG (concorrência) | — |
| 009 | publicar exige numero_revisao+aprovado_em+aprovado_por | `TestINV_PROC_009` | **proc-controle-documental-check** |
| 010 | `tipo_metodo` obrig.; A+não-normalizado→validação (fail-open lazy) | `TestINV_PROC_010` | **proc-metodo-validado-check** (fail-open lazy doc) |

Reusadas: INV-CAL-WORM-001, INV-CAL-VERSAO-001, INV-VIG-*, INV-SOFT-*,
INV-TENANT-*, INV-TENANT-PERFIL-001/003/004, INV-DOC-CANON-001, INV-HMAC-*.

## 5. Porta `vigente_em` (wire-in — C-3, molde M6 ADR-0073)

```
# infrastructure/metrologia/procedimentos_calibracao/query_service.py
def vigente_em(*, tenant_id, grandeza, faixa_min, faixa_max, unidade, data)
    -> ProcedimentoSnapshot | None:
    # filtro tenant_id EXPLÍCITO + PUBLICADO + vigente em data + faixa_contida
    # qualquer exceção -> None (fail-CLOSED; caller bloqueia RBC)
```

Wire-in em `configurar_calibracao.executar(inp, repo, cobertura=..., procedimento=_proc_fail_open_lazy)`:
- 3º parâmetro injetável (molde do `cobertura` linha 230-231).
- Roda DEPOIS do portão de escopo (após linha 323), só RBC, 1ª falha interrompe.
- Fonte server-side = `grandeza_decl`/`faixa_decl` já construídos (linhas 297-323) —
  reusa as MESMAS VOs (SEG-CAL-10 satisfeito pela peça #1).
- None → 412 `ProcedimentoVigenteAusente` (erro de domínio DISTINTO de
  `EscopoNaoCobreFaixa`). NÃO-RBC → aviso degradante (D-PROC-1), nunca bloqueia.
- Preenche `procedimento_versao_snapshot` real (código+versão+numero_revisao+
  sha256) — campo JÁ existe (C-1), não cria coluna.
- Predicate STUB `procedimento_vigente_para` deprecado (no-op) após wire-in.

## 6. Superseção (D-PROC-3) — publicar_procedimento

Dentro de `transaction.atomic()`:
1. `pg_advisory_xact_lock(hashtext(tenant||codigo||grandeza||faixa))` — serializa
   publicações concorrentes do mesmo procedimento (molde ADR-0065).
2. encerra `vigencia_fim = now()` da versão PUBLICADA vigente anterior (mesma
   chave natural), se houver — NÃO DELETE (WORM, auditoria retroativa).
3. INSERT/transição da nova versão para PUBLICADO + `aprovado_em`/`aprovado_por`/
   `numero_revisao` (INV-PROC-009).
4. UNIQUE parcial garante no banco "≤1 vigente por chave" (cinto-e-suspensório).
Evento WORM `procedimentos_calibracao.publicado` na cadeia hash (HMAC ADR-0064).

## 7. Anexo PDF (C-4 / D-PROC-5 / Q9-F) — 1ª porta storage real

- `AnexoStoragePort` Protocol (application): `salvar(pdf_bytes) -> storage_key`.
- Adapter infra (B2/filesystem) — porta "Storage" já no catálogo 18 portas ACL.
- View recebe multipart → **recalcula sha256 server-side** (ignora hash do
  cliente) → `port.salvar(bytes)` → grava `storage_key` + `anexo_pdf_sha256`.
- Anexo de PUBLICADO imutável (WORM trigger). Snapshot na calibração guarda o
  sha256 da época.

## 8. Eventos (Q9-E) — molde M6

Eventos WORM `procedimentos_calibracao.{publicado,revisado,revogado}` em
ACOES_CANONICAS, hash-chain HMAC ADR-0064, correlation_id real do envelope.

## 9. Fatias (INV-RITUAL-002) — deltas para o /tasks

- **Fatia 0 (pré) — peça compartilhada (D-PROC-6):** extrair `faixa_cobertura.py`
  + re-export em escopos_cmc + **reverde M6 idêntico**. Commit isolado.
- **Fatia 1a — domínio puro:** enums (RASCUNHO/PUBLICADO/REVOGADO) + entities
  (ProcedimentoSnapshot + ProcedimentoUsado probatório) + repository Protocols +
  invariantes puras (001/005/006/009/010 puros) + máquina de estados.
- **Fatia 1b — schema+infra:** models tipados + migrations (initial → RLS v2 →
  triggers WORM B → grants → seed authz `procedimentos_calibracao.{cadastrar,
  publicar,revisar,revogar,ver}`) + UNIQUE parcial não-overlap + query_service
  `vigente_em` + CAS + drill `validar_procedimentos_calibracao`.
- **Fatia 2 — use cases+API:** cadastrar(RASCUNHO)/publicar(superseção+lock)/
  revisar(nova versão)/revogar + AnexoStoragePort + upload sha256 server-side +
  ViewSet REST + serializers + idempotência (IDEMP-001) + urls na raiz.
- **Fatia 3 — wire-in + GATE-CAL-PROC-VIGENTE-PREDICATE:** porta real no
  configurar_calibracao (ordem escopo→procedimento) + preenche snapshot + teste
  transição fail-open→fail-closed (TST-005) + suíte M4 reverde + INV-PROC-* em
  REGRAS + TestINV_PROC_* + 3 hooks + validação cl. 7.11.

Cada fatia: ritual auditores (essenciais + roteados, MÉDIO+ bloqueia).

## 10. GATEs

GATE-CAL-PROC-VIGENTE-PREDICATE (central, Fatia 3) · GATE-PROC-DRILL-LOCAL
(PG real + **drill cronometrado de concorrência** superseção — limite honestidade
TL) · GATE-PROC-ANEXO-HASH (sha256 server-side + anexo PUBLICADO imutável) ·
GATE-PROC-METODO-VALIDADO (cl. 7.2.2 fail-open lazy → `licencas-acreditacoes`) ·
GATE-PROC-VALIDACAO-7.11 (parecer RBC credenciado — pré-produção).

## 11. Riscos (TL — limite de honestidade)

Concorrência de superseção (D-PROC-3) é race que passa em code review; UNIQUE
parcial + advisory lock mitiga, mas drill cronometrado PG real antes do 1º tenant
RBC externo é obrigatório (GATE-PROC-DRILL-LOCAL). Extração de `faixa_contida`
(Fatia 0) exige reverde M6 idêntico antes de prosseguir.

## 12. Próximo passo

`/tasks` (T-PROC-NNN) derivando estas 4 fatias + Fatia 0. Sem código antes do
tasks. `/implement` começa pela Fatia 0 (peça compartilhada) → 1a (domínio, sem
PG).
