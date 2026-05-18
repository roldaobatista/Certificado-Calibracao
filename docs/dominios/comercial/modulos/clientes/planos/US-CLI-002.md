---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-002
---

# Plano US-CLI-002 — Visão 360° do cliente

> Story em `docs/dominios/comercial/modulos/clientes/prd.md` §6 US-CLI-002 (3 ACs).

## ACs

- **AC-CLI-002-1**: timeline cronológica reversa com eventos de TODOS os módulos (OS criada/concluída, certificado emitido, NF-e, NPS, contato registrado).
- **AC-CLI-002-2**: carregamento p95 < 1.5s para clientes com até 500 eventos.
- **AC-CLI-002-3 (INV-013)**: cada abertura grava em `audit_trail.acessos_dados_cliente` `{user_id, tenant_id, cliente_id, finalidade, timestamp, ip_hash}` ANTES de renderizar.

## Escopo realista pra Marco 1

Módulos consumidores (OS, certificados, NF-e, NPS) NÃO existem. AC-1 é cobrado por **estrutura de contrato** + **timeline vazia** retornando dados de `auditoria` (eventos que JÁ existem: `cliente.criado`, `cliente.mesclado`, `cliente.bloqueado`).

- **AC-1** parcial: timeline lê de `auditoria` filtrado por `tenant_id` + `resource_summary=cliente_id`. Quando módulos Wave A subirem, eles publicam eventos no `auditoria` e a timeline automaticamente os mostra. Sem migration adicional pra esta US.
- **AC-2** medido: teste de performance com 500 linhas de auditoria sintéticas.
- **AC-3** crítico — vai cravado. Tabela `audit_trail.acessos_dados_cliente` nova; gravação síncrona antes da resposta.

## Sequência de tasks

- **T-CLI-031**: nova tabela `acessos_dados_cliente` em `src/infrastructure/audit/` (reusa app existente — não precisa app novo). Campos: id, tenant_id, usuario_id, cliente_id, finalidade, ip_hash, timestamp. RLS pattern v2. Trigger anti-mutation (INV-013 estendida).
- **T-CLI-032**: função `registrar_acesso_dados_cliente(...)` em `services.py` do app audit, INSERT-only.
- **T-CLI-033**: endpoint `GET /api/v1/clientes/{id}/visao-360/` na view. Authz `clientes.visao360` (perfis: admin_tenant, tecnico, rt_signatario, cliente_externo_leitura — todos com escopo próprio quando ABAC entrar Wave A).
- **T-CLI-034**: lógica: registrar acesso → ler eventos de `auditoria` (`tenant_id` + `resource_summary=cliente_id`) ordenando por timestamp DESC → retornar JSON.
- **T-CLI-035**: migration seed `clientes.visao360` na matriz authz para os 4 perfis.
- **T-CLI-036**: testes — 7:
  - `test_visao_360_grava_audit_acesso_INV_013_antes_de_responder`
  - `test_visao_360_retorna_eventos_do_cliente_em_ordem_reversa`
  - `test_visao_360_filtra_eventos_de_outros_clientes` (cross-cliente)
  - `test_visao_360_filtra_eventos_de_outros_tenants` (cross-tenant via RLS)
  - `test_visao_360_perfil_sem_permissao_403` (perfil que nao tem)
  - `test_visao_360_performance_500_eventos_p95_abaixo_1500ms` (smoke)
  - `test_acesso_dados_cliente_eh_imutavel_via_trigger_pg`

## Non-goals

- UI/tela (só backend)
- Eventos de OS/certificados/NF-e/NPS — esses módulos não existem; quando subirem, os eventos aparecerão automaticamente porque a timeline lê de `auditoria` filtrado por resource_summary
- Cache (Wave A — Redis)
- Paginação rica (lista os primeiros 200 eventos; Wave A adiciona cursor)

## Subagentes a consultar

- `tech-lead-saas-regulado`: APROVADO COM RESSALVAS (6, todas endereçadas).
- `advogado-saas-regulado`: APROVADO COM RESSALVAS BLOQUEANTES (5, todas endereçadas).

---

## Endereçamento da revisão (11 ressalvas)

### Tech-lead
- **TL1 (CRÍTICA — filtro de timeline)**: `auditoria` filtrado por `payload_jsonb->>'cliente_id'` (não `resource_summary`). Índice expressional novo `(tenant_id, ((payload_jsonb->>'cliente_id')::uuid), timestamp DESC)`.
- **TL2 (CRÍTICA — app)**: manter no app `audit` existente; tabela `acessos_dados_cliente` com RLS + trigger anti-mutation próprios.
- **TL3 (CRÍTICA — commit-before-response real)**: aceitar limitação do `ATOMIC_REQUESTS=True` no Marco 1. Audit INSERT acontece **antes** do queryset da timeline + antes da serialização do response. Caso extremo "view crasha após INSERT mas antes do response" cai em rollback — Wave A entrega outbox pattern pra cumprir 100%. Documentar débito.
- **TL4 (ALTA — finalidade enum)**: `FinalidadeAcessoCliente` TextChoices + CHECK constraint.
- **TL5 (ALTA — LIMIT 200)**: queryset da timeline limita a 200 itens (paginação cursor entra Wave A).
- **TL6 (MÉDIA — reuso trigger)**: copiar pattern de `authz_decisions_anti_*`.

### Advogado
- **R1 (BLOQUEANTE — payload completo)**: tabela adiciona `categoria_dado_acessado` (enum: pii_identificadora, pii_sensivel, dado_fiscal, dado_regulatorio, metadado) + `recurso` JSONB **sem PII cru** (apenas UUIDs).
- **R2 (BLOQUEANTE — enum finalidades)**: cravar 8 valores: `atendimento_pos_venda`, `preparar_orcamento`, `executar_os`, `emitir_documento_fiscal`, `cobranca_inadimplencia`, `auditoria_interna`, `atendimento_lgpd_titular`, `investigacao_incidente`. Doc em `docs/conformidade/comum/finalidades-acesso-dados.md` (criar).
- **R3 (BLOQUEANTE — quem vê)**: SELECT em `acessos_dados_cliente` filtra por tenant_id (RLS pattern v2). Roldão Aferê NÃO acessa direto — apenas via RAT-15 (Wave B). Como dono Balanças Solution (dogfooding), acessa via login do tenant.
- **R4 (BLOQUEANTE — retenção)**: 5 anos no MVP-1 (linha "audit ações sensíveis" de `retencao-matriz.md`). Crypto-shredding via KMS Wave B.
- **R5 (BLOQUEANTE — art. 18 II)**: documentar como contrato futuro Wave B (`portal-cliente.minha-trilha-de-acesso`). Schema atual suporta.

## Sequência revisada

- **T-CLI-031**: nova tabela `acessos_dados_cliente` em `audit/` com campos completos (R1).
- **T-CLI-032**: enum `FinalidadeAcessoCliente` (TextChoices) + CHECK constraint na migration.
- **T-CLI-033**: `registrar_acesso_dados_cliente()` em `audit/services.py`.
- **T-CLI-034**: índice expressional em `auditoria` `(tenant_id, payload_jsonb->>'cliente_id', timestamp DESC)` — migration nova.
- **T-CLI-035**: endpoint `GET /api/v1/clientes/{id}/visao-360/`. Authz `clientes.visao360`. Aceita query param obrigatório `?finalidade=executar_os` (enum).
- **T-CLI-036**: lógica — registrar acesso → queryset filtrado por `payload_jsonb->>'cliente_id'` + tenant + LIMIT 200 (TL5).
- **T-CLI-037**: doc `docs/conformidade/comum/finalidades-acesso-dados.md` com 8 enum cravados.
- **T-CLI-038**: migration seed `clientes.visao360` para 4 perfis.
- **T-CLI-039**: atualizar `docs/governanca/debitos-ritual.md` com débito Wave A (outbox pattern) + Wave B (titular ver own logs).
- **T-CLI-040**: 7 testes:
  - `test_visao_360_grava_acesso_inv_013_antes_de_responder`
  - `test_visao_360_retorna_eventos_em_ordem_reversa`
  - `test_visao_360_filtra_eventos_de_outros_clientes`
  - `test_visao_360_isolamento_cross_tenant`
  - `test_visao_360_finalidade_obrigatoria_no_query_param`
  - `test_acessos_dados_cliente_imutavel_via_trigger_pg`
  - `test_acessos_recurso_payload_sem_pii_cru`
