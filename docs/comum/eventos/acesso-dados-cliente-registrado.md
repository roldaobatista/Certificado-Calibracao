---
owner: roldao
revisado-em: 2026-05-22
proximo-review: 2026-08-22
status: draft
diataxis: reference
audiencia: agente
tipo: schema-evento
versao: v1
relacionados:
  - docs/conformidade/comum/isolamento-multi-tenant.md
  - docs/comum/automacoes-catalogo.md
  - docs/faseamento/F-A/tasks-saneamento.md
  - REGRAS-INEGOCIAVEIS.md
---

# Evento `AcessoDadosCliente.Registrado` v1

> **Para que serve:** dispara toda vez que uma query toca dado classificado como "regulado" (PII de cliente final, dados fiscais com identificadores, registros 17025 com nome de signatário). Audit é gravado em `audit_trail.acessos_dados_cliente` (síncrono — INV-013) **e** publicado neste evento para que consumers de governança (alerta de supressão, contagem diária) reajam de forma desacoplada.
>
> **Por que existe (origem):** F-A-M1 da auditoria Onda 2 (2026-05-22). O `audit_trail.acessos_dados_cliente` cobre o gravamento síncrono; faltava o **evento** para a porta de automações (catálogo eventos) — sem ele, consumers ficavam invisíveis no diagrama do bus.
>
> **Versão:** v1 (Onda 2). Mudança breaking exige nova versão (`v2`) + período de coabitação (consumer + publisher).

---

## 1. Quando dispara

Toda escrita em `audit_trail.acessos_dados_cliente` dispara este evento — uma linha em `audit_trail` ↔ um evento. Idempotência em `(causation_id, acao='acesso_dados_cliente.registrado')` garante zero duplicação.

**Não dispara quando:**
- Acesso a dado classe **não-regulado** (configuração, metadados públicos).
- Scan de QR público (`escopo=anonimo` — fica em `audit_trail.eventos` action=`equipamento.qr_scanned`, evento separado).

---

## 2. Schema do payload

```jsonc
{
  "event_id": "<uuid v4>",
  "_schema_version": 1,
  "event_name": "acesso_dados_cliente.registrado",
  "occurred_at": "<ISO 8601 UTC-aware>",
  "correlation_id": "<uuid v4 ou null>",
  "actor": "<usuario_id ou 'sistema'>",
  "payload": {
    "tenant_id": "<uuid>",
    "usuario_id": "<uuid>",
    "recurso": {
      "tabela": "cliente_final",      // string com nome canônico
      "chave": "<uuid da linha lida>", // referência da linha; NUNCA PII bruta
      "campos": ["nome", "cpf"]        // lista de campos PII visualizados; SEM valores
    },
    "finalidade": "execucao_contrato", // base LGPD — enum fechado
    "ip_hash": "<HMAC-SHA256 hex>",    // ip do cliente, salgado por tenant (ver INV-013)
    "key_id_hash_ip": "v1",            // versão da chave de hash em uso (ciclo PII)
    "user_agent_hash": "<HMAC-SHA256 hex>", // opcional; útil pra fingerprinting de fraude
    "registrado_via": "view|api|admin|job" // canal pelo qual o acesso aconteceu
  },
  "causation_id": "<uuid da request original>",
  "tenant_id": "<uuid do tenant>"
}
```

### 2.1 Campos obrigatórios

`event_id`, `_schema_version`, `event_name`, `occurred_at`, `tenant_id`, `payload.usuario_id`, `payload.recurso.tabela`, `payload.recurso.chave`, `payload.finalidade`, `payload.ip_hash`.

### 2.2 Campos proibidos

- **Qualquer PII em texto claro** (CPF, e-mail, telefone, endereço). Hash só.
- **Senha** (mesmo hasheada).
- **Token de sessão** (mesmo hasheado).

### 2.3 Enum `finalidade`

Sincronizado com `docs/conformidade/comum/finalidades-lgpd.md`:

- `execucao_contrato` (art. 7º V)
- `obrigacao_legal` (art. 7º II)
- `legitimo_interesse` (art. 7º IX)
- `consentimento_titular` (art. 7º I)
- `protecao_credito` (art. 7º X)
- `exercicio_direito_titular` (art. 18)
- `auditoria_interna` (decisão arquitetural)
- `auditoria_externa_cgcre_anpd` (auditor RBC visitante / fiscalização)

---

## 3. Consumers conhecidos

| Consumer | Responsabilidade | Latência | Idempotência |
|----------|-----------------|----------|--------------|
| `job_contagem_diaria_acesso_pii` | Agrega contagem diária de acessos por (tenant_id, usuario_id, recurso.tabela). Materializa em tabela analítica `bi.acessos_pii_diario` para dashboards Grafana (alerta de pico anômalo) e relatório LGPD do controlador. | <24h | `(event_id)` |
| `alerta_supressao_acesso_anomalo` | Detecta padrões suspeitos (mesmo usuário lendo >N CPFs em <M minutos; acesso fora de horário comercial; acesso a tenant que não tem acesso histórico recente). Publica `seguranca.alerta_supressao` para o SOC interno. | <60s | `(event_id, regra)` |
| `relatorio_lgpd_titular` | Sob demanda, agrega "todos os acessos a meus dados nos últimos 12 meses" para resposta de art. 18 LGPD do titular. | sob demanda | n/a |

> **Onde declarar:** consumer `job_contagem_diaria_acesso_pii` é declaração de **Onda 1** no `docs/comum/automacoes-catalogo.md`. Este documento apenas **referencia** o nome; não edita o catálogo (regra de fronteira da Onda 2).

---

## 4. Garantias

- **Síncrono na escrita do audit:** evento entra no `bus_outbox` na **mesma transação** que grava `audit_trail.acessos_dados_cliente`. Garantia 3 do `publicar_evento` (`docs/.../event_helpers.py`).
- **Idempotente:** `(causation_id, acao='acesso_dados_cliente.registrado')` UNIQUE no outbox.
- **Tenant-safe:** `tenant_id` no envelope **e** no payload — RLS valida ambos.
- **Sanitização em escrita:** `payload` passa por `sanitizar_payload_audit` antes do publish — proteção contra PII vazada por engano (SEC-SANITIZE-001).

---

## 5. Exemplo

```json
{
  "event_id": "9c4a3f8e-2b1d-4e6a-8f7c-3a9b2d1e4f5c",
  "_schema_version": 1,
  "event_name": "acesso_dados_cliente.registrado",
  "occurred_at": "2026-06-15T14:32:18.124000+00:00",
  "correlation_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "actor": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "payload": {
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "recurso": {
      "tabela": "cliente_final",
      "chave": "a3b1c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d",
      "campos": ["nome", "cpf", "telefone"]
    },
    "finalidade": "execucao_contrato",
    "ip_hash": "b1f4e2c8a9d6...c4e7",
    "key_id_hash_ip": "v1",
    "registrado_via": "api"
  },
  "causation_id": "7d3c1f9a-0b2e-4f6c-8d1a-5b9e3c2a4f6d",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 6. Versionamento

- **v1 (Onda 2):** schema inicial. Campos descritos acima.
- **Mudança breaking** (remoção de campo obrigatório; troca de tipo): novo `_schema_version=2` + coabitação ≥1 release.
- **Mudança não-breaking** (campo novo opcional): mesmo `v1`; consumers ignoram campo desconhecido.

---

## 7. Referências

- INV-013 — log de visualização de dados de cliente (ISO 17025 cl. 4.2)
- `docs/conformidade/comum/isolamento-multi-tenant.md` §8.1
- `docs/conformidade/comum/finalidades-lgpd.md`
- `docs/comum/automacoes-catalogo.md` — onde consumers ficam declarados
- `docs/faseamento/F-A/tasks-saneamento.md` — T-FA-S-04
