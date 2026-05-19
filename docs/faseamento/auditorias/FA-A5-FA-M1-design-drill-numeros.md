---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
frente: FA-A5 + FA-M1
revisor: conserto prescrito no consolidado (sem fork de design — não exige review subagente)
veredito: prescrito
---

# FA-A5 + FA-M1 — Design: drill robusto + sincronizar números/status

> Conserto prescrito integralmente em `F-A-CONSOLIDADO-rodada-1.md` (FA-A5 ALTO,
> FA-M1 MÉDIO). Não há decisão arquitetural nova — é endurecer o drill (que
> declarava F-A verde com evidência fraca) + alinhar números driftados. Por
> isso não passa por review de subagente (proporcionalidade — princípio 6).
> A substância (hash chain por-tenant) já foi validada pelo tech-lead no FA-C1.

## Estado real verificado

- `validar_f_a.py::_verificar_hash_chain`: 1 tenant, 5 linhas, **só caminho
  feliz** — nunca prova detecção de adulteração nem isolamento por-tenant.
- `::_benchmark_p99`: 1 tenant, 1000 inserts sequenciais — §2 L95 exige
  "10k linhas × 50 tenants sintéticos".
- `test_isolamento_cross_tenant.py::test_50_threads_x_100...`: 50×100 — §2
  L94 exige **50×1000**.
- Label hardcoded `"Hooks 88/88 verdes"` em `validar_f_a.py:61` + texto
  `:7` — hooks reais hoje 113/113.
- Drift de números: `AGENTS.md`/`CLAUDE.md`/`drill-f-a-saida.md` citam
  "295 passed / 88 / 103 / 86.01%" e "F-A FECHADA 5/5"; real ≈ 259 passed
  + cobertura ~85% + hooks 113/113 + F-A **em saneamento** (não fechada).

## Decisão (conserto prescrito)

### FA-A5 — drill robusto (`validar_f_a.py`)

1. **`_verificar_hash_chain`** vira robusto:
   - **3 tenants** criados, inserts **intercalados** (A,B,C,A,B,C…) — prova
     cadeia independente por-tenant sob intercalação.
   - Verificação **por-tenant** (`verificar_integridade_cadeia(tenant_id=X)`)
     de cada um.
   - **Injeção de elo adulterado** num tenant (INSERT direto com
     `hash_atual` mentiroso) → exigir que a verificação **detecte**
     (UNHAPPY embutido no drill: se NÃO detectar, critério REPROVA).
   - **Concorrência**: N threads inserindo no mesmo tenant sob lock
     por-tenant → cadeia final íntegra (sequência monotônica, FA-C1).
2. **`_benchmark_p99`** multi-tenant: `--escala` (default reduzido pra dev:
   3 tenants × 500; `--escala` aproxima §2: 50 tenants × 200 = 10k linhas
   intercaladas). p99 medido sobre o conjunto multi-tenant, não 1 tenant.
   Gap explícito ao "10k×50 literal" documentado (drill de dev ≠ bench de
   produção; flag `--escala` cobre o pesado).
3. Label `"88/88"` → derivada do output real do runner (já parseia
   `"N ok, 0 falhas"`); texto do docstring idem.

### FA-A5 — fuzzing 50×1000

`test_50_threads_x_100_queries_zero_vazamento` → `_x_1000_`: 50 threads ×
1000 queries (50.000) cruzadas, ZERO vazamento. `@pytest.mark.slow`
(roda no drill final, não na suite normal).

### FA-M1 — sincronizar números/status

Fonte da verdade = saída real verificada nesta sessão:
- Suite: **259 passed** (sem skip nesta config) — atualizar onde citar 295/207.
- Hooks: **113/113** — substituir 103/88.
- Cobertura: **~85%** (84.x) — substituir 86.01%.
- Status F-A: **"FECHADA COM RESSALVAS — em saneamento (rodada 1→2)"** —
  substituir "F-A FECHADA 5/5" em `AGENTS.md`, `drill-f-a-saida.md`,
  `faseamento-foundation-waves.md` §10 (acrescentar linha de saneamento,
  não apagar histórico).
- `CLAUDE.md`: hooks 103→113; remover "F-A fechada" categórico.

## Não-objetivos

- NÃO rodar o fuzzing 50×1000 nem `--escala` na suite normal (são `slow`/
  flag; rodam no drill final manual). A suite normal continua rápida.
- NÃO reescrever histórico do `faseamento-foundation-waves.md` — acrescentar
  linha de correção de drift (FA-M1), preservar a trilha.
- NÃO marcar F-A "fechada" — ela só fecha na reauditoria rodada 2 verde.
