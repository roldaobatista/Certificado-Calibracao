---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
---

# Integrações entre módulos — eventos + contratos

> **v10 (2026-05-23 — auditoria rodada 2 OS+Cal):** adicionados 9 eventos novos (`Atividade.*` 6, `OS.Faturada`/`OS.Paga`, `Calibracao.LeituraCorrigida`); consumer `metrologia/calibracao` migrou de `OS.Concluida` (legado) para `Atividade.Iniciada`; payloads cross-context obrigatoriamente carregam `correlation_id` + `causation_id` + IDs PII em `*_hash` HMAC-tenant. Total atualizado: ~276 eventos.

> **Pra quê:** módulos do Aferê (`os`, `calibracao`, `fiscal`, `financeiro`, etc.) se comunicam via eventos. Sem contrato versionado, mudança em `os` quebra `calibracao` silenciosamente.

> **v8 (2026-05-17):** catálogo expandido pra cobrir os 48 módulos do PRD v7 (~150+ eventos). Padrão de nomenclatura cravado; campos obrigatórios de envelope cravados. Aliases legados aceitos em Wave A; removidos em V2.
>
> **v9 (2026-05-17 madrugada — pós-auditoria de integrações inter-modulares com 10 agentes):** adicionados ~27 eventos novos cobrindo: (a) **6 eventos de transição regulatória** (ADR-0014) — RT desligado, snapshot acreditação, padrão vencido, ASO vencido, OS pendente revalidação, modo emergencial; (b) **6 eventos pricing composicional** (ADR-0013) — PlanoCriado, PlanoVersionado, ComponentePrecoMudou, AddonContratado, AddonCancelado, LimiteDuroAtingido, UsoMedido; (c) **3 eventos lifecycle tenant** (ADR-0015) — AssinaturaPronta, ProvisioningCompletado, PlanoMudouModulos; (d) **3 eventos consistência operação** (ADR-0016) — ClienteInadimplenteAlertaP1, BomDesatualizadaNotificada, NCNotificacaoCliente; (e) **alterações em 5 eventos existentes** — Fiscal.NFSeEmitida exige certificado_id quando tipo_servico=calibracao, Colaborador.Desligado expande payload, Engenharia.RevisaoAprovada expande payload, Treinamentos.CertificadoVencido ganha consumer agenda, BillingSaas.PlanoMudou ganha campo direcao.

---

## Padrão de nomenclatura (cravado v8)

**Forma canônica:** `[Dominio].[VerboParticipio]` (2 partes — preferencial)

- `Dominio` em PascalCase, corresponde ao módulo dono (ex: `OS`, `Calibracao`, `BillingSaas`, `ContasReceber`, `Estoque`).
- `VerboParticipio` em PascalCase, no particípio passado (ex: `Aberta`, `Concluida`, `Paga`, `Emitido`, `Cancelado`).
- Exemplos: `OS.Aberta`, `Calibracao.Aprovada`, `BillingSaas.FaturaPaga`, `Estoque.MovimentacaoRegistrada`.

**Forma estendida:** `[Dominio].[Agregado].[VerboParticipio]` (3 partes — usar SÓ quando o domínio tem múltiplos agregados ambíguos)

- Exemplos: `Calibracao.Servico.Aprovada` vs `Calibracao.Padroes.CertificadoVencendo` (mesma origem, agregados diferentes).
- Não usar 3 partes "por padrão" — verboso e quebra ferramentas de roteamento simples.

**Proibido em código novo (aceito como alias em Wave A):**
- snake_case no segundo segmento: `Estoque.movimento_registrado` → `Estoque.MovimentacaoRegistrada`
- minúsculo: `documento.criado` → `Documento.Criado`; `acs.usuario.criado` → `AcessoSeguranca.UsuarioCriado`
- sem prefixo de domínio: `OSAberta` → `OS.Aberta`; `Pago` → `ContasReceber.Pago`; `NcAberta` → `Qualidade.NCAberta`

**Migração:** durante Wave A o bus aceita aliases (mapeamento em `events/aliases.py`). Auditor `schema-version` bloqueia *novos* handlers em aliases. Em V2, aliases são removidos.

---

## Envelope obrigatório de evento (cravado v8)

Todo evento publicado **DEVE** carregar este envelope (validado pelo bus antes de aceitar publish):

```json
{
  "event_id": "uuid-v4",
  "event_name": "Dominio.VerboParticipio",
  "_schema_version": "v1",
  "tenant_id": "uuid-v4",
  "occurred_at": "2026-05-17T18:42:00.000Z",
  "correlation_id": "uuid-v4 opcional",
  "causation_id": "uuid-v4 opcional",
  "actor": { "tipo": "user|system|integration", "id": "uuid" },
  "payload": { ... campos específicos do evento ... }
}
```

**Regras:**
- `event_id` (UUID v4): chave de idempotência — handler verifica e ignora duplicata. Gerado no publish.
- `_schema_version` (string `v1`, `v2`, ...): versionamento explícito. Mudança breaking → nova versão; handlers escutam versões específicas.
- `tenant_id` (UUID): obrigatório — bus rejeita publish sem `tenant_id` (defesa multi-tenant). NULL apenas pra eventos do plano-de-controle (raros e marcados).
- `occurred_at` (ISO 8601 UTC com millis): quando o evento aconteceu no domínio (NÃO quando foi publicado — pode haver atraso).
- `correlation_id` / `causation_id`: rastreamento de trilha (event A causou B causou C).
- `actor`: quem causou (usuário, job de sistema, webhook integração).
- `payload`: corpo específico — apenas IDs e campos imutáveis; NÃO duplicar estado mutável de outros módulos (consultar agregado quando precisar).

**Auditor** (pre-commit em `.claude/hooks/` — a implementar): bloqueia publish sem envelope completo; bloqueia handler sem checagem de `event_id`; bloqueia mudança de schema sem `_schema_version` nova.

---

## Princípio

Módulo NÃO chama módulo direto.

- ❌ `calibracao.views.emit` importa `os.models.OS` → acoplamento direto
- ✅ `os.tasks` publica evento `OSConcluida` → handler em `calibracao` cria certificado

---

## Bus de eventos

Implementação (ADR-0007): **outbox pattern com procrastinate**.

```
1. App muda estado no DB + insere linha em `outbox_events` (mesma transação)
2. procrastinate worker lê outbox + dispatcha handlers
3. Handler é idempotente (chave do evento)
4. Outbox marca evento como processado
```

Vantagem: sem broker externo (Kafka, RabbitMQ) no MVP-1; PostgreSQL basta. Pode migrar pra broker quando volume justificar.

---

## Catálogo de eventos (incremental — ampliar quando módulo existir)

### Domínio: OS (revisado pós-ADR-0023 — TEMA-E.1+E.2 auditoria 2026-05-23)

> **Eventos `Atividade*` adicionados pela ADR-0023.** Consumer `metrologia/calibracao` migrou de `OS.Concluida` (modelo antigo) para `AtividadeIniciada filter tipo=calibracao` — calibração técnica é disparada por atividade, não por conclusão da OS toda. Inversão corrige TEMA-E.2 da auditoria.

| Evento | Origem | Schema (campos críticos) | Quem consome |
|--------|--------|--------|--------------|
| `OSAberta` | `os.usecase.abrir_os` | `{tenant_id, os_id, cliente_id_hash, atividades_planejadas: [{atividade_id, tipo, sequencia}], correlation_id, abertura_at}` | `crm`, `mobile.sync` |
| `OSAtribuida` | `os.usecase.atribuir_tecnico` | `{tenant_id, os_id, tecnico_id_hash, atribuicao_at, correlation_id, causation_id}` | `mobile.sync`, `agenda` |
| `OSConcluida` | `os.usecase.concluir_os` (computed when all atividades terminais) | `{tenant_id, os_id, conclusao_at, tipo_predominante, tem_nc, atividades: [{id, tipo, estado_final}], correlation_id}` | `crm`, `financeiro` (faturamento), `mobile.sync`. **NÃO consumido por `metrologia/calibracao`** — calibração consome `AtividadeIniciada` em vez. |
| `OSCancelada` | `os.usecase.cancelar_os` | `{tenant_id, os_id, razao_hash, cancelamento_at, correlation_id}` | `financeiro`, `crm`, `agenda` |
| `OS.Reaberta` | `os.usecase.reabrir_os` | `{tenant_id, os_id: nova, os_origem_id: original, chamado_origem_id?, motivo_hash, garantia_procedente, correlation_id, causation_id: original.correlation_id}` | `caixa-tecnico`, `chamados`, `portal-cliente`, `custeio-real` |
| **`AtividadeAdicionada`** (US-OS-010 — ADR-0023) | `os.usecase.adicionar_atividade` | `{tenant_id, os_id, atividade_id, tipo, sequencia, correlation_id, adicionada_at}` | `mobile.sync` |
| **`AtividadeIniciada`** (ADR-0023) | `os.usecase.iniciar_atividade` | `{tenant_id, os_id, atividade_id, tipo, tecnico_executor_id_hash, iniciada_at, client_event_id, correlation_id, causation_id}` | **`metrologia/calibracao`** (filter `tipo=calibracao` — cria registro técnico), `mobile.sync`, `crm` |
| **`AtividadeConcluida`** (ADR-0023) | `os.usecase.concluir_atividade` | `{tenant_id, os_id, atividade_id, tipo, conclusao_at, tem_nc, correlation_id, causation_id}` (sem `link_modulo_tecnico` — Onda 7A removeu) | `metrologia/certificados` (filter `tipo=calibracao AND tem_nc=False` — libera emissão), `financeiro` (preço por atividade quando Wave B) |
| **`AtividadeNaoConforme`** (ADR-0023 + TEMA-E.6) | `os.usecase.marcar_nc_atividade` | `{tenant_id, os_id, atividade_id, tipo, razao_nao_conformidade_hash, marcada_at, correlation_id, causation_id}` | `qualidade` (encadeia CAPA via `metrologia/calibracao` quando `tipo=calibracao` — quem abre `NaoConformidade.Aberta` é o módulo de calibração, NÃO o auditor de qualidade direto — NOVO-ALTO-12 R2), `crm`, `metrologia/certificados` (bloqueia emissão) |
| **`AtividadeNCResolvida`** (ADR-0023 + TEMA-E.6) | `os.usecase.resolver_nc_atividade` | `{tenant_id, os_id, atividade_id, tipo, resolvido_at, nc_id_hash (FK pra NaoConformidade fechada), eficacia_verificada_por_hash, correlation_id, causation_id}` | `metrologia/certificados` (libera emissão), `qualidade` (consumer informativo) |
| **`AtividadeCancelada`** (ADR-0023 + MED-6 tech-lead) | `os.usecase.cancelar_atividade` | `{tenant_id, os_id, atividade_id, tipo, razao_hash, cancelamento_at, correlation_id}` | `mobile.sync`, `financeiro`, **`metrologia/calibracao`** (filter `tipo=calibracao` — cancela `Calibracao` em andamento; NOVO-MÉD-3 R2) |
| **`OS.Faturada`** (NOVO-ALTO-11 R2) | `financeiro.usecase.emitir_nf_por_os` | `{tenant_id, os_id, nf_id, valor_total, faturado_em, correlation_id, causation_id}` | `crm` (timeline), `bi`, `comissoes` |
| **`OS.Paga`** (NOVO-ALTO-11 R2) | `financeiro.usecase.confirmar_pagamento_os` | `{tenant_id, os_id, valor_pago, pago_em, correlation_id, causation_id}` | `crm`, `bi`, `comissoes` |

### Domínio: Calibração

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `CertificadoEmitido` | `calibracao.usecase.emitir` | `{tenant_id, certificado_id, os_id, hash_pdf, emissao_at, signatario_id}` | `fiscal` (NFS-e opcional), `crm` (timeline), `financeiro` (cobrança) |
| `CertificadoRevisado` | `calibracao.usecase.revisar` | `{tenant_id, certificado_id, versao_anterior, versao_nova, razao}` | `crm`, audit log |
| `CertificadoCancelado` | `calibracao.usecase.cancelar` | `{tenant_id, certificado_id, razao}` | `fiscal` (CC-e se NFS-e foi emitida), audit log |

### Domínio: Fiscal

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `NFSeEmitida` | `fiscal.usecase.emitir_nfse` | `{tenant_id, nfse_id, certificado_id?, valor, emissao_at, plataforma}` | `financeiro` (conta a receber) |
| `NFSeCancelada` | `fiscal.usecase.cancelar_nfse` | `{tenant_id, nfse_id, razao}` | `financeiro` |
| `NFSeFalhou` | `fiscal.usecase.tentar_emitir` | `{tenant_id, certificado_id, erro, tentativas}` | Roldão (alerta SEV-2) |

### Domínio: Financeiro

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `BoletoGerado` | `financeiro.usecase.gerar_boleto` | `{tenant_id, boleto_id, valor, vencimento_at}` | `crm.recalibracao` (lembrete) |
| `Pago` | `financeiro.usecase.confirmar_pagamento` | `{tenant_id, conta_a_receber_id, pagamento_at}` | `crm.timeline` |

### Domínio: CRM

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `LembreteRecalibracaoEnviado` | `crm.scheduler.dispatch_lembrete` | `{tenant_id, cliente_id, certificado_id, canal: whatsapp\|email, enviado_at}` | audit log |

---

## Versionamento de schema

Cada evento tem versão (`v1`, `v2`):
- Campo novo OPCIONAL → mesma versão (backward compatible)
- Campo OBRIGATÓRIO novo OU mudança de tipo → nova versão (`OSConcluidaV2`)
- Handlers escutam versões específicas; transition period suporta ambas

Migrations de schema obrigatórias revisadas pelo subagent `tech-lead-saas-regulado`.

---

## Idempotência

Cada evento tem `event_id` UUID (gerado no publish). Handler verifica `event_id` antes de processar → safe pra reprocessar.

---

## Ordem garantida?

**Por tenant + por entidade:** sim (procrastinate processa em ordem; outbox preserva ordem de insert).
**Cross-entity:** não — handler deve ser tolerante a out-of-order ou consultar estado atualizado do DB.

---

## Dead letter

Handler falha 5x → evento vai pra `dead_letter_events`. Roldão notificado SEV-2. Investigação manual.

---

## Auditor

Auditor Segurança em pre-commit:
- Import direto de model de outro módulo (e.g., `from os.models import OS` em `calibracao/`) → CONCERN
- Handler sem chave de idempotência → FAIL
- Mudança de schema sem nova versão → FAIL (auditor compara `EventSchema` com versão anterior)

---

## Referências

- ADR-0007 (camada domínio + outbox)
- `idempotencia.md`
- `retry.md`
- `governanca-modelo-comum.md` (fronteira comum vs módulo)
- `arquitetura/anti-corrosion-layer.md` (porta Queue)

---

## Catálogo completo v8 (48 módulos)

> **Como ler:** evento listado pelo nome canônico (após padronização v8); coluna **Aliases** mostra nomes legados aceitos em Wave A. Origem é o módulo dono (publisher único); consumers são todos os módulos que escutam. Schema completo (payload) vive em `docs/dominios/<dominio>/modulos/<modulo>/modelo-de-dominio.md`.

### Domínio: COMERCIAL

#### Módulo `clientes`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Cliente.Criado` | clientes | crm, operacao/os, financeiro/contas-receber | — |
| `Cliente.Atualizado` | clientes | crm (re-segmentação) | — |
| `Cliente.Bloqueado` | clientes | operacao/os (impede OS), crm, comercial/contratos | — |
| `Cliente.Desbloqueado` | clientes | operacao/os, comercial/contratos | — |
| `Cliente.Dedup.Mesclado` | clientes | todos (atualizam FK) | — |

#### Módulo `crm`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Lead.Criado` | crm | crm UI | — |
| `Lead.Convertido` | crm | clientes (timeline) | — |
| `Oportunidade.MovidaEtapa` | crm | financeiro (forecast) | — |
| `Oportunidade.Ganha` | crm | financeiro, mapa-do-dono | — |
| `Oportunidade.Perdida` | crm | mapa-do-dono | — |
| `NPS.Respondido` | crm | clientes (timeline), automacoes-bpm | — |
| `Automacao.Executada` | crm | auditoria, mapa-do-dono | — |
| `Tarefa.Criada` | crm | UI vendedor | — |

#### Módulo `marketplace`

> **Fronteira com `portal-cliente`:** marketplace é vitrine pública + carrinho + captação de leads; **não tem autenticação própria** (delegada ao `portal-cliente`) nem visão consolidada do cliente. Após login no marketplace, redireciona pro portal. Solicitações originadas no marketplace são entregues ao portal via evento `Marketplace.SolicitacaoEnviada`. Ver PRDs de ambos os módulos.

| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Marketplace.SolicitacaoEnviada` | marketplace | crm (cria lead), orcamentos (cria rascunho), **portal-cliente** (cria `SolicitacaoMarketplaceRecebida` na visão 360° — US-POR-012) | — |
| `Marketplace.ClienteLogou` | marketplace | auditoria, **portal-cliente** (reaproveita `SessaoPortal` — autenticação única — e devolve ack pro marketplace fazer redirect) | — |
| `Marketplace.AssinouRecorrente` | marketplace | contratos, agenda | — |
| `Marketplace.PagamentoConfirmado` | marketplace | **financeiro/contas-receber** (cria título já liquidado + emite `ContasReceber.Pago`), orcamentos (marca pago) | — |
| `Marketplace.ConversaoRegistrada` | marketplace | analytics | — |

#### Módulo `orcamentos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Orcamento.Enviado` | orcamentos | crm | — |
| `Orcamento.Lido` | orcamentos | crm | — |
| `Orcamento.Aprovado` | orcamentos | operacao/os (cria OS rascunho), financeiro, crm | `Comercial.OrcamentoAprovado` |
| `Orcamento.Recusado` | orcamentos | crm | — |
| `Orcamento.Expirado` | orcamentos | crm | — |
| `Orcamento.Convertido` | orcamentos | crm | `Orcamentos.OrcamentoFechado` (alias) |
| `Orcamento.Enviado` (versão portal) | orcamentos | comercial/portal-cliente | `Comercial.OrcamentoEnviado` |

#### Módulo `contratos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Contrato.Criado` | contratos | financeiro (forecast MRR), crm | — |
| `Contrato.PreOSGerada` | contratos | operacao/os | — |
| `Contrato.OSConfirmada` | contratos | operacao/os | — |
| `Contrato.VigenciaAVencer` | contratos | crm | — |
| `Contrato.Renovado` | contratos | financeiro/contas-receber, billing-saas (se SaaS) | `ContratoRenovado` |
| `Contrato.Suspenso` | contratos | financeiro | — |
| `Contrato.Encerrado` | contratos | financeiro, crm | — |
| `Contrato.Aditivado` | contratos | financeiro | — |

#### Módulo `sla-contratual`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `SLA.Cronometrando` | sla-contratual | UI atendimento | — |
| `SLA.Pausado` / `SLA.Despausado` | sla-contratual | UI, auditoria | — |
| `SLA.AlertaPreventivo` | sla-contratual | comunicacao-omnichannel, escalonamento | — |
| `SLA.Cumprido` | sla-contratual | **financeiro/contas-receber** (bonificação) | — |
| `SLA.Estourou` | sla-contratual | **financeiro/contas-receber** (penalidade), diretoria | — |
| `SLA.PenalidadeCalculada` | sla-contratual | **financeiro/contas-receber** (cria desconto/multa) | — |
| `SLA.BonificacaoCalculada` | sla-contratual | **financeiro/contas-receber** (cria nota de crédito) | — |
| `SLA.RelatorioEmitido` | sla-contratual | comunicacao-omnichannel, auditoria | — |

#### Módulo `comunicacao-omnichannel`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Comunicacao.MensagemRecebida` | comunicacao-omnichannel | distribuição, regras | — |
| `Comunicacao.MensagemEnviada` | comunicacao-omnichannel | auditoria | — |
| `Comunicacao.StatusMensagemAtualizado` | comunicacao-omnichannel | UI | — |
| `Comunicacao.ConsentimentoRegistrado` | comunicacao-omnichannel | LGPD, CRM | — |
| `Comunicacao.OptOutAplicado` | comunicacao-omnichannel | automacoes | — |
| `Comunicacao.ConvertidoEmChamado` | comunicacao-omnichannel | chamados | — |
| `Comunicacao.ConvertidoEmLead` | comunicacao-omnichannel | crm | — |
| `Comunicacao.TemplateRejeitado` | comunicacao-omnichannel | gerente | — |

#### Módulo `portal-cliente`

> **Fronteira com `marketplace`:** portal-cliente é dono da **área restrita autenticada** (autenticação única + visão 360°: OS, orçamentos, faturas, certificados, contratos, mensagens, preferências, edição cadastral). Consome `Marketplace.SolicitacaoEnviada` para integrar solicitações de vitrine ao 360° do cliente (US-POR-012) e consome `Marketplace.ClienteLogou` para confirmar/reaproveitar sessão e disparar redirect.

| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Portal.UsuarioRegistrado` | portal-cliente | auditoria, notificações | — |
| `Portal.LoginRealizado` / `Portal.LoginBloqueado` | portal-cliente | auditoria, segurança | — |
| `Comercial.OrcamentoAprovadoPeloCliente` | portal-cliente | operacao/os, financeiro, auditoria WORM | — |
| `Comercial.OrcamentoRejeitadoPeloCliente` | portal-cliente | comercial, auditoria | — |
| `Portal.MensagemCriada` | portal-cliente | chamados, notificações | — |
| `Portal.SolicitacaoCadastralCriada` | portal-cliente | atendente (fila) | — |
| `Portal.SegundaViaGerada` | portal-cliente | financeiro, auditoria | — |
| `Portal.CertificadoBaixado` | portal-cliente | auditoria (ISO 17025) | — |

**Eventos consumidos (handoff Marketplace → Portal):**
| Evento esperado | Origem | Uso aqui |
|---|---|---|
| `Marketplace.SolicitacaoEnviada` | marketplace | cria `SolicitacaoMarketplaceRecebida` (índice da visão 360°), exibe no dashboard; quando `Orcamento.Enviado` chegar, vincula `orcamento_id` |
| `Marketplace.ClienteLogou` | marketplace | reaproveita `SessaoPortal` existente (autenticação única) + devolve ack pro marketplace fazer redirect pra área restrita |

#### Módulo `precificacao`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Precificacao.RegraPublicada` | precificacao | orcamentos, marketplace, contratos | — |
| `Precificacao.TabelaPublicada` | precificacao | orcamentos, marketplace, contratos | — |
| `Precificacao.AprovacaoSolicitada` | precificacao | notificações | — |
| `Precificacao.AprovacaoDecidida` | precificacao | orcamentos, notificações | — |
| `Precificacao.OrcamentoAbaixoMargemMinima` | precificacao | notificações, analytics | — |
| `Precificacao.PrecoMinimoVioladoTentativa` | precificacao | analytics | — |

---

### Domínio: OPERAÇÃO

#### Módulo `os` (revisado pós-ADR-0023 — TEMA-E.1+E.2 auditoria 2026-05-23)
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `OS.Aberta` | os | crm, mobile.sync, comunicacao-omnichannel | `OSAberta` (legado) |
| `OS.Atribuida` | os | mobile.sync, agenda | `OSAtribuida` |
| `OS.Concluida` | os | crm, financeiro/contas-receber, bi, comissoes, custeio-real, caixa-tecnico, fiscal | `OSConcluida`, `Operacao.OSEncerrada`. **REMOVIDO consumer `metrologia/calibracao`** — calibração consome `Atividade.Iniciada` agora. |
| `OS.Cancelada` | os | financeiro, crm, agenda | `OSCancelada` |
| `OS.Reaberta` | os | custeio-real, chamados, portal-cliente, caixa-tecnico | `Operacao.OSReaberta` |
| **`Atividade.Adicionada`** (ADR-0023) | os | mobile.sync | — |
| **`Atividade.Iniciada`** (ADR-0023) | os | **metrologia/calibracao** (filter tipo=calibracao), mobile.sync, crm | — |
| **`Atividade.Concluida`** (ADR-0023) | os | metrologia/certificados (filter tipo=calibracao AND tem_nc=False), financeiro | — |
| **`Atividade.NaoConforme`** (ADR-0023) | os | qualidade (CAPA), crm, metrologia/certificados (bloqueia emissão) | — |
| **`Atividade.NCResolvida`** (ADR-0023 + TEMA-E.6) | os | metrologia/certificados (libera emissão), qualidade | — |
| **`Atividade.Cancelada`** (ADR-0023 + MED-6) | os | mobile.sync, financeiro | — |

#### Módulo `chamados`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Chamado.Aberto` | chamados | crm, comunicacao-omnichannel, base-conhecimento | `ChamadoAberto`, `Chamados.ChamadoAberto` |
| `Chamado.Triado` | chamados | observabilidade | `ChamadoTriado` |
| `Chamado.ConvertidoEmOS` | chamados | operacao/os | `ChamadoConvertidoEmOS` |
| `Chamado.Fechado` | chamados | crm, comunicacao-omnichannel | `ChamadoFechado` |
| `Chamado.SLAEscalado` | chamados | observabilidade | `ChamadoSLAEscalado` |

#### Módulo `agenda`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Agenda.SlotAlocado` | agenda | os, crm, capacity-planning | `AgendaSlotAlocado` |
| `Agenda.Reagendada` | agenda | os, crm, capacity-planning | `AgendaReagendada` |
| `Agenda.Bloqueada` | agenda | rh, observabilidade, capacity-planning | `AgendaBloqueada` |
| `Agenda.JornadaUMCViolada` | agenda | auditor, dpo | `JornadaUMCViolada` |
| `Agenda.EventoCriado` / `Alterado` / `Cancelado` | agenda | capacity-planning | — |
| `Agenda.SugestaoAplicada` | agenda | capacity-planning, bi | — |

#### Módulo `capacity-planning-operacional`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `CapacityPlanning.GargaloDetectado` | capacity-planning | notificações, métricas | — |
| `CapacityPlanning.SobrecargaDetectada` | capacity-planning | notificações | — |
| `CapacityPlanning.DistribuicaoSugerida` | capacity-planning | **operacao/agenda** (exibe sugestão), os | — |
| `CapacityPlanning.SimulacaoAplicada` | capacity-planning | agenda | — |
| `CapacityPlanning.IndicacaoContratacao` | capacity-planning | rh/colaboradores | — |

#### Módulo `garantia`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Garantia.Aberta` | garantia | os, financeiro | — |
| `Garantia.Analisada` | garantia | financeiro | — |
| `Garantia.Procedente` / `Improcedente` / `Parcial` | garantia | financeiro, reincidência | — |
| `GarantiaFornecedor.Aberta` | garantia | fornecedores, estoque | — |
| `GarantiaFornecedor.Retornada` | garantia | financeiro | — |

#### Módulo `app-tecnico`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `AppTecnico.CheckInRealizado` | app-tecnico | os, agenda | — |
| `AppTecnico.OSExecutadaCampo` | app-tecnico | os, faturamento, qualidade | — |
| `AppTecnico.PecaConsumida` | app-tecnico | estoque | — |
| `AppTecnico.PecaSolicitada` | app-tecnico | estoque, coordenador | — |
| `AppTecnico.DespesaLancada` | app-tecnico | caixa-tecnico, financeiro | — |
| `AppTecnico.AdiantamentoSolicitado` | app-tecnico | caixa-tecnico | — |
| `AppTecnico.ConflitoSyncEscalado` | app-tecnico | coordenador | — |

#### Módulo `base-conhecimento`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `BaseConhecimento.ArtigoPublicado` | base-conhecimento | chamados, os, treinamentos | — |
| `BaseConhecimento.ArtigoArquivado` | base-conhecimento | chamados, os | — |
| `BaseConhecimento.SugestaoExibida` / `SugestaoAplicada` | base-conhecimento | métricas | — |

#### Módulo `projetos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Projeto.Aberto` | projetos | crm, financeiro | — |
| `Projeto.Concluido` | projetos | financeiro, comercial | — |
| `Etapa.Concluida` | projetos | financeiro (se marco) | — |
| `Marco.Atingido` | projetos | financeiro | — |
| `Aditivo.Aprovado` | projetos | financeiro, crm, comercial | — |
| `Risco.Materializado` | projetos | governança/qa | — |

---

### Domínio: METROLOGIA

#### Módulo `calibracao`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Calibracao.Recepcionada` | calibracao | notificação | — |
| `Calibracao.Configurada` | calibracao | **metrologia/certificados** (prepara template) | — |
| `Calibracao.LeiturasFinalizadas` | calibracao | cálculo interno | — |
| `Calibracao.IncertezaCalculada` | calibracao | revisão | — |
| `Calibracao.RevisadaPrimeira` | calibracao | conferência 2 | — |
| `Calibracao.SegundaConferenciaAprovada` | calibracao | certificados | — |
| `Calibracao.Aprovada` | calibracao | certificados, cliente, auditoria, comunicacao-omnichannel | `Calibracao.CertificadoEmitido` |
| `Calibracao.Rejeitada` | calibracao | qualidade (abre NaoConformidade interna), certificados (bloqueia emissão); **NÃO consumido por OS** — encadeamento OS↔Cal é via `Atividade.NaoConforme` (NOVO-ALTO-13 R2: inversão lógica corrigida) | — |
| `Calibracao.LeituraCorrigida` (NOVO-ALTO-16 R2 — cl. 7.5 rasura digital) | calibracao | auditoria (audit WORM via EventoDeCalibracao + INV-CAL-AUD-001), qualidade (monitora taxa de correção como indicador de competência do executor) | — |
| `Calibracao.VencendoEm30d` | calibracao | crm (OP1), comunicacao, portal-cliente | `Metrologia.CalibracaoVencendo` |
| `Padroes.CertificadoVencendo` | calibracao (subdomínio padrões) | **rh/qualidade** (NC preventiva), RT signatário, **certificados** (bloqueia emissão dependente) | — |
| `Padroes.VerificacaoIntermediariaReprovada` | calibracao | rh/qualidade (NC automática), RT | — |
| `Proficiencia.EscoreInsatisfatorio` | calibracao | rh/qualidade (NC), RT | — |

#### Módulo `certificados`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Certificados.Emitido` | certificados | auditoria, notificação, portal-cliente | `Metrologia.CertificadoEmitido` |
| `Certificados.Assinado` | certificados | envio, auditoria | — |
| `Certificados.Enviado` | certificados | notificação | — |
| `Certificados.Baixado` | certificados | auditoria LGPD | — |
| `Certificados.Reemitido` | certificados | cliente, auditoria | — |
| `Certificados.Cancelado` | certificados | auditoria | — |
| `Certificados.VerificacaoPublica` | certificados | métricas | — |
| `Certificados.NCAberta` | certificados | qualidade | — |

#### Módulo `licencas-acreditacoes`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Licencas.DocumentoCadastrado` | licencas-acreditacoes | auditoria, notificação | — |
| `Licencas.DocumentoRenovado` | licencas-acreditacoes | notificação, bloqueio (resolve) | — |
| `Licencas.AlertaDisparado` | licencas-acreditacoes | notificação | — |
| `Licencas.DocumentoVencido` | licencas-acreditacoes | bloqueio, auditoria | — |
| `Licencas.BloqueioAtivado` | licencas-acreditacoes | certificados, calibracao | — |
| `Licencas.ModoEmergencialAcionado` | licencas-acreditacoes | auditoria, watchdog | — |

---

### Domínio: FINANCEIRO

#### Módulo `contas-receber`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `ContasReceber.TituloEmitido` | contas-receber | comercial (timeline), portal-cliente | `TituloEmitido` |
| `ContasReceber.BoletoGerado` | contas-receber | crm (lembrete) | `BoletoGerado` |
| `ContasReceber.Pago` | contas-receber | comercial, comissões, fiscal (NFS-e opcional), crm | `Pago` |
| `ContasReceber.TituloVencido` | contas-receber | régua cobrança (Wave B), portal-cliente, crm | `TituloVencido` |
| `ContasReceber.TituloCancelado` | contas-receber | comissões (estorno) | `TituloCancelado` |
| `ContasReceber.DescontoAplicado` | contas-receber | auditoria, bi | — |

#### Módulo `contas-pagar`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `ContasPagar.LancamentoCriado` | contas-pagar | auditoria | `LancamentoCriado` |
| `ContasPagar.LancamentoAprovado` | contas-pagar | auditoria | `LancamentoAprovado` |
| `ContasPagar.Pago` | contas-pagar | despesas (`Despesa.Reembolsada`), auditoria | `Pagamento` |
| `ContasPagar.LancamentoCancelado` | contas-pagar | auditoria | `LancamentoCancelado` |

#### Módulo `fiscal`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Fiscal.NFSeEmitida` | fiscal | comercial (timeline), contas-receber (anexa fatura) | `NFSeEmitida` |
| `Fiscal.NFeEmitida` | fiscal (V2) | idem | — |
| `Fiscal.NFCancelada` | fiscal | auditoria | — |
| `Fiscal.CCeEmitida` | fiscal | auditoria | — |
| `Fiscal.NumeracaoInutilizada` | fiscal | auditoria | — |
| `Fiscal.ContingenciaAtivada` / `ContingenciaEncerrada` | fiscal | observabilidade | — |
| `Fiscal.RegimeAlterado` | fiscal | precificacao (invalida cache) | — |

#### Módulo `billing-saas`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `BillingSaas.AssinaturaCriada` | billing-saas | auth, módulos (liberam features) | — |
| `BillingSaas.FaturaPaga` | billing-saas | fiscal (dispara NFS-e), contabilidade, relatorios-financeiros (MRR) | `Assinatura.Recorrencia.Faturada` |
| `BillingSaas.NFSeEmitida` | billing-saas | notificações, contabilidade, WORM audit | — |
| `BillingSaas.NFSeFalhou` | billing-saas | operador comercial Aferê (P1) | — |
| `BillingSaas.CobrancaFalhou` | billing-saas | notificações | — |
| `BillingSaas.TenantSuspenso` / `Reativado` | billing-saas | auth, todos os módulos | — |
| `BillingSaas.PlanoMudou` | billing-saas | auth, módulos | — |
| `BillingSaas.TrialExpirando` | billing-saas | notificações | — |

#### Módulo `comissoes`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Comissoes.ComissaoPrevista` | comissoes | financeiro, vendedor | `ComissaoPrevista` |
| `Comissoes.ComissaoDevida` | comissoes | financeiro | `ComissaoDevida` |
| `Comissoes.ComissaoPaga` | comissoes | financeiro, vendedor | `ComissaoPaga` |
| `Comissoes.ComissaoEstornada` | comissoes | auditoria | `ComissaoEstornada` |
| `Comissoes.ComissaoCalculada` | comissoes | custeio-real | — |

#### Módulo `caixa-tecnico`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `CaixaTecnico.AdiantamentoSolicitado` | caixa-tecnico | aprovador | `AdiantamentoSolicitado` |
| `CaixaTecnico.AdiantamentoAprovado` | caixa-tecnico | financeiro | `AdiantamentoAprovado` |
| `CaixaTecnico.DespesaLancada` | caixa-tecnico | aprovador | `DespesaLancada` |
| `CaixaTecnico.DespesaValidada` | caixa-tecnico | custeio-real (Wave B) | `DespesaValidada` |
| `CaixaTecnico.DespesaRejeitada` | caixa-tecnico | técnico | — |
| `CaixaTecnico.DespesaAprovada` | caixa-tecnico | custeio-real | — |
| `CaixaTecnico.PrestacaoFechada` | caixa-tecnico | financeiro | `PrestacaoFechada` |

#### Módulo `despesas`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Despesa.Criada` | despesas | notificações, auditoria | — |
| `Despesa.Aprovada` | despesas | contas-pagar, caixa-tecnico, relatorios-financeiros | — |
| `Despesa.Rejeitada` | despesas | notificações | — |
| `Despesa.Reembolsada` | despesas | relatorios-financeiros | — |
| `Despesa.Compensada` | despesas | caixa-tecnico, relatorios-financeiros | — |

#### Módulo `custeio-real`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `CusteioReal.CustoApurado` | custeio-real | dashboards, notificações | — |
| `CusteioReal.AlertaDeficitarioCriado` | custeio-real | notificações | — |
| `CusteioReal.CustoReapurado` | custeio-real | auditoria, dashboards | — |
| `CusteioReal.CustoAtualizado` | custeio-real | precificacao (invalida cache) | — |

#### Módulo `relatorios-financeiros`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Conciliacao.Concluida` | relatorios-financeiros | auditoria, notificações | — |
| `RelatorioAgendado.Disparado` | relatorios-financeiros | notificações | — |

---

### Domínio: RH-FROTA-QUALIDADE

#### Módulo `colaboradores`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Colaborador.Cadastrado` | colaboradores | operacao/agenda | `ColaboradorCadastrado` |
| `Colaborador.PapelAtribuido` / `PapelRevogado` | colaboradores | acesso-seguranca (RBAC) | — |
| `Colaborador.HabilidadeAtualizada` | colaboradores | operacao (re-elegibilidade) | — |
| `Colaborador.Desligado` | colaboradores | operacao, financeiro/comissoes | `ColaboradorDesligado` |
| `Colaboradores.AusenciaRegistrada` | colaboradores | capacity-planning, agenda | — |
| `Colaboradores.EscalaAtualizada` | colaboradores | capacity-planning | — |

#### Módulo `frota`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Frota.VeiculoCadastrado` | frota | operacao | `VeiculoCadastrado` |
| `Frota.JornadaIniciada` / `JornadaEncerrada` | frota | rh (INV-020), auditoria | — |
| `Frota.PausaRegistrada` | frota | rh | — |
| `Frota.Inv020Violado` | frota | governanca (P0), dpo | `Inv020Violado` |
| `Frota.ChecklistCompletado` | frota | operacao | — |
| `Frota.ManutencaoVencida` | frota | operacao, almoxarife | — |

#### Módulo `qualidade`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Qualidade.NCAberta` | qualidade | responsável, dono | `NcAberta` |
| `Qualidade.NCBloqueouEmissao` | qualidade | responsável, dono (P0) | `NcBloqueouEmissao` |
| `Qualidade.NCFechada` | qualidade | auditoria | `NcFechada` |
| `Qualidade.NCReabertaPorPendencia` | qualidade | responsável | `NcReabertaPorPendencia` |
| `Qualidade.EficaciaVencida` | qualidade | RQ | `EficaciaVencida` |
| `Qualidade.NPSRespondido` | qualidade | crm | `NpsRespondido` |
| `Qualidade.ReclamacaoRegistrada` | qualidade | atendimento | `ReclamacaoRegistrada` |
| `Qualidade.RiscoIdentificado` | qualidade | governanca | `RiscoIdentificado` |

#### Módulo `treinamentos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Treinamentos.EventoConcluido` | treinamentos | colaboradores, RH | — |
| `Treinamentos.CertificadoEmitido` | treinamentos | seguranca-trabalho, qualidade, operacao | — |
| `Treinamentos.CertificadoVencendo` | treinamentos | RH, colaborador | — |
| `Treinamentos.CertificadoVencido` | treinamentos | operacao (bloqueio), qualidade | — |
| `Treinamentos.BypassExecutado` | treinamentos | governanca, auditoria | — |
| `Treinamentos.TrilhaVersionada` | treinamentos | operacao, qualidade, base-conhecimento | — |

#### Módulo `seguranca-trabalho`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `SST.EPIEntregue` | seguranca-trabalho | colaboradores, financeiro (custo) | — |
| `SST.ASOVencendo` | seguranca-trabalho | colaboradores, notificações | — |
| `SST.TreinamentoSegVencendo` | seguranca-trabalho | treinamentos, operacao/agenda | — |
| `SST.AcidenteRegistrado` | seguranca-trabalho | operacao, qualidade | — |
| `SST.OSBloqueadaSemChecklist` | seguranca-trabalho | operacao, governanca | — |
| `SST.TecnicoBloqueadoSemNR` | seguranca-trabalho | operacao/agenda | — |

#### Módulo `auditoria-externa`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `AuditoriaExterna.AuditoriaPlanejada` | auditoria-externa | calendário, notificações | — |
| `AuditoriaExterna.NCMaiorRegistrada` | auditoria-externa | diretoria (P0), qualidade | — |
| `AuditoriaExterna.NCFechada` | auditoria-externa | histórico, qualidade | — |
| `AuditoriaExterna.DocExigidoVencido` | auditoria-externa | RQ | — |
| `AuditoriaExterna.SemaforoMudou` | auditoria-externa | diretoria | — |
| `AuditoriaExterna.DrillConcluido` | auditoria-externa | RQ | — |

---

### Domínio: SUPORTE-PLATAFORMA

#### Módulo `acesso-seguranca`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `AcessoSeguranca.UsuarioCriado` | acesso-seguranca | onboarding, email | `acs.usuario.criado` |
| `AcessoSeguranca.UsuarioDesativado` | acesso-seguranca | sessões (encerra), notificações | `acs.usuario.desativado` |
| `AcessoSeguranca.LoginSucesso` | acesso-seguranca | métricas, alerta localização | `acs.login.sucesso` |
| `AcessoSeguranca.LoginFalha` | acesso-seguranca | rate-limit, alerta burst | `acs.login.falha` |
| `AcessoSeguranca.LoginBloqueado` | acesso-seguranca | segurança | `acs.login.bloqueado` |
| `AcessoSeguranca.SessaoEncerrada` | acesso-seguranca | auditoria | `acs.sessao.encerrada` |
| `AcessoSeguranca.SessaoRepudiada` | acesso-seguranca | segurança (P1), admin | `acs.sessao.repudiada` |
| `AcessoSeguranca.PermissaoAlterada` | acesso-seguranca | caches RBAC | `acs.permissao.alterada` |
| `AcessoSeguranca.AcessoNegado` | acesso-seguranca | métricas, alerta anormal | `acs.acesso.negado` |
| `AcessoSeguranca.RegistroAlterado` | acesso-seguranca | auditoria, indexador busca | `acs.registro.alterado` |
| `AcessoSeguranca.ConsentimentoAceito` | acesso-seguranca | módulos sensíveis (base legal) | `acs.consentimento.aceito` |
| `AcessoSeguranca.ConsentimentoRevogado` | acesso-seguranca | marketing, parceiros | `acs.consentimento.revogado` |
| `AcessoSeguranca.LGPDSolicitacaoAberta` | acesso-seguranca | workflow LGPD | `acs.lgpd.solicitacao_aberta` |
| `AcessoSeguranca.LGPDSolicitacaoConcluida` | acesso-seguranca | notificação titular | `acs.lgpd.solicitacao_concluida` |

#### Módulo `automacoes-bpm`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `BPM.PendenciaCriada` | automacoes-bpm | crm, notificações | — |
| `BPM.AprovacaoConcedida` / `AprovacaoRejeitada` | automacoes-bpm | módulo origem (Orçamentos, OS, etc.) | — |
| `BPM.SlaEstourado` | automacoes-bpm | escalonamento, observabilidade | — |
| `BPM.InstanciaConcluida` | automacoes-bpm | **roteamento por `entidade_origem_tipo`**: orcamentos, contratos, os, chamados, engenharia-tecnica, despesas, precificacao, licencas-acreditacoes | — |
| `BPM.RegraExecutada` | automacoes-bpm | observabilidade | — |
| `BPM.AlertaDisparado` | automacoes-bpm | crm, log | — |

#### Módulo `configuracoes-sistema`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Config.EmpresaAtualizada` | configuracoes-sistema | módulos fiscais, PDFs | — |
| `Config.SerieAtualizada` | configuracoes-sistema | emissores de documento | — |
| `Config.PapelAtualizado` | configuracoes-sistema | auth (invalida cache RBAC) | — |
| `Config.WorkflowVersionado` | configuracoes-sistema | módulo dono da entidade | — |
| `Config.IntegracaoAtivada` / `IntegracaoDesativada` | configuracoes-sistema | módulos consumidores | — |
| `Config.RetencaoAjustada` | configuracoes-sistema | jobs de purge | — |
| `Config.FeatureLigada` | configuracoes-sistema | módulo da feature | — |
| `Config.MudancaSensivelRegistrada` | configuracoes-sistema | auditor + DPO tenant | — |

#### Módulo `engenharia-tecnica`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Engenharia.ProjetoCriado` | engenharia-tecnica | crm | — |
| `Engenharia.RevisaoSubmetida` | engenharia-tecnica | bpm, notificações | — |
| `Engenharia.RevisaoAprovada` | engenharia-tecnica | os, orcamentos, estoque (BOM), crm | — |
| `Engenharia.RevisaoRejeitada` | engenharia-tecnica | autor (notif) | — |
| `Engenharia.RevisaoMarcadaObsoleta` | engenharia-tecnica | os, estoque | — |
| `Engenharia.ComponenteCadastrado` | engenharia-tecnica | analytics | — |
| `Engenharia.BOMAtualizada` | engenharia-tecnica | orcamentos, estoque | — |

#### Módulo `equipamentos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Equipamento.Cadastrado` | equipamentos | metrologia, comercial | `Equipamento.cadastrado` |
| `Equipamento.VersaoCriada` | equipamentos | metrologia (revalida) | `Equipamento.versao_criada` |
| `Equipamento.Sucateado` | equipamentos | comercial, operacao | `Equipamento.sucateado` |
| `Equipamento.Transferido` | equipamentos | comercial | `Equipamento.transferido` |

#### Módulo `estoque`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Estoque.MovimentacaoRegistrada` | estoque | financeiro (CMP), operacao (saldo OS), bi | `Estoque.movimento_registrado` |
| `Estoque.SaidaPeca` | estoque | custeio-real (linha custo `pecas`), operacao | — |
| `Estoque.EntradaPeca` | estoque | contas-pagar, bi | — |
| `Estoque.TransferenciaEmitida` / `Aceita` / `Recusada` | estoque | operacao, almoxarife | `Estoque.transferencia_*` |
| `Estoque.MinimoAtingido` | estoque | operacao, fornecedores | `Estoque.minimo_atingido` |
| `Estoque.LoteVencendo` | estoque | almoxarife | `Estoque.lote_vencendo` |
| `Estoque.InventarioFinalizado` | estoque | financeiro | `Estoque.inventario_finalizado` |
| `Estoque.ItemEsgotado` | estoque | marketplace (vitrine indisponível) | — |

#### Módulo `fornecedores`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Fornecedor.Cadastrado` | fornecedores | — | `Fornecedor.cadastrado` |
| `Fornecedor.Homologado` | fornecedores | comercial | `Fornecedor.homologado` |
| `Fornecedor.Bloqueado` | fornecedores | operacao | `Fornecedor.bloqueado` |
| `Cotacao.Enviada` | fornecedores | gateway email/whatsapp | `Cotacao.enviada` |
| `Cotacao.Fechada` | fornecedores | pedido-compra | `Cotacao.fechada` |
| `PedidoCompra.Enviado` | fornecedores | financeiro (contas a pagar futuro) | — |
| `PedidoCompra.RecebidoTotal` | fornecedores | estoque, avaliacao-fornecedor | `PedidoCompra.recebido_total` |
| `AvaliacaoFornecedor.Registrada` | fornecedores | dashboards | — |

#### Módulo `gestao-documental`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Documento.Criado` | gestao-documental | auditoria, busca, notificação | `documento.criado` |
| `Documento.VersaoCriada` | gestao-documental | auditoria | `documento.versao_criada` |
| `Documento.Aprovado` | gestao-documental | notificação, auditoria | `documento.aprovado` |
| `Documento.Vencendo` | gestao-documental | notificação | `documento.vencendo` |
| `Documento.Vencido` | gestao-documental | notificação, dashboards | `documento.vencido` |
| `Documento.Assinado` | gestao-documental | auditoria, notificação | `documento.assinado` |
| `Documento.AcessoExterno` | gestao-documental | auditoria | `documento.acesso_externo` |

#### Módulo `onboarding`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Onboarding.ImplantacaoCriada` | onboarding | configuracoes-sistema, billing, notificações | — |
| `Onboarding.EtapaConcluida` | onboarding | notificações, métricas | — |
| `Onboarding.ImportacaoConcluida` | onboarding | clientes, produtos, estoque, equipamentos | — |
| `Onboarding.ValidacaoFalhou` | onboarding | notificações P1 | — |
| `Onboarding.TermoAssinado` | onboarding | billing, auditoria | — |
| `Onboarding.SandboxPromovido` | onboarding | todos os módulos | — |

#### Módulo `produtos-pecas-servicos`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Catalogo.ItemCadastrado` | produtos-pecas-servicos | estoque, financeiro | `Catalogo.item_cadastrado` |
| `Catalogo.ItemAtualizado` | produtos-pecas-servicos | **marketplace, precificacao, operacao** | — |
| `Catalogo.PrecoAlterado` | produtos-pecas-servicos | financeiro, marketplace | `Catalogo.preco_alterado` |
| `Catalogo.ItemInativado` | produtos-pecas-servicos | operacao, marketplace | `Catalogo.item_inativado` |
| `Catalogo.KitAlterado` | produtos-pecas-servicos | operacao | `Catalogo.kit_alterado` |

#### Módulo `release-management`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Release.Publicada` | release-management | suporte-saas, métricas | `release.publicada` |
| `Release.Revertida` | release-management | alertas, auditoria | `release.revertida` |
| `FeatureFlag.Alterada` | release-management | auditoria, cache invalidação | `feature_flag.alterada` |
| `FeatureFlag.Aposentada` | release-management | métricas | `feature_flag.aposentada` |
| `Beta.TenantInscrito` / `TenantCancelado` | release-management | flags | `beta.tenant_*` |
| `Migracao.Iniciada` / `Checkpoint` / `Concluida` / `Falhou` | release-management | observabilidade, alertas P0 | `migracao.*` |
| `BreakingChange.Anunciado` / `Proximo` | release-management | comunicação, notificação tenants | `breaking_change.*` |

#### Módulo `suporte-saas`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `Ticket.Aberto` | suporte-saas | roteamento, notificação | `ticket.aberto` |
| `Ticket.Respondido` | suporte-saas | notificação usuário | `ticket.respondido` |
| `Ticket.Resolvido` | suporte-saas | métricas, CSAT trigger | `ticket.resolvido` |
| `Ticket.SLAViolado` | suporte-saas | alertas | `ticket.sla_violado` |
| `Ticket.CSATRecebido` | suporte-saas | métricas | `ticket.csat_recebido` |
| `SessaoRemota.Solicitada` / `Iniciada` / `Encerrada` | suporte-saas | tenant admin, auditoria | `sessao_remota.*` |
| `Sugestao.Aprovada` | suporte-saas | notificação | `sugestao.aprovada` |
| `Manutencao.Agendada` / `Iniciada` / `Concluida` | suporte-saas | notificação, banner | `manutencao.*` |

---

### Domínio: DADOS

#### Módulo `bi`
| Evento | Origem | Consumers principais | Aliases |
|---|---|---|---|
| `BI.RelatorioGerado` | bi | notificações, auditoria | — |
| `BI.LinkPublicoAcessado` | bi | auditoria, segurança | — |
| `BI.DataMartAtualizado` | bi | observabilidade | — |
| `BI.AlertaKPI` | bi | notificações, dashboard executivo | — |

---

## Resolução de eventos órfãos (v8)

Achados de auditoria 2026-05-17 — eventos sem publisher ou consumer correspondente:

### Publicados sem consumer — RESOLVIDOS
| Evento | Resolução |
|---|---|
| `Marketplace.PagamentoConfirmado` | consumer adicionado em `financeiro/contas-receber` (cria título já liquidado + emite `ContasReceber.Pago`) |
| `Calibracao.Configurada` | consumer adicionado em `metrologia/certificados` (prepara template antes da emissão) |
| `Padroes.CertificadoVencendo` | consumers adicionados em `rh/qualidade` (NC preventiva) + `metrologia/certificados` (bloqueia emissão dependente) + RT signatário (notificação) |
| `SLA.PenalidadeCalculada` | consumer explícito em `financeiro/contas-receber` (cria desconto/multa) |
| `SLA.BonificacaoCalculada` | consumer explícito em `financeiro/contas-receber` (cria nota de crédito) |
| `CapacityPlanning.DistribuicaoSugerida` | consumer adicionado em `operacao/agenda` (exibe sugestão + gera `Agenda.SugestaoAplicada` quando aceita) |
| `BPM.InstanciaConcluida` | payload expandido com `entidade_origem_tipo`; consumers explícitos: orcamentos, contratos, os, chamados, engenharia-tecnica, despesas, precificacao, licencas-acreditacoes |

### Consumidos sem publisher — RESOLVIDOS
| Evento esperado | Resolução |
|---|---|
| `Catalogo.ItemAtualizado` | publisher adicionado em `suporte-plataforma/produtos-pecas-servicos` (evento agregador de mudanças de descrição/spec/status/kit/versão) |
| `Estoque.SaidaPeca` | publisher adicionado em `suporte-plataforma/estoque` (subtipo emitido em paralelo a `MovimentacaoRegistrada` quando tipo=saida) |
| `Estoque.MovimentacaoRegistrada` | publisher renomeado/padronizado em `suporte-plataforma/estoque` (alias do `Estoque.movimento_registrado` legado) |
| `Assinatura.Recorrencia.Faturada` | substituído por `BillingSaas.FaturaPaga` (campo `ciclo` distingue recorrência de avulsa); alias aceito em Wave A, removido em V2 |

---

## v9 — Eventos novos pós-auditoria de integrações (17/05/2026 madrugada)

### Eventos de transição regulatória (ADR-0014)

| Evento | Origem | Consumers principais | Observação |
|---|---|---|---|
| `Certificados.SignatarioTransicaoIniciada` | colaboradores → certificados | calibracao (bloqueia novos do tipo), contratos (pendente_designacao_rt), comunicacao-omnichannel (notifica cliente), audit | Disparado quando `Colaborador.Desligado` afeta RT signatário |
| `Certificados.SnapshotAcreditacaoGravado` | certificados (ao emitir RBC) | audit WORM, bi (rastreabilidade) | Snapshot imutável defendendo retroatividade Cgcre |
| `Padroes.CertificadoVencido` | calibracao/padroes (job diário) | certificados (bloqueia emissão), qualidade (NC automática INV-022), audit | Diferente do `CertificadoVencendo` (alerta); este é o que bloqueia |
| `SST.ASOVencido` | seguranca-trabalho (job diário) | agenda (bloqueia alocação), colaboradores (status), audit | Mesma lógica de `Treinamentos.CertificadoVencido` |
| `Calibracao.OSPendenteRevalidacao` | calibracao | app-tecnico (push), RT (notif), audit | Quando `Engenharia.RevisaoAprovada` afeta procedimento usado em OS em execução |
| `Padroes.ModoEmergencialAcionado` | calibracao/padroes | dono Aferê (escalação ANTI-11), audit WORM | RT força emissão com bypass — exige A3 + justificativa ≥50 chars |

### Eventos de pricing composicional (ADR-0013)

| Evento | Origem | Consumers principais | Observação |
|---|---|---|---|
| `BillingSaas.PlanoCriado` | billing-saas (operador comercial) | Auditor de Segurança valida, catálogo público atualiza | US-BIL-009 |
| `BillingSaas.PlanoVersionado` | billing-saas (operador edita) | Histórico, notificação interna, BI | Versionamento automático INV-026 |
| `BillingSaas.ComponentePrecoMudou` | billing-saas | Telemetria pricing, auditor produto | Granularidade de mudança |
| `BillingSaas.AddonContratado` | billing-saas (tenant) | acesso-seguranca (provisiona), módulo do addon (libera) | Mid-cycle pro-rata |
| `BillingSaas.AddonCancelado` | billing-saas (tenant) | acesso-seguranca (revoga próximo ciclo), módulo do addon | Efeito no próximo ciclo |
| `BillingSaas.LimiteDuroAtingido` | billing-saas (medição) | Notifica tenant, AuthorizationProvider (bloqueia conforme acao_ao_estourar) | Hard cap vs overage |
| `BillingSaas.UsoMedido` | módulos consumidores (fiscal, omnichannel, gestao-documental) | billing-saas (agrega em fatura) | `MeterUsoEvent` agregado |

### Eventos de lifecycle de tenant (ADR-0015)

| Evento | Origem | Consumers principais | Observação |
|---|---|---|---|
| `BillingSaas.AssinaturaPronta` | billing-saas | onboarding (inicia), acesso-seguranca (provisiona admin), audit | Disparado APÓS provisioning chain completar (não na criação) |
| `Onboarding.ProvisioningCompletado` | onboarding | billing-saas (libera primeira fatura), comunicacao-omnichannel (e-mail bem-vindo) | Checkpoint atômico |
| `BillingSaas.PlanoMudouModulos` | billing-saas | acesso-seguranca (sincroniza `tenant_features` em ≤5min), todos módulos afetados | Único ponto que sincroniza pricing→features (gap auditor H) |

### Eventos de consistência operacional (ADR-0016)

| Evento | Origem | Consumers principais | Observação |
|---|---|---|---|
| `ContasReceber.ClienteInadimplenteAlertaP1` | financeiro/contas-receber (job diário) | clientes (publica `Cliente.Bloqueado` se passou de 90d), comunicacao-omnichannel (régua) | Gate de bloqueio inadimplente |
| `Engenharia.BomDesatualizadaNotificada` | engenharia-tecnica | orcamentos (marca como `pendente_revalidacao_bom`), os (bloqueia conversão) | Auditor F gap crítico |
| `Qualidade.NCNotificacaoCliente` | qualidade | comunicacao-omnichannel (envia notif), portal-cliente (exibe na timeline) | Auditor C gap crítico |

---

## Alterações em eventos existentes (v8 → v9)

| Evento | Mudança v9 | Origem da alteração |
|---|---|---|
| `Fiscal.NFSeEmitida` | Payload ganha `tipo_servico: enum (calibracao, manutencao, consultoria, avulso)`. `certificado_id` **obrigatório** quando `tipo_servico=calibracao` (constraint + hook validador no bus). | INV-INT-001 (ADR-0014) |
| `Colaborador.Desligado` | Payload ganha `is_rt_signatario: bool, tipos_servico_assinava: list[str], comissoes_pendentes_count: int`. Consumers expandidos: certificados, calibracao, contratos, comunicacao-omnichannel, comissoes, acesso-seguranca, suporte-saas. | INV-INT-002 (ADR-0014) + Auditor E (RH) |
| `Engenharia.RevisaoAprovada` | Payload ganha `procedimentos_calibracao_afetados: list[procedimento_id]`. Consumer novo: calibracao (publica `Calibracao.OSPendenteRevalidacao`). | INV-INT-006 (ADR-0014) |
| `Treinamentos.CertificadoVencido` | Consumer novo: agenda (atualiza `tecnico_habilitacoes`, bloqueia alocação). | INV-INT-005 (ADR-0014) |
| `Padroes.CertificadoVencendo` | Mantém papel de alerta (30d antes). Novo evento `Padroes.CertificadoVencido` é quem bloqueia. | INV-INT-004 (ADR-0014) |
| `BillingSaas.PlanoMudou` | Payload ganha `direcao: enum (upgrade, downgrade, lateral)`, `canal_aquisicao: str opcional` (preenchido no Lead). | Auditor I (BI) — CAC e churn discriminados |
| `BillingSaas.TenantSuspenso` | Payload ganha `modo: enum (read_only, bloqueado_total)`. Consumer obrigatório `acesso-seguranca` força logout de sessões ativas. | Auditor G (Plataforma) |
| `Qualidade.NCAberta` | Payload ganha `entidade_origem_tipo: enum, entidade_origem_id: UUID`. | Auditor I (BI) — taxa de NC por tipo |
| `Comissoes.ComissaoCalculada` | Payload ganha `tecnico_id: UUID, valor: Money, periodo_inicio: date, periodo_fim: date`. | Auditor I (BI) — receita por técnico |
| `OS.Reaberta` | Payload ganha `os_origem_id: UUID, chamado_origem_id: UUID opcional`. Consumer novo: caixa-tecnico (marca despesas pra reconciliar). | Auditor D (Operação) — rastreabilidade bidirecional |

---

## Total v9

- **48 módulos** com eventos catalogados.
- **~267 eventos** publicados (240 da v8 + 19 da v9 + 8 alterações de payload).
- **6 domínios:** comercial (8 módulos), operação (8), metrologia (3), financeiro (8), rh-frota-qualidade (6), suporte-plataforma (13), dados (1) + 1 cross-cutting (acesso-seguranca).
- **0 eventos órfãos** após resolução v8 + cobertura v9.
- Aliases legados marcados — auditor bloqueia novos handlers em aliases.

---

## v10 — Eventos novos pós-ADR-0023 + auditoria 10 lentes (2026-05-23)

### Eventos novos (Domínio OS — ADR-0023 OS com Atividades)

- `Atividade.Adicionada` — US-OS-010 / atividade adicionada a OS em andamento
- `Atividade.Iniciada` — substitui `OS.Concluida` como gatilho de `metrologia/calibracao` (filter `tipo=calibracao`)
- `Atividade.Concluida` — consumer `metrologia/certificados` libera emissão (filter `tipo=calibracao AND tem_nc=False`)
- `Atividade.NaoConforme` — bloqueia emissão certificado + abre CAPA
- `Atividade.NCResolvida` — libera certificado após ciclo CAPA fechado (TEMA-E.6)
- `Atividade.Cancelada` — cancelar atividade individual sem cancelar OS toda

### Alterações em eventos existentes (v9 → v10)

- **`OS.Aberta`**: payload ganha `atividades_planejadas: [{atividade_id, tipo, sequencia}]` (ADR-0023). `tipo` da OS-toda removido — vai em cada atividade.
- **`OS.Concluida`**: payload ganha `atividades: [{id, tipo, estado_final}]` + `tipo_predominante`. **Consumer `metrologia/calibracao` REMOVIDO** (inversão TEMA-E.2).
- **TODOS eventos OS/Calibração/Certificados**: ganham `correlation_id` + `causation_id` obrigatórios (TEMA-E.5 — cadeia forense).
- **TODOS payloads cross-context**: `cliente_id`/`tecnico_id`/`revisor_id`/`conferente_id`/`ator_id` UUID cru proibidos — só `*_hash` HMAC-tenant (TEMA-C.12 + INV-OS-AUD-001 + INV-CAL-AUD-001).
- **`Calibracao.Aprovada`**: payload ganha `atividade_os_id` + `os_id` (TEMA-E.7) — permite certificado consumer voltar pra OS sem extra query.
- **`Certificados.Cancelado`**: consumer `fiscal` adicionado pra disparar CC-e quando cert virou base de NFS-e (TEMA-E.8).

### Cadeia forense correlation_id (TEMA-E.5)

Toda entidade nova (`OS`, `AtividadeDaOS`, `Calibracao`, `Certificado`, `NotaFiscal`) ganha coluna `correlation_id uuid NOT NULL`. Propagação:

- `OSAberta.event_id` → `OS.correlation_id` (raiz da cadeia)
- Atividade herda `correlation_id` da OS pai
- Calibração herda da AtividadeDaOS pai
- Certificado herda da Calibração
- NotaFiscal herda do Certificado / AtividadeConcluida
- `causation_id` aponta sempre pro evento imediatamente anterior

Hook valida que entidade derivada nunca tem `correlation_id` NULL ou diferente do pai (TEMA-E.5).

## Total v10

- **48 módulos** com eventos catalogados.
- **~273 eventos** publicados (267 da v9 + 6 novos `Atividade.*`).
- Todos eventos publicados pós-2026-05-23 carregam `correlation_id` + `causation_id` obrigatórios + IDs PII em hash HMAC-tenant.
- **Invariantes de integração:** INV-INT-001..010 (criadas nas ADRs 0014, 0015, 0016 pós-auditoria).
