# Auditoria de cerimônia do processo — rodada 1 (relatório consolidado)

---
owner: claude-code (mandato Roldão)
revisado-em: 2026-06-12
status: stable
---

> **Mandato (Roldão, 2026-06-12):** auditoria LIVRE do processo de desenvolvimento inteiro, SEM deferência às normas locais — identificar o que é cerimônia sem ganho que atrasa, e o que de fato protege o produto. As normas são do Roldão; **nenhuma recomendação se aplica sem veto/aprovação item a item dele.**
>
> **Método:** 6 investigações paralelas (custo por fase do ritual · eficácia dos auditores · custo dos hooks · duplicação de contagens · inflação ADR/INV/contexto · calibração risco×estágio), todas com medição real (git log, cronômetro, grep, leitura dos relatórios de auditoria das 10 frentes M3→PPS).
>
> **Não re-litigado:** INV-RITUAL-001 (achado MÉDIO trava fechamento) é decisão explícita do Roldão — custo apresentado em §6, sem recomendação de reabrir. Fatiamento (INV-RITUAL-002), roteamento (INV-RITUAL-003) e `status-projeto.sh` já decididos em 2026-05-29.

---

## §1 Números-chave (medidos)

| Métrica | Valor | Fonte |
|---|---|---|
| Proporção de esforço em LINHAS (3 frentes recentes) | 59% produto / 27% teste / 14% processo | inv. #1 (git --stat PPS/CFG/M5) |
| Proporção em TEMPO na frente PPS | P9 (auditores) = ~40% do tempo total; implementação = ~30% | inv. #1 (timestamps) |
| 2ª passada de auditores na PPS | ~4h pra produzir 26 linhas de doc e ZERO achado | inv. #1, commit `2939465` |
| Execuções de auditor M3→PPS | ~132 (~18M tokens); **~76% retornaram PASS limpo**; ~56 eram puramente confirmatórias | inv. #2 |
| Taxa de bug real por achado MÉDIO+ | ~37% (M3/M4, pré-reforma) → ~65-72% (CFG/PPS, pós-reforma) | inv. #2 |
| drift-docs como auditor LLM | 32 achados MÉDIO+, **0 bugs de produto** (100% contagem/status) | inv. #2 |
| supplychain em fechamento | **0 achados MÉDIO+ em toda a história** | inv. #2 |
| Verificação adversarial (M8) | dos 5 MÉDIOs, só 1 sobreviveu (1 falso-positivo + 3 rebaixados) | inv. #2 |
| Pedágio dos hooks por EDIÇÃO de arquivo | **~8,3 s** (71 hooks PreToolUse; 16 s sob carga); ~0,8 s por comando Bash | inv. #3 (cronometrado, 5 reps) |
| Pedágio por sessão típica de implementação | **~24 min** só de hooks (sessão pesada: ~47 min) | inv. #3 |
| Composição do custo | ~95% é spawn de processo (bash+2×perl por hook); 68 de 71 hooks acordam e morrem sem fazer nada num Edit típico | inv. #3 |
| `_test-runner.sh` completo | 10 min 44 s; rodado em 79 commits que tocaram hooks (~14h acumuladas) | inv. #3 |
| Falsos positivos de hook | **215+ marcas `# <hook>: skip` no código** (authz-check sozinho: 86) | inv. #3 |
| Rastro de bloqueio dos hooks | **ZERO** — nenhum hook persiste log; impossível saber quantas vezes cada um bloqueou de verdade | inv. #3 |
| Commits que tocam SÓ `.agent/CURRENT.md` | 113 (12,4% dos 913) | inv. #4 |
| CURRENT.md real | 98 linhas / 70 KB / ~36k tokens (autodeclara "≤40 linhas"; linhas de até 7.104 chars) | inv. #4/#5 |
| Carga fixa de contexto por sessão | ~38-50k tokens ANTES da 1ª palavra (CLAUDE+AGENTS+MEMORY+CURRENT) | inv. #5 |
| ADRs na tabela §11 carregada toda sessão | 82; **42 (51%) não mudariam nenhuma decisão de código atual** se fossem pra índice frio | inv. #5 |
| Regras em REGRAS-INEGOCIAVEIS.md | **340 IDs** (não 148 — o número do contrato já está em drift); 125 sem âncora mecânica, das quais ~85-90 são de módulos que NÃO EXISTEM | inv. #5 |
| Drift vivo achado durante a auditoria | AGENTS.md L292 diz "72 ativos" (real: 74) e o gate `--check` retorna OK — policiar cópia é estruturalmente furado | inv. #4 |
| Prova interna de que schema não se adia | SAN-PERFIL-TENANT (4 sprints) + SAN-INCERTEZA-PONTO (5 fatias) = preço real de retrofit de modelo de dados | inv. #6 |

---

## §2 Tese consolidada

O processo **NÃO está superdimensionado onde é caro errar**: RLS/WORM/triggers/snapshots/HMAC (retrofit impossível com dado real), anti-mascaramento, testes de invariante, drills PG-real, replay metrológico, P0 investigação e P2 revisão de plano são o que protege o ativo que existe hoje — e o projeto tem prova interna disso (2 retrofits caros de schema; drill que pegou 8 bugs na F-A; `varchar(20)` latente que só o INSERT real do M8 pegou).

O excesso está em **4 lugares**, todos mensuráveis:

1. **Tempo de máquina dos hooks** — checagem certa, momento e arquitetura errados (a cada edição, 74 processos, em vez de 1 dispatcher + pré-commit).
2. **Auditoria confirmatória** — re-passadas completas que produzem zero achado (~76% das 132 execuções foram PASS limpo); auditores que nunca acharam nada (supplychain, drift-docs) rodando por hábito.
3. **Máquina de cópia de status** — os mesmos números colados em 6 camadas de arquivo, um auditor pra policiar as cópias, ~40 achados "ALTO/MÉDIO" que eram número desatualizado, 113 commits só de diário.
4. **Papel de conformidade antecipado** — RAT/DPIA/dossiês/minutas emendados por módulo para tratamentos que não ocorrem e leitores licenciados que (por decisão do Roldão) só entram pré-produção; tudo barato de consolidar depois, ao contrário do schema.

---

## §3 Recomendações para veto item a item

Legenda de classificação: **(a)** cerimônia pura — cortar · **(b)** seguro superdimensionado pro estágio — re-agendar em GATE (nada deletado) · **(cal)** recalibração sem corte.

### Pacote A — Hooks (economia ~20 min/sessão + ~10 min/iteração de hook; NENHUMA checagem removida)

| ID | Recomendação | Classe | Economia |
|---|---|---|---|
| R1 | **Dispatcher único**: consolidar os 71 hooks de Edit/Write em 1 script (1 bash + 1 perl que parseia o JSON uma vez e roda os checks como funções). 8,3s → ~0,3-0,5s por edição. De quebra, ganha **log persistente de bloqueio** (hoje zero rastro). | (cal) | ~20 min/sessão |
| R2 | **Mover ~68 dos 74 hooks pra pré-commit** (diff staged, 1× por commit): os ~40 de invariante de domínio (que já têm teste pytest + trigger PG — o hook é a 3ª camada, a mais cara e mais fraca), os ~18 arquiteturais (migration só "existe" no commit) e os ~10 de doc/processo. **Ficam em write-time só os ~6 anti-desastre** (block-destructive, secrets-scanner, anti-mascaramento, mock-in-production, seed-anti-pii-real, csv-safety-import). | (cal) | incluso em R1 |
| R3 | **Test-runner seletivo**: mudança em hook roda só os casos do hook alterado (<1 min); suíte cheia de 10m44s só no fechamento de fase. | (a) | ~10 min/iteração |
| R4 | **Teto de crescimento**: hook novo de invariante de módulo nasce no dispatcher pré-commit por padrão (sem isso, a extrapolação é 200+ hooks e 20+ s/edição no fim da Wave A). | (cal) | evita regressão |

### Pacote B — Auditores (economia ~3-4h/frente ≈ 15-20% do tempo; trava MÉDIO do Roldão INTACTA)

| ID | Recomendação | Classe | Economia |
|---|---|---|---|
| R5 | **2ª passada escopada**: re-rodar SÓ os auditores que tiveram MÉDIO+, restritos ao diff do conserto. Proibir "passada de confirmação" extra (M5 fez 17 execuções pra confirmar o já confirmado). Full re-run só se o conserto adicionou código novo substancial. Evidência: PPS gastou 4h numa 2ª passada completa que achou ZERO. | (a) | ~3-3h30/frente |
| R6 | **Verificação adversarial de TODO achado MÉDIO+ antes do mutirão de conserto** (padrão M8 generalizado — lá matou 4 de 5 MÉDIOs). É o amortecedor que mantém a trava do Roldão barata. | (c→praxe) | evita consertos de ruído |
| R7 | **Aposentadorias formais**: `drift-docs` deixa de ser auditor LLM (32 achados, 0 bugs; o resíduo útil — pendência stale, ADR proposta superada — vira varredura mensal); `supplychain` sai do fechamento (0 achados na história; dispara só quando o diff toca pyproject/lock/Dockerfile — o hook DEP fica); `conformidade-lgpd` roteado por gatilho PII (já é a prática M6-M9; falta emendar o `ritual-orquestrador.md`). | (a) | 2-3 execuções/frente |
| R8 | **Tabela fechada de severidade por tipo**: drift de contagem nunca mais é ALTO (M3 teve 8×); nome de teste nunca é CRÍTICO (M3 Q-OS-01..04). Não reabre INV-RITUAL-001 — calibra a régua que alimenta a trava. | (cal) | menos mutirões |
| R9 | **TST-004/006/007 viram script** (grep mecânico de nome de teste/UUID literal/varredura), não julgamento de LLM dentro do auditor-qualidade. | (a) | ruído −12 achados/ciclo |
| R10 | **BAIXOs em lote pós-fechamento em módulo não-metrológico** (hoje ~14-20 BAIXOs são serializados DENTRO do ciclo). ⚠️ Toca a regra "resolver TUDO crítico→baixo" do Roldão — **precisa de decisão explícita dele**; sem aprovação, fica como está. | (cal) | ~1-2h/frente |

### Pacote C — Documentos e contexto (economia ~30-50k tokens/sessão + 30-50 commits/mês; drift de contagem morre POR CONSTRUÇÃO)

| ID | Recomendação | Classe | Economia |
|---|---|---|---|
| R11 | **Fonte única de contagens**: número vivo SÓ em `STATUS-GERADO.md`; AGENTS/CLAUDE/README trocam número por ponteiro; gate vira **denylist** (falha se existir `\d+ hooks/casos/ADRs/INVs` nos contratos — teria pego o "72 ativos" de hoje). | (a) | mata a classe de drift |
| R12 | **CURRENT.md cumpre o próprio cabeçalho**: ≤40 linhas CURTAS (~3 KB) — frente em curso, próximo passo, decisões abertas, gates bloqueantes. Módulo FECHADO migra pro `diario/` (abandonado desde 29/05) no ato do fechamento. 36k → ~1k tokens. | (a) | ~33k tokens/sessão |
| R13 | **AGENTS.md emagrece** (54 KB → ~8 KB): tabela §11 slim só com as ~40 ADRs vivas (ID + 6 palavras + módulo); as 42 frias/exauridas + 3 reservadas vão pra `docs/adr/INDICE.md` (frio); apagar enumeração-changelog dos 74 hooks em §3/§12 (é `ls` colado em prosa); header de status vira 3 linhas com ponteiros. | (a) | ~11k tokens/sessão e por subagente |
| R14 | **REGRAS-INEGOCIAVEIS.md fatiada**: núcleo transversal (~35 invariantes que o agente precisa LEMBRAR) + fatias por módulo em `docs/dominios/<mod>/invariantes.md` (auditor roteado lê só a fatia do diff); as ~85-90 famílias de módulos INEXISTENTES vão pra spec futura do módulo. 60k tokens → ~2,5k núcleo + fatia. | (b) | ~400-500k tokens/ritual P9 |
| R15 | **CLAUDE.md do projeto sem duplicar o global** (perfil do usuário + regra #0 já vêm do global; projeto mantém só deltas do harness Windows/GitBash/comandos). | (a) | ~1,2k tokens/sessão |
| R16 | **Fim dos commits isolados de CURRENT por fatia** — o handoff entra no commit da própria fatia. | (a) | ~30 min/frente |

### Pacote D — Papel de conformidade → GATEs (nada deletado; tudo re-agendado com gatilho nomeado)

| ID | Recomendação | Classe | Gate de reativação |
|---|---|---|---|
| R17 | **RAT LGPD formal + DPIA + censo de retenção saem do ciclo por módulo** → 1 passe consolidado. Spec mantém apontador-PII de 1 linha ("PII: campos X,Y — base legal Z") pra não perder conhecimento. Linha de retenção POR módulo continua SÓ quando há código de retenção (job/trigger). ⚠️ Gatilho certo: o 1º titular real é o **deploy do dogfooding** (clientes da Balanças Solution), não o 1º tenant externo. | (b) | **GATE-LGPD-RAT-CONSOLIDACAO** (novo) — bloqueia deploy dogfooding com dados reais |
| R18 | **Dossiês/URS cl. 7.11 em PROSA** → gate (tenant perfil A real OU auditoria CGCRE marcada). A EVIDÊNCIA executável (replay fixtures, `versao_motor`, marcador OQ em migration) **continua por módulo** — essa é irrecuperável depois. | (b) | **GATE-CGCRE-DOSSIE-PROSA** (novo) + GATE-PROC-VALIDACAO-7.11 (existente) |
| R19 | **Congelar emendas de minutas jurídicas/cláusulas de seguro por módulo** (OAB/SUSEP só entram pré-produção por decisão do Roldão — polir prosa que será reescrita é desperdício). Advogado/corretora seguem no P2 só pra risco de DESIGN (estrutura de dado, texto de tela). | (b) | GATE-LGPD-TOU/POP/DPA-MASTER + GATE-SEG-* (existentes) |
| R20 | **P8 enxuto**: matriz-reconciliação mantém §1/§2 (INV↔teste — única rastreabilidade que não existe em outro lugar) e §8 (ata do P9); corta §3/§4 (duplicam git log e settings.json; nenhum auditor as lê). Reconhecer formalmente que `INV-*` é o portador da rastreabilidade (IDs `AC-*` formais têm zero ocorrência nas frentes novas e a frente fechou 8/8 PASS assim). | (a) | — |
| R21 | **Workflow 6-leitores+3-lentes pra gerar tasks** só em módulo de risco metrológico/financeiro alto; módulo operacional usa P2 padrão. | (b) | critério no ritual |
| R22 | **Promoção de frontmatter draft→stable em lote periódico**, não como passo formal de cada fechamento. | (a) | — |

---

## §4 O que NÃO muda (valor real confirmado — confirmado pelas 6 lentes)

- **RLS v2 / WORM / triggers / snapshots probatórios / HMAC versionado / canonicalização** — retrofit proibitivo ou impossível; prova interna: SAN-PERFIL-TENANT + SAN-INCERTEZA-PONTO.
- **Anti-mascaramento / gate vermelho / block-destructive / secrets-scanner em write-time** — sem isso, 73 mil linhas de código IA não são confiáveis.
- **Testes de invariante nomeados + drills PG-real + replay metrológico** — drill REFUTADO como cerimônia (8 bugs na F-A; bug latente de schema no M8 que 100% da suíte com dados falsos nunca exercitou).
- **P0 investigação (regra #0)** — artefato MAIS consumido da cadeia; no M9 evitou reconstruir função inteira.
- **P2 revisão de plano pelos subagentes** — maior proteção/custo do processo (3 erros metrológicos do M5 pegos antes de 1 linha de código).
- **Fatiamento + roteamento (INV-RITUAL-002/003)** — derrubaram achados de 41→0-9 por frente; reforma que já se pagou.
- **P7 (INVs + hooks + testes)** — 35-40 min/frente, rastreabilidade real (INV-PPS: 73 referências).
- **P9 1ª passada roteada** — é a parte que paga o ritual (CFG: feature inteira faltando + rota de eliminação PII; PPS: bug 500, race, PII crua em WORM).
- **Auditores seguranca, idempotencia, produto, conformidade-lgpd (roteado), llm-correctness, performance** — concentram os achados que nenhum teste/hook pegaria (40-50% dos bugs reais só o auditor pegou).
- **spec/plan/tasks enxutos** — já no tamanho certo.
- **STATUS-GERADO.md + diario/** — os mecanismos de emagrecimento JÁ existem; falta usá-los como fonte única.

---

## §5 Economia total estimada (se tudo aprovado)

| Frente de economia | Estimativa |
|---|---|
| Tempo por frente de módulo (ritual) | **−20 a 25%** do tempo total (R5/R7/R10/R16/R20) |
| Tempo de máquina por sessão | **−20 min** (hooks R1-R3) |
| Contexto por sessão (toda sessão, todo subagente) | **−30 a 50k tokens** (R11-R15) |
| Tokens por ritual P9 | **−400-500k** (R14 + R5/R7) |
| Commits de contabilidade | **−30 a 50/mês** (R11/R12/R16) |
| Risco assumido | **~zero** — nenhum item movido protege algo que exista hoje; todos com gate nomeado |

## §6 Custo da trava MÉDIO (INV-RITUAL-001) — apresentado, sem recomendação

Decisão explícita do Roldão (mantida 2026-05-29). Custo medido: M4 (pré-reforma) = 26 MÉDIOs → ~4h30 de mutirões, sendo 35% drift de contagem; M8 (com verificação adversarial) = 5 MÉDIOs → 1 real; M9 = zero. **Com R6 (adversarial como praxe) + R8 (severidade por tipo) + R11 (fim do drift de contagem por construção), o custo residual da trava cai pra ~minutos/módulo.** O argumento mais forte A FAVOR da trava continua de pé: OBS-CAL-01 (M4) era "um MÉDIO de log" que na verdade era trilha WORM regulatória declarada e nunca emitida.

## §7 Pendências herdadas da auditoria máquina-dev (2026-05-29) ainda não feitas

Hook `fatiamento-plano-check` · automação banco-real one-shot · gerador da tabela de ADRs (absorvido por R13) · enxugar matriz-reconciliacao (absorvido por R20).

---

*Investigações executadas por 6 agentes paralelos em 2026-06-12; relatórios integrais nas transcrições da sessão.*

## §8 Decisão do Roldão (2026-06-12, AskUserQuestion)

**APROVADO TUDO — os 4 pacotes integrais, incluindo R10** (BAIXOs em lote pós-fechamento em módulo não-metrológico; todos continuam sendo consertados — muda só o momento). Aplicação iniciada na mesma data: pacotes B/C/D primeiro (governança + docs + gates), pacote A (dispatcher de hooks + migração pré-commit) na sequência como frente técnica própria.

**Aplicação CONCLUÍDA em 2026-06-12 — 5 commits:** `40d0fe3` (decisão §8) · `5097942` (pacote C: denylist + CURRENT 40 linhas + AGENTS slim + INDICE ADRs + CLAUDE enxuto) · `cca02b4` (pacotes B+D: ritual R5-R10/R20-R22 + checa-tst-mecanico + 2 GATEs novos + congelamentos) · `d76ff5e` (pacote A: write-time 66→5 hooks anti-desastre; 67 no manifest pré-commit; dispatcher `.githooks/pre-commit` com log de bloqueio; runner seletivo + gate anti-órfão) · `07991c2` (R14: 37 INVs de módulos não construídos → `docs/faseamento/invariantes-futuras.md`). Validação final: `_test-runner` completo verde + simulações de bloqueio/passagem do pré-commit + denylist verde. Nota: o 1º bloqueio REAL do novo pré-commit aconteceu durante o próprio fechamento (frontmatter inválido no STATUS-GERADO — gerador corrigido na causa raiz).
