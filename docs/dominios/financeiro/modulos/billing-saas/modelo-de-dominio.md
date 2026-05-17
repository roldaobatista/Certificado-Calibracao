---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/modelo-de-dominio.md
  - docs/comum/governanca-modelo-comum.md
---

# Modelo de domínio — Módulo Billing SaaS

> Entidades específicas do módulo de assinaturas. Tenant é entidade transversal (`docs/comum/modelo-de-dominio.md`).

---

## Entidades

### Plano
- **Atributos obrigatórios:** `id`, `codigo` (A/B/C/D), `nome`, `preco_mensal`, `preco_anual`, `moeda`, `ativo`, `limite_usuarios`, `modulos_liberados` (lista), `duracao_trial_dias` (0 = sem trial).
- **Atributos opcionais:** `descricao`, `limite_volume` (ex: nº OS/mês), `ordem_exibicao`.
- **Invariantes:** `INV-038` (plano em uso por assinatura não pode ser excluído, apenas deprecado); `INV-026` (mudança em plano cria nova versão; assinaturas mantêm versão contratada — preço não retroage); constraint `UNIQUE (codigo)` por catálogo.
- **Ciclo de vida:** criada por operador comercial → ativa → descontinuada (não pode ser deletada se existe assinatura vinculada).

### Assinatura
- **Atributos obrigatórios:** `id`, `tenant_id` (`INV-TENANT-001`), `plano_id`, `plano_versao`, `status` (`trial`/`ativa`/`suspensa`/`cancelada`/`trial_expirado`), `data_inicio`, `proximo_vencimento`, `ciclo` (`mensal`/`anual`), `metodo_pagamento_id`.
- **Atributos opcionais:** `trial_termina_em`, `cancelada_em`, `motivo_cancelamento`.
- **Invariantes:** uma única assinatura ATIVA por tenant; mudanças de status registradas em histórico.
- **Ciclo de vida:** criada na contratação → trial (se aplicável) → ativa → (suspensa↔ativa por inadimplência) → cancelada (terminal).

### Fatura SaaS
- **Atributos obrigatórios:** `id`, `tenant_id`, `assinatura_id`, `numero`, `data_emissao`, `data_vencimento`, `valor`, `status` (`aberta`/`paga`/`falhou`/`estornada`), `tentativas_cobranca`.
- **Atributos opcionais:** `cupons_aplicados`, `desconto_total`, `valor_liquido`, `pago_em`, `gateway_transacao_id`, `nfse_id` (ID interno do `FiscalProvider`), `nfse_authorization_code`, `nfse_pdf_url`, `nfse_status` (`pendente`/`emitida`/`rejeitada`/`cancelada`), `nfse_rejection_reason`.
- **Invariantes:** `numero` sequencial por tenant; fatura paga é imutável (correção via estorno + nova fatura); emissão de NFS-e é idempotente (`INV-026`) — uma NFS-e por fatura paga.
- **Ciclo de vida:** gerada por job → tentativa cobrança → paga (dispara emissão NFS-e via `FiscalProvider`) OU falhou (retentativas D+1, D+3, D+7) OU estornada.

### Cupom
- **Atributos obrigatórios:** `id`, `codigo`, `tipo` (`percentual`/`valor_fixo`), `valor`, `validade_inicio`, `validade_fim`, `usos_max`, `usos_atuais`, `recorrencia` (`unica`/`N_ciclos`).
- **Atributos opcionais:** `planos_aplicaveis` (lista), `descricao`.
- **Invariantes:** `codigo` único globalmente; cupom expirado/esgotado não aplicável.

### MetodoPagamento
- **Atributos obrigatórios:** `id`, `tenant_id`, `tipo` (`cartao`/`boleto`/`pix`), `gateway`, `gateway_token` (tokenizado — NUNCA PAN/CVV — `SEC-PCI-001`), `ativo`.
- **Atributos opcionais:** `bandeira`, `ultimos_4`, `nome_titular`, `vencimento_mes`, `vencimento_ano`.
- **Invariantes:** `SEC-PCI-001` — proibido armazenar dados completos de cartão; apenas token do gateway.

### HistoricoAssinatura
- **Atributos:** `id`, `assinatura_id`, `evento` (criação, upgrade, downgrade, suspensão, reativação, cancelamento), `de_plano`, `para_plano`, `de_status`, `para_status`, `quando`, `quem` (user_id ou `system`), `motivo`.
- **Invariantes:** imutável (append-only WORM); toda mudança em Assinatura gera linha aqui.

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| Assinatura | Assinatura, HistoricoAssinatura, MetodoPagamento (ref) | uma ativa por tenant; histórico imutável |
| Fatura SaaS | Fatura SaaS, aplicações de cupom | número sequencial por tenant; paga é imutável |
| Plano | Plano + versões | versionamento; descontinuação preserva contratos vigentes |
| Cupom | Cupom + usos | unicidade global; controle de usos atomicamente |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| Dinheiro | `{valor, moeda}` | Sim |
| Ciclo | `mensal` ou `anual` | Sim |
| StatusAssinatura | enum (trial/ativa/suspensa/cancelada/trial_expirado) | Sim |
| FaixaBloqueio | enum (normal/warning/read_only/suspensa) — derivada de dias em atraso | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `BillingSaas.AssinaturaCriada` | nova assinatura | `{tenant_id, assinatura_id, plano_codigo, status}` | Auth (provisiona acesso), módulos (liberam features) |
| `BillingSaas.FaturaPaga` | cobrança confirmada (recorrência mensal/anual ou avulsa) | `{tenant_id, fatura_id, valor, pago_em, ciclo: mensal\|anual\|avulso}` | Fiscal (dispara `BillingSaas.NFSeEmitida`), Contabilidade, `relatorios-financeiros/` (projeção MRR) — **substitui evento legado `Assinatura.Recorrencia.Faturada`** (alias aceito em Wave A, removido em V2) |
| `BillingSaas.NFSeEmitida` | NFS-e da assinatura SaaS autorizada (US-BIL-008) | `{tenant_id, fatura_id, nfse_id, authorization_code, pdf_url, emitida_em, provider}` | Notificações (email PDF ao tenant), Contabilidade, WORM audit |
| `BillingSaas.NFSeFalhou` | NFS-e rejeitada pela prefeitura ou provider | `{tenant_id, fatura_id, rejection_reason, provider, tentativa_n}` | Operador comercial Aferê (P1), Notificações |
| `BillingSaas.CobrancaFalhou` | gateway recusou | `{tenant_id, fatura_id, motivo, tentativa_n}` | Notificações (email tenant) |
| `BillingSaas.TenantSuspenso` | bloqueio D+15 | `{tenant_id, motivo}` | Auth (corta acesso), todos módulos (entram read-only/blocked) |
| `BillingSaas.TenantReativado` | pagamento regulariza | `{tenant_id}` | Auth, módulos |
| `BillingSaas.PlanoMudou` | upgrade/downgrade | `{tenant_id, de_plano, para_plano, efetivo_em}` | Auth (ajusta limites), módulos (liberam/restringem) |
| `BillingSaas.TrialExpirando` | D-7/D-3/D-1 | `{tenant_id, dias_restantes}` | Notificações (email) |

---

## Comandos (entradas no módulo)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `contratarPlano` | UI tenant | tenant criado, plano ativo | assinatura criada, evento emitido |
| `mudarPlano` | UI tenant ou operador | assinatura ativa | upgrade imediato OU downgrade agendado |
| `cancelarAssinatura` | UI tenant | assinatura ativa | status=cancelada, dados preservados conforme retenção |
| `aplicarCupom` | UI tenant | cupom válido e na janela | desconto agendado pra próxima fatura |
| `gerarFatura` | job cron | assinatura ativa com vencimento hoje | fatura criada, cobrança iniciada |
| `processarWebhookGateway` | gateway externo | assinatura HMAC válida | atualiza status fatura |
| `forcarReativacao` | operador comercial | tenant suspenso | status=ativa (com trilha em histórico) |

---

## Porta ACL utilizada

Este módulo consome **exclusivamente** a porta **`PaymentGatewayProvider`** (porta #11 em `docs/arquitetura/anti-corrosion-layer.md`) para toda interação com gateways externos de pagamento. Nenhum SDK de gateway (Stripe, PagSeguro/PagBank, Mercado Pago) é importado direto pelo código de domínio do módulo.

**Métodos consumidos:**
- `criar_cobranca(valor, metodo, cliente, tenant_id, idempotency_key, descricao)` — `gerarFatura` chama na geração da cobrança
- `tokenizar_cartao(dados_cartao_client_side, tenant_id)` — recebe **apenas o token** já gerado client-side (Stripe Elements / Checkout Transparente); backend nunca toca PAN/CVV
- `receber_webhook(payload, tenant_id)` — `processarWebhookGateway` despacha eventos do gateway
- `consultar_status(payment_id)` — reconciliação quando webhook se perde
- `reembolsar(payment_id, valor, motivo)` — estorno total/parcial gera nova `Fatura SaaS` estornada

**Eventos da porta consumidos pelo domínio:** `Pagamento.Confirmado` → `BillingSaas.FaturaPaga`; `Pagamento.Falhou` → `BillingSaas.CobrancaFalhou`; `Pagamento.Reembolsado` → status `Fatura.estornada`; `Cartao.Tokenizado` → auditoria + persistência do `MetodoPagamento` (apenas token).

**Implementações por onda:** `StripeProvider` (1ª — MVP-1), `PagSeguroProvider`/`PagBankProvider` (2ª — BR), `MercadoPagoProvider` (3ª — alta penetração BR).

**Compliance PCI-DSS (reforça `SEC-PCI-001` em `MetodoPagamento`):**
- Dados completos de cartão (PAN, CVV) **NUNCA** trafegam pelo backend Aferê. Tokenização é **client-side** via SDK do gateway.
- `MetodoPagamento` armazena somente: `gateway`, `gateway_token`, `ultimos_4`, `bandeira`, `vencimento_mes/ano`.
- Esta arquitetura mantém Aferê em escopo PCI-DSS **SAQ-A** (não SAQ-D).

Para emissão de NFS-e da própria assinatura (após `BillingSaas.FaturaPaga`) o módulo também consome a porta `FiscalProvider` (porta #1).

---

## Schema físico

Ver `../schema-banco.md` deste módulo (a criar quando ADR-0001 fechar).

## Diagramas

```mermaid
classDiagram
    Tenant "1" -- "1" Assinatura
    Assinatura "1" -- "*" FaturaSaaS
    Assinatura "*" -- "1" Plano
    Assinatura "1" -- "1..*" MetodoPagamento
    Assinatura "1" -- "*" HistoricoAssinatura
    FaturaSaaS "*" -- "*" Cupom
```

## Como este modelo evolui

- Entidade nova → adicionar + verificar fronteira comum/módulo.
- Atributo novo em Assinatura → migration + versionamento (assinaturas existentes mantêm forma anterior).
- Status novo → ADR explicando transições válidas.
