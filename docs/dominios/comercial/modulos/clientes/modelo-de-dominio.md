---
owner: Roldão
revisado-em: 2026-05-22
status: stable
modulo: clientes
dominio: comercial
diataxis: reference
---

# Modelo de Domínio — Módulo Clientes

> Entidades **específicas**. Entidades transversais (Tenant, Usuário) em `docs/comum/modelo-de-dominio.md`.

## Entidades

### Cliente (agregado raiz)
- **Atributos obrigatórios:** `id` (uuid), `tenant_id` (FK), `tipo` (TipoPessoa — enum estendido ADR-0039), `nome_ou_razao`, `criado_em`, `criado_por`, `cliente_canonico_id` (INV-CLI-001).
- **Atributos opcionais comuns:** `nome_fantasia` (PJ/MEI), `ie`, `im`, `rating` (A/B/C/D), `segmento_ids` (array — Wave B módulo CRM, ver T-CLI-SAN-05), `limite_credito` (VO `LimiteCredito` — Wave A T-CLI-SAN-04), `bloqueio_comercial` (struct: ativo, motivo, em).
- **Tipo (ADR-0039):** `TipoPessoa = {PF, PJ, MEI, CLIENTE_EXTERIOR}`.
  - PF/PJ/MEI usam `documento` (CPF 11 dígitos ou CNPJ alfanumérico ADR-0017 `^[A-Z0-9]{12}[0-9]{2}$`) + `lgpd_aceite_em` + `lgpd_aceite_versao`.
  - CLIENTE_EXTERIOR usa `tax_id_estrangeiro` + `pais_origem` (ISO 3166-1 alpha-2, ≠ `BR`); aceite contratual base legal "execução de contrato" (LGPD art. 7º V) substitui aceite LGPD.
  - PJ/MEI carregam `regime_tributario` (SIMEI/SIMPLES/PRESUMIDO/REAL/ISENTO_EXTERIOR); MEI sempre SIMEI (CHECK).
- **Atributos LGPD extras:** `aceite_lgpd_ip_hash` (SHA-256 hex 64 chars — T-CLI-SAN-08), `documento_zona_b_anonimizado` (bool default False — ver `reativacao-anonimizacao.md`), `documento_zona_b_anonimizado_em`, `documento_zona_b_anonimizado_motivo`.
- **Atributo opcional PJ:** `cpf_responsavel_legal` (DV validado — T-CLI-SAN-09).
- **Identidade canônica:** `cliente_canonico_id` (INV-CLI-001) — aponta para vencedor vivo da cadeia após mescla; default `=self` na criação.
- **Invariantes:** `INV-024` (dedup mesmo documento), `INV-TENANT-001/002/003`, `INV-CLI-001`, `INV-CLI-CONTATO-001`, `INV-CLI-ENDERECO-001`, `INV-CLI-REATIV-001`, `INV-CLI-SUCESSAO-001..003`.
- **Ciclo de vida:** criado → ativo → (opcional bloqueado_comercial) → (opcional arquivado_por_inatividade | arquivado_por_sucessao | anonimizado_zona_b_c — ver `sucessao-societaria.md` e `reativacao-anonimizacao.md`). NUNCA hard-delete (LGPD + Receita 5 anos + ISO 17025 cl. 8.4).

### Endereço (formalizado Onda 4 C2-CLI)
- **Atributos:** `id` (uuid), `cliente_id` (FK), `tenant_id`, `tipo` (enum `{principal, cobranca, entrega, unidade_filial}`), `cep`, `logradouro`, `numero`, `complemento`, `bairro`, `cidade`, `uf`, `pais` (default `BR`; cliente CLIENTE_EXTERIOR usa ISO 3166-1 alpha-2 do país do endereço).
- **Cardinalidade:** PJ pode ter N endereços `tipo=unidade_filial` (matriz + filiais operacionais). PF normalmente 1-2 (`principal` + `cobranca` se diferentes). CLIENTE_EXTERIOR mínimo 1 endereço com `pais ≠ BR`.
- **Invariante:** **INV-CLI-ENDERECO-001** — todo `Cliente` tem ≥1 `Endereco` com `tipo=principal` (default na criação do cadastro). Tentativa de excluir o único endereço principal bloqueia; reatribuir antes.
- **Cadastro PF MVP:** US-CLI-001 permite criar com endereço principal mínimo (CEP + logradouro + numero + cidade + uf); demais campos opcionais.

### Contato (formalizado Onda 4 C1-CLI)
- **Atributos:** `id` (uuid), `cliente_id` (FK), `tenant_id`, `nome`, `cargo` (enum `{RT_cliente, financeiro, comercial, tecnico_responsavel, outro}`), `telefones[]` (array de E.164 normalizado), `emails[]` (array RFC 5322 normalizado lowercase), `canal_preferido` (enum `{whatsapp, email, telefone}`), `consentimento_whatsapp_em` (datetime NULL), `consentimento_whatsapp_canal` (text NULL — canal de coleta do consentimento), `principal` (bool — exatamente 1 por cliente).
- **Cargo `RT_cliente`:** "Responsável Técnico do cliente" — pessoa que assina pelo lado do cliente em laudos ISO 17025 (cl. 7.8 — laudo deve identificar destinatário técnico). Não confundir com `tecnico_responsavel` (RT do tenant Aferê, ADR-0022).
- **Invariante:** **INV-CLI-CONTATO-001** — todo `Cliente` PJ/MEI tem ≥1 `Contato` com `principal=True`. Quando emissão envolve laudo ISO 17025, exige ≥1 `Contato.cargo=RT_cliente` ativo no cliente — caso contrário, emissão bloqueia com texto canônico "Cliente exige RT cadastrado antes de emitir laudo ISO 17025". Para `Cliente` PF, contato implícito é o próprio cliente; `cargo=outro` permitido.
- **Consentimento WhatsApp (LGPD):** se canal WhatsApp for usado em régua D+30/60/89 (T-CLI-SAN-02), `consentimento_whatsapp_em NOT NULL` + `consentimento_whatsapp_canal NOT NULL` são pré-requisitos; ausência → fallback automático para e-mail.

### Segmento
- **Atributos:** `id`, `tenant_id`, `nome`, `cor`, `criterio` (manual ou auto via regra).
- **Tipo:** value object configurável pelo tenant — tag aplicável a Cliente.

### EventoTimeline (materializada — formalizado Onda 4 A1-CLI / T-CLI-SAN-01)
- **Atributos:** `id` (uuid), `tenant_id`, `cliente_id` (FK), `tipo` (enum `{OS_criada, OS_concluida, certificado_emitido, NF_emitida, NPS_respondido, contato_registrado, bloqueio_aplicado, desbloqueio_aplicado, sucessao_registrada}`), `payload` (jsonb), `origem_modulo` (text — `os`, `certificados`, `nf`, `nps`, `comunicacao-omnichannel`, `clientes`), `ocorrido_em` (datetime).
- **Persistência:** **tabela própria** `evento_timeline_cliente` no schema do tenant — NÃO mais filtro `LIKE/IN` em tabelas de origem. Índice composto `(tenant_id, cliente_id, ocorrido_em DESC)` garante p95 < 1.5s em tenants até 10k clientes × 500 eventos cada.
- **Regra:** append-only; alimentada via consumers idempotentes (IDEMP-001) dos eventos publicados pelos módulos origem. Backfill executado por job dedicado `backfill_evento_timeline` quando módulo Wave A liga o consumer.
- **Vínculo com Visão 360°:** US-CLI-002 AC-2 (p95 < 1.5s) materializada via esta tabela.

### SucessaoSocietaria (formalizado Onda 4 C3-CLI)
- **Atributos:** `id` (uuid), `tenant_id`, `predecessor_cliente_id` (FK Cliente, PROTECT), `sucessor_cliente_id` (FK Cliente, PROTECT), `tipo` (enum `{FUSAO, CISAO, INCORPORACAO, INCORPORACAO_CNPJ_NOVO}`), `data_evento` (date), `fundamento_legal` (text ≥10 chars), `ato_societario_anexo_id` (FK AnexoDocumento NOT NULL), `ato_aprovacao_id` (FK Usuario), `criado_em`, `criado_por`, `observacoes` (text NULL).
- **Cardinalidade:** 1 predecessor pode ter N sucessores (cisão); 1 sucessor pode ter N predecessores (fusão).
- **Invariantes:** **INV-CLI-SUCESSAO-001..003** (ver `sucessao-societaria.md`). Sucessão estritamente intra-tenant; predecessor não-deletável; exige anexo + fundamento legal.

### DocumentoAnonimizadoHistorico (formalizado Onda 4 A2-CLI)
- **Atributos:** `id` (uuid), `tenant_id`, `documento_hash` (bytes — SHA-256 de `documento_original + tenant_salt`), `tipo` (enum `{CPF, CNPJ}`), `cliente_id_original` (FK Cliente — anonimizado Zona B/C), `anonimizado_em` (datetime), `motivo` (text — `lgpd_titular_18_vi` | `lgpd_titular_18_iv` | `lgpd_caducidade`).
- **Regra:** linha imutável criada no momento da anonimização Zona B ou C. Usado para disparar regra `INV-CLI-REATIV-001` no cadastro novo. Hash com `tenant_salt` impede correlação cross-tenant.

## Agregados (DDD)

| Agregado raiz | Inclui | Invariantes |
|---|---|---|
| Cliente | Endereço, Contato | INV-024, INV-CLI-001, INV-CLI-CONTATO-001, INV-CLI-ENDERECO-001, INV-TENANT-001/002 |
| Segmento | (standalone — Wave B módulo CRM, ver T-CLI-SAN-05) | INV-TENANT-001/002 |
| EventoTimeline | (filho de Cliente — materializada T-CLI-SAN-01) | INV-TENANT-001 |
| SucessaoSocietaria | (relaciona predecessor↔sucessor) | INV-CLI-SUCESSAO-001..003 |
| DocumentoAnonimizadoHistorico | (filho lógico de Cliente anonimizado) | INV-CLI-REATIV-001 |

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| Documento | CPF (11 dígitos) ou CNPJ (14 caracteres `[A-Z0-9]{12}[0-9]{2}`, maiúsculo, normalizado sem máscara) com DV validado por Módulo 11. CNPJ alfanumérico a partir de jul/2026 — ver ADR-0017. | Sim |
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
| `Cliente.Atualizado` | Mudança de dado relevante | `{cliente_id, campos_alterados: list[str]}` — campo `campos_alterados` formalizado Onda 4 M1-CLI; lista atributos do agregado que mudaram (declarativo, não delta de valores) | crm (re-segmentação), BI |
| `Cliente.SucessaoSocietariaRegistrada` | Wizard de sucessão concluído (ver `sucessao-societaria.md`) | `{predecessor_ids[], sucessor_id, tipo, data_evento, sucessao_ids[]}` | equipamentos, contas-receber, contas-pagar, certificados, BI |
| `Cliente.CadastroPosAnonimizacaoCriado` | Cadastro novo com documento previamente anonimizado (ver `reativacao-anonimizacao.md`) | `{cliente_id_novo, cliente_id_anonimizado, documento_hash, motivo_anonimizacao_original, justificativa_cadastro_novo, aceite_lgpd_versao, operador_id, ocorrido_em}` | BI (LGPD), auditoria, CGCRE |
| `Cliente.Anonimizado` | Zona A/B/C aplicada (ADR-0021 / ADR-0032 propagação cross-módulo) | `{cliente_id, zona, motivo, anonimizado_em}` | equipamentos, certificados, contas-receber (propagação `ReferenciaPIIAnonimizavel`) |
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
