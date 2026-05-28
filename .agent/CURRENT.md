# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** Auditoria 10 lentes pré-Wave A em execução — **Ondas 1+2+3 FECHADAS; Onda 4 PARCIAL (T-CAL-124+126+127+128+132 ViewSets fechados; GATE-CAL-DOMAIN-MODEL-DRIFT RESOLVIDO 2026-05-28 commit `89a56d5` — destrava T-CAL-125+129; T-CAL-130+131+133 pendentes sem use cases); Onda 5 PENDENTE.** Commits 2026-05-27 noite (`27dd0d5`..`b7541e9`) + 2026-05-28 (`89a56d5`). Consolidado em `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`.

## Estado da suíte (2026-05-27 noite pós T-CAL-132)

- pytest M4 views REST (8 classes serializer): **39/39 PASS** em 5.5s.
- pytest M4 chave amplo: 144/144 PASS em 10s.
- pytest M3+M4 amplo (último full): 786 passed / 1 skip.
- Hooks `_test-runner.sh`: **413/413 PASS / 51 hooks ativos**.
- Drills PG real SAN-PERFIL: 17/17 migrations + 6/6 snapshots PASS.
- ruff/mypy: limpos nos arquivos novos (13 issues pré-existentes em migrations + models.py:1550 não tocados).

## Ondas executadas 2026-05-27 noite

- ✅ **Onda PRE-A.1** drift docs — 5 CRÍT + 5 ALTO + 14 MÉD resolvidos.
- ✅ **Onda PRE-A.2** ADRs — 37 ADRs processadas: 24 promovidas + 5 emendas perfil + ADR-0022 v2 + ADR-0025 v2 + ADR-0068 (sucessão RT, novo) + ADR-0069 (bypass cl. 6.2, novo) + ADR-0019 superseded-by 0028 + 3 reservadas (0059/0060/0061).
- ✅ **Onda PRE-A.3** PRDs — 16 PRDs Wave A draft→stable via 4 agentes paralelos. 6 FAIL L6 fechadas + 15 US novas + 20 INVs novas.
- 🟡 **Onda PRE-A.4** bus + TRACKs + F-C3 — INT-01 retrofit M3 OS + INT-02 retrofit M4 calibração (786 testes verdes) + INT-03 perfil_no_evento no envelope + INT-04 hook BLOCK + F-C3 supply-chain (dependabot.yml + pin SHA Dockerfile + 3 workflows).

## Pendente Onda 4 (~8-10d trabalho restante)

- T-CAL-124 ✅ **FECHADO** (commit `c66cf90`): LeituraViewSet (registrar-leitura + corrigir/rasura cl. 7.5) + 2 adapters Django + helper `derivar_user_id_hash` + 8 testes + **DRIFT FIX**: `calibracao/urls.py` plugado em `config/urls.py` raiz (CalibracaoViewSet T-CAL-123 estava órfã desde P5).
- T-CAL-126 ✅ **FECHADO** (commit `edc0960`): RevisaoViewSet (aprovar-revisao + rejeitar-revisao).
- T-CAL-127 ✅ **FECHADO** (commit `edc0960`): ConferenciaViewSet (aprovar-2a-conferencia + emissão evento bus `calibracao_aprovada` INT-02).
- T-CAL-128 ✅ **FECHADO** (commit `77238dc`): NaoConformidadeViewSet (abrir + fechar) + DjangoNaoConformidadeRepository. **GAP-NC-INTERMEDIATE-TRANSITIONS** Wave A: 3 transições intermediárias (definir-acao/executar/verificar-eficacia) não expostas via API; admin via shell até Wave A.
- T-CAL-132 ✅ **FECHADO** (commit `b7541e9`): ReclamacaoViewSet (abrir + atribuir-rt + responder) + DjangoReclamacaoCalibracaoRepository. **SEG-CAL-11 GATE Wave A M5**: `certificado_id` + `certificado_emitido_em` ainda aceitos no body; quando M5 plugar, fetch server-side de Certificado.
- **GATE-CAL-DOMAIN-MODEL-DRIFT ✅ RESOLVIDO** (2026-05-28 commit `89a56d5`): `ComponenteIncertezaSnapshot` ganhou proveniência §16.6 (tipo_origem/distribuicao/divisor/formula via 3 enums novos) + `AvaliacaoPeriodicaSubcontratadoSnapshot` ganhou os 4 campos cl. 6.6.2. Novo input `ComponenteParaCalculo` valida Tipo A (s_x + n>=6 = CHECK) e INV-CAL-INC-004; motor GUM permanece puro. Novo adapter `DjangoOrcamentoIncertezaRepository`. Guardião `tests/regressao/test_cal_domain_model_drift.py` introspecta `model._meta.fields` (pega regressão futura). ruff/mypy limpos; 714 passed/1 skip; auditor-qualidade + llm-correctness PASS.
- T-CAL-125 / T-CAL-129 ⏳ **DESTRAVADOS** — falta só a camada REST (serializer + view action + url) do `OrcamentoIncertezaViewSet` (calcular-incerteza + avaliar-conformidade) e `SubcontratacaoViewSet`. ViewSet REST + round-trip PG real da sentinela dof-infinito → **GATE-CAL-VIEWSETS-WAVE-A**.
- T-CAL-130 / T-CAL-131 / T-CAL-133 ⛔ **WAVE A — criação de módulos novos**: PadraoViewSet/Escopo/Proficiencia/AceiteRegraDecisao exigem criar os módulos `metrologia/padroes` + `escopos-cmc` + `procedimentos` (ADR-0040/0066 = Wave A). Use cases não existem. **Não iniciar sem autorização de arrancar Wave A.**
- **Limpa-mesa (4.10) ✅ FECHADA tão-quanto-possível-pré-Wave-A** (2026-05-28):
  - GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA ✅ **DONE** (commit `be20192`): validador `senha_breakglass.py` (≥14 + 4 categorias + dicionário + sequência + entropia + veto email/nome) + 9 testes + auditor-seguranca PASS.
  - GATE-FB-4 ✅ **já satisfeito** — vedação PII-por-valor já consta em `INV-AUTHZ-002` (REGRAS linha 351).
  - GATE-DEP-001/002 ✅ **já satisfeito** — Dockerfile FROM + workflows `uses:` já com pin SHA (Onda PRE-A.4 SUPPLY-1).
  - GATE-EQP-RT-AUTHZ ⛔ **BLOQUEADO Wave A** — exige perfil `gestor_qualidade` que não existe no seed authz (nasce no módulo qualidade Wave A; é perfil transversal usado por ADR-0026/0069).
  - GATE-EQP-DEP-WEASYPRINT-UPGRADE ⛔ **DEFER Wave A/DevOps** — upgrade 62→68 quebra pin `pydyf<0.11`; CVE-2025-68616 já mitigado in-app (custom url_fetcher).
- **F-C3 paginação DRF (4.11) — PRÓXIMO FOCADO (alto raio de impacto)**: paginação TOTALMENTE ausente (sem `DEFAULT_PAGINATION_CLASS`/`PAGE_SIZE`). Só 3 arquivos têm endpoint de lista (equipamentos/ordens_servico/responsavel_tecnico). Config global muda formato de resposta de todo list endpoint → retrofit de testes que checam formato. Fazer como unidade focada (settings + classe paginação + retrofit testes + hook + auditores).
- Retrofit Sprint 4 `perfil_no_evento` em `contas-receber` + `fiscal` ⛔ **NÃO construível** — módulos não existem (Wave A).
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` plugado nos 3 use cases M3 (1.5d, fecha ADR-0063 fail-open).

## Pendente Onda 5 (sem contratações externas)

F-C2 dev (structlog real + INV-LOG + endpoints health/ready/deep + SIGTERM + correlation_id contextvar) + drills internos estruturais. GATEs externos rastreados como `GATE-EXTERNO-PRODUCAO` em `docs/conformidade/comum/gates-externos-pre-producao.md` (a criar).

## Decisões Roldão 2026-05-27 noite

HTMX + 5 SPAs / Aferê PJ separada DEPOIS / Onda 3 com 4 agentes paralelos / **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`) / **resolver TUDO — críticos, altos, médios, baixos**.
