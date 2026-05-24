---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - .claude/hooks/mass-assignment-check.sh
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0012-autorizacao-unificada.md
---

# Campos protegidos contra mass-assignment

> **Onda 2 plano-v2 (2026-05-23):** auditor QUAL apontou item 121-122 da checklist (mass assignment / usuário podendo alterar `role`, `isAdmin`, `credits`, `verified` via PATCH genérico). Hook `mass-assignment-check.sh` valida que serializers DRF que tocam estas tabelas declaram `read_only_fields` explícito.

## Princípio

`ModelSerializer` do DRF por default expõe TODOS os campos do modelo para escrita. Em PATCH/PUT, um cliente malicioso ou desatento pode mandar `{"tenant_id": "<outro-tenant>"}` ou `{"is_admin": true}` e o serializer aceita.

**Defesa em camadas:**

1. **RLS** (PostgreSQL) impede gravação cross-tenant — INV-TENANT-001..004.
2. **AuthorizationProvider** (ADR-0012) controla quem pode acessar o endpoint.
3. **Esta denylist** força declaração explícita de `read_only_fields` em serializer DRF que toca campo sensível.

## Denylist canônica

Os campos abaixo NUNCA podem aparecer em `fields` writable de `ModelSerializer` (ou equivalente em `Serializer` puro). DEVEM estar em `read_only_fields` ou ser setados via método interno (`perform_create`, signal, default).

### Multi-tenant + identidade

| Campo | Modelo afetado | Razão |
|---|---|---|
| `tenant_id` | Todos | INV-TENANT-001 — cliente NUNCA define tenant. Setado por middleware via `request.tenant_id`. |
| `id` (UUID PK) | Todos | UUID gerado pelo banco (uuid_generate_v4). Cliente não controla ID. |
| `criado_em` / `atualizado_em` / `deletado_em` | Todos | Setado por trigger PG ou `auto_now` Django. |
| `criado_por` / `alterado_por` | Auditáveis | Setado via `request.user` no `perform_create/update`, nunca aceito do payload. |

### Autorização

| Campo | Modelo afetado | Razão |
|---|---|---|
| `is_admin` / `is_superuser` / `is_staff` | `Usuario` | Escalation. Promoção só via `manage.py` ou painel ops com aprovação 2 humanos (Wave A). |
| `perfis_aplicados` / `papeis` / `roles` | `Usuario`, `auth_usuario_perfil` | Atribuição de perfil só via `AuthorizationProvider.atribuir_perfil()` com audit log. |
| `email_verificado` / `email_confirmado` | `Usuario` | Setado por consumer de evento `Email.LinkClicado` (Wave A). |
| `mfa_secret` / `mfa_otp_seed` | `Usuario` | Setado por fluxo MFA dedicado (`/conta/mfa/ativar`), nunca via PATCH genérico. |
| `senha_hash` / `password_hash` | `Usuario` | Setado por `set_password()`. Endpoint dedicado. |

### Financeiro

| Campo | Modelo afetado | Razão |
|---|---|---|
| `saldo` / `creditos` / `balance` | Wallet/Carteira (Wave A) | Mutação só via transação contábil (`debitar`/`creditar` use case). |
| `valor_pago` / `data_pagamento` | `ContasReceber`, `Pagamento` | Setado por consumer de evento `Pagamento.Confirmado`. |
| `comissao_calculada` | `Comissao` (Wave B) | Calculado server-side a partir da regra de comissão; nunca do payload. |

### Calibração / Certificado

| Campo | Modelo afetado | Razão |
|---|---|---|
| `assinatura_a3_*` | `Certificado` (Marco 4) | Setado por fluxo de assinatura A3 (Lacuna). |
| `data_emissao_certificado` | `Certificado` | Setado pelo use case `emitir_certificado`, nunca do payload. |
| `numero_certificado` | `Certificado` | Sequence global (paradigma ADR-0056). |
| `hash_probatorio` | `RegistroTecnico`, `AceiteAtividade` | Hash determinístico computado server-side (ADR-0029). |

### Equipamento (Marco 2)

| Campo | Modelo afetado | Razão |
|---|---|---|
| `cliente_canonico_id` | `Equipamento` | Imutável após criação (INV-EQP-LOC-001 cliente_canonico_imutavel hook). |
| `bloqueado_*` | `Equipamento` | Mutação só via use case `bloquear_equipamento` com motivo + audit. |
| `eh_matriz` | Algum modelo Marco 2 | Definido na criação; alteração via fluxo dedicado. |

### OS (Marco 3)

| Campo | Modelo afetado | Razão |
|---|---|---|
| `numero_os` | `OrdemServico` | Sequence global (ADR-0056). |
| `estado` | `OrdemServico`, `AtividadeDaOS` | Transição de estado só via use cases declarados (`abrir`, `iniciar`, `concluir`, etc — Fase 5). |
| `tenant_snapshot_at_open` | `OrdemServico` | Setado no `OS.Aberta` consumer, nunca do payload. |
| `aceite_atividade_id` | `OrdemServico` | FK gerada no use case `aceitar_atividade`. |

### Auditoria

| Campo | Modelo afetado | Razão |
|---|---|---|
| Qualquer campo de `auditoria` / `audit_trail.*` | Todas | Tabela append-only com trigger PG anti-mutation. Mass-assignment impossível por design, mas listado por completude. |

## Como o hook valida

`.claude/hooks/mass-assignment-check.sh` aplica a:

- `src/**/serializers.py`
- `src/**/serializer.py`
- `src/**/*serializer*.py`

Lógica:

1. Detecta `class XxxSerializer(serializers.ModelSerializer)` ou `class XxxSerializer(ModelSerializer)`.
2. Se a `Meta.model` é uma das classes listadas acima, exige que `Meta.read_only_fields` contenha **todos** os campos sensíveis declarados pra essa classe.
3. Detecta também `fields = "__all__"` em ModelSerializer de tabela sensível — bloqueia sempre.

Allowlist via comentário inline na classe Meta: `# mass-assignment: skip -- <razão ≥10 chars>` (ex: serializer de um endpoint admin interno que precisa setar role manualmente).

## Como adicionar novo campo à denylist

PR neste arquivo + revisão `auditor-seguranca` + (se aplicável) revisão `advogado-saas-regulado`. Adicionar campo sem PR = drift.

## GATEs

- **GATE-MASS-ASSIGN-1:** criar hook `mass-assignment-check.sh` + casos de teste (parte desta Onda 2).
- **GATE-MASS-ASSIGN-2:** retrofit dos serializers existentes (Marco 1 + Marco 2 + Marco 3 Fase 5 nascente) garantindo `read_only_fields` declarado para cada item acima. Auditar quando F-C3 entrar.
