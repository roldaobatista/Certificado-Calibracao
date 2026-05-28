# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** **WAVE A ARRANCADA (2026-05-28 — autorização Roldão "pode").** 1º módulo = **M5 `metrologia/padroes`** (ADR-0040). Ritual: `/specify` ✅ (`spec.md`) → `/plan` ✅ v1 (`plan.md`) → **revisão 4 subagentes ✅** (`reviews-consolidado.md`). → **plan v2 `ready-for-tasks` (2026-05-28).** C-1..C-16 resolvidos: **ADR-0070** (Shewhart híbrido read-model+WORM `AnaliseCartaControle` + INV-PAD-010), **ADR-0071** (2º caminho=2 implementações mesmo mensurando + Welch-Satterthwaite; refines ADR-0025 v2), **ADR-0072** (path metrologia/* aninhado) — todas ✅ aceitas + no registro AGENTS §11. Drift C-6 corrigido (porta nova fail-closed). PRD §8 emendado (dado funcionário 5a/25a + PDF cert externo cifrado PII-terceiro). Estados v2: +`RECAL_RETORNADO_PENDENTE_APROVACAO`; flag `rastreabilidade_origem_revogada`. Deltas em `plan.md §14`. **`/tasks` ✅** (`tasks.md` — T-PAD-001..080). **`/implement` P1 ✅ COMPLETO (2026-05-28)** — domínio puro: enums + shewhart (5 regras WE Decimal, ADR-0070) + valor_convencional (2 impl + Welch-Satterthwaite, ADR-0071) + 7 snapshots + 6 Protocols + máquina de estados. **44 testes verdes**, ruff/mypy limpos. Commits `46fefed`/`14c271e`/`b3c40d2`. **`/implement` P2 ✅ COMPLETO (2026-05-28)** — schema infra (path aninhado ADR-0072 `src/infrastructure/metrologia/padroes/`): 6 models + 4 migrations (0001 initial + 0002 RLS pattern v2 + 0003 triggers WORM + 0004 grants app_user) aplicadas em PG real. **Decisão C-10/T-PAD-015: GUC `app.padrao_recal_em_curso`** (não read-model — entidade já modela `incertezas_certificado` no padrão; reset no checkout do pool em `connection.py`). Triggers: INV-PAD-006 (incertezas só via recal/GUC) + INV-SOFT-002 (sem DELETE físico) + WORM em recal(pós-retorno+aprovação RT one-shot)/VI/PT/AnaliseCartaControle. **11 testes PG-real verdes** (6 triggers caminho UNHAPPY + estrutura RLS/grants), ruff/mypy limpos, hooks 413 exit 0, django check limpo. **4 auditores pré-commit: seguranca PASS / qualidade PASS / llm-correctness CONCERNS→consertado (2 MÉDIO: docstring nao_conformidade_id + teste one-shot) / lgpd CONCERNS→consertado (matriz retenção M5).** GATEs BAIXO rastreados: INV-PAD-010 renomear teste quando entrar em REGRAS (P7); INV-PAD-002 CHECK não-vazio JSONB no use case cadastro (P3). **Próximo: P3 use cases** (`src/application/metrologia/padroes/`) → P4 porta fail-closed (GATE-PAD-PORTA-M4) → P5 ViewSet → P6 jobs → P7 INV+hooks → P8 drill → P9 10 auditores. Verificar com `--no-cov --reuse-db` (memória `feedback_test_db_nao_dropar_create_db`). Pré-Wave-A Ondas 1-4 fechadas; F-C2/F-C3 só bloqueiam deploy externo. Commits 2026-05-28: `89a56d5`/`be20192`/`9472d24`/`cb0c610` + docs.

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
- **F-C3 paginação DRF (4.11) ✅ FECHADA** (2026-05-28 commit `9472d24`): `PaginacaoPadrao` (page_size=50, max_page_size=200 anti-unbounded) em `src/infrastructure/comum/pagination.py` + `DEFAULT_PAGINATION_CLASS`/`PAGE_SIZE` em base.py. **Retrofit ZERO** — código já era defensivo (teste lista RT já tratava `count`). Auto-paginados: EquipamentoViewSet + ResponsavelTecnicoViewSet; OSViewSet.list já capava 1–200. 8 testes paginação + ~42 testes API/view verdes; auditor-qualidade PASS. **Achado infra:** extensões PG do test_afere vêm de `docker/postgres/init/*.sh` (só volume fresco) — não dropar/`--create-db` (memória `feedback_test_db_nao_dropar_create_db`). Pendente menor: hook anti-`pagination_class=None` (baixa prioridade — default global cobre).
- Retrofit Sprint 4 `perfil_no_evento` em `contas-receber` + `fiscal` ⛔ **NÃO construível** — módulos não existem (Wave A).
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` plugado nos 3 use cases M3 (1.5d, fecha ADR-0063 fail-open).

## Pendente Onda 5 (sem contratações externas)

F-C2 dev (structlog real + INV-LOG + endpoints health/ready/deep + SIGTERM + correlation_id contextvar) + drills internos estruturais. GATEs externos rastreados como `GATE-EXTERNO-PRODUCAO` em `docs/conformidade/comum/gates-externos-pre-producao.md` (a criar).

## Decisões Roldão 2026-05-27 noite

HTMX + 5 SPAs / Aferê PJ separada DEPOIS / Onda 3 com 4 agentes paralelos / **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`) / **resolver TUDO — críticos, altos, médios, baixos**.
