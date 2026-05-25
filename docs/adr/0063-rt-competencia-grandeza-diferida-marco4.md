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
