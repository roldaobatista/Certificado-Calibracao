---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Modelo de Domínio — Módulo Clientes

> Entidades **específicas**. Entidades transversais (Tenant, Usuário) em `docs/comum/modelo-de-dominio.md`.

## Entidades

### Cliente (agregado raiz)
- **Atributos obrigatórios:** `id` (uuid), `tenant_id` (FK), `tipo` (PF/PJ), `nome_ou_razao`, `documento` (CPF ou CNPJ normalizado), `criado_em`, `criado_por`, `lgpd_aceite_em`, `lgpd_aceite_versao`.
- **Atributos opcionais:** `nome_fantasia` (PJ), `ie`, `im`, `rating` (A/B/C/D), `segmento_ids` (array), `limite_credito`, `bloqueio_comercial` (struct: ativo, motivo, em).
- **Invariantes:** `INV-024` (dedup mesmo documento), `INV-TENANT-001/002/003`.
- **Ciclo de vida:** criado → ativo → (opcional bloqueado) → arquivado (soft-delete). NUNCA hard-delete (LGPD requer retenção fiscal + auditoria).

### Endereço
- **Atributos:** `id`, `cliente_id`, `tipo` (principal/cobrança/entrega/unidade), `cep`, `logradouro`, `numero`, `complemento`, `bairro`, `cidade`, `uf`, `pais`.
- **Regra:** cliente PJ pode ter N endereços (unidades/filiais); PF normalmente 1-2.

### Contato
- **Atributos:** `id`, `cliente_id`, `nome`, `cargo` (RT/financeiro/comercial/outro), `telefones[]`, `emails[]`, `canal_preferido` (whatsapp/email/telefone), `consentimento_whatsapp` (bool + data + canal).
- **Regra:** PJ requer pelo menos 1 contato; PF é o próprio cliente como contato implícito.

### Segmento
- **Atributos:** `id`, `tenant_id`, `nome`, `cor`, `criterio` (manual ou auto via regra).
- **Tipo:** value object configurável pelo tenant — tag aplicável a Cliente.

### EventoTimeline
- **Atributos:** `id`, `cliente_id`, `tipo` (OS_criada, certificado_emitido, NF_emitida, NPS_respondido, contato_registrado, bloqueio_aplicado), `payload` (jsonb), `origem_modulo`, `ocorrido_em`.
- **Regra:** append-only; alimentada via consumo de eventos de outros módulos.

## Agregados (DDD)

| Agregado raiz | Inclui | Invariantes |
|---|---|---|
| Cliente | Endereço, Contato | INV-024, INV-TENANT-001/002 |
| Segmento | (standalone) | INV-TENANT-001/002 |
| EventoTimeline | (filho de Cliente) | INV-TENANT-001 |

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| Documento | CPF ou CNPJ normalizado (só dígitos) com algoritmo validado | Sim |
| LimiteCredito | { valor: Decimal, moeda: BRL } | Sim |
| BloqueioComercial | { ativo: bool, motivo: enum, em: datetime, por: user_id } | Sim |

## Máquina de estados — Cliente

```
[criado] → ativo
ativo → bloqueado (motivo: inadimplência | fraude | pedido_cliente)
bloqueado → ativo (desbloqueio manual com justificativa)
ativo → arquivado (LGPD eliminação ou inatividade > 5 anos — V2)
arquivado → (terminal — somente leitura para auditoria fiscal)
```

## Eventos publicados

| Evento | Quando dispara | Payload | Consumidores |
|---|---|---|---|
| `Cliente.Criado` | Cadastro novo salvo | `{cliente_id, tenant_id, tipo, documento}` | crm, operação, financeiro |
| `Cliente.Atualizado` | Mudança de dado relevante | `{cliente_id, campos_alterados}` | crm (re-segmentação) |
| `Cliente.Bloqueado` | Bloqueio comercial ativado | `{cliente_id, motivo, em}` | operação (impede OS), crm (alerta vendedor) |
| `Cliente.Desbloqueado` | Bloqueio removido | `{cliente_id, em, por, justificativa}` | operação |
| `Cliente.Dedup.Mesclado` | Wizard de dedup concluído | `{cliente_master_id, cliente_perdedor_id}` | todos (atualizam FK) |

## Comandos (entradas)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `criarCliente` | UI/API | documento válido + não duplicado | cliente ativo + evento Cliente.Criado |
| `atualizarCliente` | UI/API | cliente existe + tenant_id confere | evento Cliente.Atualizado |
| `bloquearCliente` | UI/API/automação | papel autorizado | estado=bloqueado + evento Cliente.Bloqueado |
| `mesclarClientes` | UI (wizard) | 2 clientes mesmo tenant | 1 master + soft-delete perdedor |
| `importarLote` | UI (upload) | arquivo CSV/XLSX válido | N clientes criados + relatório |

## Schema físico

Tabela `clientes` em schema do tenant (RLS ativa — INV-TENANT-003). Migration em `migrations/clientes/` (a definir pós ADR-0001).

## Como evolui

Entidade nova → checar fronteira com `comum/modelo-de-dominio.md`. Atributo novo → migration + CHANGELOG.
