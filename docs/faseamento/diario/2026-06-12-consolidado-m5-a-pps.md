---
owner: claude-code
revisado-em: 2026-06-12
status: stable
---

# Diário histórico — M5 até PPS + consolidação da base + auditoria de cerimônia

> Migrado de `.agent/CURRENT.md` em 2026-06-12 (R12 da auditoria-cerimonia-rodada-1).
> CURRENT.md agora segue o próprio cabeçalho (≤40 linhas). Fonte de contagens: `docs/governanca/STATUS-GERADO.md`.

---

## M5 `metrologia/padroes` (1º módulo Wave A) — FECHADO 2026-05-29

**Fase:** Wave A em curso. M5 FECHADO — ritual completo P1→P10. P9 (10 auditores) abriu achados; Roldão mandou construir os 3 (dossiê CGCRE + carta read-model + vínculo auxiliar CRUD); P10 entregou via REST (INV-PAD-007 provado ponta-a-ponta). Re-passada INV-RITUAL-003 (9 auditores) + confirmação (8 auditores) = **8 PASS, zero achado bloqueante** — todos os achados de gravidade média resolvidos na causa-raiz; 3 BAIXO viraram GATE rastreado (GATE-LGPD-PAD-DOSSIE-1 / GATE-OBS-PAD-CORRELACAO-LOG / GATE-SEG-PAD-DEFESA-PROFUNDIDADE). Verificação independente: p5+p10 23/23 verde, ruff/mypy limpos, hooks verde, drill `validar_m5_padroes` 43/43. INV-RITUAL-001 satisfeito. Frontmatter dos docs M5 promovido `draft→stable`. Commits da fase: `d6e1f69`/`d37011c`/`152fbf1`/`dab606e` + fechamento.

ADRs aceitas no M5: **0070** (carta Shewhart híbrida), **0071** (2 implementações cl. 7.11 do MESMO mensurando), **0072** (path infra metrologia aninhado).

---

## M6 `metrologia/escopos-cmc` (3º módulo Wave A) — FECHADO 2026-05-30

Ritual P0-P3 (planejamento) FECHADO. Dossiê (workflow 5 leitores, 80 achados) → spec v2 → plan v2 `ready-for-tasks` → tasks (5 fatias, T-ECMC-NNN). Revisões tech-lead + RBC = APROVA COM CORREÇÕES (2 CRÍTICO + 6 ALTO) → **ADRs aceitas: 0073** (validação no use case, não DRF), **0074** (cobertura RBC tridimensional), **0075** (separação terminológica B/C/D ≠ CMC acreditada A) + emenda ADR-0066.

Decisões Roldão: rótulo "CMC (menor incerteza declarada)" + extração automática do PDF CGCRE (com conferência humana — Fatia 4) + todos os perfis declaram (A=RBC, B/C/D=capacidade interna).

**Fatias 1a+1b+2 FECHADAS (2026-05-30):** domínio + schema + use cases + REST + idempotência + WORM + 82 testes M6 verdes + drill + hooks.

**Fatia 3 Etapa 1 FECHADA (2026-05-30):** wire-in porta `CoberturaEscopoPort` no use case `configurar_calibracao`. Predicate STUB `cmc_cobre` DEPRECADO (no-op). Fail-open lazy enquanto fonte estruturada não existir (GATE-CAL-CMC-PREDICATE).

**Ordem de dependência bloco metrologia CRAVADA (2026-05-30):** `docs/faseamento/ordem-dependencia-bloco-metrologia.md`. ADR-0076 aceita (faixa DECLARADA na config vs pontos medidos na emissão).

**Frente SAN-FAIXA-CALIBRADA FECHADA (2026-05-30):** `Calibracao.grandeza_calibrada`+`faixa_calibrada_declarada` cravados. GATE-CAL-CMC-PREDICATE (portão de configuração) FECHADO. Commits `cb8fd56`/`af85cbb`/`dc08489`/`b246bc9`/`2af1d6d`.

**Fatia 4 (extração PDF CGCRE) FECHADA (2026-05-30):** motor `extracao.py` determinístico + use cases `importar_escopo_pdf`/`confirmar_escopo_extraido` + REST + fixture replay cl. 7.11.

**P7 FECHADO (2026-05-30):** INV-ECMC-001..009 + 3 hooks + 22 testes + drill 17/17.

**P8 FECHADO:** emenda PRD + matriz-feature-perfil + matriz-reconciliacao.

**P9 FECHADO — M6 FECHADO (2026-05-30):** 6/6 PASS ZERO C/A/M. 4 achados BAIXO viraram GATE rastreado. Frontmatter M6 promovido `draft→stable`.

---

## M7 `metrologia/procedimentos-calibracao` (4º módulo Wave A) — FECHADO 2026-05-31

Ritual P0→P9 completo. Planejamento fechado 2026-05-30: spec v2 → revisões consultor-rbc + tech-lead (APROVA COM CORREÇÕES) → plan + tasks (5 fatias, T-PROC-NNN). Decisões D-PROC-1..6 cravadas. Nenhuma ADR nova.

**Fatia 0** (`777169d`): extraiu `faixa_contida`+`avaliar_contencao`→`faixa_cobertura.py` compartilhado.

**Fatias 1a+1b** (`195e954`/`bbbc7a7`): domínio + schema + 5 migrations RLS v2/WORM + UNIQUE não-overlap INV-PROC-008 + porta `vigente_em` fail-closed + drill 12/12.

**Fatia 2** (`1d89bd3`/`ef89a35`): use cases cadastrar/revisar/publicar/revogar + REST + advisory lock `pg_advisory_xact_lock` + supersede + 48 testes M7 + hooks.

**Fatia 3 FECHADA (2026-05-31):** wire-in `CoberturaProcedimentoPort` no `configurar_calibracao`. Predicate STUB `procedimento_vigente_para` DEPRECADO. GATE-CAL-PROC-VIGENTE-PREDICATE FECHADO. INV-PROC-001..010 em REGRAS + 3 hooks.

**P9 FECHADO — M7 FECHADO (2026-05-31):** 6/6 PASS ZERO C/A/M (observabilidade CONCERNS BAIXO). 2 achados BAIXO resolvidos na causa-raiz.

---

## M8 `metrologia/certificados` (5º módulo Wave A) — FECHADO 2026-06-01

**Planejamento P0-P3 (2026-05-31):** spec escopada ao NÚCLEO METROLÓGICO da emissão. P0 `T-CER-000`. Revisões consultor-rbc + tech-lead = AMBAS APROVA COM CORREÇÕES. BLOQUEIO CRÍTICO (NC-01): `U(ponto)≥CMC(ponto)` exige incerteza POR PONTO → **ADR-0077** (orçamento por ponto retrofit M4). **ADR-0078** (tabela `certificados` achatada). Decisão Roldão: incerteza POR PONTO + média derivada.

**Frente SAN-INCERTEZA-PONTO (2026-05-31):** Fatias domínio + schema + use case + replay + drill. Motor GUM intacto. `cadeia_pontos_hash`+`replay_determinismo_hash_no_ponto`. GATE-CAL-DRILL-LOCAL drift consertado. ADR-0077 IMPLEMENTADA. Commits `8d05ac7`/`a26b409`/`81a90a5`/`1bed40c`/`6f60356`/`fab581b`.

**Implementação M8 (2026-05-31→2026-06-01):** `tasks.md` (60 tasks, workflow 6-leitores + 3 lentes adversariais). Fatias 0 + 1a + 1b + 1b-numeração + 2 + 2b. Bug latente pescado: `arredondamento_aplicado_regra` varchar(20)→(40) (REGRA_ID 27ch não cabia — só INSERT real detectou). ADR-0078 promovida proposta→aceito.

**Fatia 3 FECHADA (2026-06-01):** família INV-CER-* (16) + TestINV_CER_* + 3 hooks. GATE-CER-CGCRE-VIG-DATA-POPULAR aberto (popula no M9).

**P9 FECHADO — M8 FECHADO (2026-06-01):** 6 auditores. 3 PASS + 3 CONCERNS. Verificação adversarial: 1 achado real (OBS-2) de 5. TODOS resolvidos na causa-raiz. INV-RITUAL-001 satisfeito.

---

## M9 `metrologia/licencas-acreditacoes` (5º e ÚLTIMO do bloco metrologia) — FECHADO 2026-06-03

**Planejamento P0-P3 (2026-06-01):** P0 investigação `T-LIC-000`. Seam: `aplicar_evento_cgcre` + campos `Tenant.acreditacao_*` JÁ EXISTEM; falta entidade `Licenca` (FONTE rica). Tese: `Licenca`=fonte; `Tenant.acreditacao_vigencia_fim`=cache via `aplicar_evento_cgcre` → fecha GATE-CER-CGCRE-VIG-DATA-POPULAR. CRÍTICO confirmado regra #0: função não tinha param de vigência → Fatia 1c estende. **ADR-0079** (Licenca fonte rica + cache Tenant via SECURITY DEFINER).

**Fatia 1a** (`84a36f0`): domínio + 35 testes puros. **Fatia 1b** (`8eb7ecf`): 5 tabelas + 5 migrations. **Fatia 1c** (`bbf8b7c`): migration tenant/0012 estende `aplicar_evento_cgcre` + hook INV-LIC-VIG-SYNC-001 + 3 casos `_test-runner`.

**Fatia 2 (2026-06-02, `33336b4`):** mappers + repositories + query_service + 5 use cases + REST + drill 42/42 PG-real. ADR-0079 PROMOVIDA.

**Fatia 3 (2026-06-03, `cc20a23`):** wire-in renovação de acreditação CGCRE via porta. Job `verificar_alertas_licencas`. Teste não-drift `cache==fonte`. GATE-CER-CGCRE-VIG-DATA-POPULAR + GATE-LIC-DRIFT FECHADOS.

**Fatia 4 (2026-06-03, `5ac904b`):** endpoint `historico` + aptidão signatário (`verificar_signatario`). INV-LIC-001..005 + 3 hooks + retenção-matriz.

**P9 FECHADO — M9 FECHADO (2026-06-03):** 6/6 PASS ZERO C/A/M. INV-RITUAL-001 satisfeito. **BLOCO METROLOGIA COMPLETO (5/5).**

---

## Consolidação da base — COMPLETA 2026-06-05

Decisão Roldão 2026-06-03 (pós-bloco-metrologia): consolidar antes de avançar.

- **GATE-CAL-DRILL-LOCAL** — drill `validar_m4_calibracao` 56/56 PG real verde.
- **GATE-OS-VALIDAR-DRILL** — drill `validar_m3_os` 54/54 criado (`0a5f515`).
- **GATE-OS-GRANDEZA-EM-ATIVIDADE COMPLETO** — executor (configurar_calibracao) + signatário (emissão). Wire-in 2 portas só RBC. Commits `fbe34df`/`4b6da46`.
- **GATE-CAL-SEG ("10 ViewSets ACTION_MAP") FECHADO** — porta REST M4 ligada (`e765a13`/`a55ea94`/`3b8ef4c`). 3 predicates ABAC removidos do ViewSet (mascaravam o 422 de domínio — ADR-0073).
- **F-C2 Observabilidade — 4 fatias FECHADAS** (`e765bae`/`174fdc6`/`b886b20`/`ca26483`): logs estruturados structlog (OBS-002 fechado), health endpoints, graceful drain, métricas Prometheus GATE-OBS-METRIC-SCRAPE-1. GATE-DEP-003 (imagem base não-pinada) rastreado.

---

## Frente fiscal/NFS-e — FECHADA 2026-06-09

Escolha dependency-first: deadline externo DURO 01/09/2026 (CGSN 189/2026; ADR-0008). Destrava contas-receber + caixa-técnico + billing.

**P0** (`T-FIS-000`): greenfield. Seam pronto. **P1/P2/P3 FECHADOS (2026-06-08):** spec v2 + revisões 3 subagentes (3× APROVA COM CORREÇÕES, 26 achados) + plan + tasks (T-FIS-010..051, 5 fatias). Convergência: trava de perfil no use case (ADR-0073); fonte de verdade RBC = snapshot `Certificado.tipo_acreditacao` do M8 (INV-FIS-002). Decisão Roldão: terminologia perfil D = "calibracao".

**Fatia 1a** (`e9a01a5`): domínio puro `src/domain/fiscal/` — 32 testes puros.
**Fatia 1b** (`06c96cb`): schema PG + 5 migrations + drill 11/11.
**Fatia 2** (`668dd04`): use cases emitir/cancelar/consultar + REST + 12 E2E.
**Fatia 3 P7** (`d8a97b8`): INV-FIS-001..009 + TestINV_FIS + 3 hooks + 16 casos.
**P8** (`1e0c17d`): matriz-reconciliação + emenda ADR-0008 + emenda PRD.
**P9 FECHADO (2026-06-09):** 6/6 PASS ZERO C/A/M. Achados BAIXO resolvidos. GATEs pré-produção rastreados: PLUGNOTAS/FOCUS-REAL·B2-XML·SMOKE-TRIMESTRAL·CONTRATO·CIRCUIT-BREAKER·A3-OCSP·LGPD-FIS-DENYLIST-01·IDEMP-FIS-EMITIR-RACE.

---

## Plano de dependência do sistema (2026-06-09)

Auditoria 15 agentes resolveu 55 módulos em 11 níveis topológicos. Achado central: cadeia de preço INVERTIDA no faseamento v8 — consumidores (`orcamentos`/`contas-receber`) em Wave A, mas produtores (`configuracoes-sistema`/`produtos-pecas-servicos`/`precificacao`) em Wave B.

**Ordem cravada próximas frentes:** (1) `configuracoes-sistema` → (2) `produtos-pecas-servicos`+TabelaPreco → (3) `precificacao` (parcial, stub custo) → (4) `colaboradores` (base) → (5) `orcamentos`. Plano: `docs/faseamento/plano-dependencia-sistema.md`.

---

## Frente `configuracoes-sistema` — FECHADA 2026-06-11

**P0:** greenfield; correção regra #0 (dívida numeração fiscal NÃO existe — NFS-e numerada pelo BaaS). Frente é #1 pela via TRIBUTÁRIA.

**P1/P2/P3 FECHADOS:** spec v2 + revisões tech-lead (TL-01..09) + advogado (ADV-01..08) AMBOS APROVA COM CORREÇÕES. **ADR-0080** criada (numeração 2 regimes por tipo: gap-less para fatura/certificado; buracos-aceitos para os/orcamento). Emendas cross-doc aplicadas.

**Fatia 1a:** domínio puro — 17 testes puros. **Fatia 1b:** 5 tabelas + 6 migrations + drill 39/39 PG-real + 21 testes PG-real.

**Fatia 2 + 3 (P7) + P8 FECHADOS:** use cases + REST + INV-CFG-* + 2 hooks + matriz + ADR-0080 aceita.

**P9 FECHADO (2026-06-11):** 1ª passada 8 auditores (0C/0A/7M/~16B) → conserto causa-raiz 6 commits → 2ª passada 7 auditores **7/7 PASS ZERO C/A/M**. INV-RITUAL-001 satisfeito.

---

## Frente `produtos-pecas-servicos` + TabelaPreco — FECHADA 2026-06-11

**P0+P1+P2+P3 FECHADOS (2026-06-11):** dossiê + spec v2 + revisões tech-lead (TL-PPS-01..16) + advogado (ADV-PPS-01..09) AMBOS APROVA COM CORREÇÕES. **ADR-0081** proposta (duas fontes de preço lista×venda fail-closed). Decisões D-PPS-1..10 cravadas. GATE-PPS-WIREIN-OS bloqueante pré-1º tenant externo.

**Fatia 1a** (`0742529`): domínio — 16 testes puros. **Fatia 1b** (`8a8b0a2`): schema + 6 migrations + drill 29/29.

**Fatia 2:** use cases + REST + 30 puros + 16 E2E. **Fatia 3:** importação CSV em staging — 11 testes + drill 36/36.

**P7** (`f3807c6`): INV-PPS-* (9) + TestINV_PPS + 2 hooks. **P8** (`989dee5`): matriz + ADR-0081 promovida a aceito.

**P9 FECHADO (2026-06-11):** 1ª passada 8 auditores (0C/0A/9M/~20B) → conserto causa-raiz mesmo dia → 2ª passada 8/8 **PASS ZERO C/A/M**. Suíte PPS 105/105 + drill 36/36 + makemigrations limpo.

---

## Frente `precificacao` (parcial, stub custo) — P0+P1+P2 FECHADOS (2026-06-12)

**P0** (`T-PRC-000`, commit `0f511d4`): greenfield. Seams prontos (PPS porta `preco_para_os`+`PrecoResolvido`, Imposto/RegimeTributario, moldes de porta, WORM Padrão B). PRD draft US-PRC-001..008 + 7 agregados. Recorte Wave A parcial: preço-fixo + margem-alvo manual; `CustoProvider` STUB fail-closed; cost-plus + preço mínimo DIFERIDOS.

**Rodada batch Roldão (2026-06-12):** (1) preço = DOIS modos (componentes-checklist + fechado-com-aviso); (2) alçadas desconto 3 níveis 10%/20%/dono; (3) semáforo de margem (verde/amarelo/vermelho), números completos só pra papel `precificacao.ver_margem`.

**P1 FECHADO** (`e9f5799`): spec v1 recorte núcleo Wave A sobre PRD US-PRC-001..008.

**P2 FECHADO** (`88cd519`): revisões tech-lead (TL-PRC-01..18) + advogado (ADV-PRC-01..09) AMBOS APROVA COM CORREÇÕES (0C/10A/11M/4B). Spec v2 incorpora D-PRC-1..15, `CalculoPrecoResultado` autossuficiente pra replay, 12 INV-PRC candidatas, predicate ABAC `alcada_cobre`. Emendas cross-doc P2→P3 APLICADAS (`dcb8621`): retencao-matriz +4 linhas, lgpd-rat +RAT-PRC-DESCONTO, ADR-0081 emenda param `tabela_id` + fallback por item.

**PRÓXIMO: P3 — `plan.md` + `tasks.md` → implement → P7 → P8 → P9.**

---

## Auditoria de cerimônia do processo — APROVADA INTEGRAL (2026-06-12)

6 investigações paralelas rodaram. Relatório: `docs/faseamento/auditorias/AUDITORIA-CERIMONIA-rodada-1.md`. 22 recomendações R1..R22 em 4 pacotes: A hooks / B auditores / C docs+contexto / D conformidade→GATEs.

**Decisão Roldão (2026-06-12): APROVADO TUDO — os 4 pacotes integrais.** Aplicação: pacotes B/C/D primeiro (governança + docs + gates), pacote A (dispatcher de hooks + migração pré-commit) na sequência como frente técnica própria.

---

## SAN-PERFIL-TENANT — Sprints 5-6 pendentes (Wave A)

Sprints 1-4 FECHADOS (2026-05-27 noite). Sprint 5-6 = Wave A: templates certificado + onboarding UX + direitos-titular + export trimestral seguradora + sinistro export. Tasks em `docs/faseamento/SAN-PERFIL-TENANT/tasks.md`.

---

## Melhorias de processo aplicadas (auditoria máquina-dev 2026-05-29)

Fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco ATIVO (INV-RITUAL-003), contador automático (`scripts/status-projeto.sh`), guia de armadilhas (`docs/operacao/testes-armadilhas.md`). INV-RITUAL-001 (MÉDIO bloqueia) mantido por decisão do Roldão.

---

## Pendência de produto aberta

Terminologia B/C/D do M6: "Capacidade interna declarada (sem acreditação RBC)" — refinamento RBC da decisão do Roldão por cl. 8.1.3. Veto item-a-item do Roldão pendente.
