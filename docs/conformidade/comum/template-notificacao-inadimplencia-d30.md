---
owner: agente-ia
revisado-em: 2026-06-16
status: draft
escopo: módulo contas-receber — texto do e-mail de aviso de inadimplência D+30/D+45 (perfil A) ao cliente final (T-CR-044 / D-CR-9 / Caminho C)
relacionados:
  - docs/faseamento/contas-receber/spec.md (D-CR-9, D-CR-21, D-CR-22)
  - docs/faseamento/contas-receber/tasks.md (T-CR-044)
  - src/application/contas_receber/notificar_inadimplencia.py (montagem do corpo)
versao_canonica: MINUTA PROVISÓRIA — NÃO CANÔNICA
fundamento_legal: CDC art. 6º III/IV + art. 39 V + art. 42/71 + Lei 14.181/2021 (superendividamento) + LGPD art. 6º III (minimização) / art. 39 (operador)
---

# Template de notificação de inadimplência D+30/D+45 — MINUTA PROVISÓRIA

> ⚠️ **CONGELADO até GATE-LGPD-RAT-CONSOLIDACAO** (decisão Roldão 2026-06-12). Este texto é
> **minuta provisória**, gerada por IA — NÃO pode ser disparado a pessoa física real antes da
> revisão de advogado(a) humano(a) com OAB ativa (consumerista/digital). O código que monta e
> envia o e-mail (`notificar_inadimplencia.py` + `job_notificar_inadimplencia.py`) está pronto e
> testado, mas o **conteúdo definitivo** entra no passe único do gate, junto com a cláusula nos
> termos de uso e a entrada no RAT.

## Enquadramento (parecer advogado Caminho C, 2026-06-16)

- **Destinatário:** o cliente final (devedor), com **remetente = o tenant** (o laboratório). O Aferê
  é OPERADOR técnico do envio — nunca aparece como cobrador. Reusa o enquadramento RAT-06 (lembrete
  WhatsApp operado pelo Aferê em nome do tenant).
- **Quando:** só perfil A em Wave A (D-CR-9); D+30 (aviso prévio) e D+45 (no limite do grace).
- **Minimização (D-CR-19 / LGPD art. 6º III):** só título, valor, vencimento, dias em atraso, data
  de bloqueio prevista e canal de regularização. **Sem CPF, sem dados de terceiro.** O e-mail do
  cliente é lido de `Cliente.email` **só no momento do envio** — NUNCA persistido no evento/WORM
  (o evento carrega `cliente_referencia_hash`).
- **Aviso ao admin do tenant:** via evento `contas_receber.inadimplencia_dura_atingida` (payload
  rico), consumido pelo painel/CRM — não por e-mail redundante (RLS `upt_self_select`).

## Campos obrigatórios do corpo (CDC + LGPD)

1. Identificação do credor = **o tenant** (razão social do laboratório), nunca o Aferê.
2. Título(s): número, valor original, data de vencimento, dias em atraso.
3. **Data prevista do bloqueio** (aviso prévio explícito — Lei 14.181) + o que SERÁ bloqueado
   (abertura de nova OS / novo orçamento) e o que **NÃO** será (certificados de OS em andamento,
   downloads, leitura histórica — D-CR-21 / CDC art. 39 V).
4. **Canal de regularização** (onde quitar/negociar).
5. Tom neutro e informativo, sem ameaça nem termo vexatório (CDC art. 42 + art. 71).
6. Rodapé: "enviado pela plataforma Aferê a serviço de [LAB]; dúvidas sobre a cobrança = canal do
   tenant".

## Minuta provisória do corpo (espelha `montar_aviso`)

```
[MINUTA PROVISÓRIA — texto definitivo aguarda revisão jurídica (GATE-LGPD-RAT)]

Prezado(a) cliente,

Consta(m) em aberto, junto a {LAB}, o(s) seguinte(s) título(s):
- Título {id}: R$ {valor} (vencido em {data}, {dias} dias em atraso)

Total em aberto: R$ {total}.

Para evitar a suspensão de NOVOS atendimentos a partir de {data_bloqueio}, regularize em:
{canal_regularizacao_url}

Importante: serviços já em andamento, certificados já emitidos e o acesso ao seu histórico
NÃO são interrompidos.

Esta mensagem foi enviada pela plataforma Aferê a serviço de {LAB}. Dúvidas sobre esta
cobrança devem ser tratadas diretamente com {LAB}.
```

## Pendências para o gate jurídico (GATE-LGPD-RAT-CONSOLIDACAO)

- [ ] Texto definitivo do e-mail (revisão consumerista/digital OAB).
- [ ] Cláusula nos termos de uso: "ativar a flag de bloqueio automático = o Contratante ordena o
      envio da notificação de inadimplência em seu nome".
- [ ] Entrada no RAT: PII `Cliente.email` + identificação do título; base legal do controlador
      (tenant); finalidade aviso prévio CDC; retenção do log de envio 5 anos (prova de aviso).
- [ ] Fail-closed de bloqueio (perfil A não bloqueia sem prova de envio) — Fatia 3b-3.
