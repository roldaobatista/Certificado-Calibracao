---
owner: roldao
revisado-em: 2026-05-29
status: draft
idioma: pt-BR
limite-linhas: 240
proposito: plano anual de ação do Encarregado pelo Tratamento de Dados Pessoais (DPO) — auditorias, treinamentos, comunicação com ANPD, indicadores e relatório anual
---

<!--
template: dpo-action-plan.template.md
destino: docs/conformidade/lgpd/dpo-action-plan-<ano>.md
uso: plano anual (um por ano civil). Próximo ano é redigido em novembro do ano anterior; aprovação até dezembro; vigência de janeiro a dezembro.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
revisão obrigatória: trimestral (gates de acompanhamento) + anual (próximo plano).
-->

# Plano de Ação do Encarregado — <Ano>

> **CONDICIONAL** — só se aplica a projeto regulado / que trata dado pessoal e designa Encarregado (DPO). Se o produto NÃO trata dado pessoal, marcar este arquivo como N/A em `docs/nao-aplica.md` com gatilho de reavaliação.

> **Encarregado** (ou **DPO**, sigla em inglês para Data Protection Officer) = a pessoa designada pelo controlador para liderar a conformidade com a LGPD (Art. 41). Este documento descreve **o que o Encarregado vai fazer no ano**: que auditorias, que treinamentos, como conversa com a ANPD, como mede se está dando certo, e como reporta no fim do ano. Sem plano, a função vira reativa (só apaga incêndio); com plano, vira preventiva.

## 1. Identificação

| Campo | Valor |
|---|---|
| Encarregado titular | Roldão (dono) — encarregado inicial acumulado (decisão 2026-05-29; permitido no porte atual) |
| Encarregado suplente | ⚠️ a definir — recomendado **advogado externo em meio-período** ao abrir para o 2º cliente (a função pede independência; há conflito natural dono-vende × encarregado-freia) |
| Vigência | 2026 (a formalizar por ata de nomeação) |
| Aprovado por | ⚠️ Roldão — formalizar por escrito (ata) antes de operar com cliente real |
| Orçamento aprovado | ⚠️ a definir (treinamentos + ferramentas + consultoria jurídica pontual) |

> **Nota (2026-05-29):** nomeação registrada também no ROPA §2 e `mercado-regulatorio §8`. **Gatilho de revisão:** ao abrir comercialmente para outros clientes, reavaliar encarregado dedicado/independente e preencher o orçamento e o calendário abaixo. O calendário de auditorias e treinamentos abaixo é o modelo a executar quando a operação iniciar.

## 2. Calendário de auditorias trimestrais

| Trimestre | Período | Escopo | Responsável pela execução | Entregável | Status |
|---|---|---|---|---|---|
| Q1 | jan-mar | Auditoria do ROPA — toda operação tratada está registrada? base legal correta? prazo de retenção honesto? | DPO + amostragem técnica | relatório `docs/conformidade/lgpd/auditoria-q1-<ano>.md` | <planejado / em andamento / concluído> |
| Q2 | abr-jun | Auditoria de exercícios de direito (Art. 18) — todos os pedidos do semestre foram atendidos no SLA? | DPO + amostragem de logs | relatório `docs/conformidade/lgpd/auditoria-q2-<ano>.md` | <status> |
| Q3 | jul-set | Auditoria de operadores e suboperadores — contratos vigentes? cláusulas LGPD presentes? auditoria do operador feita? | DPO + jurídico | relatório `docs/conformidade/lgpd/auditoria-q3-<ano>.md` | <status> |
| Q4 | out-dez | Auditoria de segurança da informação — controles do threat-model funcionando? incidentes do ano tiveram post-mortem? | DPO + Security Owner | relatório `docs/conformidade/lgpd/auditoria-q4-<ano>.md` | <status> |

**Critério de aprovação trimestral:** zero achados CRÍTICOS abertos. Achados ALTOS com plano de remediação e prazo. Auditoria reprovada → plano de ação corretivo em 30 dias.

## 3. Treinamentos obrigatórios

| Treinamento | Público | Carga | Frequência | Responsável | Status |
|---|---|---|---|---|---|
| LGPD básica — princípios, direitos, bases legais | **todos os colaboradores** (inclusive estagiários e PJ) | 2h | anual (mês de janeiro) + onboarding de cada novo colaborador | DPO + RH | <status> |
| LGPD para devs — coleta mínima, log seguro, response do Art. 18 implementado em código | **equipe técnica** | 4h | anual (mês de março) | DPO + Security Owner | <status> |
| Tratamento de incidente de privacidade — runbook, comunicação à ANPD em 72h, comunicação ao titular | **lideranças + on-call** | 2h + drill | semestral | DPO + Ops | <status> |
| Atendimento a titular — empatia, linguagem clara, validação de identidade | **suporte ao cliente** | 3h | semestral | DPO + CS | <status> |
| Dado sensível (Art. 11) e dado de menor | **quem trata** | 2h | anual | DPO | <status> |

**Registro:** lista de presença + comprovante de conclusão fica em `docs/conformidade/lgpd/treinamentos/2026-05-28-<tema>.md`. Quem não cumpriu o treinamento obrigatório no ano corrente tem **acesso a dado pessoal suspenso** até regularizar.

## 4. Canal de comunicação com a ANPD

### 4.1 Quem fala com a ANPD
**Exclusivamente o DPO titular** (ou suplente formalmente designado). Qualquer outra pessoa que receba contato da ANPD encaminha imediatamente para o DPO **sem responder**.

### 4.2 Tipos de comunicação previstos

| Tipo | Quando | Prazo | Canal |
|---|---|---|---|
| Notificação de incidente de segurança | confirmação de breach com risco a titulares | **72h** após ciência (referência prática internacional) | sistema oficial da ANPD <https://www.gov.br/anpd> |
| Resposta a fiscalização / pedido de informação | quando ANPD oficiar | conforme prazo do ofício (geralmente 15-30 dias) | canal oficial do ofício |
| Comunicação proativa de mudança relevante | mudança na natureza do tratamento que afete titulares | quando a mudança entra em vigor | e-mail registrado + sistema oficial |
| Consulta de orientação (Art. 38 § único) | risco residual de AIPD permanecer alto | quando esgotadas mitigações internas | sistema oficial |

### 4.3 Registro de todas as comunicações
Toda comunicação com a ANPD vira linha em `docs/conformidade/lgpd/comunicacoes-anpd.md` (data, protocolo, assunto, resposta, status). Conteúdo dos anexos guardado em pasta cifrada com retenção mínima de 10 anos.

## 5. Programa de revisão de bases legais

Toda base legal declarada no ROPA é revisitada anualmente para garantir que ainda é válida.

| Etapa | Quando | Saída |
|---|---|---|
| Listar bases legais em uso | janeiro | tabela atualizada do ROPA |
| Para cada base, verificar se ainda se aplica (contrato vigente? consentimento ainda dado? interesse legítimo passou no teste de balanceamento atualizado?) | fevereiro | parecer por linha do ROPA |
| Tratamentos com base legal inválida ou enfraquecida — plano de remediação (mudar base, parar tratamento, anonimizar) | março | plano em `docs/conformidade/lgpd/bases-legais-revisao-<ano>.md` |
| Execução do plano | até junho | linhas do ROPA atualizadas |
| Confirmação anual no relatório do DPO | dezembro | seção do relatório |

## 6. Indicadores (KPIs) da função

> **KPI** = "número que mostra se a coisa está indo bem ou mal". Sem número, é opinião.

| Indicador | Meta | Frequência de medição | Fonte do dado |
|---|---|---|---|
| % de pedidos do Art. 18 atendidos dentro do SLA de 15 dias | ≥ 98% | mensal | log central de pedidos (`direitos-do-titular.md` §6) |
| Tempo médio de resposta a pedido do titular | ≤ 7 dias | mensal | mesmo log |
| Nº de incidentes de privacidade no trimestre | tendência decrescente | trimestral | `docs/operacao/incidentes/` |
| % de incidentes notificados à ANPD dentro de 72h | 100% | por incidente | `comunicacoes-anpd.md` |
| % de colaboradores com treinamento LGPD em dia | 100% | mensal | RH + registro de treinamentos |
| Nº de achados CRÍTICOS abertos em auditoria | 0 | trimestral | relatórios trimestrais |
| Nº de operadores com contrato LGPD vigente / total | 100% | trimestral | jurídico |
| Tempo até detecção de incidente (MTTD) | ≤ 24h | por incidente | post-mortem |
| Tempo até notificação aos titulares (após confirmação de risco) | ≤ 7 dias | por incidente | post-mortem |
| Nº de AIPDs realizadas no trimestre vs. tratamentos novos de alto risco | 1:1 | trimestral | inventário de AIPDs |

## 7. Relatório anual

Entregue à diretoria, conselho e (sob demanda) à ANPD, até **31 de janeiro** do ano seguinte. Estrutura mínima:

1. **Resumo executivo** — 1 página em linguagem clara.
2. **Auditorias do ano** — resumo de cada trimestre, achados, status de remediação.
3. **Pedidos do titular** — volume, distribuição por direito, % no SLA, tendência.
4. **Incidentes de privacidade** — número, severidade, tempo de detecção, tempo de notificação, post-mortems com aprendizados.
5. **Comunicações com a ANPD** — número, motivos, status.
6. **Treinamentos** — cobertura, presença, avaliação.
7. **Revisão de bases legais** — bases ainda válidas vs ajustadas.
8. **KPIs** (§6) — meta vs realizado, comentário.
9. **Plano do próximo ano** — esboço do `dpo-action-plan-<próximo-ano>.md`.
10. **Anexos** — relatórios trimestrais, lista de operadores, AIPDs concluídas.

Publicado em `docs/conformidade/lgpd/relatorio-anual-<ano>.md`. Versão pública (sumarizada) opcional no site, no link da política de privacidade.

## 8. Independência e recursos

- DPO **reporta diretamente** à alta administração (CEO ou Conselho), sem subordinação ao time técnico ou comercial — Art. 41 §2 LGPD.
- Orçamento próprio aprovado no início do ano (§1).
- Acesso irrestrito a logs, sistemas, contratos.
- Pode acionar auditor externo quando necessário.
- Não pode ser punido nem demitido por exercer a função (proteção análoga ao GDPR Art. 38; reconhecida pela ANPD como boa prática).

## 9. Vinculação

- `ropa.md` — fonte da auditoria Q1.
- `direitos-do-titular.md` — fonte da auditoria Q2 e do KPI de pedidos.
- `aipd-*.md` — insumo do programa de revisão de bases.
- `runbooks/incidente-seguranca.md` — fluxo executado quando há breach.
- `SECURITY.md` — política externa que esta função sustenta.
- `docs/descoberta/mercado-regulatorio.md` — contexto regulatório do domínio (leis, órgãos, prazos) que define o escopo e a obrigatoriedade deste plano.

## 10. Checklist de promoção draft → stable

- [ ] DPO titular e suplente nomeados formalmente (ata).
- [ ] Orçamento aprovado pela diretoria.
- [ ] Calendário §2 com responsáveis confirmados.
- [ ] Treinamentos §3 agendados (datas reais).
- [ ] KPIs §6 com fonte de dado funcionando (não placeholder).
- [ ] Estrutura do relatório anual §7 entendida pela diretoria.
- [ ] `revisado-em` atualizado; `status: stable`.
