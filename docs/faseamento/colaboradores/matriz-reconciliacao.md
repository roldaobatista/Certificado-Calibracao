---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: colaboradores
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/colaboradores/spec.md
  - docs/faseamento/colaboradores/plan.md
  - docs/faseamento/colaboradores/tasks.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `colaboradores` (RH mínimo, base nível 2)

> **Pra quê:** provar, item por item, que cada US/INV da spec virou código real + teste.
> Formato R20 (ritual-orquestrador.md §3.7 — auditoria de cerimônia 2026-06-12):
> SOMENTE §1 rastreabilidade US/INV↔código, §2 INV↔teste, §8 ata do P9.
> Path aninhado domínio `src/{domain,application}/rh_frota_qualidade/colaboradores/` + infra flat
> `src/infrastructure/colaboradores/` (D-COL-1).
> Frente #4 da cadeia de construção (nível 2 topológico).

---

## 1. Rastreabilidade US/INV ↔ código

| US / entidade | ACs / decisões | INV | Arquivo de código (símbolo) | Status |
|---|---|---|---|---|
| US-COL-001 dedup CPF | AC-COL-01-1 (UNIQUE parcial tenant+cpf WHERE não-deletado; VO CPF; 409) | **INV-COL-CPF** | `src/domain/rh_frota_qualidade/colaboradores/entities.py` (`Colaborador.cpf: CPF`) · `src/infrastructure/colaboradores/models.py` (`ColaboradorModel` UNIQUE parcial) · migration `0001_initial.py` + `src/application/rh_frota_qualidade/colaboradores/cadastro.py` (`cadastrar_colaborador` → 409 `DuplicateCpf`) | ✅ |
| US-COL-002 papel→elegiveis | AC-COL-02 (sem papel não retorna em `/elegiveis`; papéis filtram listagem) | **INV-COL-ELEGIVEIS-MINIMO** | `src/application/rh_frota_qualidade/colaboradores/consultas.py` (`consultar_elegiveis`) · `src/infrastructure/colaboradores/serializers.py` (`ElegivelDTO`) | ✅ |
| US-COL-003 signatário escopo | AC-COL-03 (SIGNATARIO exige usuario_id + RT casa + escopo vigente; bloqueio hard perfil A; configurável B/C/D) | **INV-COL-SIGNATARIO-IDENTIDADE**, **INV-COL-SIGNATARIO-ESCOPO** | `src/domain/rh_frota_qualidade/colaboradores/regras.py` (`pode_atribuir_signatario`) · `src/application/rh_frota_qualidade/colaboradores/papeis.py` (`atribuir_papel` bloco SIGNATARIO) | ✅ |
| US-COL-004 comissão | AC-COL-04 (comissao_default_pct Decimal 5,2; CHECK 0..100; GET comissao-vigente; audit INV-001) | — | `src/domain/rh_frota_qualidade/colaboradores/entities.py` (`Colaborador.comissao_default_pct`) · migration `0001_initial.py` (CHECK) · `src/application/rh_frota_qualidade/colaboradores/consultas.py` (`comissao_vigente`) · `src/infrastructure/colaboradores/views.py` (audit via `publicar_evento`) | ✅ |
| US-COL-005 matriz habilidades | AC-COL-05 (catálogo seed OU livre; nível; GET /elegiveis DTO mínimo) | **INV-COL-ELEGIVEIS-MINIMO** | `src/domain/rh_frota_qualidade/colaboradores/entities.py` (`Habilidade`, `CatalogoHabilidade`) · migration `0006_seed_catalogo_habilidade.py` (seed global literal) · `src/application/rh_frota_qualidade/colaboradores/habilidades.py` (`registrar_habilidade`) | ✅ |
| US-COL-006 desligamento | AC-COL-06 (data_desligamento → revoga papéis → some de /elegiveis; histórico preservado; hard-delete bloqueado) | **INV-COL-DESLIGAMENTO-CASCADE**, **INV-COL-INATIVO** | `src/domain/rh_frota_qualidade/colaboradores/regras.py` (`cascade_revoga_papeis`, `derivar_ativo`) · `src/application/rh_frota_qualidade/colaboradores/cadastro.py` (`desligar_colaborador`) · migration `0003_trigger_defensivo.py` (trigger PG BEFORE DELETE) · porta `ColaboradorReferenciadoPort` + stub conservador | ✅ |
| US-COL-006-2 evento ≤2s | AC-COL-06-2 (outbox transacional; payload v9; chave idempotente estável) | — | `src/application/rh_frota_qualidade/colaboradores/cadastro.py` (`desligar_colaborador` → `publicar_evento(..., outbox=True)`) · `src/domain/rh_frota_qualidade/colaboradores/regras.py` (`montar_payload_desligamento` v9) | ✅ (6 consumers → GATE-COL-CONSUMERS) |
| US-COL-007 WCAG | AC-COL-07 (erro PT-BR sem jargão; dado servido pronto p/ UI acessível) | — | `src/infrastructure/colaboradores/views.py` (mensagens PT-BR em erros) | ✅ |
| `Colaborador` + soft-delete (D-COL-3) | DOIS mecanismos: desligamento (data_desligamento + ativo derivado) + soft-delete Padrão C (deletado_em) | — | `src/infrastructure/colaboradores/models.py` (`ColaboradorModel` 2 managers: `ativos`, default, `all_objects`) · `src/domain/rh_frota_qualidade/colaboradores/entities.py` (`Colaborador`) | ✅ |
| `Papel` mutável com revogação auditada (D-COL-4) | data_inicio/data_fim/revogado_em colunas (NÃO JanelaVigencia em row mutável); DONO único por tenant sob advisory lock (ADR-0065); troca DONO namespace 880_405 | **INV-COL-DONO-UNICO** | `src/infrastructure/colaboradores/models.py` (partial unique `WHERE papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL`) · migration `0001_initial.py` · `src/infrastructure/colaboradores/repositories.py` (advisory lock `880_405`) · `src/application/rh_frota_qualidade/colaboradores/papeis.py` (`revogar_papel`) | ✅ |
| `CatalogoHabilidade` global (D-COL-5) | model próprio em colaboradores; seed literal global; sem tenant_id; SELECT global app_user; INSERT só via seed | — | `src/infrastructure/colaboradores/models.py` (`CatalogoHabilidadeModel` — sem tenant_id) · migration `0002_rls.py` (isenção RLS por tenant) · migration `0004_grants.py` (SELECT global) · migration `0006_seed_catalogo_habilidade.py` | ✅ |
| Documento + foto (D-COL-6) | AnexoStoragePort + AnexoStorageLocal; foto mesma porta; EXIF strip; sem blur; tipo CTPS/CNH/CERTIFICADO_CURSO/OUTRO (sem ASO — R-COL-2); coerência documento×vínculo (alerta) | **INV-COL-DOC-VINCULO** | `src/application/rh_frota_qualidade/colaboradores/documentos.py` (`anexar_documento`) · `src/domain/rh_frota_qualidade/colaboradores/regras.py` (`coerencia_documento_vinculo`) | ✅ |
| Mascaramento PII multi-papel (D-COL-7) | `filtrar_visao_pii` choke-point ÚNICO; MATRIZ_VISAO_PII; CPF só DONO (demais últimos 2); e-mail/tel Dono/Gerente/próprio; CTPS/CNH Dono+próprio | **INV-COL-PII-MASCARA** | `src/infrastructure/colaboradores/serializers.py` (`filtrar_visao_pii`, `MATRIZ_VISAO_PII`) | ✅ |
| PII hash em evento/log (D-COL-8) | CPF/nome/documento HMAC-tenant (pseudonimização ADR-0029/0064) em payload/log/4xx | **INV-COL-PII-LOG** | `src/infrastructure/colaboradores/views.py` (hash antes de publicar; `_falha` sem PII em claro) · `src/application/rh_frota_qualidade/colaboradores/*.py` (helper hash canônico) | ✅ |
| Base legal por vínculo (D-COL-12 / ADV-COL-01) | constante `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` no domínio (fonte que o RAT do GATE fotografa) | — | `src/domain/rh_frota_qualidade/colaboradores/base_legal.py` (`BASE_LEGAL_POR_VINCULO_E_CATEGORIA`) | ✅ |
| Porta `ColaboradorReferenciadoPort` (D-COL-3 / TL-COL-07) | Protocol + stub conservador (assume "referenciado" → bloqueia hard-delete; fail-safe ADR-0066) | **INV-COL-INATIVO** | `src/domain/rh_frota_qualidade/colaboradores/portas.py` (`ColaboradorReferenciadoPort`, stub conservador) | ✅ |
| Anti-N+1 (TL-COL-12) | `prefetch_related` papéis/habilidades/documentos em list + retrieve; /elegiveis filtra no banco; `assertNumQueries` | — | `src/infrastructure/colaboradores/views.py` (`ColaboradorViewSet.list` com prefetch) | ✅ |
| MOTORISTA_UMC sem CNH = pendência (R-COL-1) | salva com `pendencia_cnh=true`; sem 422 no cadastro; bloqueio na alocação (frota/agenda) | — | `src/domain/rh_frota_qualidade/colaboradores/regras.py` (`pendencia_cnh_motorista`) · `src/application/rh_frota_qualidade/colaboradores/papeis.py` (`atribuir_papel` bloco MOTORISTA_UMC) | ✅ |

---

## 2. INV ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste nomeado (arquivo:classe) | Cobertura E2E adicional |
|---|---|---|---|
| INV-COL-CPF | UNIQUE parcial (tenant_id, cpf) WHERE deletado_em IS NULL (migration 0001) + VO `CPF` domínio + 409 `DuplicateCpf` no use case | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_CPF` | `tests/test_colaboradores_schema_fatia1b.py` (re-cadastro pós-soft-delete OK; dedup → IntegrityError) |
| INV-COL-SIGNATARIO-IDENTIDADE | `pode_atribuir_signatario` domínio: `usuario_id IS NOT NULL` + `RTCompetencia` vigente com mesmo `usuario_id` (casa pessoa, não só FK) | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_SIGNATARIO_IDENTIDADE` | `tests/test_colaboradores_fatia2_e2e.py` (sem usuario_id → 422; RT inexistente → 422; RT de outro → 422) |
| INV-COL-SIGNATARIO-ESCOPO | `pode_atribuir_signatario` domínio: escopo vigente na data; hard perfil A via `tenant_perfil_e` | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_SIGNATARIO_ESCOPO` | `tests/test_colaboradores_dominio.py` (sem escopo perfil A → bloqueia; perfil B → aviso) |
| INV-COL-DONO-UNICO | partial unique `WHERE papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL` (migration 0001) + advisory lock 880_405 | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_DONO_UNICO` | `tests/test_colaboradores_schema_fatia1b.py` (2º DONO → IntegrityError) |
| INV-COL-INATIVO | trigger PG BEFORE DELETE (migration 0003) + stub conservador `ColaboradorReferenciadoPort` (bloqueia hard-delete) | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_INATIVO` | `tests/test_colaboradores_schema_fatia1b.py` (delete físico → trigger raise) |
| INV-COL-DESLIGAMENTO-CASCADE | `cascade_revoga_papeis` domínio + use case `desligar_colaborador` (revoga papéis ativos no mesmo atomic) | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_DESLIGAMENTO_CASCADE` | `tests/test_colaboradores_dominio.py` (cascade revoga todos os papéis ativos) |
| INV-COL-PII-MASCARA | `filtrar_visao_pii` choke-point ÚNICO em TODOS serializers + hook `col-pii-mascara-check` | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_PII_MASCARA` | `tests/test_colaboradores_fatia2_e2e.py` (Gerente não vê CPF; próprio vê CPF; sem papel → tudo mascarado) |
| INV-COL-ELEGIVEIS-MINIMO | serializer `ElegivelDTO` allowlist separado (`colaborador_id`, `nome_exibicao`, `papel`, `habilidades`, `ativo`) em `/elegiveis` | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_ELEGIVEIS_MINIMO` | `tests/test_colaboradores_fatia2_e2e.py` (`/elegiveis` nunca retorna CPF/e-mail/telefone/comissão) |
| INV-COL-DOC-VINCULO | `coerencia_documento_vinculo` domínio (alerta — não bloqueia) + hook `col-evento-pii-hash-check` | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_DOC_VINCULO` | `tests/test_colaboradores_dominio.py` (TERCEIRIZADO+CTPS → alerta; CLT+CTPS → sem alerta) |
| INV-COL-PII-LOG | `_falha()` em views.py nunca inclui CPF/nome cru; payload evento usa HMAC-tenant + hook `col-evento-pii-hash-check` | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_PII_LOG` | `tests/test_colaboradores_fatia2_e2e.py` |
| INV-COL-COMISSAO-AUDIT | alteração de `comissao_default_pct` grava audit via `publicar_evento` (cadeia hash INV-001) | `tests/regressao/test_inv_col_classes_nomeadas.py:TestINV_COL_COMISSAO_AUDIT` | `tests/test_colaboradores_fatia2_e2e.py` |
| INV-TENANT-001..003 (transversal) | RLS v2 FORCE nas 4 tabelas-tenant (migration `0002_rls.py`); `catalogo_habilidade` isento (global) | `tests/test_colaboradores_schema_fatia1b.py` (RLS UNHAPPY cross-tenant ×4) | — |
| IDEMP-001 (transversal) | Idempotency-Key em todas as escritas (cadastrar/desligar/atribuir_papel/revogar/habilidades/documentos); `/elegiveis`/`/comissao-vigente` SEM key (leituras) | `tests/test_colaboradores_fatia2_e2e.py` (idempotência desligar 2x → 1 evento) | — |

---

## GATEs rastreados (não bloqueiam fechamento do núcleo)

### GATEs funcionais colaboradores (COL-*)

| GATE | Bloqueia | Descrição |
|---|---|---|
| **GATE-COL-ANEXO-B2** | B2 WORM real dos documentos+foto | Hoje `AnexoStorageLocal`; B2 WORM real necessário antes do 1º dado pessoal em produção. |
| **GATE-COL-COMISSAO-COUNT** | `comissoes_pendentes_count` real no payload `Colaborador.Desligado` | Hoje `=0` stub; fecha quando frente `comissoes` (N6) existir e publicar contagem real. |
| **GATE-COL-CONSUMERS** | 6 reatores de `Colaborador.Desligado` ativos | Consumers a plugar: `acesso-seguranca`, `os`, `comissoes`, `caixa-tecnico`, `certificados`, `suporte-saas` — módulos futuros plugam handlers no outbox sem retrofit do publisher. |
| **GATE-COL-PERFIL-MATRIZ** | Predicate `can_assign_signatario` perfil-aware | Linha adicionada à `docs/conformidade/comum/matriz-feature-perfil.md` (A8 — T-COL-060 P8). Fechar quando predicate usar `tenant_perfil_e` em produção real. |

### GATE LGPD congelado (NÃO escrever agora — GATE-LGPD-RAT-CONSOLIDACAO)

| Achado | Descrição | Congelado até |
|---|---|---|
| **A3 — RAT CTPS/CNH/foto/certificados** | Registro de Atividade de Tratamento por categoria de dado × base legal (D-COL-12 / ADV-COL-01 / `BASE_LEGAL_POR_VINCULO_E_CATEGORIA`). | GATE-LGPD-RAT-CONSOLIDACAO |
| **A4 — Retenção por campo** | Prazo de retenção CTPS/CNH/foto por vínculo (ADR-0021 zonas). | GATE-LGPD-RAT-CONSOLIDACAO |
| **A6 — Zona ADR-0021 por campo de colaborador** | Mapeamento zona A/B/C de cada campo PII do módulo. | GATE-LGPD-RAT-CONSOLIDACAO |
| **A7 — DPIA cadastro colaborador** | DPIA completa do formulário de cadastro (não-ASO; ASO fora R-COL-2). | GATE-LGPD-RAT-CONSOLIDACAO |
| **`[OAB-PRE-PROD]`** | Texto de bloqueio fundamentado ao titular (direito de eliminação); ratificação matriz de zonas aplicada a colaborador; DPA Aferê↔tenant sobre PII de colaborador; designação formal de DPO. | Antes do 1º dado real de pessoa física em produção |

> **Base legal registrada no domínio** (não diferida): constante `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` em `src/domain/rh_frota_qualidade/colaboradores/base_legal.py` captura a base legal CLT (art.7º II) × PJ (art.7º V) × estagiário (Lei 11.788). Esta é a fonte que o RAT do GATE irá fotografar.

---

## 8. P9 — ritual auditores roteados (INV-RITUAL-003) — a preencher no P9

> Seção reservada para a ata do P9 (mutirão de auditores — T-COL-061).
> Auditores roteados: qualidade · segurança · llm-correctness · idempotência ·
> **conformidade-lgpd OBRIGATÓRIO (PII pesado)** · produto · performance
> (list/elegiveis N+1) · observabilidade (PII em log + tenant_id/correlation_id).
> Supplychain: SÓ se dep nova. Drift-docs: FORA (R7).
> Verificação adversarial de TODO MÉDIO+ antes do mutirão (R6); 2ª passada escopada (R5).
> Zero CRÍTICO/ALTO/MÉDIO → INV-RITUAL-001 satisfeito → FECHADA.
