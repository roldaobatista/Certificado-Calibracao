---
owner: agente-ia
revisado-em: 2026-06-03
proximo-review: 2026-09-03
status: ready-for-implement
diataxis: reference
audiencia: [agente, consultor-rbc, tech-lead]
frente: consolidacao-base
tipo: plano-frente
relacionados:
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
  - src/application/metrologia/calibracao/configurar_calibracao.py
  - src/infrastructure/ordens_servico/predicates_os.py
  - REGRAS-INEGOCIAVEIS.md
---

# Plano — GATE-OS-GRANDEZA-EM-ATIVIDADE (competência do executor por grandeza)

> **Origem:** decisão Roldão 2026-06-03 (consolidar a base pós-bloco-metrologia).
> Investigação regra #0 + **parecer `consultor-rbc-iso17025` (2026-06-03)** consolidados aqui.
> **Não precisa de ADR nova** — a ADR-0063 (aceita 2026-05-25) já decidiu a Opção A; o parecer
> **confirma** que está metrologicamente correta e detalha a sequência.

## 1. Estado real investigado (regra #0)

- `AtividadeDaOS.grandeza` (M3) **existe** (CharField) mas fica sempre `""` — ninguém preenche.
- Os 3 use cases M3 (`atribuir_tecnico`/`iniciar_atividade`/`operacoes_avancadas.transferir`)
  invocam `rt_competencia_cobre` com `grandeza=""` → **fail-open controlado** (ADR-0063).
- `Calibracao` (M4) **TEM** `atividade_os_id` (FK → AtividadeDaOS) + `executor_id` +
  `grandeza_calibrada`/`faixa_calibrada_*` (definidas na **configuração**, M4).
- Fluxo temporal: abrir OS → adicionar atividade (sem grandeza) → atribuir técnico →
  iniciar atividade → **configurar calibração (grandeza definida aqui)** → medir → emitir.
- A grandeza só existe na **configuração** — por isso o fail-open em M3 é correto por norma
  (a atividade técnica não começou; cl. 6.2 regula competência *para a atividade desempenhada*).

## 2. Decisão metrológica (parecer consultor-rbc — HÍBRIDO A + C, rejeita B)

**Dois pontos de enforcement OBRIGATÓRIOS e INDEPENDENTES (papéis distintos):**

| Papel | Cláusula | Onde validar | Status |
|-------|----------|--------------|--------|
| **Executor** (quem mede) | 6.2.1 + 6.2.5 e) | **`configurar_calibracao` (M4)** — quando a grandeza é cravada, ANTES de medir | ⏳ a implementar (Opção A) |
| **Signatário** (quem assina) | NIT-DICLA-021 | **`emitir_certificado` (M8)** — competência na grandeza na data `executada_em` | ⏳ confirmar INV-CER-COMP-001 |

- **Manter fail-open na atribuição/início M3** = CONFORME (a grandeza não existe ali; bloquear
  seria semanticamente errado). Documentar docstring "fail-open by design quando grandeza=''".
- **Rejeitar Opção B** (exigir grandeza na criação da atividade) — inverte a cl. 7.1.1 (a grandeza
  é resultado da análise crítica do RT ao examinar o instrumento, não decisão do balcão comercial).
- **Propagação M4→M3** (lazy): `configurar_calibracao` faz `UPDATE AtividadeDaOS.grandeza`, o que
  fecha o predicate M3 **retroativamente** para transferências de técnico POSTERIORES (drop-in
  ADR-0063 ponto 3).

**NCs MAIOR se NÃO implementar (perfil A/RBC):**
- NC-01 (6.2.1) — executor mede sem competência; só detectado no signatário (emissão).
- NC-02 (7.1.1+6.2) — `AtividadeDaOS.grandeza` nunca populada → predicate fail-open eterno.
- NC-03 (NIT-DICLA-021) — INV-CER-COMP-001 do signatário (confirmar se implementado no M8).

## 3. Sequência de implementação (ordem por dependência)

1. **Porta `CompetenciaExecutorPort`** (Protocol, molde das portas `cobertura`/`procedimento`
   ADR-0073 já existentes em `configurar_calibracao`) — default fail-open lazy p/ testes puros.
2. **`configurar_calibracao` (RBC + grandeza declarada):** após o portão de procedimento —
   - lê o técnico responsável: `AtividadeDaOS.tecnico_executor_id` (origem=ATIVIDADE_OS) OU
     `capacidade_tecnica_confirmada_por_user_id` (origem=AVULSA);
   - `competencia_executor(tenant_id, tecnico_id, grandeza, faixa, data)` → não cobre → 422
     `ExecutorSemCompetencia`;
   - propaga `repo.propagar_grandeza_para_atividade(atividade_os_id, grandeza)` (origem=ATIVIDADE_OS).
3. **Adapter real** (view injeta): junta leitura de `AtividadeDaOS.tecnico_executor_id` +
   `rt_competencia_cobre` (predicate M3 já existente, lógica real em `predicates_os.py:67-131`).
4. **Confirmar/implementar trava do signatário** na emissão M8 (INV-CER-COMP-001) — auditar
   `emitir_certificado.py`; se TRACK não-implementado, plugar competência-por-grandeza do signatário.
5. **Testes:** (a) atividade grandeza=MASSA + técnico sem competência → 422 em `configurar`;
   (b) gêmeo na emissão (signatário sem competência → bloqueio); (c) propagação preenche
   `AtividadeDaOS.grandeza` e transferência posterior passa a bloquear (drop-in).
6. **Docstring fail-open** nos use cases M3 (GATE-OS-PREDICATE-RT-FAIL-OPEN-DOC).

## 4. Verificação
configurar 24/24 + M4 chave + emissão M8 reverde + drill `validar_m3_os`/`validar_m4_calibracao`
+ ruff/mypy. Fecha **GATE-OS-GRANDEZA-EM-ATIVIDADE** (ADR-0063 ponto 4) + reforça INV-CER-COMP-001.

## 5. Pendência externa (declarada)
Parecer do consultor-rbc é **consultivo** (subagente IA, sem credencial CGCRE). Revisão por
consultor RBC humano credenciado fica **pré-produção** (`project_sem_contratacoes_externas_ate_producao`).
