---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
proximo-passo: ready-for-implement
diataxis: reference
audiencia: [agente, auditor]
frente: colaboradores
tipo: tasks
relacionados:
  - docs/faseamento/colaboradores/plan.md
  - docs/faseamento/colaboradores/spec.md
---

# Tasks — frente `colaboradores` (RH mínimo, base nível 2)

> T-COL-NNN. Fatias do `plan.md`. Cada fatia fecha com verificação real
> (regra "não declarar pronto sem rodar") antes da próxima. Refs: AC-COL-*
> (PRD), INV-COL-* (spec §5), D-COL-* (spec §3), TL/ADV-COL-* (reviews).

## Fatia 1a — domínio puro (`src/domain/rh_frota_qualidade/colaboradores/`)

- [ ] **T-COL-010** `enums.py` — `Vinculo` (CLT/PJ/ESTAGIARIO/SOCIO/TERCEIRIZADO),
      `Papel` (TECNICO/SIGNATARIO/ATENDENTE/GERENTE/DONO/QUALIDADE/MOTORISTA_UMC),
      `NivelHabilidade` (APRENDIZ/CAPACITADO/MESTRE), `TipoDocumento`
      (CTPS/CNH/CERTIFICADO_CURSO/OUTRO — **sem ASO**, R-COL-2). Ref: D-COL-4/5/6; glossário.
- [ ] **T-COL-011** `entities.py` — `Colaborador` (cpf VO, usuario_id?, vinculo,
      data_admissao, data_desligamento?, comissao_default_pct, ativo derivado, soft-delete
      campos), `Papel` (papel, data_inicio, data_fim?, revogado_em?, responsabilidade_tecnica_id?,
      pendencia_cnh), `Habilidade` (catalogo_id? XOR descricao_livre, nivel, evidencia_url?,
      data_avaliacao), `Documento` (tipo, storage_key, sha256, data_upload, data_validade?),
      `CatalogoHabilidade` (codigo, descricao, grandeza?). Frozen dataclasses; CPF imutável.
      NÃO reusar `JanelaVigencia` em Papel (TL-COL-09). Ref: spec §4; D-COL-2/3/4.
- [ ] **T-COL-012** `base_legal.py` — constante `BASE_LEGAL_POR_VINCULO_E_CATEGORIA`
      (CLT=art.7º II obrigação legal; PJ/TERCEIRIZADO=art.7º V contrato; ESTAGIARIO=Lei 11.788;
      categorias: identificacao/CTPS/CNH/foto/certificado) — fonte que o RAT do GATE fotografa.
      Ref: ADV-COL-01. **NÃO escrever RAT** (congelado).
- [ ] **T-COL-013** `regras.py` (domínio puro) — `pode_atribuir_signatario(usuario_id, rt_casa:bool,
      escopo_vigente:bool, perfil)` (usuario_id NOT NULL + rt casa + escopo; hard perfil A —
      INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO) · `validar_dono_unico` · `pendencia_cnh_motorista`
      (sem CNH → pendencia=true, SEM erro — R-COL-1) · `coerencia_documento_vinculo`
      (TERCEIRIZADO/PJ × CTPS → alerta) · `derivar_ativo` (data_desligamento) ·
      `cascade_revoga_papeis` · `montar_payload_desligamento` (v9: is_rt_signatario,
      tipos_servico_assinava, comissoes_pendentes_count=0 stub, chave idempotente). Ref: D-COL-10/11/13.
- [ ] **T-COL-014** `portas.py` — `ColaboradorReferenciadoPort` (Protocol: "colaborador é
      referenciado a jusante em OS/cert/comissão?") + stub **conservador** (assume sim → bloqueia
      hard-delete; fail-safe ADR-0066). Ref: D-COL-3/TL-COL-07; INV-COL-INATIVO.
- [ ] **T-COL-015** `erros.py` (`DuplicateCpf`, `SignatarioSemUsuario`, `SignatarioRtNaoCasa`,
      `SignatarioSemEscopo`, `CpfInvalido`, `ColaboradorInativo`, `DonoJaExiste`,
      `HardDeleteBloqueado`, `ComissaoForaDaFaixa`, `DocumentoIncompativelVinculo`) +
      `repository.py` (Protocols: ColaboradorRepository, PapelRepository, HabilidadeRepository,
      DocumentoRepository, CatalogoHabilidadeRepository) — tipos reais, zero `Any` de escape. Ref: spec §4.
- [ ] **T-COL-016** Testes puros (`tests/test_colaboradores_dominio.py`): signatário sem
      usuario_id → erro; RT não casa → erro; signatário OK perfil A; 2º DONO → `DonoJaExiste`;
      motorista sem CNH → pendencia=true (R-COL-1); terceirizado+CTPS → alerta vínculo;
      cascade revoga papéis; payload desligamento v9 completo; comissão fora 0..100 → erro;
      catalogo XOR livre. ruff/mypy limpos.

## Fatia 1b — schema PG (`src/infrastructure/colaboradores/`)

- [ ] **T-COL-020** `models.py` (5 tabelas colunas tipadas; `colaborador` com 2 managers —
      `ativos` filtra `data_desligamento IS NULL`, default filtra `deletado_em IS NULL`,
      `all_objects` expõe — TL-COL-04) + `apps.py` (`app_label=colaboradores`) + INSTALLED_APPS
      (`src.infrastructure.colaboradores`) + `urls.py` raiz (molde clientes/PPS). **Verificar
      conftest `_APP_MODULE_SUBPATH`** (provável N/A — infra flat). Ref: D-COL-1; spec §4.
- [ ] **T-COL-021** Migration 0001 CreateModel (5 tabelas) + UNIQUE parcial CPF
      `(tenant_id, cpf) WHERE deletado_em IS NULL` (INV-COL-CPF) + partial unique DONO
      `WHERE papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL` (INV-COL-DONO-UNICO) +
      CHECK `0 ≤ comissao_default_pct ≤ 100` (TL-COL-14) + CHECK `catalogo_id` XOR
      `descricao_livre` (D-COL-5) + `catalogo_habilidade` GLOBAL (sem tenant_id). Ref: spec §5.
- [ ] **T-COL-022** Migration 0002 RLS v2 FORCE + 4 policies nas 4 tabelas-tenant
      (`colaborador`/`_papel`/`_habilidade`/`_documento`). `catalogo_habilidade` é GLOBAL:
      **sem RLS por tenant** + isenção do migration-linter de tenant_id (risco 6). Ref: INV-TENANT-001/003.
- [ ] **T-COL-023** Migration 0003 trigger PG **defensivo BEFORE DELETE** no `colaborador`
      (bloqueia delete físico se houver papel/filha/evento — proteção mínima INV-COL-INATIVO,
      TL-COL-07) + (se tabela `*_eventos` própria for criada) trigger anti-mutation
      (INV-AUDIT-IMMUT-002). Ref: D-COL-3/14.
- [ ] **T-COL-024** Migration 0004 grants `app_user` (incl. SELECT global em
      `catalogo_habilidade`; INSERT em catalogo só via seed). Ref: plan §arquitetura.
- [ ] **T-COL-025** Migration 0005 seed authz `colaboradores.*` (`cadastrar`, `editar`,
      `desligar`, `ver`, `ver_pii`, `gerir_papel`, `gerir_habilidade`, `ver_comissao`,
      `ver_auditoria`, `consultar_elegiveis`) — molde `authz/0003`. Ref: spec §7.
- [ ] **T-COL-026** Migration 0006 seed `CatalogoHabilidade` GLOBAL literal (lista de grandezas:
      massa, volume, temperatura, dimensional, pressão, …) via `RunPython` molde **global**
      authz/0003 (NÃO per-tenant); idempotente; reverse. **Lista literal — sem import metrologia**
      (quebra aresta gap #4). Ref: D-COL-5/TL-COL-10.
- [ ] **T-COL-027** `mappers.py` + `repositories.py` Django (advisory lock troca DONO namespace
      `880_405` — confirmar livre; reuso do stub `ColaboradorReferenciadoPort`) + injeção
      `AnexoStorageLocal`. Ref: D-COL-4/TL-COL-11.
- [ ] **T-COL-028** Drill `validar_colaboradores` (5 tabelas/colunas/RLS/global/trigger/grants/
      seeds) + conftest `_SEED_MIGRATIONS` += seed authz + seed catalogo. Testes PG-real
      (`tests/test_colaboradores_schema_fatia1b.py`): RLS UNHAPPY cross-tenant ×4; UNIQUE CPF
      parcial (re-cadastro pós-soft-delete OK); partial unique DONO (2º DONO → IntegrityError);
      CHECK comissão; delete físico bloqueado por trigger; `catalogo_habilidade` legível por 2
      tenants distintos; seeds presentes. Verificar: migrate + makemigrations --check + drill PASS.

## Fatia 2 — use cases + REST (`src/application/rh_frota_qualidade/colaboradores/` + `infrastructure/.../views.py`)

- [ ] **T-COL-030** `application/.../cadastro.py` — `cadastrar_colaborador` (CPF VO + dedup →
      409; base legal por vínculo) + `editar_colaborador` (CPF imutável) + `desligar_colaborador`
      (data_desligamento + cascade revoga papéis + publica `Colaborador.Desligado` outbox MESMA
      transação — D-COL-10; idempotente por chave estável — TL-COL-13). Ref: AC-COL-01/06/06-2.
- [ ] **T-COL-031** `application/.../papeis.py` — `atribuir_papel` (SIGNATARIO: usuario_id NOT
      NULL + RT casa por usuario_id + escopo vigente, hard perfil A — INV-COL-SIGNATARIO-*;
      DONO: advisory lock + partial unique; MOTORISTA_UMC: pendencia_cnh — R-COL-1) +
      `revogar_papel` (revogado_em, não deleta). Ref: AC-COL-03; D-COL-4/11; TL-COL-01.
- [ ] **T-COL-032** `application/.../habilidades.py` — `registrar_habilidade` (catalogo XOR
      livre; nivel) + `application/.../documentos.py` — `anexar_documento` (`AnexoStoragePort` +
      SHA-256 server-side + EXIF strip foto sem blur — TL-COL-06; `coerencia_documento_vinculo`
      alerta — INV-COL-DOC-VINCULO). Ref: AC-COL-05; D-COL-5/6.
- [ ] **T-COL-033** `application/.../consultas.py` — `consultar_elegiveis` (DTO allowlist mínimo
      — INV-COL-ELEGIVEIS-MINIMO; filtra no banco; só ativos com papel+habilidade) +
      `comissao_vigente` (`{pct_default, vigente_desde}`). Ref: AC-COL-02/04/05; ADV-COL-04.
- [ ] **T-COL-034** `infrastructure/.../serializers.py` — choke-point ÚNICO
      `filtrar_visao_pii(papeis_solicitante, sujeito, dados)` (`MATRIZ_VISAO_PII[campo][papel]`
      + `proprio_colaborador`; CPF só DONO/últimos 2; e-mail/tel Dono/Gerente/próprio; CTPS/CNH
      Dono+próprio) em TODOS serializers + serializer `ElegivelDTO` allowlist separado. Ref:
      D-COL-7; INV-COL-PII-MASCARA/-ELEGIVEIS-MINIMO.
- [ ] **T-COL-035** `infrastructure/.../views.py` — `ColaboradorViewSet` (list prefetch +
      filtros + busca `q` com guard-CPF — ADV-COL-08 / create / retrieve / partial_update /
      destroy=desligamento / `papeis` / `habilidades` / `documentos` / `auditoria` /
      `elegiveis` / `comissao-vigente`). ACTION_MAP `colaboradores.*` + Idempotency-Key em
      escrita (leitura/`elegiveis`/`comissao-vigente` SEM) + `_falha` log SEM PII em claro
      (INV-COL-PII-LOG). `prefetch_related` (anti-N+1 — TL-COL-12). Ref: spec §7.
- [ ] **T-COL-036** Eventos `Colaborador.*` em `acoes_canonicas` (**outbox=True** — D-COL-10):
      Cadastrado/PapelAtribuido/PapelRevogado/HabilidadeAtualizada/Desligado — payload
      hashificado POR EVENTO (spec §6: `cpf_hash`/`nome_hash`/`ator_id_hash`/`motivo_hash`;
      refs em claro). Reusar helper hash canônico (M5/M9/PPS/PRC). Ref: D-COL-8; INV-COL-PII-LOG.
- [ ] **T-COL-037** Testes: puros com Fakes (cadastrar/desligar/atribuir papel) + E2E PG-real:
      dedup CPF → 409; signatário UNHAPPY identidade ×3 (sem usuario / RT inexistente / RT de
      outro); mascaramento por papel × campo (Gerente não vê CPF; próprio vê próprio CPF;
      sem papel → tudo mascarado); `/elegiveis` nunca retorna PII fora da allowlist; desligar →
      1 linha `bus_outbox` payload v9 (TL-COL-02); idempotência desligar 2x → 1 evento;
      guard busca-CPF (não-Dono busca CPF → vazio); `assertNumQueries` list/elegiveis (sem N+1).

## Fatia 3 (P7) — INVs + hooks + testes nomeados

- [ ] **T-COL-050** Família `INV-COL-*` em REGRAS-INEGOCIAVEIS.md (nova seção `## INV-COL-*`,
      molde seção INV-PRC): CPF, SIGNATARIO-IDENTIDADE, SIGNATARIO-ESCOPO, DONO-UNICO, INATIVO,
      DESLIGAMENTO-CASCADE, PII-MASCARA, ELEGIVEIS-MINIMO, DOC-VINCULO, PII-LOG, COMISSAO-AUDIT +
      INV-TENANT/001/016 herdadas — colunas enforcement/origem/perfil/efeito. Ref: spec §5.
- [ ] **T-COL-051** `TestINV_COL_*` nomeadas (TST-004; PG-real onde é banco: CPF/DONO-UNICO/
      INATIVO; puro onde é domínio: SIGNATARIO-*/DOC-VINCULO/DESLIGAMENTO-CASCADE; E2E onde é
      serializer/log: PII-MASCARA/ELEGIVEIS-MINIMO/PII-LOG). Ref: T-COL-050.
- [ ] **T-COL-052** Hooks novos no `.claude/hooks/pre-commit-manifest.tsv` (ritual R5 —
      pré-commit, NÃO write-time): `col-pii-mascara-check` (`/colaboradores/.*serializers\.py$`),
      `col-evento-pii-hash-check` (`/colaboradores/.*\.py$` — denylist PEPH/PPS),
      `col-hard-delete-check` (`/colaboradores/.*(views|repositories)\.py$`) + scripts em
      `.claude/hooks/` + casos no `_test-runner.sh` + evento `Colaborador.Anonimizado` no
      catálogo (A5) + contagens via `scripts/status-projeto.sh --check` (NUNCA em prosa).
      Verificar: `bash .claude/hooks/_test-runner.sh` verde. Ref: spec §5; ADV-COL-04/06.

## P8/P9 — fechamento

- [ ] **T-COL-060** Emendas cross-doc REAIS: `faseamento-modulos.md` (colaboradores Wave B→A
      nível 2 + nota seed literal — A9) · `api.md`/`ui.md` (remover 422 MOTORISTA + ASO —
      R-COL-1/2) · `exports.md` (CPF últimos 2 + ASO fora E-COL-04) · `matriz-feature-perfil.md`
      (SIGNATARIO por perfil — A8) · nota no `plano-dependencia-sistema` (CatalogoHabilidade em
      colaboradores, não configuracoes-sistema) + matriz-reconciliacao.md ENXUTA (R20: §1 AC/INV↔
      código, §2 INV↔teste, §8 ata P9) + registro GATE-COL-* (STATUS-GERADO + AGENTS §12) + GATEs
      LGPD congelados rastreados (A3/A4/A6/A7) + frontmatters Família 0 draft→stable (lote R22).
      Verificar: `status-projeto.sh --check`. Ref: plan P8.
- [ ] **T-COL-061** P9 auditores roteados (INV-RITUAL-003): 6 essenciais (qualidade·segurança·
      llm·idempotência·**conformidade-lgpd OBRIGATÓRIO**·produto) + performance (list/elegiveis) +
      observabilidade (PII em log + tenant_id/correlation_id); supplychain SÓ se dep nova; drift-docs
      FORA (R7). Verificação adversarial de TODO MÉDIO+ antes do mutirão (R6); 2ª passada escopada
      (R5). Conserto causa-raiz → re-passada → zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md.
      BAIXOs em lote pós-fechamento (R10).
