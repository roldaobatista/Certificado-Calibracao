---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-003
versao: 2
historico:
  - 2026-05-18 v1 rascunho (rejeitado por tech-lead REPROVADO + advogado APROVADO COM RESSALVAS BLOQUEANTES)
  - 2026-05-18 v2 reescrita absorvendo R1-R12 do tech-lead + R1-R9 do advogado
---

# Plano US-CLI-003 v2 — Importação 1-clique CSV

> **Story (PRD §6 US-CLI-003):** Importar planilha de clientes (1-clique) — dono migrando de Cali/Bling sobe CSV, vê preview com mapeamento sugerido, executa e recebe relatório.

## 0. Pareceres absorvidos

- `revisoes/US-CLI-003-tech-lead.md` — REPROVADO v1; 12 ressalvas (R1-R4 críticas: DoS, formula injection, dedup sem isolation, predicado tenant suspenso; R5-R9 altas; R10-R12 médias).
- `revisoes/US-CLI-003-advogado.md` — APROVADO COM RESSALVAS BLOQUEANTES v1; 9 ressalvas (R1-R3, R5, R6 críticas/bloqueantes: PJ-com-PF, base legal PF, ciclo arquivo, audit, declaração procedência; R4, R7 altas; R8, R9 altas).

Cada ressalva está mapeada para tasks T-CLI-041 a T-CLI-060 abaixo.

## 1. ACs (do PRD §6)

- **AC-CLI-003-1**: GIVEN arquivo CSV válido WHEN upload em `/importar-preview/` THEN preview com 10 primeiras linhas + delimitador detectado + encoding detectado + mapeamento sugerido (schema R6 tech-lead).
- **AC-CLI-003-2**: GIVEN confirmação + 3 declarações de procedência (R6 advogado) WHEN executa em `/importar-executar/` THEN cria clientes em lote, dedup automático via UNIQUE INDEX parcial, descarte de dados sensíveis (R9 advogado), relatório final sanitizado sem PII (R7 advogado), audit `cliente.importacao_executada` sem PII (R5 advogado).

## 2. Escopo cravado (decisões absorvidas das revisões)

### 2.1. Formato de arquivo

- **Somente CSV** no Marco 1 (XLSX, Cali/Bling parsers, Excel — Wave A).
- **Encoding**: UTF-8 (com ou sem BOM) — aceita. Latin-1 / ISO-8859-1 — **rejeita 400** com mensagem "salve como UTF-8 (Excel: Salvar Como > CSV UTF-8)" (R5 tech-lead).
- **Delimitador**: `,` ou `;` com detecção automática via `csv.Sniffer` (R5 tech-lead).
- **Limite de bytes**: **2 MiB** (`2 * 1024 * 1024`). Excedeu → **413 Payload Too Large** estruturada (R1 tech-lead + R3 advogado).
- **Limite de linhas**: **1000** (excluindo header). Excedeu → **400** estruturada (R1 tech-lead).
- **Content-Type whitelist**: `text/csv`, `application/csv`, `application/vnd.ms-excel`, `text/plain`. Outro → **415** (R1 tech-lead).

### 2.2. Síncrono no Marco 1

- Execução síncrona dentro de uma única transação SERIALIZABLE (R3 tech-lead).
- Procrastinate diferido pra Wave A — mesmo use case ganha `@procrastinate.task` lá (R11 tech-lead).
- Timeout Gunicorn 30s; drill p95 < 10s em 1000 linhas (teste `slow`).

### 2.3. Sanitização contra CSV injection (R2 tech-lead)

- Toda string que começa com `=`, `+`, `-`, `@`, `\t`, `\r` recebe prefixo `'` (apostrofo) **na escrita no banco**.
- Função `sanitizar_celula_csv` em `src/infrastructure/clientes/csv_safety.py`, reutilizável por export futuro.

### 2.4. Dedup transacional + concorrência (R3 tech-lead)

- **Isolation level**: `SERIALIZABLE` por importação (`SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`).
- **Advisory lock por tenant**: `pg_advisory_xact_lock(hashtext('importacao_clientes:' || tenant_id::text))` no início — duas importações simultâneas do mesmo tenant serializam; tenants diferentes não competem.
- **Dedup intra-arquivo**: pré-processamento agrupa por `(tipo_pessoa, documento)`; **última linha vence**; relatório reporta `linhas_colapsadas_intra_arquivo: N`.
- **bulk_upsert** via `Cliente.objects.bulk_create(update_conflicts=True, unique_fields=["tenant_id","tipo_pessoa","documento"], update_fields=[...])` — usa Django 5.0 nativo, respeita UNIQUE INDEX parcial criado em US-CLI-005.

### 2.5. Atomicidade (R9 tech-lead)

- **Pré-processamento separa válidas/inválidas em memória.**
- `skip_invalid=false` (default): qualquer linha inválida → **400** estruturada com lista de motivos, **nenhuma linha persistida**.
- `skip_invalid=true`: válidas inseridas em transação única; inválidas viram `rejeitados[]` no relatório.

### 2.6. Idempotência de re-upload (R7 tech-lead)

- Calcular `sha256(arquivo_bytes)` antes do processamento.
- `update_existing=true` (default): re-aplica SET; valores iguais ⇒ `sem_mudanca` (3ª categoria do relatório).
- `update_existing=false`: duplicatas vão pra `rejeitados` com motivo `ja_existe_no_tenant`.
- Audit grava `arquivo_hash`; rerun com mesmo hash retorna `reimportacao_detectada: true, ultima_importacao_em: <ts>` (operador decide).

### 2.7. Ciclo de vida do arquivo (R3 advogado — CRÍTICA)

- Arquivo é **transitório**: vive só durante a chamada HTTP. **Nunca persiste em B2/disco**.
- `try/finally` garante delete de qualquer tempfile que o Django parser tenha criado.
- Não há "salvar arquivo entre preview e executar" — o front reenviou o blob ele já tem; servidor não armazena.
- Teste `test_arquivo_csv_apagado_apos_execucao` verifica ausência do tempfile pós-execução (sucesso OU erro).

### 2.8. Declaração de procedência (R6 advogado — CRÍTICA)

Antes de executar, tenant marca 3 checkboxes + campo livre de origem:
1. ☐ "Tenho base legal documentada (contrato, consentimento ou obrigação legal)."
2. ☐ "Comuniquei aos titulares (ou comunicarei em até 10 dias úteis) — LGPD art. 9º."
3. ☐ "Não há dados sensíveis (LGPD art. 5º II) nas colunas mapeadas."
4. Campo livre `origem_sistema_anterior` (≤200 chars).

Grava em tabela `ClienteImportacaoDeclaracao` (RLS, retenção 5 anos), referenciada por hash no audit. Sem as 3 checks ⇒ **400**.

### 2.9. Base legal de PF / PJ-com-PF / dados sensíveis (R1, R2, R8, R9 advogado)

**PJ default**: dispensa aceite com `aceite_lgpd_dispensa_motivo` ∈ 3 valores:
- `pj_sem_pf_associada` — nenhuma coluna PF mapeada.
- `pj_com_pf_aceite_declarado_pelo_tenant` — tenant marcou checkbox declarando aceite (R6 advogado).
- `pj_com_pf_pendente_aceite` — linha entra com `aceite_lgpd_pendente=true`; bloqueia comunicação WhatsApp até titular re-aceitar.

**PF default**: **rejeita** linha com motivo `pf_sem_aceite`. Tenant pode liberar via flag `pf_aceite_origem` ∈ {`contrato_preexistente_documentado`, `consentimento_coletado_offline`, `migracao_sistema_anterior_com_aceite`} — quando passada, cliente é criado com `aceite_lgpd_base_legal` ∈ {`art_7_v`, `art_7_i`} + `aceite_lgpd_evidencia_externa = sha256(termo_declarado)`.

**CPF de sócio em PJ** (R8 advogado): preview detecta colunas `cpf_responsavel|cpf_socio|responsavel_legal_cpf` e oferece 3 destinos: (a) atributo PJ `cpf_responsavel_legal`, (b) contato PF separado com aceite pendente, (c) descarte. Default seguro = (b).

**Dados sensíveis** (R9 advogado): preview detecta regex case-insensitive `(saude|saúde|cid|diagnostico|raça|raca|cor|religiao|religião|orientacao|sexual|biometr|dna|genetic|sindical|sindicato|politic)` em headers; **descarta automaticamente** dessas colunas na execução; `dados_sensiveis_filtrados` agregado no audit.

### 2.10. Predicado ABAC `tenant_nao_suspenso` (R4 tech-lead)

- Registrar predicado em `src/infrastructure/clientes/predicates_authz.py` (mesma localização de `cliente_nao_bloqueado` US-CLI-004).
- Stub atual: retorna sempre `allowed=True` (ADR-0015 fluxo 3 ainda não tem modelo); marca TODO + dependência.
- Anexado à action `clientes.importar`.
- 1 teste passando (`test_importar_com_tenant_stub_nao_suspenso_passa`) + 1 teste skip-marker (`test_importar_com_tenant_suspenso_nega_403` — skip até ADR-0015 entrar).

### 2.11. Authz

- Action: `clientes.importar`.
- Perfil: apenas `admin_tenant` (TL7 — least privilege).
- Predicado ABAC: `tenant_nao_suspenso` (stub R4 tech-lead).

### 2.12. Audit `cliente.importacao_executada` (R10 tech-lead + R5 advogado — payload sanitizado)

```json
{
  "event_id": "<uuid v4>",
  "tenant_id": "<uuid>",
  "importacao_id": "<uuid>",
  "arquivo_hash": "<sha256(arquivo_bytes)>",
  "arquivo_nome_hash": "<sha256(filename)>",
  "arquivo_tamanho_bytes": 142933,
  "declaracao_hash": "<sha256(declaracao_jsonb)>",
  "procedencia_declarada": "<string ≤200 chars>",
  "delimitador": ";",
  "encoding": "utf-8",
  "update_existing": true,
  "skip_invalid": false,
  "pf_aceite_origem": "contrato_preexistente_documentado",
  "totais": {
    "linhas_lidas": 1000,
    "linhas_colapsadas_intra_arquivo": 3,
    "criados": 850,
    "atualizados": 100,
    "sem_mudanca": 40,
    "rejeitados": 7,
    "pj_dispensa_aceite": 700,
    "pj_com_pf_pendente_aceite": 80,
    "pf_rejeitadas_por_falta_aceite": 0,
    "dados_sensiveis_filtrados": 2
  },
  "rejeitados_motivos_agregados": {
    "cnpj_invalido": 4,
    "cpf_invalido": 0,
    "ja_existe_no_tenant": 3,
    "pf_sem_aceite": 0
  },
  "rejeitados_linhas_hashes": [
    {"linha_numero": 42, "linha_hash": "<sha256(linha_bytes+salt_tenant)>", "motivo": "cnpj_invalido"}
  ],
  "ip_hash": "<sha256(ip+salt_tenant)>",
  "usuario_id": "<uuid>",
  "executado_em": "<ISO8601>"
}
```

**Regras absolutas**:
- 1 importação = **1 linha de audit** (NUNCA 1 por linha — protege hash chain do audit).
- PII proibida no payload: `nome`, `documento`, `email`, `telefone` — só hashes salgados por tenant.
- Hash salgado: `sha256(linha + salt_tenant)` (R5 risco do advogado).

### 2.13. Relatório final (R7 advogado)

**Resposta HTTP do `/importar-executar/`**:
- Totais (igual ao audit acima).
- Lista de até 50 linhas rejeitadas com `{linha_numero, motivo_codigo, motivo_descricao_curta}` — **sem nome/CPF/email/telefone**.
- Tenant cruza com o CSV local dele.

**Consulta posterior** via `GET /clientes/importacoes/`:
- Lista `{usuario_hash, timestamp, arquivo_hash, totais, procedencia_declarada}`.
- Perfil `admin_tenant`.
- Cada abertura gera log `acessos_dados_cliente` com `finalidade="consulta_relatorio_importacao"` + `cliente_id=NULL` + `recurso={tabela:"cliente_importacao", id:<import_id>}` (INV-013).
- Nova finalidade adicionada ao enum de US-CLI-002.

### 2.14. RAT-17 (R4 advogado)

- Criar entrada **RAT-17 — Importação em massa de cadastro de cliente final** em `docs/conformidade/comum/lgpd-rat.md`.
- DPIA-06 diferida pra Wave A (MVP-1 dogfooding-only não força DPIA formal).

### 2.15. Histórico de cliente mesclado (R/E tech-lead, risco arquitetural)

- Dedup também consulta `Cliente.all_objects` — se documento existe em soft-deleted (cliente mesclado), **rejeita** com motivo `documento_pertence_a_cliente_mesclado` + sugere consultar `vencedor_id` no audit `cliente.mesclado`.

## 3. Não-faz (non-goals)

- Cali/Bling parsers nativos (Wave A — adapters dedicados).
- Excel/XLSX (Wave A — pandas/openpyxl).
- Processamento async via Procrastinate (Wave A — `@procrastinate.task` decoração).
- PF em lote **sem flag `pf_aceite_origem`** — default é rejeitar.
- Importação de dados sensíveis art. 5º II LGPD — V2+ com base art. 11 + DPIA + consentimento por linha.
- Importação de menores de idade — V2 (detector + filtro).
- Rollback de importação completa — V2 (`undo_importacao_id`).
- Resolução manual campo-a-campo de conflitos — Wave A.
- Portal LGPD do titular re-aceitando importações pendentes — Wave B.

## 4. Sequência de tasks

| ID | Descrição | AC | Hook que ativa |
|---|---|---|---|
| **T-CLI-041** | Settings: `DATA_UPLOAD_MAX_MEMORY_SIZE=2*1024*1024` + `FILE_UPLOAD_MAX_MEMORY_SIZE` ajustado + DRF parser whitelist | AC-1 | — |
| **T-CLI-042** | `src/infrastructure/clientes/csv_safety.py` — `sanitizar_celula_csv` (R2 tech-lead) | AC-2 | — |
| **T-CLI-043** | `src/infrastructure/clientes/csv_io.py` — `ler_csv_normalizado(file) -> (delimitador, encoding, headers, linhas)` (R5 tech-lead) + heurística `HEADER_HEURISTICAS` + detector sensíveis (R9 advogado) | AC-1 | — |
| **T-CLI-044** | `src/domain/comercial/clientes/repository.py` — estender `ClienteRepository` com `bulk_upsert` + DTOs `ClienteImportacaoInput`, `ResultadoImportacao`, `LinhaRejeitada` (R8 tech-lead) | AC-2 | — |
| **T-CLI-045** | Migration `0012_cliente_importacao_declaracao.py` — modelo `ClienteImportacaoDeclaracao` (R6 advogado) + RLS policy + 3 checkboxes + origem | AC-2 | `migration-rls-check`, `policy-test-coverage` |
| **T-CLI-046** | Migration `0013_cliente_lgpd_base_legal.py` — campos `aceite_lgpd_base_legal` (enum), `aceite_lgpd_evidencia_externa` (text), `aceite_lgpd_pendente` (bool), `cpf_responsavel_legal` (CharField) no `Cliente` (R2, R8 advogado) | AC-2 | — |
| **T-CLI-047** | `src/application/comercial/clientes/importar_clientes.py` — use case puro com Repository (R8 tech-lead) — pré-processamento, validação, classificação 3-vias PJ, sanitização, dedup intra-arquivo, descarte sensíveis, bulk_upsert, rejeitados | AC-1, AC-2 | `anti-mascaramento` |
| **T-CLI-048** | `src/infrastructure/clientes/repositories.py` — `DjangoClienteRepository.bulk_upsert` com `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` + `pg_advisory_xact_lock` + `bulk_create(update_conflicts=True)` (R3 tech-lead) | AC-2 | — |
| **T-CLI-049** | Predicate ABAC `tenant_nao_suspenso` (stub) em `predicates_authz.py` + registro action `clientes.importar` (R4 tech-lead) | AC-2 | `authz-check` |
| **T-CLI-050** | Validador PJ-com-PF: inspeciona linha mapeada e decide `dispensa_motivo` ∈ 3 valores (R1 advogado) | AC-2 | — |
| **T-CLI-051** | Garantia delete tempfile `try/finally` no view (R3 advogado) | AC-1, AC-2 | — |
| **T-CLI-052** | Adicionar RAT-17 em `docs/conformidade/comum/lgpd-rat.md` (R4 advogado) | — | `paths-frontmatter-validator` |
| **T-CLI-053** | Adicionar finalidade `consulta_relatorio_importacao` ao enum `FinalidadeAcessoCliente` (US-CLI-002 R2) — migration audit (R7 advogado) | AC-2 | `migration-rls-check` |
| **T-CLI-054** | `src/infrastructure/clientes/views.py` — `importar_preview` action + `importar_executar` action + `importacoes` list action; ACTION_MAP atualizado | AC-1, AC-2 | `authz-check` |
| **T-CLI-055** | `src/infrastructure/clientes/serializers.py` — `ImportarPreviewSerializer`, `ImportarExecutarSerializer`, `DeclaracaoProcedenciaSerializer` | AC-1, AC-2 | — |
| **T-CLI-056** | Migration seed `0014_seed_authz_importar.py` — adiciona `clientes.importar` na lista de perfil `admin_tenant` apenas (R4 advogado, TL7) | AC-2 | `migration-rls-check` |
| **T-CLI-057** | Audit `cliente.importacao_executada` — payload sanitizado seção 2.12 (R5 advogado + R10 tech-lead) | AC-2 | `audit-immutability-check` |
| **T-CLI-058** | Rejeitar `documento_pertence_a_cliente_mesclado` quando documento existe em soft-deleted (E risco arquitetural tech-lead) | AC-2 | — |
| **T-CLI-059** | URL patterns: `POST /api/v1/clientes/importar-preview/`, `POST /api/v1/clientes/importar-executar/`, `GET /api/v1/clientes/importacoes/` | AC-1, AC-2 | — |
| **T-CLI-060** | Suite de testes (≥15) — ver seção 5 abaixo | AC-1, AC-2 | `_test-runner` |

## 5. Testes (T-CLI-060 — ≥15 cobrindo happy + unhappy + segurança + LGPD)

**AC-CLI-003-1 — Preview:**
1. `test_preview_devolve_10_linhas_e_mapeamento_sugerido` — happy path UTF-8 sem BOM com `;` brasileiro.
2. `test_preview_detecta_csv_utf8_bom_com_ponto_virgula` — detecta BOM + delimitador.
3. `test_preview_rejeita_latin1_com_400_e_dica_utf8` — encoding inválido.
4. `test_preview_detecta_delimitador_misto_pelo_maior_consenso` — sniffer correto.
5. `test_preview_mapeia_header_cpf_cnpj_pra_documento` — heurística.
6. `test_preview_devolve_confianca_baixa_quando_header_desconhecido` — heurística inverso.
7. `test_preview_detecta_coluna_dados_sensiveis_e_avisa_descarte` — R9 advogado.
8. `test_preview_detecta_coluna_cpf_responsavel_e_oferece_3_destinos` — R8 advogado.

**AC-CLI-003-2 — Executar:**
9. `test_executar_cria_clientes_pj_em_lote_sem_pf` — dispensa caminho 1.
10. `test_executar_pj_com_email_de_pessoa_marca_pendente_aceite` — R1 advogado caminho 3.
11. `test_executar_pj_com_tenant_declarando_aceite_grava_motivo_correto` — R1 advogado caminho 2.
12. `test_executar_pf_sem_flag_rejeita_linha` — R2 advogado default.
13. `test_executar_pf_com_flag_contrato_preexistente_cria_com_base_art_7_v` — R2 advogado.
14. `test_executar_atualiza_existente_quando_documento_bate_e_update_existing_true` — happy path update.
15. `test_executar_relatorio_separa_criados_atualizados_sem_mudanca_rejeitados` — 4 categorias.
16. `test_executar_rejeita_linha_com_cnpj_invalido` — validação.
17. `test_executar_limite_1000_linhas_excedido_retorna_400` — R1 tech-lead.
18. `test_executar_skip_invalid_false_com_1_linha_invalida_nao_persiste_nada` — R9 tech-lead.
19. `test_executar_skip_invalid_true_com_1_linha_invalida_persiste_resto_e_relata` — R9 tech-lead.
20. `test_executar_documento_duplicado_intra_arquivo_colapsa_ultima_vence` — R3 tech-lead.
21. `test_executar_documento_de_cliente_mesclado_rejeita_com_link_vencedor` — risco E tech-lead.
22. `test_executar_dados_sensiveis_descartados_contagem_no_audit` — R9 advogado.

**Segurança / DoS / Injeção:**
23. `test_upload_excede_2mib_retorna_413` — R1 tech-lead.
24. `test_upload_content_type_invalido_retorna_415` — R1 tech-lead.
25. `test_importar_neutraliza_formula_em_nome_e_email` — R2 tech-lead (CSV injection).
26. `test_arquivo_csv_apagado_apos_execucao_sucesso_e_erro` — R3 advogado.
27. `test_2_importacoes_simultaneas_mesmo_tenant_serializam_sem_deadlock` — R3 tech-lead (marker `slow`).
28. `test_bulk_upsert_1000_linhas_p95_abaixo_de_10s` — R11 tech-lead (marker `slow`).

**Idempotência:**
29. `test_rerun_mesmo_arquivo_update_existing_true_e_idempotente_sem_mudanca` — R7 tech-lead.
30. `test_rerun_mesmo_arquivo_emite_alerta_reimportacao` — R7 tech-lead.

**Audit + LGPD:**
31. `test_audit_importacao_nao_contem_cpf_cnpj_nome_email_telefone` — R5 advogado + R10 tech-lead (regex scan no payload).
32. `test_audit_e_um_evento_unico_nunca_um_por_linha` — protege hash chain.
33. `test_executar_sem_declaracao_procedencia_retorna_400` — R6 advogado.
34. `test_relatorio_imediato_nao_lista_pii_dos_criados` — R7 advogado.
35. `test_consulta_lista_importacoes_dispara_inv_013` — R7 advogado.

**Authz:**
36. `test_importar_exige_perfil_admin_tenant` — TL7.
37. `test_importar_com_tenant_stub_nao_suspenso_passa` — R4 tech-lead.
38. `test_importar_com_tenant_suspenso_nega_403` — R4 tech-lead (`@pytest.mark.skip(reason="ADR-0015 fluxo 3 pending")`).

## 6. Modelos / tabelas envolvidos

- **Estender** `infrastructure.clientes.Cliente`: `aceite_lgpd_base_legal` (enum), `aceite_lgpd_evidencia_externa` (text), `aceite_lgpd_pendente` (bool default=False), `cpf_responsavel_legal` (CharField 11, nullable).
- **Nova** tabela `infrastructure.clientes.ClienteImportacaoDeclaracao`:
  - `id` UUID PK
  - `tenant_id` FK Tenant (RLS)
  - `usuario_id` UUID
  - `criado_em` timestamp
  - `arquivo_hash` sha256
  - `arquivo_tamanho_bytes` int
  - `tem_base_legal` bool (checkbox 1)
  - `compromisso_comunicar_titulares` bool (checkbox 2)
  - `declara_sem_dados_sensiveis` bool (checkbox 3)
  - `procedencia_declarada` varchar(200)
  - `pf_aceite_origem` enum (nullable)
- **Estender** `infrastructure.audit.FinalidadeAcessoCliente` (enum): + `consulta_relatorio_importacao`.

## 7. Endpoints

- `POST /api/v1/clientes/importar-preview/` — multipart/form-data, arquivo CSV. Resposta: schema R6 tech-lead (delimitador_detectado, encoding_detectado, linhas_amostra, headers_arquivo, mapeamento_sugerido, campos_destino_disponiveis, colunas_sensiveis_detectadas, colunas_cpf_responsavel_detectadas, arquivo_hash).
- `POST /api/v1/clientes/importar-executar/` — multipart/form-data + JSON form fields:
  - `arquivo` (file, reenvio do mesmo blob)
  - `mapeamento` (JSON do front)
  - `declaracao` (JSON com 3 booleans + procedencia_declarada)
  - `pf_aceite_origem` (opcional)
  - `cpf_responsavel_destino` (opcional, default `contato_pf_separado`)
  - `skip_invalid` (bool, default false)
  - `update_existing` (bool, default true)
- `GET /api/v1/clientes/importacoes/` — lista histórico do tenant; cada abertura dispara INV-013 finalidade `consulta_relatorio_importacao`.

## 8. Hooks ativados (validações automáticas)

- `block-destructive`, `secrets-scanner`, `_test-runner`, `INV-checker`, `tenant-id-validator`, `anti-mascaramento`, `context-budget`, `paths-frontmatter-validator`, `bus-envelope-validator`, `authz-check`, `provisioning-checkpoint-check`, `mock-in-production`, `migration-rls-check`, `audit-immutability-check`, `pyproject-validator`, `policy-test-coverage`.

## 9. Invariantes citadas

- **INV-001** (multi-tenant blast radius).
- **INV-013** (log de acesso a dado de cliente — relatório de importação + consulta histórico).
- **INV-024** (audit sem PII cru).
- **INV-TENANT-001/002** (RLS deny-by-default).
- **INV-AUTHZ-001/002** (deny-by-default + ACTION_MAP).
- **INV-AUTHZ-004** (predicate registry — `tenant_nao_suspenso` stub).
- **INV-INT-009** (suspensão de tenant desliga features — operacionalizada por `tenant_nao_suspenso`).
- **SEC-LEAST-PRIV-001** (`clientes.importar` só `admin_tenant`).

## 10. ADRs citadas

- **ADR-0001** (stack — Django/PG/DRF).
- **ADR-0002** (multi-tenant RLS).
- **ADR-0007** (camada domínio + Repository Protocol).
- **ADR-0012** (autorização porta).
- **ADR-0015** (lifecycle tenant — predicate `tenant_nao_suspenso` é canal único).
- **ADR-0017** (CNPJ alfanumérico — VO já implementado em US-CLI-001 é reusado pra validar CNPJ no preview/executar).

## 11. Riscos / pontos sensíveis

- **Síncrono no Marco 1**: drill p95 < 10s precisa passar em CI; se quebrar, forçar Procrastinate aqui (não em Wave A).
- **Pré-processamento em memória 1000 linhas**: ~50-100 MiB RSS por request; 4 requests paralelos cabem na VPS atual (3 GiB livres). Monitorar quando Wave A entrar.
- **Hash chain do audit em batch**: regra absoluta — 1 importação = 1 audit. Hook `audit-immutability-check` valida não-mutação.
- **Re-import de cliente mesclado**: dedup consulta `Cliente.all_objects`; rejeita com motivo específico em vez de criar duplicata silenciosa.
- **Tenant declara procedência falsa**: mitigação contratual via DPA (cláusula "tenant assume responsabilidade pela legalidade da procedência declarada"). Auditoria amostral em Wave B.
- **CSV injection sanitização**: aplicada na **escrita** (entrada no banco); export futuro deve aplicar a mesma função no **boundary de saída** (defesa em profundidade).
- **Latin-1 rejeitado**: 30% dos uploads BR podem quebrar inicialmente; mensagem amigável compensa.

## 12. Subagentes consultados (revisões em `revisoes/`)

- `tech-lead-saas-regulado` — REPROVADO v1; aprovação esperada em re-review pós-v2 (12 ressalvas endereçadas).
- `advogado-saas-regulado` — APROVADO COM RESSALVAS BLOQUEANTES v1; aprovação esperada em re-review pós-v2 (9 ressalvas endereçadas).
- Antes do go-live público (não MVP-1 dogfooding): advogado humano OAB ativa revisa (a) textos dos 3 checkboxes (R6), (b) catálogo de motivos de rejeição visíveis ao tenant, (c) mensagem de descarte de dados sensíveis (R9), (d) cláusula DPA. Estimar 2-3h.

## 13. Diferido pra fases futuras

- **Wave A**: parsers nativos Cali/Bling; Excel/XLSX; Procrastinate worker async; DPIA-06 formal.
- **Wave B**: portal LGPD do titular re-aceitando importações pendentes; auditoria amostral de procedências declaradas; rollback de importação completa.
- **V2+**: importação de dados sensíveis art. 11 LGPD + DPIA dedicada; importação de menores (art. 14 LGPD).
