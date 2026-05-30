---
owner: <DPO-ou-Encarregado>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 260
proposito: procedimento operacional para atender pedidos de titular de dados pessoais (LGPD Art. 18 — 9 direitos) — canal, SLA, runbook, registro
---

<!--
template: direitos-do-titular.template.md
destino: docs/conformidade/lgpd/direitos-do-titular.md
uso: documento único do projeto com a operacionalização dos 9 direitos do Art. 18 LGPD.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
revisão obrigatória: 12 meses ou ao mudar canal de atendimento ou ao receber orientação nova da ANPD.
-->

# Procedimento de Atendimento aos Direitos do Titular — LGPD Art. 18

> **Documento CONDICIONAL.** Só se aplica a projeto que trata dado pessoal. Se o produto não trata dado de pessoas, **não preencha** — registre o motivo em `docs/nao-aplica.md`.

> **Direito do titular** = o que a pessoa cujo dado tratamos pode exigir de nós a qualquer momento. A LGPD lista 9 direitos no Art. 18, e o titular tem o direito de **resposta em até 15 dias** após o pedido. Não atender = multa da ANPD + risco reputacional + ação judicial. Este documento define **como cada um dos 9 direitos é atendido na prática**.

## 1. Canal único de atendimento

Todos os pedidos chegam por **um canal documentado e publicado**:

| Canal | Endereço | Quem responde |
|---|---|---|
| E-mail | <dpo@exemplo.com> | DPO / encarregado |
| Formulário web | <https://exemplo.com/privacidade/exercer-direito> | mesma fila |
| Postal (LGPD exige aceitar) | <endereço completo> | DPO via digitalização |

**Publicação obrigatória:** link visível no rodapé do site, na política de privacidade e na app store/landing do produto.

## 2. SLA e prazos legais

| Etapa | Prazo máximo |
|---|---|
| Acusar recebimento | 48 horas úteis |
| Validar identidade do titular | 5 dias corridos |
| Concluir o atendimento e responder | **15 dias corridos** (Art. 19 §1 II LGPD — para pedidos de acesso; demais direitos a ANPD aceita o mesmo prazo como referência) |
| Em caso de pedido complexo (volume alto, múltiplas bases, integração com terceiros) | prazo pode ser estendido com **justificativa por escrito ao titular** dentro do prazo original |

## 3. Validação de identidade (anti-fraude)

Antes de atender, confirmar que quem pede é o titular (ou seu representante legal). Sem isso, atender o pedido vira **vazamento**.

| Como | Quando aceita |
|---|---|
| Titular já logado no produto + confirmação por 2FA | sempre — fluxo padrão |
| E-mail cadastrado + código de confirmação | sempre — fluxo padrão |
| Documento de identidade + selfie | quando o titular não tem mais acesso ao cadastro |
| Procuração + documento do representante | quando representante legal (advogado, pai/responsável por criança, curador) |
| Certidão de óbito + comprovante de herdeiro | quando pedido em nome de titular falecido |

> **Atenção:** registrar a validação no log de auditoria, mas **não guardar a cópia do documento além do necessário** (LGPD Art. 9 — minimização). Após validar, ID e foto vão para retenção mínima (30 dias) e são descartados.

## 4. Os 9 direitos do Art. 18 — procedimento por direito

### 4.1 Inciso I — Confirmação da existência de tratamento

**O que o titular pede:** "vocês têm dado meu?"
**Como atendemos:** sim/não, em linguagem clara, sem exigir mais informação.
**Runbook técnico:** `docs/operacao/runbooks/atender-confirmacao-tratamento.md` — consulta no banco por chave do titular (e-mail, CPF, ID).
**SLA:** 15 dias.
**Registro:** log de auditoria com timestamp, identidade verificada, resposta enviada.

### 4.2 Inciso II — Acesso aos dados

**O que o titular pede:** "me mostre tudo o que vocês têm sobre mim."
**Como atendemos:** exportar em formato legível (JSON ou CSV + PDF resumo) com **todos os dados pessoais** vinculados ao titular, **finalidade**, **base legal** e **compartilhamentos**.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-acesso.md`.
**SLA:** 15 dias.
**Registro:** log + cópia do que foi enviado (criptografada, retenção 5 anos para defesa em fiscalização).

### 4.3 Inciso III — Correção de dado incompleto, inexato ou desatualizado

**O que o titular pede:** "meu nome está escrito errado / mudei de e-mail / endereço atualizado."
**Como atendemos:** corrigir no banco + propagar para sistemas integrados que receberam o dado anterior.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-correcao.md`.
**SLA:** 15 dias.
**Registro:** log com valor antigo (hash) e novo (hash), timestamp, quem aprovou.

### 4.4 Inciso IV — Anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade

**O que o titular pede:** "vocês coletaram mais do que precisavam / vocês continuam guardando o que já não serve."
**Como atendemos:** revisar com DPO; se procedente, anonimizar (preferido — mantém estatística sem identificar) OU eliminar.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-anonimizacao.md`.
**SLA:** 15 dias.
**Registro:** log + parecer do DPO.

### 4.5 Inciso V — Portabilidade dos dados a outro fornecedor

**O que o titular pede:** "me dê meus dados em formato que eu possa entregar para um concorrente."
**Como atendemos:** exportar em formato **interoperável** (JSON ou CSV) com schema documentado em `docs/conformidade/lgpd/schema-portabilidade.md`. Não envia segredo comercial nosso (algoritmo, modelo); envia o dado **do titular**.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-portabilidade.md`.
**SLA:** 15 dias.
**Registro:** log + arquivo enviado (hash registrado).

### 4.6 Inciso VI — Eliminação dos dados tratados com o consentimento do titular

**O que o titular pede:** "esqueçam de mim."
**Como atendemos:** **hard-delete** quando a base legal era consentimento e ele revogou. Cuidado: se a base legal for **outra** (obrigação legal, execução de contrato, processo judicial), os dados sob essa outra base **permanecem** e isso é explicado ao titular.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-eliminacao.md` (template `atender-pedido-eliminacao-runbook.template.md`).
**SLA:** 15 dias.
**Registro:** log WORM (write-once-read-many) com timestamp, identidade verificada, escopo eliminado, exceções aplicadas (se algum dado permaneceu, por qual base legal).
**Exceções legais para reter** (LGPD Art. 16):
- I — cumprimento de obrigação legal/regulatória do controlador (ex: nota fiscal: 5 anos).
- II — estudo por órgão de pesquisa (com anonimização sempre que possível).
- III — transferência a terceiro (desde que respeitados os requisitos).
- IV — uso exclusivo do controlador (anonimizados).

### 4.7 Inciso VII — Informação das entidades públicas e privadas com as quais o controlador realizou uso compartilhado de dados

**O que o titular pede:** "para quem vocês mandaram meu dado?"
**Como atendemos:** lista de operadores e suboperadores que receberam o dado do titular específico (não a lista geral). Baseado no ROPA + log de envio.
**Runbook técnico:** `docs/operacao/runbooks/atender-pedido-compartilhamento.md`.
**SLA:** 15 dias.
**Registro:** log + lista enviada.

### 4.8 Inciso VIII — Informação sobre a possibilidade de não fornecer consentimento e sobre as consequências da negativa

**O que o titular pede:** "se eu não consentir, o que perco?"
**Como atendemos:** resposta clara: "se você não consentir com X, não conseguirá usar a funcionalidade Y, mas continua usando Z". Sem coerção (consentimento forçado é nulo — Art. 8 §3).
**Runbook técnico:** geralmente atendido pela própria interface (botão de revogar com explicação). Para pedido explícito, segue o canal padrão.
**SLA:** 15 dias.
**Registro:** log + resposta enviada.

### 4.9 Inciso IX — Revogação do consentimento

**O que o titular pede:** "estou tirando o consentimento que dei antes."
**Como atendemos:** **botão de revogar** acessível dentro do produto (configurações → privacidade). Para pedido fora do produto, segue canal padrão. Após revogar, tratamentos cuja **única base era o consentimento** param imediatamente; dados sob aquela base entram em fluxo de eliminação (inciso VI) salvo se houver exceção legal.
**Runbook técnico:** `docs/operacao/runbooks/atender-revogacao-consentimento.md`.
**SLA:** revogação em si — **imediata** (o consentimento é revogado no momento do clique/recebimento). Eliminação subsequente — 15 dias.
**Registro:** log + timestamp da revogação (Art. 8 §5 — provar que houve consentimento E que foi revogado).

## 5. Direito adicional — revisão de decisão automatizada (Art. 20)

Não está no Art. 18 mas é direito relacionado e gera pedidos similares.

**O que o titular pede:** "uma máquina decidiu algo sobre mim, quero revisão por pessoa."
**Como atendemos:** revisão por humano qualificado, **diferente** de quem operou o sistema originalmente. Resposta com critério geral usado (sem revelar segredo comercial), conforme AIPD do tratamento.
**Runbook técnico:** `docs/operacao/runbooks/atender-revisao-decisao-automatizada.md`.
**SLA:** 15 dias úteis.
**Vinculação:** seção 8 da AIPD do tratamento específico.

## 6. Registro central de pedidos

Toda solicitação vira linha em log estruturado (banco dedicado, append-only):

| Campo | Descrição |
|---|---|
| `id` | UUID do pedido |
| `data_recebimento` | timestamp ISO 8601 |
| `canal` | e-mail / web / postal |
| `direito_invocado` | inciso I-IX ou Art. 20 |
| `identidade_validada` | método + timestamp |
| `escopo_atendido` | descrição em linguagem clara |
| `excecoes_aplicadas` | quais dados não foram afetados e por qual base legal |
| `data_resposta` | timestamp do envio |
| `sla_cumprido` | bool |
| `link_evidencia` | path do log WORM |

Esse log é insumo do **relatório anual do DPO** (KPI: % de pedidos atendidos no prazo).

## 7. Casos especiais

- **Pedido de menor de idade**: validar com responsável legal antes de qualquer ação envolvendo dado da criança/adolescente.
- **Pedido de titular falecido**: aceitar herdeiro com certidão de óbito + comprovante de herança.
- **Pedido coletivo** (advocacy / ação coletiva): tratar como múltiplos pedidos individuais; comunicar DPO + jurídico.
- **Pedido manifestamente excessivo ou repetitivo** (LGPD Art. 19 §1 II): pode ser cobrado custo administrativo razoável ou recusado com justificativa por escrito.
- **Pedido envolvendo dado sensível**: redobrar cuidado na validação de identidade.

## 8. Vinculação

- `ropa.md` — fonte da informação "quem tem dado de quem, por que, com quem compartilha".
- `retencao-dados.md` — prazos legais que limitam o direito de eliminação.
- `aipd-<tratamento>.md` — canal de revisão de decisão automatizada por tratamento.
- `runbooks/atender-pedido-*.md` — implementação técnica de cada direito.
- `SECURITY.md` — política externa onde o canal é publicado.
- INV-AGENT-AUDIT-* — invariantes que garantem o log WORM.

## 9. Checklist de promoção draft → stable

- [ ] Canal de §1 está publicado no site, política de privacidade e app store.
- [ ] DPO designado e contato funcional (testado).
- [ ] Cada um dos 9 incisos tem runbook correspondente em `docs/operacao/runbooks/`.
- [ ] Log central §6 implementado e testado (entrada + recuperação).
- [ ] Validação de identidade §3 testada com casos reais (não fraudável trivialmente).
- [ ] Primeiro pedido real (ou simulado em drill) foi atendido dentro do SLA.
- [ ] `revisado-em` atualizado; `status: stable`.
