---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: aceito
aceito-em: 2026-05-25
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0063 — Predicate `rt_competencia_cobre` invocado mas fail-open controlado em Marco 3 OS (grandeza diferida para Marco 4 Calibração)

## Contexto

Auditor produto (2ª passada P5 do M3 OS, 2026-05-25) identificou que os 4 AC binários do PRD `os` v stable —

- **AC-OS-002-3** (`adicionarAtividade` → predicate `tenant_tem_rt_ativo_competencia` → 422 `TenantSemRTAtivo`)
- **AC-OS-002b-4** (`atribuirTecnico` → predicate `rt_competencia_cobre` → 422 `ExecutorSemCompetencia`)
- **AC-OS-003-6** (`iniciarAtividade` → re-validação competência na data de início)
- **AC-OS-012-2** (`transferirTecnico` → predicate competência novo técnico → 422 `TecnicoSemCompetencia`)

— não eram cumpridos em runtime: o predicate `rt_competencia_cobre` existe em `src/infrastructure/ordens_servico/predicates_os.py:67-131` com lógica REAL (consulta `ResponsavelTecnicoTenant` + `RTCompetencia`), mas as 4 views/use cases não acionavam ele.

Investigação revelou bloqueio estrutural: **`AtividadeDaOS` não persiste campo `grandeza`** no modelo atual (Marco 3). `grandeza` aparece apenas em payloads de evento de consumers de `acreditacao`. O predicate `rt_competencia_cobre` declara fail-open controlado quando `resource.grandeza` ausente:

```python
def rt_competencia_cobre(resource: dict[str, Any]) -> tuple[bool, str]:
    grandeza = resource.get("grandeza") or ""
    if not grandeza:
        return True, ""  # nao aplica (manutencao/instalacao/etc.)
```

Adicionar campo `grandeza` em `AtividadeDaOS` (migration + retrofit dos use cases + atualização de hooks) é mudança de modelo significativa que pertence ao Marco 4 `calibracao` (onde grandeza é primeira-classe — cada calibração tem grandeza+faixa+padrão metrológico). Marco 3 OS é fluxo operacional comercial (abrir/atribuir/iniciar/concluir/cancelar), não fluxo metrológico.

## Decisão

1. **Predicate `rt_competencia_cobre` é INVOCADO nos 3 use cases que carregam executor** (`atribuir_tecnico`, `iniciar_atividade`, `transferir_tecnico`) com o resource dict disponível em M3:
   - `tenant_id`, `executor_user_id`, `data` (data corrente).
   - **`grandeza` NÃO disponível** em M3 → predicate retorna `(True, "")` fail-open controlado por design documentado.
   - **`adicionar_atividade` NÃO invoca** — AC-OS-002-3 (tenant tem RT ativo para a grandeza) exige predicate tenant-level (`tenant_tem_rt_ativo_competencia`) que NÃO existe ainda; entra Marco 4 com `AtividadeDaOS.grandeza`.
2. **AC-OS-002-3 + AC-OS-002b-4 + AC-OS-003-6 + AC-OS-012-2 são MODIFICADOS** no PRD `os` para refletir:
   - "Predicate `rt_competencia_cobre` é invocado em runtime; comportamento de bloqueio (422 `TenantSemRTAtivo` / `ExecutorSemCompetencia` / `TecnicoSemCompetencia`) entra em vigor quando `AtividadeDaOS.grandeza` for persistido — pertence ao Marco 4 `calibracao` (módulo metrológico onde grandeza é primeira-classe)."
3. **Quando Marco 4 plugar `grandeza` em `AtividadeDaOS`** (via migration), o predicate começa a bloquear automaticamente — **zero mudança nos use cases**. Pattern de injeção via resource dict é drop-in.
4. **GATE-OS-GRANDEZA-EM-ATIVIDADE Wave A**: rastreio formal para entregar `AtividadeDaOS.grandeza` + migration + bump default do predicate em Marco 4 P3.

## Mitigação operacional (período de fail-open Marco 3)

- Marco 3 é **dogfooding-only** (Balanças Solution — projeto `project_sem_cliente_externo_agora`). Sem clientes externos pagos, risco de "técnico sem competência inicia calibração" é controlado por processo interno (gerente Balanças autoriza atribuição).
- **GATE-SEG-BPT-1** (feature flag `OS_PRODUTIVO_DOGFOODING_BS = False` por default) bloqueia OS produtiva em Balanças até apólice BPT emitida — predicate `pode_criar_os_produtiva_balancas` cobre.
- **GATE-OS-PREDICATE-RT-COMPETENCIA Wave A** (originalmente proposto pelo auditor produto na 1ª passada) é fechado por esta ADR — substituído por GATE-OS-GRANDEZA-EM-ATIVIDADE Wave A com escopo concreto (campo + migration + retrofit).

## Non-goals desta ADR

- NÃO adiciona campo `grandeza` em `AtividadeDaOS` agora (escopo Marco 4).
- NÃO altera contrato do predicate `rt_competencia_cobre` (já correto).
- NÃO mexe em `ResponsavelTecnicoTenant` / `RTCompetencia` (já corretos desde Marco 2 — ADR-0022).

## Consequências

- ✅ Predicate é invocado em runtime — auditor produto valida invocação.
- ✅ AC do PRD modificado refletindo realidade — não há AC binário em estado `stable` parcialmente válido.
- ✅ Caminho de bloqueio efetivo cravado (`grandeza` em `AtividadeDaOS` Marco 4).
- ✅ Fail-open documentado por ADR + mitigado por dogfooding-only + GATE-SEG-BPT-1.
- ⚠️ **Quando Marco 4 entregar**: `AtividadeDaOS.grandeza` migration vai mudar comportamento de runtime (predicate começa a bloquear). PRD de Marco 4 deve declarar isso como consequência cravada.

## Decisão final

**ACEITO 2026-05-25**. Predicate invocado + ADR modifica os 4 ACs + GATE-OS-GRANDEZA-EM-ATIVIDADE Wave A registrado. INV-RITUAL-001 satisfeito.

---

## Atualização M4 P3 — Opção A lazy (2026-05-25)

Review P2 do tech-lead-saas-regulado (P-CAL-T4) e decisão Roldão (D-M4-2 = **Opção A**) refinam o caminho de plug do predicate em Marco 4:

### Inversão temporal identificada

Marco 3 cria `AtividadeDaOS(tipo=calibracao)` em `iniciar_atividade` **antes** de existir `Calibracao` (consumer cria `Calibracao` em resposta a `Atividade.Iniciada`). Logo, no momento de `iniciar_atividade`, **ninguém ainda escolheu a grandeza** — a grandeza só é definida em `configurar_calibracao` (US-CAL-002 do Marco 4). Plug ingênuo de `grandeza` em `iniciar_atividade` resultaria em predicate fail-open eterno.

### Opção A — Lazy em `configurar_calibracao` + 3 use cases pós (ESCOLHIDA)

`AtividadeDaOS.grandeza` é **populada lazy** quando `ConfiguracaoCalibracao` é cravada. Predicate `rt_competencia_cobre` é invocado em **3 pontos**, não em `iniciar_atividade`:

| Use case | Predicate invocado | Comportamento |
|---|---|---|
| `configurar_calibracao` (US-CAL-002) | `rt_competencia_cobre(executor_user_id, grandeza_acabou_de_setar, em_data=hoje)` | 1ª chance de saber a grandeza. Falha → 422 `ExecutorSemCompetencia`. |
| `aprovar_revisao` (US-CAL-007) | `rt_competencia_cobre(revisor_user_id, calibracao.grandeza, em_data=hoje)` | RT 1ª conferência precisa cobrir a grandeza. Falha → 422 `RTSemCompetencia`. |
| `aprovar_2a_conferencia` (US-CAL-008) | `rt_competencia_cobre(conferente_user_id, calibracao.grandeza, em_data=hoje)` | RT 2ª conferência precisa cobrir a grandeza + ADR-0026 4 condições + `conferente_id != revisor_id`. Falha → 422 `ConferenteSemCompetencia`. |

Em `iniciar_atividade(tipo=calibracao)` o predicate continua sendo invocado com `grandeza=""` (fail-open controlado) — **documentado como proposital, não débito**. A grandeza ainda não foi escolhida; bloquear em `iniciar_atividade` seria semanticamente errado.

### Opção B (descartada) — Grandeza obrigatória em `criar_os`

Exigir grandeza obrigatória em `criar_os(tipo=calibracao)` forçaria análise crítica cl. 7.1 a já ter resultado escolhido — não reflete o fluxo real (cliente apresenta instrumento, RT examina, depois decide grandeza). Requer migration retrofit destrutiva em M3 + backfill de dados existentes. **Custo > benefício; descartado por Roldão (D-M4-2)**.

### Tarefas concretas em M4

- **T-CAL-RT-COMP-1**: migration em `src/infrastructure/ordens_servico/migrations/` (cross-marco — cresce campo M3) — `AtividadeDaOS.grandeza VARCHAR(50) NULL` + backfill default `""` para registros existentes (dogfooding Balanças Solution).
- **T-CAL-RT-COMP-2**: `configurar_calibracao` (use case M4) faz `UPDATE atividade_da_os SET grandeza=:g WHERE id=:atividade_id` na mesma transação que cria `ConfiguracaoCalibracao`.
- **T-CAL-RT-COMP-3**: `configurar_calibracao` + `aprovar_revisao` + `aprovar_2a_conferencia` invocam `rt_competencia_cobre` com resource dict completo (`grandeza` populado).
- **T-CAL-RT-COMP-4**: teste regressão `tests/regressao/test_rt_competencia_bloqueia_grandeza_setada.py` — atividade com `grandeza=MASSA` + RT sem competência massa → 422 `ExecutorSemCompetencia` em `configurar_calibracao`.
- **T-CAL-RT-COMP-5**: drill `validar_m4_calibracao` item 3 (vide spec §11): valida invocação em 3 use cases + bloqueio efetivo.

### Consequências da Opção A

- ✅ Sem retrofit destrutivo em M3 — `iniciar_atividade` permanece intacto.
- ✅ Predicate invocado nos 3 pontos onde a grandeza É conhecida — não em ponto onde não é.
- ✅ Semântica defensável em supervisão CGCRE: "competência validada no momento da configuração técnica + no momento da aprovação técnica + no momento da 2ª conferência".
- ⚠️ `iniciar_atividade` fail-open documentado proposital — **GATE-OS-PREDICATE-RT-FAIL-OPEN-DOC** rastreado: docstring na função declara explicitamente "fail-open by design quando grandeza='' — válido até configurar_calibracao popular".
- ✅ `GATE-OS-GRANDEZA-EM-ATIVIDADE Wave A` fechado: tarefas T-CAL-RT-COMP-1..5 entregam o que faltava.

### Status pós-atualização

**ACEITO ORIGINAL 2026-05-25** (predicate invocado fail-open em M3).
**ESCLARECIDO E APROFUNDADO 2026-05-25 P3 M4** (Opção A lazy — 3 use cases pós, NÃO `iniciar_atividade`). Tasks T-CAL-RT-COMP-1..5 cravadas pra M4 P3+P4.
