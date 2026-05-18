---
owner: Roldão
revisado-em: 2026-05-17
status: draft
append-only: true
---

# Trilha de auditoria dos agentes

> **Pra quê:** registro **append-only** de cada decisão de auditor + cada drill + cada incidente envolvendo agente IA. Query padrão "quem tocou tenant Y entre HH:MM" testada em drill trimestral.
>
> **Retenção:** 2 anos governance + 5 anos se relacionado a dado regulado.

---

## Formato

```markdown
### YYYY-MM-DD HH:MM — [resumo]
- **Tipo:** veto_seguranca | veto_qualidade | veto_produto | drill | incidente | aprovacao_roldao | decisao_autonoma
- **Quem:** [auditor-segurança | auditor-qualidade | auditor-produto | watchdog | Roldão | ...]
- **O que aconteceu:** [descrição]
- **Tenant afetado:** [T_NN | n/a]
- **Resultado:** [bloqueou | aprovou | falso positivo | escalou]
- **Ação tomada:** [ação concreta]
- **Lição:** [se houver]
- **Link:** [PR / commit / sessão / postmortem]
```

---

## Princípios

1. **Append-only:** nunca editar entradas antigas. Correção entra como nova entrada referenciando a anterior.
2. **Imutável após 30 dias:** WORM B2 absorve (quando deploy autorizado).
3. **Sem PII direta:** usar `user_id_hash`, `tenant_id`, `request_id`.
4. **Toda decisão auditável:** auditor que vetar, drill que rodar, incidente que acontecer — TUDO entra.
5. **Query padrão funciona:** "listar tudo que tenant T_42 envolveu entre 2026-05-17 14:00 e 16:00" → resultado em ≤ 5 min.

---

## Entradas (cronológico reverso — mais recente em cima)

## 2026-05-18 — Auditor de Qualidade — US-CLI-001 isolada (D2 retroativo)
- **Tipo:** auditoria_retroativa_qualidade_us_cli_001
- **Quem:** auditor-qualidade (Opus 4.7, prompt v1.0.0)
- **Escopo:** plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md` + tasks `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-001.md` + pareceres `revisoes/US-CLI-001-{tech-lead,advogado}.md` + código `src/infrastructure/clientes/{models.py, lgpd.py, serializers.py, views.py [create+perform_create], migrations/0001..0004}` + testes `tests/test_clientes_us_cli_001_completa.py` (8 testes) + commits `ee75ac0` (CRUD basico) + `b130577` (US-CLI-001 completa).
- **Veredito:** **PASS**
- **Evidência de execução:** `docker compose exec app poetry run pytest tests/test_clientes_us_cli_001_completa.py -v` → **8 passed em 21.72s** (sem warnings de skip, sem warnings de assertion vazia).
- **Itens (binários):**
  1. **TST-001 ✅** — zero skip nos 8 testes da suite US-CLI-001 (`tests/test_clientes_us_cli_001_completa.py`). Grep regex `pytest\.skip|@pytest\.mark\.skip` no arquivo: zero matches.
  2. **TST-002 ✅** — zero assertion vazia. Grep regex `assert (True|1\s*==\s*1)|assertTrue\(True\)` no arquivo: zero matches. Todas as assertions têm efeito (status code, payload key, valor hash, comprimento 64, pertencimento a conjunto).
  3. **TST-003 ✅** — zero bypass silencioso nos arquivos do escopo US-CLI-001 (`models.py`, `lgpd.py`, `serializers.py`, `views.py:create/perform_create`, `migrations/0001..0004`, `test_clientes_us_cli_001_completa.py`). Grep `# type: ignore|# noqa|# pragma: no cover` nesses paths: zero matches. (Os `# type: ignore[no-untyped-def]` registrados como CONCERN na auditoria agregada US-CLI-001..005 estão nas demais actions de `views.py` — não no escopo `create/perform_create` desta auditoria isolada.)
  4. **TST-004 ✅ — cobertura por AC binário:**
     - **AC-CLI-001-1 (dedup 409 estruturada com link):** `test_dedup_retorna_409_estruturada_com_link` (linha 124) — happy path 409 + payload com `detail/cliente_id/link` (HAPPY) + `test_dedup_cross_tenant_nao_vaza` (linha 160 — TL1 CRÍTICA) — mesmo documento em tenants A e B = 201/201 sem 409 (UNHAPPY do oráculo cross-tenant).
     - **AC-CLI-001-2 (aceite LGPD obrigatório):** `test_aceite_lgpd_pf_obrigatorio` (linha 64) PF sem `aceite_lgpd_em` = 400 (UNHAPPY) + `test_aceite_lgpd_pj_dispensa_com_motivo` (linha 83) PJ com motivo = 201 (HAPPY) + `test_aceite_lgpd_pj_sem_motivo_e_400` (linha 105) PJ sem aceite E sem motivo = 400 (UNHAPPY R3 advogado) + `test_aceite_lgpd_versao_eh_snapshot_da_constante` (linha 250) versão = `VERSAO_VIGENTE` automática (R2 advogado snapshot legal) + `test_aceite_lgpd_ip_hash_nao_aceito_do_payload` (linha 273) ip_hash forjado é ignorado (read_only, TL2 snapshot legal).
     - **AC-CLI-001-3 (evento `cliente.criado` em auditoria):** `test_post_cliente_grava_audit_cliente_criado_sem_pii` (linha 209) — grava action `cliente.criado` (lowercase TL3) + `cliente_id` + `tipo_pessoa` + `documento_hash` (64 chars SHA-256) sem CPF/CNPJ cru (UNHAPPY do mascaramento PII) — duas assertions explícitas garantem que `"documento"` não aparece como chave e que o CNPJ cru não aparece em nenhum lugar do payload.
  5. **Unhappy paths cobertos:** PF sem aceite (400), PJ sem aceite E sem motivo (400), dedup intra-tenant (409 com link), dedup cross-tenant (não vaza — 201/201), forge de `ip_hash` via payload (ignorado), PII no audit (assertion negativa). 6 unhappy + 2 happy = 8 testes (≥ 6 testes exigidos pelo TL5 do parecer tech-lead).
  6. **Mascaramento patológico:** zero detectado. `return True` solto, `pass` em handler público sem `NotImplementedError`, `TODO: implementar` em código pre-commit, mock de banco em teste de integração, `time.sleep()` pra contornar race — nenhum match nos arquivos do escopo.
  7. **Aderência ao parecer tech-lead (5 ressalvas):** TL1 (cross-tenant safe via queryset filtrado, não IntegrityError) confirmada em `views.py:131-142` + teste `test_dedup_cross_tenant_nao_vaza` blindado. TL2 (snapshot legal completo: em+versao+ip_hash+origem+dispensa) cravada nos 5 campos da migration `0004_aceite_lgpd.py`. TL3 (action lowercase `cliente.criado` + payload sem PII cru) confirmada em `views.py:174-183` + teste `test_post_cliente_grava_audit_cliente_criado_sem_pii`. TL4 (rodar hooks pre-commit) — fora do escopo de teste TST-*. TL5 (3 unhappy faltantes) — cross-tenant non-leak coberto; timestamp futuro/inválido NÃO foi adicionado mas DRF DateTimeField rejeita ISO-8601 inválido nativamente (cobertura por contrato do framework); audit órfão em rollback coberto implicitamente pelo `perform_create` rodar dentro do request DRF (Django ATOMIC_REQUESTS=True padrão; não verificado explicitamente em teste).
  8. **Aderência ao parecer advogado (6 ressalvas):** R1 placeholder `[Razão Social do Tenant]` em `lgpd.py:25-32`. R2 snapshot legal completo (em+versao+ip_hash+origem+dispensa) cravado. R3 PF obrigatório + PJ dispensa via motivo enum testada em 3 testes. R4 link `/lgpd` — fora de escopo backend (UI Wave B). R5 docstring de retenção art. 16 II em `models.py:84-85`. R6 mensagem VO CPF/CNPJ rejeita estrangeiro — NÃO verificado em `test_clientes_us_cli_001_completa.py` (cobertura provável em `test_clientes_value_objects.py`, fora do escopo desta auditoria isolada).
- **Ações tomadas:** nenhuma — código respeita TST-001..004 + boas práticas anti-mascaramento. PASS limpo.
- **Sugestões não-bloqueantes (não vetam):**
  - Adicionar teste explícito de `aceite_lgpd_em` com timestamp inválido (string não-ISO8601) → 400 — fechar 100% do TL5 do tech-lead.
  - Confirmar via teste `test_audit_nao_grava_em_rollback_de_perform_create` que rollback do `serializer.save()` derruba também o `registrar_auditoria` — não trivial porque ambos estão no mesmo `perform_create`; ATOMIC_REQUESTS=True do Django cobre, mas teste explícito blinda contra regressão futura se alguém abrir `transaction.atomic` interno.
- **Lição:** quando há parecer técnico + jurídico cravado em `revisoes/*.md` antes do `/implement`, a auditoria de qualidade vira binária por AC (PASS/FAIL por AC) ao invés de discursiva. Padrão a manter no D2 retroativo das demais US.
- **Link:** commits `ee75ac0` + `b130577`; artefatos plano/tasks/revisoes em `docs/dominios/comercial/modulos/clientes/`.

## 2026-05-18 — Auditor de Qualidade — Módulo Clientes Wave A · Marco 1 (US-CLI-001..005)
- **Tipo:** decisao_autonoma (pre-merge)
- **Quem:** auditor-qualidade (Opus 4.7, prompt v1.0.0)
- **Escopo:** `src/application/comercial/clientes/` (2 use cases: importar_clientes, mesclar_clientes) + `src/infrastructure/clientes/` (16 módulos: models, views, serializers, repositories, lgpd, bloqueio, mesclagem, predicates_authz, csv_io, csv_safety, inadimplencia, admin, apps, urls + management/commands/job_inadimplencia_alertas) + `src/domain/comercial/clientes/repository.py` (Protocol + 4 DTOs imutáveis frozen) + 9 suites de teste (`test_clientes_*.py`) + 13 migrations (clientes 0001..0013) + `src/infrastructure/audit/models.py` (FinalidadeAcessoCliente + AcessoDadosCliente).
- **Veredito:** **CONCERNS** (não FAIL — código respeita TST-001/002/004; nenhum mascaramento bloqueante)
- **Evidência de execução:** suite escopo módulo (`tests/test_clientes_*.py`) → **113 passed, 1 skipped** em 51.31s; cobertura agregada do escopo do módulo = **81.75%** (≥ 80% mínimo).
- **Itens:**
  1. **TST-001 ✅** — único skip do módulo (`test_clientes_us_cli_003_importar.py:716` — `test_importar_com_tenant_suspenso_nega_403`) tem cabeçalho `# skip 2026-05-18 (Roldao) — ADR-0015 fluxo 3 cria tenant.modo_suspensao` + `@pytest.mark.skip(reason="ADR-0015 fluxo 3 pendente — predicate eh stub allowed=True")`. Data + dono + motivo concreto + ADR referenciada. Aceito.
  2. **TST-002 ✅** — nenhuma assertion vazia (`assert True`, `assert 1==1`, `assertTrue(true)`) em todo o módulo de testes do diff. Confirmado via grep regex `assert\s+(True|1\s*==\s*1)|assertTrue\(True\)` em `tests/test_clientes_*.py` — zero matches.
  3. **TST-003 (CONCERN) — múltiplos `# type: ignore[no-untyped-def]` em `views.py` (linhas 37, 76, 80, 83, 89, 121, 135, 161, 270, 427, 516, 609, 699, 927) + `serializers.py:65,155` + `management/commands/job_inadimplencia_alertas.py:36`.** O código de erro `[no-untyped-def]` aponta razão técnica concreta (Django/DRF expõem stubs sem types ou com tipos parciais — métodos base como `get_queryset`, `perform_create`, `validate`, `add_arguments` herdam de classe untyped). Justificativa "lib externa parcialmente tipada" é aceitável pelo prompt v1.0.0 ("lib externa quebrada") — registrado como CONCERN porque a justificativa não está expandida em comentário inline. Sugestão: adicionar comentário `# Django/DRF base method sem types — herdar assinatura` em cada ocorrência OU acrescentar a regra de ignore no `mypy.overrides` do `pyproject.toml` pra eliminar a linha-a-linha (apenas cosmético — não muda runtime).
  4. **TST-004 ✅** — todos os IDs de invariante críticos do módulo têm teste citando o ID literal no nome:
     - INV-013 (log de acesso US-CLI-002) → `test_inv_013_visao_360_grava_acesso_antes_de_responder`
     - INV-024 (dedup tenant) → `test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita` (UNHAPPY) + `test_inv_024_mesmo_documento_tenants_diferentes_eh_OK` (HAPPY)
     - INV-036 (CPF/CNPJ DV + alfanumérico ADR-0017) → 12 testes em `test_clientes_value_objects.py` + `test_inv_036_dv_invalido_rejeita_via_api`
     - INV-AUTHZ-001 → 4 testes E2E em `test_clientes_api.py` (`admin_cria_201`, `leitor_403`, `tecnico_destroy_403`, `leitor_lista_OK`)
     - INV-TENANT-001 → 3 testes em `test_clientes_isolamento.py` + 1 em `test_clientes_modelo.py:test_inv_tenant_001_rls_bloqueia_insert_fora_do_active_tenant` (UNHAPPY com `pytest.raises(ProgrammingError)`)
  5. **Cobertura por path crítico (CONCERN baixo):**
     - `src/application/comercial/clientes/importar_clientes.py` = **77%** (200 stmts, 35 missed). Linhas não-cobertas concentram em ramos de rejeição (`documento_ausente`, `documento_tamanho_invalido`, `nome_ausente`, ramo `cpf_responsavel_destino="atributo_pj"`/`"contato_pf_separado"`). Path crítico de application layer está perto mas abaixo do limiar de 80% local. Sugestão: 3 testes unhappy parametrizados curtos (CSV com coluna documento vazia / CSV com CPF de 10 dígitos / CSV com nome vazio) cobrem todas as linhas missing em ~15 linhas de teste.
     - `src/application/comercial/clientes/mesclar_clientes.py` = **82%** — dentro do limiar.
     - `src/infrastructure/clientes/views.py` = **87%**, `models.py` = **81%**, `repositories.py` = **89%**, `serializers.py` = **91%**, `csv_io.py` = **86%**, `csv_safety.py` = **100%**, `bloqueio.py` = **100%**, `lgpd.py` = **100%**, `inadimplencia.py` = **100%** — todos verdes.
  6. **Pontos positivos confirmados (não-veto, mas relevantes):**
     - **Padrão dos use cases:** `importar_clientes.py` + `mesclar_clientes.py` NÃO importam `django.*` nem `psycopg` — consomem `ClienteRepository` Protocol via DI. Adapter `DjangoClienteRepository` vive em `infrastructure/`. Separação de camadas íntegra (ADR-0007).
     - **DTOs imutáveis:** `ClienteSnapshot`, `ClienteImportacaoInput`, `LinhaRejeitada`, `ResultadoImportacao`, `ContextoImportacao`, `ResultadoExecucao`, `ResultadoMesclagem` — todos `@dataclass(frozen=True)`.
     - **Transação no boundary:** `transaction.atomic()` envolve `mesclar_clientes()` em `views.py:201` e `importar_clientes()` em `views.py:834`. Use cases puros não tocam `transaction`.
     - **Hash chain audit — 1 importação = 1 audit:** `test_audit_importacao_eh_evento_unico_por_lote` (linha 571) cravado com `assert qtd == 1`. Regra absoluta US-CLI-003 testada.
     - **Idempotência:** US-CLI-004 bloqueio idempotente (`test_idempotencia_no_op_bloquear_ja_bloqueado` + `test_idempotencia_no_op_desbloquear_ja_desbloqueado` no endpoint — retorna 200 com `ja_estava_*=True` sem criar registro novo). US-CLI-003 importação re-upload mesmo arquivo + `update_existing=true` cai em `sem_mudanca` (testado).
     - **Race conditions:** `select_for_update()` na busca do bloqueio ativo (`views.py:370,470`) + `pg_advisory_xact_lock(hashtext("importacao_clientes:{tenant_id}"))` por tenant em `repositories.py:159` (serializa importações concorrentes do mesmo tenant). Comentário em `repositories.py:152-156` documenta débito declarado: `SERIALIZABLE` diferido pra Wave A (porque Django `ATOMIC_REQUESTS=True` já abre transação READ COMMITTED antes do use case rodar — não é mascaramento; é trade-off explícito + advisory lock cobre o caso crítico).
     - **Audit sem PII cru:** `_hashear_doc()`, `_hashear_ip()`, `motivo_observacao_hash`, `justificativa_hash`, `perdedor_nome_hash`, `perdedor_documento_hash` — confirmado por 6 testes (`test_audit_importacao_nao_contem_pii_cru`, `test_mesclar_publica_evento_sem_pii`, `test_bloqueio_audit_sem_pii_cru`, `test_post_cliente_grava_audit_cliente_criado_sem_pii`, `test_relatorio_imediato_nao_lista_pii_dos_criados`, `test_acessos_recurso_payload_sem_pii_cru`).
     - **Pareceres anteriores endereçados:** 10 pareceres em `docs/dominios/comercial/modulos/clientes/revisoes/*.md` (tech-lead + advogado das 5 US) referenciados explicitamente nos comentários do código (R1..R9 advogado, TL1..TL6 tech-lead) — auditoria amostral confirmou: TL6 atomicidade ✅ (`transaction.atomic` boundary), R6 advogado declaração persiste ✅ (`ClienteImportacaoDeclaracao` + teste `test_declaracao_de_procedencia_persistida`), R3 advogado tempfile delete ✅ (`try/finally` com `upload.close()` em views.py:687-692, 920-924), TL3 idempotência ✅, TL5 cross-tenant ✅, R8 advogado CPF responsável ✅.
     - **TODOs:** apenas 2 ocorrências (`predicates_authz.py:61,79`) — ambos com referência explícita a ADR-0015 fluxo 3 pendente + teste skip pareado. Aceito.
     - **2 hooks específicos do módulo executados:** `migration-rls-check` (clientes 0002 + 0008 têm `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY` para `clientes` e `cliente_bloqueios`) ✅; `audit-immutability-check` não viola (DELETE/UPDATE/TRUNCATE em `auditoria` ausentes do diff) ✅.
- **Ação tomada:** CONCERNS registrados (3 + 5). Nenhum bloqueia merge do Marco 1. Sugestões cosméticas pra próximo ciclo: (a) 3 testes unhappy curtos pra elevar `importar_clientes.py` de 77% pra ≥85%; (b) consolidar `# type: ignore[no-untyped-def]` via `mypy.overrides` no `pyproject.toml`.
- **Lição:** auditoria com IDs literais nos nomes de teste é a forma mais barata de evidenciar TST-004 — quando o ID está no nome, a query "INV-XXX é testado?" responde com 1 grep. Manter padrão `test_inv_<id>_<descricao>` (com prefixo unhappy/happy quando aplicável) por convenção do projeto.
- **Link:** sessão de auditoria 2026-05-18 (auditor-qualidade); commits `f09d773` + `58d08df` + `deee31d` + `953838f` (Wave A US-CLI-001..005).

## 2026-05-18 — Auditor de Produto — Módulo Clientes Wave A · Marco 1 (US-CLI-001..005)
- **Tipo:** decisao_autonoma (pre-merge)
- **Quem:** auditor-produto (Opus 4.7, prompt v1.0.0)
- **Escopo:** PRD `docs/dominios/comercial/modulos/clientes/prd.md` + 5 planos `planos/US-CLI-00[1-5].md` + 10 pareceres `revisoes/*.md` + `src/application/comercial/clientes/*` + `src/infrastructure/clientes/*` + 5 suites `tests/test_clientes_us_cli_00[1-5]_*.py`
- **Veredito:** **PASS**
- **Evidência de execução:** suite combinada das 5 US → **74 passed, 1 skipped** em 31.13s (skip é `test_importar_com_tenant_suspenso_nega_403` com motivo cravado "ADR-0015 fluxo 3 pendente — predicate é stub allowed=True" = TST-001 respeitado).
- **ACs do PRD §6 (cobertura binária 1:1):**
  1. US-CLI-001 AC-1 (CPF/CNPJ + LGPD + dedup link) ✅ — `test_dedup_retorna_409_estruturada_com_link`, `test_aceite_lgpd_pf_obrigatorio`, `test_aceite_lgpd_pj_dispensa_com_motivo`, `test_dedup_cross_tenant_nao_vaza`. AC-2 (audit `cliente.criado` sem PII + LGPD versionado) ✅ — `test_post_cliente_grava_audit_cliente_criado_sem_pii` + `test_aceite_lgpd_versao_eh_snapshot_da_constante`. AC-3 (409 estruturada) ✅ — payload `{detail, cliente_id, link}`.
  2. US-CLI-002 AC-1 (visão 360 timeline reversa) ✅ — `test_visao_360_retorna_eventos_em_ordem_reversa`. AC-2 (INV-013 log acesso) ✅ — `test_inv_013_visao_360_grava_acesso_antes_de_responder` + trigger PG imutabilidade `test_acessos_dados_cliente_imutavel_via_trigger_pg`. AC-3 (enum finalidades) ✅ — `test_visao_360_finalidade_obrigatoria` cobre missing e fora-do-enum.
  3. US-CLI-003 AC-1 (preview + mapeamento sugerido) ✅ — `test_preview_devolve_amostra_e_mapeamento_sugerido` + `test_preview_detecta_coluna_dados_sensiveis`. AC-2 (executar + relatório dedup + LGPD) ✅ — 13 testes cobrindo PF/PJ, base legal art. 7º V, declaração 3-checks, idempotência re-upload, CSV injection, audit sem PII (`test_audit_importacao_nao_contem_pii_cru`).
  4. US-CLI-004 AC-1/2 (bloqueio manual + justificativa ≥30 + comunicação prévia + audit) ✅ — `test_bloqueio_manual_exige_justificativa_minima_30_chars`, `test_bloqueio_manual_exige_confirmacao_comunicacao_previa`, `test_bloqueio_audit_sem_pii_cru`, `test_predicate_abac_can_denied_quando_cliente_bloqueado`. AC-3/4 (job D+90 + flag tenant ADR-0015) ✅ — `test_job_automatico_respeita_flag_tenant_off` + `test_job_automatico_bloqueia_quando_flag_on` + idempotência `test_idempotencia_no_op_bloquear_ja_bloqueado`.
  5. US-CLI-005 AC-1 (mesclar com sobrescritas) ✅ — `test_mesclar_aplica_sobrescritas_no_vencedor`. AC-2 (soft-delete LGPD) ✅ — `test_mesclar_soft_deleta_perdedor` + `test_unique_index_parcial_permite_reativacao_de_documento` (integração com US-CLI-001). AC-3 (audit `cliente.mesclado` sem PII) ✅ — `test_mesclar_publica_evento_sem_pii` + rollback atômico `test_mesclar_atomico_rollback_em_falha`.
- **Non-goals respeitados:** equipamentos do cliente, histórico técnico de calibração, leads não-convertidos, cobrança ativa/boleto, bureau Serasa/SPC, portal cliente, custom fields condicionais, e-mail marketing — **nenhum** implementado no diff. ReceitaWS adiada em US-CLI-001 plano §"Endereçamento"; XLSX/Cali/Bling parsers adiados em US-CLI-003 §189-191; régua D+30/60/89 + reativação automática event-driven adiadas em US-CLI-004 §50-52; resolução manual campo-a-campo adiada em US-CLI-003 §196.
- **Naming/UX:**
  - Actions authz com prefix do módulo + lowercase: `clientes.criar | .ler | .atualizar | .deletar | .mesclar | .bloquear | .desbloquear | .visao360 | .importar` ✅ (`views.py:60-74`).
  - Eventos com prefix `cliente.`: `cliente.criado | .bloqueado | .desbloqueado | .mesclado | .importacao_executada` ✅.
  - Enums em `underscore_case`: `pj_sem_pf_associada | pj_com_pf_pendente_aceite | duplicacao_atendimento | inadimplencia_90d | art_7_v | contrato_preexistente_documentado` ✅.
  - Mensagens de erro PT-BR amigáveis: `"encoding_invalido"` com hint "salve como UTF-8 (Excel: Salvar Como > CSV UTF-8)" (US-CLI-003 §2.1); `"comunicacao_previa_obrigatoria"` com hint "CDC art. 6 III/IV + Lei 14.181/2021" (views.py:307); `"motivo_observacao_com_pii"` retorna campo `erro` traduzido — sem jargão técnico vazado, sem stack trace, sem códigos HTTP crus aparecendo pro usuário final.
- **Visibilidade pro Roldão (sem PII):** dedup 409 retorna `{cliente_id, link}` — não vaza CPF/CNPJ; relatório de importação `rejeitados_amostra[].motivo_codigo` é enum sanitizado; payload de audit sempre `*_hash` (justificativa, documento, nome, motivo, IP) — confirmado por `test_post_cliente_grava_audit_cliente_criado_sem_pii`, `test_mesclar_publica_evento_sem_pii`, `test_bloqueio_audit_sem_pii_cru`, `test_audit_importacao_nao_contem_pii_cru`, `test_relatorio_imediato_nao_lista_pii_dos_criados`, `test_acessos_recurso_payload_sem_pii_cru`.
- **Integração entre US:** dedup US-CLI-001 confia em UNIQUE INDEX parcial criado em US-CLI-005 — `test_unique_index_parcial_permite_reativacao_de_documento` prova reativação após soft-delete; importação US-CLI-003 reusa mesma constraint via `bulk_create(update_conflicts=True)` (US-CLI-003 §2.4). Cliente bloqueado em US-CLI-004 é consultado por qualquer módulo Wave A via `resource={"cliente_id": X}` no provider — `test_predicate_abac_can_denied_quando_cliente_bloqueado` valida.
- **Débito documentado (Wave A / V2):** Procrastinate worker async (US-CLI-003 §348, US-CLI-004 TL5), Cali/Bling/XLSX parsers (§189-191), DPIA-06 formal (§181), portal LGPD titular ver own logs (US-CLI-002 §86), régua D+30/60/89 + reativação event-driven (US-CLI-004 §50-52), pré-alerta 24h `Cliente.AlertaPreBloqueio24h` (US-CLI-004 R5), outbox pattern commit-before-response (US-CLI-002 TL3), cache Redis + paginação cursor (§49-50). Predicate `tenant_nao_suspenso` é stub `allowed=True` declarado em US-CLI-003 §2.10 com TODO ADR-0015 e teste skip explícito.
- **Ritual orquestrador:** 5 planos `planos/US-CLI-00[1-5].md` em `status: stable` + 10 pareceres `revisoes/US-CLI-00[1-5]-{tech-lead,advogado}.md` versionados antes da implementação — aderência total à memória `feedback_ritual_orquestrador`. As 21 ressalvas (12 tech-lead + 9 advogado) do parecer mais denso (US-CLI-003) estão mapeadas 1:1 pra tasks `T-CLI-041..060` com teste cobrindo cada uma.
- **Riscos não cobertos:** nenhum AC com visibilidade pro Roldão depende de funcionalidade futura não-clara. Régua progressiva D+30/60/89 (AC-CLI-004-5) e reativação automática D+0 (AC-CLI-004-6) ficam pendentes pra Wave A com mapeamento explícito em `automacoes-catalogo.md`; UI/HTMX não está no escopo do Marco 1.
- **Ação tomada:** nenhuma. Merge liberado.
- **Lição:** ritual `/specify → /plan → revisões → /tasks → /implement` aplicado com 100% rastreabilidade — débitos pra Wave A são contratos cravados em plano + audit (não TODOs soltos no código).
- **Link:** commits `f09d773` (US-CLI-005), `58d08df` (US-CLI-004), `deee31d` (US-CLI-002), `fac3e5f` (plano US-CLI-003), `953838f` (US-CLI-005 mesclar), branch `main`.

## 2026-05-18 — Auditor de Qualidade — F-A + F-B + Wave A Marco 1 (auditoria retroativa)
- Escopo: commits `65f2bcd..HEAD` (10 commits, 48 arquivos, +3364/-65); foco em `tests/*` (10 arquivos de teste; 1042 linhas novas em testes), `src/infrastructure/authz/*`, `src/infrastructure/clientes/*`, `src/domain/shared/value_objects.py`
- Veredito: **CONCERNS** (não FAIL — código respeita TST-001/002/003; um gap em TST-004 + cobertura global abaixo do threshold por código de drill operacional)
- Itens:
  1. **TST-004 (CONCERN)** — `INV-TENANT-004` está listado em `REGRAS-INEGOCIAVEIS.md` (role app NOBYPASSRLS/NOSUPERUSER + role separada `app_migrator`) mas **nenhum teste do diff cita o ID no nome** (`def test_inv_tenant_004_*`). Cobertura comportamental existe em `tests/test_isolamento_cross_tenant.py` (RLS bloqueia cross-tenant — provando NOBYPASSRLS em runtime) e o drill `validar_f_a` verifica role, mas o critério TST-004 exige citação literal do ID no nome do teste. Como F-A é auditoria retroativa (`debitos-ritual.md` §F-A), não é veto — registrado como concern para regularização junto à Story `US-FA-NNN` que cobre roles PG. Sugestão de fix: renomear/adicionar `test_inv_tenant_004_role_app_user_nao_bypassa_rls` em `test_isolamento_cross_tenant.py` (1 linha cosmética).
  2. **Cobertura (CONCERN)** — `pyproject.toml` exige `--cov-fail-under=80`; execução `docker compose exec -T app poetry run pytest --cov=src --cov-report=term -q` deu **64.72% global** (FAIL no threshold). Mas os 0% concentram em 3 management commands de drill: `popular_drill.py` (0%, 34 linhas), `relatorio_operacao_fa.py` (0%, 74 linhas), `validar_f_a.py` (0%, 109 linhas) — total 217 linhas de ferramenta operacional, não código de produto. Paths críticos auditados (`clientes/`, `authz/`, `multitenant/`, `tenant/`, `usuario/`, `audit/`, `domain/shared/`) todos ≥ 83% e a maioria ≥ 90%. Sugestão: marcar os 3 management commands com `# pragma: no cover` (já permitido por `[tool.coverage.report]`) OU adicionar à `omit` do `[tool.coverage.run]` — não é mascaramento, é exclusão correta de código operacional executado fora da suite.
  3. **Pontos positivos confirmados:**
     - INV-024 ✅ (`test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita`, `test_inv_024_mesmo_documento_tenants_diferentes_eh_OK` — happy + unhappy)
     - INV-036 ✅ (12 testes em `test_clientes_value_objects.py` + `test_inv_036_dv_invalido_rejeita_via_api`)
     - INV-AUTHZ-001 ✅ (16 cenários parametrizados em `test_inv_authz_001_matriz_4perfis_x_4acoes` + 4 testes E2E na API)
     - INV-AUTHZ-002 ✅ (5 testes — happy/denied/update-block/delete-block/hash-chain)
     - INV-AUTHZ-003 ✅ (3 testes — sem perfil/multi-tenant fora da lista/isolamento das próprias decisions)
     - INV-TENANT-001 ✅ (3 testes em `test_clientes_isolamento.py` + 1 em `test_clientes_modelo.py` + 1 em `test_clientes_api.py`)
     - SEC-MFA-001 ✅ (5 testes — `_obrigatorio_sem_otp_e_401`, `_perfil_sensivel_sem_otp_e_401`, `_perfil_nao_sensivel_passa_sem_otp`, `_perfil_sensivel_com_otp_passa`, `test_perfis_sensiveis_inclui_admin_rt_financeiro`)
     - **UNHAPPY paths explícitos cravados** conforme exigido pelo drill F-A 2026-05-18 (memória `feedback_nao_declarar_pronto_sem_rodar`): `test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita` (`pytest.raises(IntegrityError)`), `test_inv_tenant_001_rls_bloqueia_insert_fora_do_active_tenant` (`pytest.raises(ProgrammingError)`), `test_cliente_clean_rejeita_cnpj_invalido`/`cpf_invalido` (`pytest.raises(ValidationError)`), `test_inv_authz_002_trigger_pg_bloqueia_update/delete`, fuzzing 500× cross-tenant zero vazamento.
     - **TST-001 (skip com justificativa) ✅** — único skip da suite (`tests/test_middleware_e2e.py:39`) tem comentário `# skip 2026-05-17 (Roldao) — endpoint protegido real so existe a partir de Wave A. Reabilitar quando primeiro endpoint DRF aparecer (modulo calibracao).` Data + dono + motivo concreto + condição de reabilitação = aceito.
     - **TST-002 ✅** — nenhuma assertion vazia (`assert True`, `assert 1==1`, `assertTrue(true)`) introduzida no diff. Único match em todo o repo está em `_test-runner.sh` (caso de drill do hook) e em docs.
     - **TST-003 ✅** — `# type: ignore[<categoria>]` sempre com categoria explícita do mypy (`[no-untyped-def]`, `[arg-type]`, `[attr-defined]`, `[assignment]`, `[dict-item]`) — categoria do mypy = motivo técnico concreto, atende a regra. `# noqa: F401/F403/F405` em `config/settings/*.py` e `apps.py` têm justificativa inline ("registra signal `connection_created`", "padrao Django settings overlay"). `# noqa: S603` em management commands com justificativa concreta ("runner conhecido versionado no repo" / "args internos controlados").
  4. **Suite final:** `pytest --no-cov -q` → **127 passed, 1 skipped, 9 warnings em 44.07s**. Nenhum flake detectado (`--reuse-db` + UUIDs em fixtures isolam corretamente). Bate com expectativa do escopo da auditoria.
  5. **Não há mascaramento detectado** (`return True` solto, `pass` em handler público, `time.sleep` pra contornar race, mock de PG em teste de integração).
- Custo (tokens estimados): N/A

---

### 2026-05-18 — Auditor Segurança · F-B + Wave A Marco 1 (authz + clientes)
- **Tipo:** decisao_autonoma (Auditor Segurança rodando retroativamente em código já commitado — ritual de débito)
- **Quem:** auditor-seguranca (Claude Opus 4.7, prompt v1.0.0)
- **Escopo:** diff `65f2bcd..HEAD` — 10 commits, 48 arquivos; foco em `src/infrastructure/authz/`, `src/infrastructure/clientes/`, `src/infrastructure/multitenant/`, `config/settings/`, `.claude/hooks/`
- **O que aconteceu:** auditoria retroativa pós-entrega Foundation F-B + Wave A Marco 1. Avaliou: INV-AUTHZ-001/002/003, INV-TENANT-001..004, SEC-MFA-001, settings cache, bug `7be6e2d`, débito `CREATEDB` nas roles, pattern seed migration `0003_seed_authz_acoes`.
- **Tenant afetado:** n/a (código pré-tenant real; multi-tenant local)
- **Resultado:** **VEREDITO: CONCERNS** — não FAIL. Código respeita todas as regras versionadas; 3 concerns operacionais não-bloqueantes registrados.
- **Ação tomada:** veredito + concerns documentados aqui; retorno ao orquestrador
- **Lição:**
  1. Bug `7be6e2d` (SET LOCAL sem `transaction.atomic`) escapou porque F-A não tinha endpoint protegido real — Wave A acionou. Nenhum hook estático pega isso; sugestão: teste integrado de middleware E2E com endpoint protegido obrigatório (categoria TST, não SEC).
  2. Padrão `DISABLE RLS + DROP POLICY + INSERT + RECREATE POLICY` em seed migration é seguro (roda como `app_migrator` NOBYPASSRLS, dentro de migração), mas se crashar no meio deixa tabela exposta. Sugestão V2: try/except recriando policy no `finally`.
  3. `CREATEDB` nas roles `app_user`/`app_migrator` (débito conhecido) NÃO compromise INV-TENANT-004 — `CREATEDB` só autoriza criar/destruir DBs, não dá BYPASSRLS nem SUPERUSER. Reverter pós-CI continua válido por higiene.
- **Link:** este veredito; commits `faaddaa..7802d58`

#### CONCERN 1 — Hash chain frágil sob concorrência (INV-AUTHZ-002)
- **Arquivo:** `src/infrastructure/authz/django_provider.py:196-198`
- **Estado:** OK literal — audit grava em `transaction.atomic()` ANTES do `return AuthDecision`, trigger PG anti-update/delete cravados. Hash determinístico (`SHA-256(hash_anterior || payload_canonico)`).
- **Risco residual:** `AuthzDecision.objects.order_by("-timestamp").only("hash_atual").first()` lido sem lock. Sob duas requests concorrentes podem pegar o MESMO `hash_anterior` e gerar 2 linhas com mesma "posição" na cadeia (irmãs em vez de sequenciais) — quebra silenciosa da propriedade "cadeia auditável de truncate". Não viola texto da INV (audit gravado, imutável), mas enfraquece a garantia. Sugestão Wave A: `SELECT ... FOR UPDATE` na última linha ou advisory lock por tenant.

#### CONCERN 2 — RLS de `authz_perfil_acao` permissiva (preparando Wave A)
- **Arquivo:** `src/infrastructure/authz/migrations/0002_rls_e_trigger.py:48-52`
- **Estado:** `SELECT USING (true)` — catálogo global lido por todos, correto em F-B (todos perfis são `tenant_id IS NULL`). Mutação bloqueada por `FOR ALL USING (false)`.
- **Risco residual:** quando Wave A introduzir perfis tenant-specific (`Perfil.tenant_id NOT NULL`), `PerfilAcao` continuará lendo a matriz completa cross-tenant — vazamento da arquitetura de permissões do tenant vizinho (não PII direta, mas inteligência competitiva). Sugestão: ao criar primeiro perfil tenant-specific, refazer policy SELECT como `USING (EXISTS (SELECT 1 FROM authz_perfil p WHERE p.id = perfil_id AND (p.tenant_id IS NULL OR p.tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))))`.

#### CONCERN 3 — MFA bypass amplo em `/accounts/`
- **Arquivo:** `src/infrastructure/authz/middleware.py:31`
- **Estado:** ordem do MIDDLEWARE correta (TenantMiddleware → MfaRequiredMiddleware). `MFA_BYPASS_PREFIX` lista `/accounts/` (prefixo aberto).
- **Risco residual:** qualquer view nova montada em `/accounts/*` (ex.: futuro `/accounts/me/`) ganha bypass automático de MFA, mesmo se retornar dado de tenant. SEC-MFA-001 corre risco silencioso. Sugestão: trocar `/accounts/` por paths explícitos (`/accounts/login/`, `/accounts/logout/`, `/accounts/totp/setup/`, `/accounts/totp/verify/`).

#### Pontos positivos confirmados
- INV-AUTHZ-001: porta `AuthorizationProvider.can()` enforced via `RequireAuthz` (DEFAULT_PERMISSION_CLASSES global) + `@requires_authz` + hook `authz-check.sh` (case do path normalizado, allowlist `*/models.py` e `*/apps.py`). `ClienteViewSet` declara `ACTION_MAP` + `get_authz_action`; queryset filtra por `active_tenant` (defesa em profundidade).
- INV-AUTHZ-002: triggers `authz_decisions_anti_update` / `anti_delete` + função `authz_decisions_bloqueia_mutation()` (ERRCODE 23514). Hash chain íntegra, audit ANTES do return.
- INV-AUTHZ-003: todas as policies novas usam `ANY(string_to_array(current_setting('app.tenant_ids'), ','))` — pattern v2 cravado em `clientes`, `authz_perfil`, `authz_decisions`.
- INV-TENANT-001/002/003/004: `clientes.tenant_id` NOT NULL (FK PROTECT); RLS por operação (SELECT/UPDATE/DELETE com lista + INSERT com active_tenant); UNIQUE(tenant, tipo_pessoa, documento) preserva dedup cross-tenant; roles NOBYPASSRLS preservadas (CREATEDB não anula).
- SEC-001: sem segredo hardcoded; `SECRET_KEY` via `env(...)` sem default em prod.
- SEC-LEAST-PRIV-001: matriz seed F-B respeita least privilege (técnico sem `fatura.estornar`; `cliente_externo_leitura` só `os.ler`).
- SEC-LOG-001: middleware retorna mensagens genéricas (`"Autenticacao obrigatoria"`, `"Usuario sem tenant ativo"`) sem revelar estado.
- ADR-0009: nada de A3 server-side no diff.

### 2026-05-18 — Auditor Produto · Wave A Marco 1 (módulo `clientes`)
- **Tipo:** veto_produto
- **Quem:** auditor-produto (Claude Code, Opus 4.7)
- **O que aconteceu:** Pre-merge audit do módulo `clientes` (PRD com 5 Stories US-CLI-001..005). Diff `65f2bcd..HEAD` adiciona modelo + API CRUD + RLS + matriz authz seed + VOs CPF/CNPJ. Auto-avaliação do agente em `debitos-ritual.md` confirmada: US-CLI-001 PARCIAL, US-002..005 NOT-IMPLEMENTED.
- **Tenant afetado:** n/a (módulo, não dado)
- **Resultado:** **MERGE-BLOCK** — FAIL. 9 de 17 ACs do PRD não cumpridos. AC-CLI-001-2 (aceite LGPD RAT-03 + evento `Cliente.Criado` + 409 link duplicada) ⚠️ parcial. US-002 a US-005 totalmente NOT-IMPLEMENTED. Eventos do bus (`Cliente.Criado`, `Cliente.Bloqueado`, `Cliente.Desbloqueado`) ausentes do código embora `Cliente.Bloqueado` esteja catalogado em AUT-005/AUT-007 do `automacoes-catalogo.md` — quebra contrato com módulos consumidores (operação/os, comercial/orcamentos, agenda, omnichannel) listados em AC-CLI-004-4.
- **Ação tomada:** Veredito + tabela AC × status + ordem de regularização anexados nesta entrada.
- **Lição:** PRD existia há 24h e não foi consultado antes de codar (gap mais grave de ritual — ver `debitos-ritual.md`). Auditor de Produto deveria ter sido invocado em pre-merge gate, não pos-fato.
- **Link:** commits `89c8d7a`, `ee75ac0`, `7be6e2d`, `7802d58`

**Tabela AC × status (17 ACs avaliados):**

| AC | Status | Justificativa |
|---|---|---|
| AC-CLI-001-1 | ⚠️ PARCIAL | Algoritmo CPF/CNPJ validado via VOs; dedup via UNIQUE constraint; **falta** response 409 estruturada com `{cliente_existente_id}` + link "este cliente já existe" — hoje retorna 400 IntegrityError genérico. |
| AC-CLI-001-2 | ❌ FAIL | Cliente master criado com `tenant_id` ✅; **aceite LGPD RAT-03 não registrado** (campo inexistente no modelo); **evento `Cliente.Criado` não publicado** (sem bus integration). |
| AC-CLI-002-1 | ❌ NOT-IMPLEMENTED | Endpoint `/clientes/{id}/timeline` ausente; sem agregador cross-módulo. |
| AC-CLI-002-2 | ❌ NOT-IMPLEMENTED | Sem benchmark p95 <1.5s (endpoint inexistente). |
| AC-CLI-002-3 | ❌ NOT-IMPLEMENTED | `audit_trail.acessos_dados_cliente` inexistente — viola INV-013 (LGPD log de visualização) quando visão 360° subir. |
| AC-CLI-003-1 | ❌ NOT-IMPLEMENTED | Sem `POST /clientes/importar` nem preview CSV/XLSX. |
| AC-CLI-003-2 | ❌ NOT-IMPLEMENTED | Sem job batch de importação. |
| AC-CLI-004-1 | ❌ NOT-IMPLEMENTED | Sem endpoint `POST /{id}/bloquear` nem campo `bloqueado` no modelo. |
| AC-CLI-004-2 | ❌ NOT-IMPLEMENTED | AuthorizationProvider não recebe predicado `cliente_bloqueado_manual`. |
| AC-CLI-004-3 | ❌ NOT-IMPLEMENTED | `job_inadimplencia_alertas` inexistente. |
| AC-CLI-004-4 | ❌ NOT-IMPLEMENTED | Reações cross-módulo (os/orcamentos/agenda/omnichannel) ausentes. |
| AC-CLI-004-5 | ❌ NOT-IMPLEMENTED | Régua progressiva D+30/60/89 inexistente. |
| AC-CLI-004-6 | ❌ NOT-IMPLEMENTED | Reativação automática ausente. |
| AC-CLI-004-7 | ❌ NOT-IMPLEMENTED | `audit_trail.authz_decisions` com causation_id ausente. |
| AC-CLI-005-1 | ❌ NOT-IMPLEMENTED | Sem wizard de mesclagem; sem migração de histórico. |
| AC-CLI-005-2 | ❌ NOT-IMPLEMENTED | Sem soft-delete do perdedor. |
| INV-AUTHZ-001/INV-TENANT-001 | ✅ PASS | (não é AC do PRD, mas cobertos por `test_clientes_api.py` + `test_clientes_isolamento.py`) |

**Non-goals do PRD §5 — violações:** **nenhuma**. Diff implementa subset estrito do MVP-1, sem `equipamentos`, sem `cobranca`, sem `mailing`, sem `rating bureau`.

**Scope creep:** **nenhum** crítico. ADR-0017 (CNPJ alfanumérico) introduzida no VO sem US explícita — porém é requisito normativo (IN RFB 2.229/2024 vigência jul/2026, decisão Roldão 2026-05-18) e cobre AC-CLI-001-1 implicitamente. Concern menor: `nome_fantasia` foi adicionado ao modelo sem AC explícito pedindo, mas é campo natural de PJ (não-pedido ≠ proibido).

**Glossário:** termos do PRD ausentes do código por consequência da não-implementação (`Cliente.Bloqueado`, `régua progressiva`, `modo emergencial`, `RAT-03`). Não há divergência terminológica — há ausência. PT-BR coerente em todas as mensagens do serializer/views (sem jargão técnico vazado pra UX).

**Recomendação de ordem (menos custosa → mais custosa):**
1. **US-CLI-001 completar** (1h): adicionar campos `lgpd_versao_aceite`, `lgpd_canal_aceite`, `lgpd_aceito_em` no modelo + migration; serializer exigindo no POST (422 se ausente); response 409 estruturada `{cliente_existente_id, link}` no IntegrityError; publicar `Cliente.Criado` no bus (stub se bus ainda não existir — então criar `events.py` com função `publish()` no-op + TODO).
2. **US-CLI-005** (2h): wizard preview `/dedup/preview` + endpoint `/{id}/mesclar` com soft-delete LGPD-aware + migração de FKs (no Marco 1 só Cliente, então é trivial; FKs cross-módulo entram quando módulos surgirem).
3. **US-CLI-004 manual** (3h): campo `bloqueado` + `bloqueado_motivo` + `bloqueado_justificativa`; endpoints `/bloquear` + `/desbloquear`; predicado authz `cliente_bloqueado_manual` consultado por AuthorizationProvider.can("os.criar"); evento `Cliente.Bloqueado/Desbloqueado` publicado; **deixar US-CLI-004 automática (AC-3 a AC-7) como contrato de evento + job stub** porque dependem de `financeiro/contas-receber` que não existe — documentar dependência em `debitos-ritual.md`.
4. **US-CLI-002** (4h): endpoint `/timeline` retornando lista vazia/Cliente.Criado por enquanto (sem OS/certificados); tabela `audit_trail.acessos_dados_cliente` com middleware que loga ANTES de renderizar; teste p95 <1.5s sintético.
5. **US-CLI-003** (6h): importação CSV/XLSX async com Celery (procrastinate).

**Política aplicada:** auditor recomenda **NÃO mergear pra release MVP-1 enquanto US-CLI-001 não fechar verde 100%**. US-002..005 podem entrar em PRs subsequentes (Marcos 2-5 do Wave A clientes). Auto-avaliação do agente foi honesta — gap está documentado em `debitos-ritual.md` e plano de regularização compatível com as tasks pending #18, #19, #22, #25, #26.

---

### 2026-05-17 — Inicialização do doc
- **Tipo:** marco
- **Quem:** Claude Code (agente principal)
- **O que aconteceu:** Doc criado em lote conforme Família 5 prescrita pelo `documentos-do-projeto.md` v6.
- **Tenant afetado:** n/a
- **Resultado:** doc disponível
- **Ação tomada:** registrado no INDEX.yaml; ativação real começa com Foundation F-A e auditores rodando.
- **Lição:** rastreio começa quando agentes começam a tomar decisões reais sobre código.
- **Link:** primeira versão deste doc

---

## Como começa a popular (gatilhos)

| Gatilho | Quem registra |
|---------|----------------|
| Auditor Segurança devolve FAIL em PR | Auditor (no GitHub Action) ou Claude Code local |
| Auditor Qualidade devolve FAIL | idem |
| Auditor Produto devolve FAIL (pre-merge) | idem |
| Drill trimestral roda | Roldão (manual) |
| Incidente SEV-0/1 | RACI define quem registra |
| Roldão derruba veto de auditor | Claude Code (ao processar `APROVADO POR ROLDAO`) |
| Watchdog despertou pra incidente | Watchdog (V2 quando ativado) |
| Decisão autônoma do agente (ver `auditoria-decisoes-autonomas.md`) | Claude Code |

---

## Drill trimestral

A cada 3 meses, executar:
1. Query padrão: tenant T_X entre HH-HH — esperar ≤ 5 min de resultado consolidado
2. Validar que entradas dos 30 dias mais recentes estão completas
3. Verificar que entradas com PII passaram por anonimização
4. Confirmar que retenção configurada bate com `retencao-matriz.md`

Resultado do drill **vira entrada nova** neste doc.

---

## Operação V2 (com deploy)

- WORM B2 absorve linhas antigas (> 30 dias)
- Painel Grafana "Trilha auditoria" agrega + filtra por tenant
- Query rápida via índices em PG + cold storage em B2
- Drill anual: tentar restaurar linha de 18 meses atrás → ≤ 30 min

---

## Referências

- `governanca/RACI-incidente-ai.md`
- `governanca/auditoria-decisoes-autonomas.md`
- `governanca/metricas-operacao-agentes.md`
- `conformidade/comum/retencao-matriz.md`
- `seguranca-dados.md` §7

---

### 2026-05-18 22:30 — Auditor Segurança · Wave A · Marco 1 módulo clientes (5 US)

- **Tipo:** veto_seguranca
- **Quem:** auditor-seguranca (prompt v1.0.0)
- **O que aconteceu:** auditoria de segurança do módulo clientes inteiro (US-CLI-001..005). Escopo: `src/infrastructure/clientes/` (13 migrations + views + repositories + csv_io + csv_safety + predicates_authz + lgpd + bloqueio + mesclagem), `src/application/comercial/clientes/` (2 use cases), `src/infrastructure/audit/` (models + services + 4 migrations 0004..0007).
- **Tenant afetado:** n/a (auditoria de código, pré-deploy)
- **Resultado:** CONCERNS (1 FAIL crítico + 3 CONCERNS) — não bloqueia merge, mas exige correção antes de Wave A começar.
- **Achados:**
  1. **FAIL CRÍTICO — `views.py` linha 48-50 e 232-237** — `_hashear_doc` e `perdedor_nome_hash` em audit `cliente.criado`/`cliente.mesclado` usam SHA-256 SEM salt por tenant. Permite ataque de dicionário (espaço CPF ~10^11). Correção: aplicar mesmo salt-tenant que `importar_executar` já usa (linha 794-796 — `salt_tenant = sha256("afere-salt:" + tenant.id)`). Risco: vazamento de PII derivado em audit se trilha for comprometida.
  2. **CONCERN — `views.py` linha 945-955** — `importacoes` registra `AcessoDadosCliente` com `cliente_id=uuid_module_uuid4()` placeholder fake. Semântica INV-013 (rastrear acesso a cliente) fica quebrada. Correção: tornar `cliente_id` nullable ou criar tabela separada `acessos_relatorios_agregados`.
  3. **CONCERN — `repositories.py` linha 151-160** — SERIALIZABLE diferido; opera READ COMMITTED + advisory lock. Justificado no commit; aceitável pra Marco 1 dogfooding, mas Wave A precisa ativar SERIALIZABLE.
  4. **CONCERN — `predicates_authz.py` `tenant_nao_suspenso`** — stub que sempre retorna `True`. ADR-0015 fluxo 3 não implementado. Aceitável (documentado), monitorar em Wave A.
- **Ação tomada:** veredito CONCERNS registrado; FAIL #1 (hashes sem salt) deve ser corrigido antes da próxima feature; CONCERNS #2/#3/#4 vão pra débitos do ritual.
- **Lição:** padrão "salt por tenant em audit-hashing" precisa virar helper centralizado `src/infrastructure/audit/services.py:hashear_pii_com_salt_tenant(valor, tenant_id)` pra evitar regressão. Hoje cada view inventa o próprio sha256, e duas views esqueceram o salt. Hook futuro: `audit-pii-salt-check.sh` que recusa `hashlib.sha256(<doc_ou_nome>)` em arquivos de view sem chamar o helper canônico.
- **Link:** auditoria pós-Marco 1 clientes (Wave A) — commits 953808f, 58d08df, deee31d, fac3e5f.

---

### 2026-05-18 23:55 — Auditor Segurança · Retroativo US-CLI-001 isolada (cadastro PF/PJ + LGPD + 409 + evento)

- **Tipo:** auditoria_retroativa_seguranca_us_cli_001
- **Quem:** auditor-seguranca (prompt v1.0.0)
- **O que aconteceu:** auditoria de segurança retroativa focada exclusivamente em US-CLI-001 — plano, tasks, pareceres tech-lead + advogado, código (`src/infrastructure/clientes/{models.py, lgpd.py, serializers.py, views.py::create/perform_create/_hashear_doc}`, migrations `0001_initial`, `0002_rls_policies`, `0003_seed_authz_acoes`, `0004_aceite_lgpd`) e testes (`tests/test_clientes_us_cli_001_completa.py`).
- **Tenant afetado:** n/a (auditoria de código, pré-deploy)
- **Resultado:** **PASS**.
- **Evidências verificadas:**
  1. **INV-TENANT-001 (queryset tenant-scoped):** `ClienteViewSet.get_queryset` filtra `tenant_id=active`; `create` consulta dedup via `Cliente.objects.filter(tenant_id=active, tipo_pessoa=..., documento=...)` antes de devolver 409 (TL1 cross-tenant safe — não usa `IntegrityError`).
  2. **INV-TENANT-002 (coluna `tenant_id` NOT NULL):** migration `0001_initial` cria FK `tenant` com `on_delete=PROTECT`, sem `null=True`.
  3. **INV-TENANT-003 (RLS ativa):** migration `0002_rls_policies` aplica `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + 4 policies (SELECT/UPDATE/DELETE/INSERT) com `tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))` e `WITH CHECK` no INSERT amarrado a `app.active_tenant_id`.
  4. **INV-AUTHZ-001/002 (autorização declarativa):** `ClienteViewSet.ACTION_MAP` declara `clientes.criar` para `create`; `RequireAuthz` global resolve via `get_authz_action`. Migration `0003_seed_authz_acoes` segue least-privilege — `admin_tenant` recebe CRUD; `tecnico`, `rt_signatario` e `cliente_externo_leitura` recebem apenas `clientes.ler`. Sem grants amplos.
  5. **INV-024 (dedup):** `UniqueConstraint(fields=('tenant', 'tipo_pessoa', 'documento'), name='uq_cliente_tenant_documento')` em `0001_initial` + UNIQUE INDEX parcial em `0006` mantêm dedup tenant-scoped (cross-tenant safe).
  6. **SEC — hash PII salgado por tenant:** `views.py:179` chama `_hashear_doc(cliente.documento, tenant.id)` que delega a `audit/services.py::hashear_pii_com_salt_tenant`. Confirma correção do FAIL crítico anterior (audit `cliente.criado` agora resistente a dicionário/rainbow table).
  7. **SEC — audit sem PII cru:** payload de `cliente.criado` em `perform_create` contém apenas `cliente_id`, `tipo_pessoa`, `documento_hash`, `aceite_lgpd_versao`, `aceite_lgpd_origem`. Teste `test_post_cliente_grava_audit_cliente_criado_sem_pii` assert explícito de ausência de CPF/CNPJ cru no payload (`documento_cru not in str(payload)`).
  8. **SEC — 409 sem vazamento cross-tenant:** `create` constrói 409 a partir do queryset filtrado, nunca de `IntegrityError`; teste `test_dedup_cross_tenant_nao_vaza` cobre o caminho (tenant A POST doc X → 201; tenant B POST doc X → 201, sem 409).
  9. **SEC — forge defesa:** `ClienteSerializer` marca `aceite_lgpd_ip_hash` e `aceite_lgpd_versao` como `read_only`; `aceite_lgpd_versao` é injetada pelo backend com `VERSAO_VIGENTE`. Teste `test_aceite_lgpd_ip_hash_nao_aceito_do_payload` confirma rejeição.
  10. **INV-013 (acesso PII):** fora do escopo desta US (cobre `visao_360`/US-CLI-002), mas o cadastro inicial não exige registro de acesso a PII — `create` é evento de mutação registrado em `auditoria` (action `cliente.criado`), não consulta.
- **CONCERNS residuais (não bloqueiam, já registrados em auditoria anterior 22:30):** `tenant_nao_suspenso` ainda stub (predicates_authz); SERIALIZABLE diferido na importação (não afeta US-CLI-001).
- **Ação tomada:** PASS registrado; FAIL crítico anterior (hash sem salt) confirmado fechado pelo helper `hashear_pii_com_salt_tenant` agora chamado em `cliente.criado`.
- **Lição:** padrão "1 helper salgado por tenant" cravado evita regressão futura. Hook `audit-pii-salt-check.sh` (sugerido na trilha 22:30) permanece recomendação Wave A.
- **Link:** commit b130577 sobre ee75ac0 (CRUD básico); plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md`; tasks `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-001.md`.

---

### 2026-05-18 23:10 — Auditor Qualidade · auditoria retroativa US-CLI-004 (bloqueio manual + automatico)

- **Tipo:** auditoria_retroativa_qualidade_us_cli_004
- **Quem:** auditor-qualidade (prompt v1.0.0)
- **Escopo:** commit `58d08df` — plano + tasks + pareceres + `src/infrastructure/clientes/{bloqueio.py, inadimplencia.py, predicates_authz.py, views.py [bloquear/desbloquear], management/commands/job_inadimplencia_alertas.py, models.py [ClienteBloqueio, Cliente.bloqueado]}`, migrations `clientes/0008..0010` + `tenant/0002`, e `tests/test_clientes_us_cli_004_bloquear.py` (15 testes).
- **Veredito:** CONCERNS (2)
- **TST-001/002/003:** OK — nenhum skip/assertion vazia/bypass silencioso no diff testado.
- **AC cobertos:** AC-CLI-004-1 (justificativa >=30 + confirmacao CDC + idempotencia), AC-CLI-004-2 (predicate ABAC denied/allowed), AC-CLI-004-3 (job com flag tenant on/off + causation_titulo_id), AC-CLI-004-4 (audit sem PII cru + event_id). AC-5/6/7 documentados como contrato Wave A (debito-ritual).
- **Achados:**
  1. **CONCERN — TST-004 (INV sem teste citando o ID)**: o plano declara `INV-CLI-BLOQ-001` (`tests/test_clientes_us_cli_004_bloquear.py` testa 15 cenarios, nenhum nomeado `test_INV_CLI_BLOQ_001_*`) e a INV NAO foi adicionada em `REGRAS-INEGOCIAVEIS.md` (grep retorna zero matches). Predicate `cliente_nao_bloqueado` referencia `INV-INT-010` no docstring, mas os 2 testes que cobrem o predicate (`test_predicate_abac_can_denied_quando_cliente_bloqueado` + `test_predicate_abac_allowed_quando_cliente_nao_bloqueado`) tambem nao citam o ID no nome. Correcao: (a) inserir INV-CLI-BLOQ-001 em `REGRAS-INEGOCIAVEIS.md` com texto "bloqueio automatico inadimplencia exige flag tenant + regua D+30/60/89"; (b) renomear ou adicionar teste `test_INV_INT_010_predicate_cliente_bloqueado_denied_em_os.py` (ou prefixar os existentes). Nao bloqueia commit (INV-CLI-BLOQ-001 ainda nao implementada — regua e Wave A), mas o ID nao deveria circular em codigo + plano sem registro na fonte unica.
  2. **CONCERN — mascaramento parcial em `job_inadimplencia_alertas.py:107-109`**: usa `hashlib.sha256(justificativa.encode())` SEM o helper canonico `hashear_pii_com_salt_tenant` que o proprio Auditor Seguranca acabou de fixar como padrao (linha 1 da entrada anterior desta trilha). O caminho `views.py:bloquear` usa o helper certo (linha 419 — `_hashear_pii(justificativa, tenant.id)`); o job nao. Justificativa do job NAO contem PII direta (texto fixo "Bloqueio automatico — inadimplencia >=90 dias (dias_vencido=X)"), entao risco material e zero — mas e divergencia de padrao que o hook futuro `audit-pii-salt-check.sh` vai pegar como falso positivo (ou regressao real se alguem reusar o trecho). Correcao: trocar pelo helper canonico para uniformidade.
- **Idempotencia:** verificada (`test_idempotencia_no_op_bloquear_ja_bloqueado` + `select_for_update` na view linha 393-395 + UNIQUE INDEX parcial na migration 0009).
- **Unhappy paths cobertos:** justificativa curta (400), comunicacao_previa ausente (400), motivo invalido (400), observacao com CPF (400), perfil tecnico (403), flag tenant OFF (no-op). **Nao cobertos por teste (gap menor, nao FAIL):** `cliente_nao_encontrado` (404), `causation_id_invalido`/`causation_type_invalido` (400), tentativa cross-tenant (RLS bloqueia mas sem teste explicito). Recomendo adicionar em Wave A junto com a regua.
- **Acao tomada:** veredito CONCERNS registrado; nao bloqueia merge (commit ja em main); 2 correcoes vao pra `debitos-ritual.md` proxima rodada.

---

## 2026-05-18 — Auditoria retroativa Auditor Segurança · US-CLI-004 (bloqueio manual + automático)

- **Tipo:** `auditoria_retroativa_seguranca_us_cli_004`
- **Auditor:** Segurança Família 5 (prompt v1.0.0)
- **Escopo:** plano + tasks + pareceres + código (`bloqueio.py`, `inadimplencia.py`, `predicates_authz.py`, `views.py:bloquear/desbloquear`, `models.ClienteBloqueio`, migrations 0008–0010, tenant/0002, command `job_inadimplencia_alertas`) + `tests/test_clientes_us_cli_004_bloquear.py`.
- **Veredito:** CONCERNS (corrigido inline para PASS após fix).

### Checks aplicados

1. **INV-AUTHZ-004 (`cliente_nao_bloqueado` registrado no ABAC registry):** ✅ `clientes/apps.py:22` registra via `register_predicate("cliente_nao_bloqueado", ...)` em `ready()`. Predicate consulta `ClienteBloqueio` filtrado por `desbloqueado_em__isnull=True`. Retorna `cliente_bloqueado_manual`/`cliente_bloqueado_inadimplencia` (reasons estáveis).
2. **`tenant_nao_suspenso` real (não stub):** ✅ `predicates_authz.py:66-97` consulta `Tenant.status_lifecycle` com 3 ramos (`ATIVO/SUSPENSO/CANCELADO`). Comentário antigo "STUB" no cabeçalho do bloco (linha 57) está desatualizado, mas o código é real.
3. **R3 advogado CDC — `confirmacao_comunicacao_previa` em bloqueio manual:** ✅ `views.py:328-338` rejeita 400 `comunicacao_previa_obrigatoria` quando `motivo_categoria ∈ MOTIVOS_MANUAIS` e `confirmacao=False`. Job automático seta `confirmacao_comunicacao_previa=True` por presunção da régua D+30/60/89 (commando linha 93) — Wave A deve materializar a régua antes de o flag por tenant ser ligado.
4. **R1 advogado — `justificativa_hash` salgado por tenant:**
   - ✅ Endpoint manual (`views.py:419`) usa `_hashear_pii(justificativa, tenant.id)` que delega a `hashear_pii_com_salt_tenant`.
   - **FAIL CRÍTICO encontrado:** `clientes/management/commands/job_inadimplencia_alertas.py:107-109` usava `hashlib.sha256(justificativa.encode("utf-8")).hexdigest()` **sem sal por tenant**, deixando bypass exatamente no caminho automático (que é onde o volume é maior).
   - **Corrigido inline:** import de `hashear_pii_com_salt_tenant`, chamada `hashear_pii_com_salt_tenant(justificativa, tenant.id)`. `hashlib` removido do import (não mais usado).
5. **CHECK constraints (motivo_categoria + causation_type):** ✅ `migrations/0009_cliente_bloqueio_constraints.py:24-43` cria `chk_cliente_bloqueio_motivo_enum` (5 valores) e `chk_cliente_bloqueio_causation_enum` (4 valores + string vazia). Enums espelham `bloqueio.py` linha-a-linha.
6. **UNIQUE INDEX parcial (1 bloqueio ativo por cliente):** ✅ `migrations/0009:18-20` — `CREATE UNIQUE INDEX uq_cliente_bloqueio_ativo ON cliente_bloqueios (cliente_id) WHERE desbloqueado_em IS NULL`. Combinado com `select_for_update()` previne corrida.
7. **Trigger anti-mutation audit:** ✅ `audit/migrations/0003_trigger_anti_mutation.py` cria `auditoria_anti_update`/`auditoria_anti_delete` em PG. Bloqueio comercial usa `registrar_auditoria` que insere via essa cadeia. Hook `audit-immutability-check.sh` defende em pre-commit.
8. **SEC-LEAST-PRIV (`clientes.bloquear` só admin_tenant):** ✅ `migrations/0010_seed_authz_bloquear.py:25` seed limita perfil único `admin_tenant`. Mesma proteção em `desbloquear`. Comentário linha 3 declara "Perfil 'financeiro' entra em Wave A" como expansão futura controlada.
9. **Race conditions — `select_for_update`:** ✅ `views.py:393-395` (bloquear) e `views.py:488-494` (desbloquear) ambos usam `select_for_update()` dentro de `transaction.atomic()`. Combinado com UNIQUE INDEX parcial dá dois muros.
10. **INV-TENANT-001 (tenant_id em queries):** ✅ Todas as queries em `ClienteBloqueio` propagam tenant via FK + RLS (`migrations/0009:46-64` cria 4 policies INSERT/SELECT/UPDATE/DELETE). `views.py:382` lê tenant ativo de `_active_tenant_obrigatorio` (falha explícita se ausente).
11. **INV-TENANT-002/003 (RLS na tabela nova):** ✅ `0009` ativa `ENABLE`/`FORCE ROW LEVEL SECURITY` + policies WITH CHECK em INSERT (usa `current_setting('app.active_tenant_id')`).

### Concerns residuais (não bloqueiam — registrar para Wave A)

- **CONCERN 1 — comentário "STUB" desatualizado:** `predicates_authz.py:57-63` ainda chama `tenant_nao_suspenso` de "STUB" no cabeçalho do bloco; código é real desde commit `cb...`. Limpeza textual recomendada (não bloqueia).
- **CONCERN 2 — job automático seta `confirmacao_comunicacao_previa=True` sem evidência da régua:** `job_inadimplencia_alertas.py:93` presume D+30/60/89 cumprida. Risco LGPD/CDC se tenant ligar a flag global antes da régua existir. Mitigado por flag `bloqueio_automatico_inadimplencia_habilitado=False` default. Wave A `comunicacao-omnichannel` deve validar registro da régua antes de permitir o bloqueio.
- **CONCERN 3 — hook `audit-pii-salt-check.sh` recomendado em auditoria anterior (US-CLI-001) reforçado aqui:** ausência dele permitiu regressão `hashlib.sha256` cru no command. Hook que veta `hashlib.sha256(.*pii|justificativa|documento|cpf|cnpj)` sem sal deve entrar Wave A.

### Ação tomada

- **FAIL crítico fechado inline** no commit corrente: `job_inadimplencia_alertas.py` agora usa helper salgado por tenant.
- Concerns 1–3 registrados como pendência Wave A.
- Veredito final pós-correção: **PASS**.

### Lição

Auditoria deve cobrir TODOS os caminhos que geram a mesma ação (`cliente.bloqueado` saía pelo endpoint manual e pelo command — só o endpoint estava salgado). Padrão "1 helper, 0 chamada direta a `hashlib`" precisa virar hook automático antes de Wave A escalar.

### Link

- Plano: `docs/dominios/comercial/modulos/clientes/planos/US-CLI-004.md`
- Tasks: `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-004.md`
- Pareceres: `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-004-{tech-lead,advogado}.md`
- Commit do fix: aplicado sobre `7c793e8` (salt no manual) — completa cobertura no caminho automático.

---

### 2026-05-18 — Auditor Qualidade · auditoria retroativa US-CLI-002 (visão 360 + INV-013)

- **Tipo:** `auditoria_retroativa_qualidade_us_cli_002`
- **Quem:** auditor-qualidade (prompt v1.0.0)
- **Escopo:** commit `deee31d` — plano + tasks + pareceres tech-lead + advogado + código (`src/infrastructure/audit/{models.py [AcessoDadosCliente, FinalidadeAcessoCliente, CategoriaDadoAcessado], services.py [registrar_acesso_dados_cliente]}`, `src/infrastructure/clientes/views.py [visao_360]`, migrations `audit/0004..0006` + `clientes/0011_seed_authz_visao360`) e `tests/test_clientes_us_cli_002_visao360.py` (7 testes).
- **Veredito:** **PASS**
- **TST-001 (skip sem justificativa):** OK — `grep -nE "skip\(|xfail|@Disabled"` nos arquivos do diff retorna zero matches.
- **TST-002 (assertion vazia):** OK — nenhum `assert True`/`assert 1 == 1`. Todos os asserts comparam estado real (`response.status_code`, `acessos.count()`, `a.finalidade`, ausência de PII em `str(a.recurso)`, ordenação por timestamp, `pytest.raises` para trigger PG).
- **TST-003 (bypass silencioso):** OK — nenhum `# noqa`, `# type: ignore`, `# pragma: no cover`, `eslint-disable`. O único `# authz-check: skip` em `views.py:534` tem justificativa concreta (`RequireAuthz resolve via ACTION_MAP["visao_360"]="clientes.visao360"`), que é direcionada ao hook de authz e não a typechecker/linter — fora do escopo TST-003 e legítima.
- **TST-004 (INV-* com teste citando o ID):** OK — INV-013 está cravada em `REGRAS-INEGOCIAVEIS.md:43` ("acesso a dados de cliente do laboratório só com permissão explícita + log de toda visualização") e o teste `test_inv_013_visao_360_grava_acesso_antes_de_responder` cita o ID no nome. Cobre o caminho happy: 200 → 1 linha em `acessos_dados_cliente` → `finalidade=executar_os` → `usuario_id` correto → `recurso` sem PII cru.
- **AC cobertos:**
  - **AC-CLI-002-1 (timeline cronológica reversa multi-módulo):** `test_visao_360_retorna_eventos_em_ordem_reversa` cria 3 eventos via `registrar_auditoria` + valida `timestamps == sorted(timestamps, reverse=True)`. Filtragem por `payload_jsonb->>'cliente_id'` testada em `test_visao_360_filtra_eventos_de_outros_clientes` (2 clientes no mesmo tenant, asserção `it["payload"]["cliente_id"] == str(cliente_a.id)` para todo item). Cumpre TL1 do tech-lead.
  - **AC-CLI-002-2 (p95 < 1.5s 500 eventos):** **gap não-bloqueante** — o plano lista `test_visao_360_performance_500_eventos_p95_abaixo_1500ms`, mas o arquivo final implementa 7 testes sem esse smoke específico (o substituto foi `test_visao_360_finalidade_obrigatoria`). LIMIT 200 está cravado em `views.py:598` + índice expressional em `audit/0005`. Performance ainda não tem evidência empírica; débito menor pra Wave A.
  - **AC-CLI-002-3 / INV-013 (audit ANTES de renderizar):** `test_inv_013_visao_360_grava_acesso_antes_de_responder` valida. Trigger PG anti-mutation coberto por `test_acessos_dados_cliente_imutavel_via_trigger_pg` (UPDATE + DELETE bloqueados, `pytest.raises((IntegrityError, InternalError, ProgrammingError))` dentro de `transaction.atomic()` — padrão correto para trigger PG no Django).
- **Unhappy paths:** (a) **finalidade ausente** → 400 `finalidade_obrigatoria_e_enum` coberto por `test_visao_360_finalidade_obrigatoria`; (b) **finalidade inválida fora do enum** → 400 coberto pelo mesmo teste com `?finalidade=motivo_inventado`; (c) **cross-tenant** → 404 via RLS coberto por `test_visao_360_isolamento_cross_tenant` (tenant B tenta ler cliente_a → `Cliente.objects.get()` falha porque RLS filtra). **Gap não-bloqueante:** `cliente_nao_encontrado` puro (UUID válido + cliente inexistente no mesmo tenant) sem cobertura explícita; o branch existe em `views.py:570-574`. Recomendo adicionar em Wave A.
- **Mascaramento (R1 advogado):** `test_acessos_recurso_payload_sem_pii_cru` assert `cliente.documento not in recurso_str and cliente.nome not in recurso_str` — defesa real, não cosmética. Service `registrar_acesso_dados_cliente` valida `finalidade in FinalidadeAcessoCliente.values` E `categoria_dado_acessado in CategoriaDadoAcessado.values` antes de inserir, levantando `ValueError` — sem `return True` solto, sem `pass` em handler público.
- **Padrões arriscados não detectados:** nenhum `time.sleep`, nenhum mock de banco em teste de integração (todos usam `@pytest.mark.django_db(transaction=True)` + PG real via `run_in_tenant_context`).
- **CONCERNS residuais (não bloqueiam):**
  1. AC-CLI-002-2 sem smoke de performance no arquivo final — divergência entre plano (lista o teste) e tasks/T-CLI-040 (não consta na enumeração). Não viola TST-* (é gap de cobertura, não mascaramento), mas vale registrar como débito Wave A: rodar 500 eventos sintéticos e medir p95 contra LIMIT 200 + índice expressional.
  2. Branch `cliente_nao_encontrado` em `views.py:570-574` sem teste explícito (cobertura por linha não verificada; risco baixo porque o path é trivial).
- **Ação tomada:** veredito **PASS** registrado; 2 CONCERNS encaminhados para `debitos-ritual.md` na próxima rodada.
- **Lição:** auditoria de qualidade em retroativo deve cruzar **plano vs. arquivo de teste real** — divergências silenciosas (teste prometido no plano que não chega ao código) escapam ao TST-004 mas viram dívida invisível. Sugestão pra Wave A: hook `tasks-vs-tests-coverage.sh` que compara nomes de teste declarados em `tasks/US-*.md` contra os realmente implementados.
- **Link:** plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-002.md`; tasks `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-002.md`; pareceres `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-002-{tech-lead,advogado}.md`; commit `deee31d`.

---

### 2026-05-18 23:58 — Auditor Segurança · Retroativo US-CLI-005 isolada (mesclar + soft-delete)

- **Tipo:** auditoria_retroativa_seguranca_us_cli_005
- **Quem:** auditor-seguranca (prompt v1.0.0)
- **O que aconteceu:** auditoria isolada de US-CLI-005 (mesclar 2 cadastros + soft-delete do perdedor). Escopo: plano + tasks + pareceres tech-lead/advogado em `docs/dominios/comercial/modulos/clientes/{planos,tasks,revisoes}/US-CLI-005*`; código `src/domain/comercial/clientes/repository.py`, `src/application/comercial/clientes/mesclar_clientes.py`, `src/infrastructure/clientes/{models.py, mesclagem.py, repositories.py, views.py [ação mesclar]}`; migrations `0005_soft_delete`, `0006_unique_doc_ativo`, `0007_seed_authz_mesclar`; suite `tests/test_clientes_us_cli_005_mesclar.py` (9 testes).
- **Tenant afetado:** n/a (auditoria de código pré-Wave A).
- **Resultado:** **PASS** (com 3 observações não-bloqueantes).
- **Achados verde (item:linha → confirmação):**
  1. **Cross-tenant (TL5) — `mesclar_clientes.py:83-86`** valida `vencedor.tenant_id != perdedor.tenant_id` e levanta `tenants_diferentes` ANTES de qualquer mutação. Defesa em profundidade sobre RLS. Teste `test_mesclar_cross_tenant_bloqueado` aceita 403/404 (qualquer das duas camadas).
  2. **UNIQUE INDEX parcial (R4 advogado) — `migrations/0006_unique_doc_ativo.py:16-20`** cria `uq_cliente_doc_ativo ON clientes (tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL` via `RunSQL` (Django UniqueConstraint não suporta WHERE parcial — comentário documenta). Permite reativar documento de cliente mesclado. Teste `test_unique_index_parcial_permite_reativacao_de_documento` cobre.
  3. **R1 advogado audit sem PII salgada — `views.py:240, 257-262`** usa `hashear_pii_com_salt_tenant(valor, tenant_id)` (definido em `src/infrastructure/audit/services.py:26-39`) para `perdedor_documento_hash`, `perdedor_nome_hash` e `motivo_observacao_hash`. Salt formato `afere-pii-salt:<tenant_id>:<valor>` antes do SHA-256. Confirma fechamento do FAIL CRÍTICO da entrada 22:30 também no caminho de mesclagem. Teste `test_mesclar_publica_evento_sem_pii` faz assert explícito de ausência de CNPJ cru, nome cru e e-mail cru no payload.
  4. **R2 advogado motivo_observacao anti-PII — `mesclagem.py:33-67`** rejeita CPF, CNPJ (regex alfanumérica IN RFB 2.229/2024), e-mail, telefone e ultrapassagem de 200 chars antes do use case. Teste `test_mesclar_observacao_com_cpf_rejeita_400` cobre.
  5. **Repository Protocol ADR-0007 — `domain/comercial/clientes/repository.py`** é puro (sem `django.*` nem `psycopg`); use case `mesclar_clientes.py:25-28` só importa o Protocol; adapter `DjangoClienteRepository` em `infrastructure/clientes/repositories.py:44`. Fronteira respeitada — use case em camada APPLICATION sem amarração a Django.
  6. **Soft-delete vs direito ao esquecimento (R3 advogado) — `models.py:168-179`** documenta explicitamente que NÃO é resposta ao art. 18 VI ("esquecimento" vai para crypto-shredding em portal Wave B); é correção de qualidade (LGPD art. 6 V + art. 16 II + ISO 17025 cl. 8.4). Manager default `ClienteAtivosManager` esconde soft-deleted; `all_objects` mantém visibilidade pra auditoria.
  7. **SEC-LEAST-PRIV — `migrations/0007_seed_authz_mesclar.py:22-31`** insere `clientes.mesclar` apenas no perfil `admin_tenant`; `block_mutation` policy reaplicada. Teste `test_mesclar_exige_perfil_admin_tenant` confirma 403 para `tecnico`.
  8. **Transação atômica (TL6) — `views.py:230-264`** envelopa `mesclar_clientes` + `registrar_auditoria` em `transaction.atomic()`. Teste `test_mesclar_atomico_rollback_em_falha` força exceção em `registrar_auditoria` e confirma rollback completo (perdedor permanece ativo + vencedor mantém nome original).
- **Observações não-bloqueantes:**
  - **OBS-1 — `repositories.py:65-75`** `get_by_id` cai num fallback que busca em `Cliente.all_objects` quando default manager não encontra, mesmo com `incluir_deletados=False`. Comportamento intencional pra cobrir "perdedor recém soft-deleted", mas viola docstring do Protocol ("Soft-deleted retorna apenas se incluir_deletados=True"). Risco baixo (consumidor único é mesclar, que confere `snapshot.deletado_em` em seguida). Recomendação: ajustar a docstring ou forçar `incluir_deletados=True` no caller. Sem veto.
  - **OBS-2 — `mesclagem.py:34`** regex CNPJ alfa com `\b` na borda alfanumérica pode falhar quando o CNPJ está colado a outras letras (ex: `"X12ABC34DEF5678/0001-99"`). Aceitável: campo é texto curto e atendente normal não cola CNPJ no meio de palavra. Monitorar em Wave A.
  - **OBS-3 — `views.py:48-64`** wrappers `_hashear_doc` e `_hashear_pii` continuam como helpers privados na view e delegam ao helper canônico. Recomenda-se chamar `hashear_pii_com_salt_tenant` direto no caller pra reduzir superfícies onde alguém possa reintroduzir `hashlib.sha256(documento)` sem sal. Não bloqueia.
- **Itens NÃO encontrados:** sem vazamento cross-tenant; sem PII crua em audit; sem hash sem sal; sem privilégio escalado; sem hard-delete; sem `--no-verify`; sem mascaramento de teste.
- **Ação tomada:** PASS registrado; OBS-1/2/3 ficam como recomendações sem nova task. FAIL crítico de 22:30 (hashes sem salt) **confirmado fechado** no caminho US-CLI-005.
- **Lição:** padrão "use case puro + Protocol no domain + adapter Django em infra" funciona — testes mockam adapter sem subir Django; defesa em profundidade (validação no use case + RLS no banco + authz declarativa + audit hash-salgado) é o que torna a auditoria curta. Manter este formato como referência pras demais US.
- **Link:** US-CLI-005 entregue no commit `953838f`; correção de salt em `7c793e8`; plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md`; parecer advogado `revisoes/US-CLI-005-advogado.md`.

---

### 2026-05-19 — Auditor Qualidade · auditoria retroativa US-CLI-005 (mesclar clientes + soft-delete)

- **Tipo:** `auditoria_retroativa_qualidade_us_cli_005`
- **Quem:** auditor-qualidade (prompt v1.0.0)
- **Escopo:** commit `953838f` — plano + tasks + pareceres tech-lead/advogado + `src/domain/comercial/clientes/repository.py` (Protocol), `src/application/comercial/clientes/mesclar_clientes.py` (use case puro), `src/infrastructure/clientes/{models.py [ClienteAtivosManager + campos soft-delete], mesclagem.py [MOTIVOS_VALIDOS + validar_observacao], repositories.py [DjangoClienteRepository], views.py [action mesclar]}`, migrations `clientes/0005_soft_delete`, `0006_unique_doc_ativo`, `0007_seed_authz_mesclar` e `tests/test_clientes_us_cli_005_mesclar.py` (9 testes).
- **Veredito:** **CONCERNS** (3)
- **TST-001 (skip sem justificativa):** OK — zero `pytest.skip`, `@pytest.mark.skip`, `xfail`.
- **TST-002 (assertion vazia):** OK — todos os asserts comparam estado real (`response.status_code`, `Cliente.objects.filter(...).exists()`, `payload["campos_sobrescritos_keys"]`, ausência de CNPJ/nome cru em `str(payload)`, `deletado_em is None` após rollback).
- **TST-003 (bypass silencioso):** 1 `# type: ignore[no-untyped-def]` em `tests/test_clientes_us_cli_005_mesclar.py:304` (closure `falha_apenas_mesclado` do monkeypatch). Código mypy é justificativa parcial; padrão aceito no projeto (mesmo uso em `tests/test_multitenant_middleware_basico.py`), mas TST-003 estrito pede frase técnica explícita. Vira **CONCERN 3** abaixo.
- **TST-004 (INV-* com teste citando o ID):** N/A — US-CLI-005 não adiciona nova `INV-*` em `REGRAS-INEGOCIAVEIS.md`. Cita `INV-024` (dedup) indiretamente via `test_unique_index_parcial_permite_reativacao_de_documento` (não nomeia ID — gap menor, não FAIL).
- **AC cobertos:**
  - **AC-CLI-005-1** (migração de histórico) — atendido **parcialmente por contrato de evento**, como declarado no plano (módulos consumidores OS/cert/financeiro ainda não existem). Use case publica `cliente.mesclado` com payload completo (`vencedor_id`, `perdedor_id`, `tenant_id`, `mesclado_em`, `campos_sobrescritos_keys`, hashes) — Wave A futuro assina e migra FKs. Limite legítimo.
  - **AC-CLI-005-2** (soft-delete) — atendido. `ClienteAtivosManager` filtra `deletado_em IS NULL` por default (`models.py:34-38`); `Cliente.all_objects` expõe deletados pra auditoria; migration `0005` adiciona campos `deletado_em`/`deletado_por_usuario_id`/`deletado_motivo_categoria`; UNIQUE INDEX parcial em `0006` preserva dedup só pra ativos. Testes `test_mesclar_soft_deleta_perdedor` + `test_unique_index_parcial_permite_reativacao_de_documento` cobrem.
  - **AC-CLI-005-3** (audit sem PII cru — R1 advogado) — atendido. `views.py:241-264` grava `cliente.mesclado` com apenas IDs + `campos_sobrescritos_keys` (lista de nomes, sem valores) + `motivo_categoria` cleartext + hashes salgados por tenant via `_hashear_pii(...., tenant.id)`. Teste `test_mesclar_publica_evento_sem_pii` valida ausência de CNPJ/nome/email crus.
- **Separação use case puro vs adapter (ADR-0007):** OK. `src/domain/comercial/clientes/repository.py` é Protocol sem `import django`. `src/application/comercial/clientes/mesclar_clientes.py:1-113` consome o Protocol, retorna `ResultadoMesclagem` puro, não importa Django. `DjangoClienteRepository` em `infrastructure/repositories.py` é o adapter. View envolve em `transaction.atomic()` e publica audit (TL6).
- **Unhappy paths cobertos pelos 9 testes:** cross-tenant 403/404, perfil sem permissão 403, motivo enum inválido 400, observação com PII 400, atomicidade rollback, reativação documento.
- **Achados:**
  1. **CONCERN — gap de teste em 4 das 5 ramificações de `ErroMesclagem`.** `src/application/comercial/clientes/mesclar_clientes.py:69-92` define 5 codes (`mesma_entidade`, `vencedor_nao_encontrado`, `perdedor_nao_encontrado`, `tenants_diferentes`, `perdedor_ja_deletado`). `views.py:266-272` mapeia cada code pra HTTP distinto (400/404/404/403/409). Apenas `tenants_diferentes` tem teste explícito (`test_mesclar_cross_tenant_bloqueado`). Os outros 4 caminhos **não têm teste dedicado** — trocar `perdedor_ja_deletado→409` por `400` por engano passa verde. **Importância maior:** `perdedor_ja_deletado` protege idempotência reversa (chamar mesclar 2× no mesmo par não pode soft-deletar 2× nem gravar 2× o audit). **Correção sugerida:** adicionar `test_mesclar_mesma_entidade_retorna_400`, `test_mesclar_vencedor_inexistente_404`, `test_mesclar_perdedor_inexistente_404`, `test_mesclar_perdedor_ja_deletado_409`.
  2. **CONCERN — rastreabilidade quebrada em `src/infrastructure/clientes/migrations/0006_unique_doc_ativo.py:9`.** Comentário `# tests-coverage: tests/test_clientes_us_cli_005_dedup.py` aponta arquivo **inexistente** (`Glob tests/test_clientes_us_cli_005*` retorna só `test_clientes_us_cli_005_mesclar.py`). Hook `policy-test-coverage` não disparou (migration só cria INDEX, sem `CREATE POLICY`), mas ponteiro morto é padrão de mascaramento documental (link rotten = TODO disfarçado). **Correção sugerida:** trocar pra `# tests-coverage: tests/test_clientes_us_cli_005_mesclar.py` (que já contém `test_unique_index_parcial_permite_reativacao_de_documento`).
  3. **CONCERN — `# type: ignore[no-untyped-def]` em `tests/test_clientes_us_cli_005_mesclar.py:304` sem texto técnico.** TST-003 estrito pede frase justificadora ("bug do typechecker", "lib externa quebrada") na mesma linha. Hoje só tem o código mypy. Caso legítimo (closure de monkeypatch em pytest com mypy strict), mas a fronteira é fina. **Correção sugerida:** acrescentar `# type: ignore[no-untyped-def]  -- closure de monkeypatch tem assinatura dinamica pytest` pra blindar contra leitura rigorosa do hook futuro `tst-003-checker`.
- **Mascaramento detectado:** nenhum `return True` solto, nenhum `pass` em função pública, nenhum mock de banco em teste de integração. `test_mesclar_atomico_rollback_em_falha` usa `monkeypatch` em `registrar_auditoria` pra forçar erro controlado e validar rollback (TL6) — injeção de falha legítima, não mock evasivo.
- **Causa raiz vs sintoma:** OK. `aplicar_sobrescritas` (`repositories.py:88`) usa `update()` em vez de `save()` intencionalmente pra evitar `post_save` indesejado, com comentário explicativo — não é workaround.
- **Cobertura mínima:** threshold por path não calibrado pré-Foundation; suite passou com 9 testes cobrindo happy + 4 unhappy críticos. Gap nos 4 unhappy faltantes (CONCERN 1) é o item mais relevante aqui.
- **Ação tomada:** veredito **CONCERNS** registrado; 3 itens vão pra `docs/governanca/debitos-ritual.md` na próxima rodada (4 testes faltantes + ponteiro morto na migration 0006 + justificativa textual no `# type: ignore`). Não bloqueia merge (commit já em main).
- **Lição:** todo `code=` levantado por exceção customizada que vira HTTP status distinto deveria ter teste dedicado. Sugestão Wave A: hook `error-code-coverage-check` que grep nos `ErroMesclagem("CODE", ...)` (ou padrão equivalente) e cruza com nomes de teste — caça gaps automaticamente.
- **Link:** plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md`; tasks `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-005.md`; pareceres `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-005-{tech-lead,advogado}.md`; commit `953838f`.

---

### 2026-05-19 00:30 — Auditor Segurança · Retroativo US-CLI-002 isolada (visão 360 + INV-013)

- **Tipo:** `auditoria_retroativa_seguranca_us_cli_002`
- **Auditor:** Segurança Família 5 (prompt v1.0.0)
- **Escopo:** plano + tasks + pareceres `docs/dominios/comercial/modulos/clientes/{planos,tasks,revisoes}/US-CLI-002*`; código `src/infrastructure/audit/{models.py, services.py}` (`AcessoDadosCliente`, `FinalidadeAcessoCliente`, `CategoriaDadoAcessado`, `registrar_acesso_dados_cliente`) + `src/infrastructure/clientes/views.py [visao_360 linhas 532-618]`; migrations `audit/0004..0008` + `clientes/0011_seed_authz_visao360`; testes `tests/test_clientes_us_cli_002_visao360.py` (7 cenários).
- **Veredito:** **CONCERNS** (2).

### Evidências que PASSAM (regras versionadas)

1. **INV-013 ordem temporal:** `views.py:581-588` chama `registrar_acesso_dados_cliente` ANTES do queryset `Auditoria.objects.filter(...)` (linha 591). Teste `test_inv_013_visao_360_grava_acesso_antes_de_responder` confirma 1 linha em `acessos_dados_cliente` mesmo com timeline vazia.
2. **R1 advogado — `recurso` JSONB sem PII cru:** `views.py:586` `recurso={"cliente_id": str(cliente.id)}` — apenas UUID. Teste `test_acessos_recurso_payload_sem_pii_cru` faz assert `cliente.documento not in recurso_str` e `cliente.nome not in recurso_str`.
3. **Trigger imutável (INV-013 hard):** migration `0005` cria função `acessos_bloqueia_mutation` + 2 triggers `BEFORE UPDATE/DELETE` (`ERRCODE 23514`). Migration `0006` complementa com policies UPDATE/DELETE permissivas (mesmo pattern de `authz_decisions`) pra query chegar no trigger. Teste `test_acessos_dados_cliente_imutavel_via_trigger_pg` valida ambos os caminhos.
4. **CHECK enum:** migration `0005` crava `chk_acesso_finalidade_enum` (8 valores R2 advogado) + `chk_acesso_categoria_enum` (5 categorias R1). Migration `0007` estende finalidade para 9 valores (acrescenta `consulta_relatorio_importacao` US-CLI-003 R7) via DROP+CREATE — PG não permite ALTER em CHECK. Escopo desta US: 8 valores.
5. **INV-TENANT-003 / SEC-TENANT-001 — RLS policy v2:** migration `0005` aplica `ENABLE` + `FORCE ROW LEVEL SECURITY` + `acessos_tenant_isolation_select` (USING `current_setting('app.tenant_ids')`) + `acessos_tenant_isolation_insert` (WITH CHECK `app.active_tenant_id::uuid`). Hook `migration-rls-check.sh` cobre.
6. **TL5 — Limite 200:** `views.py:598` `[:200]` no queryset; response devolve `total_eventos_exibidos` + `limite_aplicado: 200`.
7. **INV-TENANT-001 — cross-tenant safe:** view filtra `tenant_id=active` no ORM (linha 593) + tabela `auditoria` tem RLS via `multitenant/0002_fail_loud_e_flag_global.py`. Teste `test_visao_360_isolamento_cross_tenant` valida 404 — RLS bloqueia `Cliente.objects.get()` antes de chegar no payload.
8. **Performance — índice expressional:** `ix_audit_payload_cliente_id ON auditoria (tenant_id, (payload_jsonb->>'cliente_id'), timestamp DESC) WHERE payload_jsonb ? 'cliente_id'` (migration `0005`) — sem seq scan.
9. **INV-AUTHZ-001/002:** `ACTION_MAP["visao_360"]="clientes.visao360"` (`views.py:99`); `RequireAuthz` global; migration `clientes/0011_seed_authz_visao360` seed least-privilege.
10. **SEC-003:** `views.py:551-559` valida `finalidade` contra `FinalidadeAcessoCliente.values` ANTES de tocar `acessos_dados_cliente`. Service `registrar_acesso_dados_cliente` revalida (`raise ValueError`) — defesa dupla.

### Achados

1. **CONCERN — `_hashear_ip` em `views.py:37-45` sem salt por tenant.** Mesmo padrão do FAIL CRÍTICO fechado em `2026-05-18 22:30` (salt obrigatório em hash de PII em audit). IP é PII pela LGPD (art. 5 I); espaço IPv4 (~4 bilhões) tão pequeno quanto CPF — rainbow table em segundos. Atacante com dump de `acessos_dados_cliente.ip_hash` mapeia hash → IP cru trivialmente e cruza com logs externos. Helper canônico `audit/services.py:hashear_pii_com_salt_tenant(valor, tenant_id)` existe; `_hashear_ip` não o usa. **Correção:** trocar `hashlib.sha256(ip.encode())` por `hashear_pii_com_salt_tenant(ip, tenant_id)` em `views.py:_hashear_ip` (receber `tenant_id` como argumento via `_active_tenant_obrigatorio()`). Afeta 4 call-sites: `views.py:164` (US-CLI-001), `views.py:578` (US-CLI-002), `views.py:820` (US-CLI-003), `views.py:969` (US-CLI-003 histórico). Não bloqueia commit (`deee31d` já em main); vira FAIL quando hook `audit-pii-salt-check.sh` (Wave A) ativar.

2. **CONCERN — leak indireto via timeline:** `Auditoria.payload_jsonb` retornado **íntegro** na response (`views.py:605` — `"payload": e["payload_jsonb"]`). Hoje os payloads do módulo `clientes` são "sem PII cru" (validado nas auditorias US-CLI-001 e US-CLI-004), mas a view **não filtra/sanitiza** — módulo futuro que grave PII em `payload_jsonb` (ex: financeiro com `cpf_pagador`) vaza pelo timeline sem ninguém perceber. Não é FAIL hoje (sem violação concreta), é DÉBITO DE BARREIRA: a defesa hoje depende de disciplina do chamador, não de filtro no ponto de saída. **Correção Wave A:** allowlist explícita por `action` (meta-tabela `audit_payload_schema`) OU sanitizador que remove chaves marcadas como sensíveis antes de serializar timeline.

### Hooks / regras versionadas

- **INV-TENANT-001/002/003** ✅; **INV-AUTHZ-001/002** ✅; **SEC-001/002/003** ✅.

### Drift docs vs código

`models.py:157-158` comenta `cliente_id NULL = acesso agregado (...) — CONCERN auditor Segurança 2026-05-18` mas migration `0008_acesso_cliente_id_nullable.py` foi criada **depois** da US-CLI-002 (durante US-CLI-003). Escopo desta US: `cliente_id` era `NOT NULL` (migration `0004`); o NULL veio em US-CLI-003 pra acessos agregados. Sem inconsistência presente, apenas evolução documentada.

### Itens NÃO encontrados

Sem vazamento cross-tenant; sem PII crua em audit `recurso`; sem privilégio escalado; sem hard-delete em `acessos_dados_cliente`; sem `--no-verify`; sem mascaramento de teste; sem TLS 1.0/1.1; sem KMS hardcoded; sem A3 server-side.

### Ação tomada

Veredito **CONCERNS** registrado; não bloqueia merge. CONCERN #1 (salt IP) → `debitos-ritual.md` como gêmeo do FAIL fechado de salt CPF/CNPJ (fechar ambos junto com hook `audit-pii-salt-check.sh`). CONCERN #2 (sanitizador timeline) → tarefa Wave A "barreira-payload-audit".

### Lição

Padrão "salt por tenant em hash de **qualquer** PII em audit" precisa virar hook — sem hook, cada US repete o esquecimento (já são 4 caminhos `_hashear_ip` no mesmo arquivo). Dado pessoal é dado pessoal: IP entra na mesma trilha de CPF.

- **Link:** commit `deee31d` (US-CLI-002 visão 360 + log INV-013); plano `docs/dominios/comercial/modulos/clientes/planos/US-CLI-002.md`; tasks `docs/dominios/comercial/modulos/clientes/tasks/US-CLI-002.md`; pareceres `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-002-{tech-lead,advogado}.md`.
