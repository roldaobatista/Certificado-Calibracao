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
  - docs/adr/0005-engine-automacoes.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
---

# Modelo de domínio — Módulo Automações & BPM

> Entidades específicas. Transversais (Tenant, Usuario, Grupo) ficam em `docs/comum/modelo-de-dominio.md`.

---

## Entidades

### Fluxo
- **Atributos obrigatórios:** `id`, `tenant_id`, `nome`, `descricao`, `status` (rascunho|ativo|inativo|deprecado), `versao_corrente`, `criado_em`, `criado_por`.
- **Atributos opcionais:** `tags`, `categoria`, `modulo_origem`.
- **Invariantes:** `INV-TENANT-NNN` (tenant isolation), `INV-NNN` (versão imutável após publicação).
- **Ciclo de vida:** rascunho → ativo (publicação cria `VersaoFluxo`); pode voltar a rascunho gerando nova versão; nunca deletado, só inativado/deprecado.

### VersaoFluxo
- **Atributos:** `id`, `fluxo_id`, `numero_versao`, `definicao` (JSON/YAML do desenho), `publicada_em`, `publicada_por`, `modo` (shadow|ativo).
- **Imutabilidade:** snapshot — não muda após publicação. Mudança gera versão nova.

### Etapa
- **Atributos:** `id`, `versao_fluxo_id`, `nome`, `tipo` (decisao_humana|acao_automatica|condicional|inicio|fim), `sla_horas`, `responsavel_tipo` (usuario|grupo|alcada), `responsavel_id`, `escalonamento_para`.

### Transicao
- **Atributos:** `id`, `versao_fluxo_id`, `etapa_origem_id`, `etapa_destino_id`, `condicao` (predicado serializado).

### InstanciaFluxo
- **Atributos:** `id`, `versao_fluxo_id`, `tenant_id`, `entidade_origem_tipo` (orcamento|os|nf|...), `entidade_origem_id`, `status` (em_andamento|concluida|cancelada|falha), `iniciada_em`, `concluida_em`, `payload_inicial`.
- **Ciclo de vida:** criada quando evento dispara fluxo → percorre etapas → terminada quando alcança etapa "fim" OU é cancelada.

### Pendencia
- **Atributos:** `id`, `instancia_id`, `etapa_id`, `aprovador_id`, `aprovador_efetivo_id` (após delegação), `sla_expira_em`, `status` (pendente|aprovada|rejeitada|expirada|escalada), `decidida_em`, `comentario`.
- **Invariantes:** `INV-NNN` (pendência decidida é imutável; rejeição/aprovação registradas em log).

### Regra
- **Atributos:** `id`, `tenant_id`, `nome`, `evento_origem` (id do catálogo), `condicao`, `acao`, `modo` (shadow|ativo|inativo), `versao_corrente`.
- **Ciclo de vida:** análogo a Fluxo (rascunho → ativo via VersaoRegra).

### VersaoRegra
- **Atributos:** `id`, `regra_id`, `numero_versao`, `definicao`, `publicada_em`.

### ExecucaoRegra
- **Atributos:** `id`, `versao_regra_id`, `tenant_id`, `payload_entrada`, `condicao_resultado` (bool), `acao_resultado` (sucesso|falha), `mensagem_erro`, `executada_em`, `reprocessamento_de_id` (nullable, FK pra outra execucao).
- **Imutabilidade:** registro imutável. Reprocessamento cria registro novo.

### Delegacao
- **Atributos:** `id`, `tenant_id`, `titular_id`, `substituto_id`, `valido_de`, `valido_ate`, `motivo`.
- **Invariantes:** não permite delegação encadeada > 1 nível (a definir em ADR).

### CatalogoEvento
- **Atributos:** `id`, `modulo`, `nome` (ex: `Orcamentos.Submetido`), `descricao_pt`, `schema_payload`, `frequencia_tipica`, `status` (ativo|deprecado).
- **Origem:** sincronizado a partir do registry de eventos publicados (ADR-0007).

### CatalogoCondicao
- **Atributos:** `id`, `nome`, `descricao_pt`, `aplicavel_a` (lista de evento_ids), `template_predicado`.

### CatalogoAcao
- **Atributos:** `id`, `nome`, `descricao_pt`, `requer_conexao` (ex: gateway WhatsApp), `template_parametros`.

### Alerta
- **Atributos:** `id`, `tenant_id`, `tipo` (vencimento|sla|estoque_min|financeiro|fiscal|contrato|calibracao|frota), `regra_id` (opcional — alguns alertas têm regra associada), `canal` (email|whatsapp|sms|in_app), `destinatario`.

---

## Agregados

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| Fluxo | Fluxo, VersaoFluxo, Etapa, Transicao | versão imutável; tenant isolation |
| Regra | Regra, VersaoRegra | versão imutável; tenant isolation |
| InstanciaFluxo | InstanciaFluxo, Pendencia | pendência decidida imutável; pertence a tenant |
| ExecucaoRegra | ExecucaoRegra | imutável; chain de reprocessamento rastreável |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| `Alcada` | `{valor_min, valor_max, categoria, aprovador_tipo}` | Sim |
| `Sla` | `{horas, calendario_referencia}` | Sim |
| `Predicado` | expressão booleana serializada (DSL ou JSON-logic) | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `BPM.PendenciaCriada` | nova pendência atribuída | `{pendencia_id, aprovador_id, sla_expira_em, contexto}` | CRM, notificações |
| `BPM.AprovacaoConcedida` | aprovador clica aprovar | `{pendencia_id, decidido_por, decidido_em, comentario}` | módulo origem (Orçamentos, OS, etc.) |
| `BPM.AprovacaoRejeitada` | aprovador clica rejeitar | idem | idem |
| `BPM.SlaEstourado` | SLA passou sem decisão | `{pendencia_id, etapa, novo_responsavel}` | escalonamento, observabilidade |
| `BPM.InstanciaConcluida` | fluxo chega à etapa final | `{instancia_id, entidade_origem, resultado}` | módulo origem |
| `BPM.RegraExecutada` | regra disparou (sucesso ou falha) | `{execucao_id, regra_id, resultado, payload}` | observabilidade |
| `BPM.AlertaDisparado` | alerta enviado | `{alerta_id, destinatario, canal}` | CRM, log |

---

## Comandos (entradas no módulo)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `publicarFluxo` | UI editor | usuário tem permissão; definição válida | nova VersaoFluxo + status `ativo` |
| `iniciarInstancia` | engine (em resposta a evento) | fluxo `ativo`; payload válido | InstanciaFluxo criada |
| `decidirPendencia` | UI painel | aprovador efetivo == usuário logado | Pendencia decidida + evento publicado |
| `cadastrarDelegacao` | UI configurações | usuário == titular | Delegacao criada |
| `publicarRegra` | UI editor | definição válida | nova VersaoRegra + status `ativo` |
| `reprocessarExecucao` | UI execuções | execução tem status `falha` | nova ExecucaoRegra com link à original |
| `cadastrarAlerta` | UI configurações | tipo válido | Alerta criado |

---

## Schema físico

Ver `../schema-banco.md` quando criado (ADR-0001 + ADR-0002 definem padrão multi-tenant).

## Como este modelo evolui

- Entidade nova → verificar fronteira comum/módulo (`governanca-modelo-comum.md`).
- Atributo novo → migration + bump CHANGELOG.
- Evento publicado novo → atualizar `CatalogoEvento` + comunicar consumidores.
