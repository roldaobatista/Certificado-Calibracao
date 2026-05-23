---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# Runbook do Encarregado de Dados (DPO) — Plataforma Aferê

> LGPD art. 41 e art. 41 §1º + Res. CD/ANPD 2/2022, 15/2024, 18/2024 e 19/2024.
> **MINUTA — REQUER VALIDAÇÃO OAB**.

---

## 1. Status Atual

1.1. **Designação formal pendente** até o 1º tenant externo pago.
1.2. **Durante o dogfooding (Balanças Solution + Aferê):** Roldão Batista (sócio fundador) acumula a função informalmente, com auxílio do subagente `advogado-saas-regulado`.
1.3. **Designação formal antes do 1º tenant externo pago** é GATE bloqueante.

---

## 2. Perfil Exigido

2.1. **Conhecimentos:**
- LGPD (lei + resoluções ANPD 2/2022, 15/2024, 18/2024, 19/2024);
- Marco Civil da Internet;
- segurança da informação base (ISO 27001 awareness);
- contratos SaaS B2B;
- noções ISO 17025 (para entender retenção 25 anos).

2.2. **Pessoa física com responsabilidade pessoal** — pode ser sócio, empregado, prestador PJ ou serviço de DPO terceirizado, desde que pessoa física identificada e nomeada.

2.3. **Independência funcional** — DPO não pode acumular cargo que gere conflito (ex.: chefe de TI sozinho, sem reporte separado).

---

## 3. Atribuições (LGPD art. 41 §2º)

3.1. **Aceitar reclamações e comunicações dos titulares**, prestar esclarecimentos e adotar providências.
3.2. **Receber comunicações da ANPD** e adotar providências.
3.3. **Orientar funcionários e contratados** sobre práticas de proteção de dados.
3.4. **Executar demais atribuições determinadas pelo controlador ou estabelecidas em normas complementares**.

3.5. **Atribuições internas adicionais Aferê:**
- aprovar inclusão de nova finalidade em `finalidades-lgpd.md`;
- aprovar inclusão de novo sub-operador em `subprocessadores.md`;
- aprovar DPIAs novas/revistas;
- conduzir drill anual de incidente;
- revisar trimestralmente acessos administrativos;
- aprovar mudanças materiais na PoP.

---

## 4. Fluxo — Atendimento a Direitos do Titular (LGPD art. 18)

4.1. **Prazo legal: 15 dias corridos** (Res. CD/ANPD 2/2022 e 15/2024).

4.2. **Passos:**

| Dia | Ação |
|---|---|
| D+0 | Recebimento via canal público (dpo@dominio). Registro em ticket com correlation_id. |
| D+0..1 | Verificação de identidade proporcional (Res. ANPD 2/2022 art. 13). |
| D+1..3 | Classificação: dado sob controle Aferê (Controladora) OU sob controle Tenant. |
| D+1..5 | Se Tenant: redirecionamento ao Tenant (Controlador) com prazo restante. Comunicação ao Titular sobre redirecionamento. |
| D+3..12 | Coleta interna de informações; execução do direito (acesso/correção/eliminação/portabilidade). |
| D+12..15 | Resposta formal ao Titular; registro em trilha audit imutável. |
| D+15 | **PRAZO MÁXIMO.** Resposta enviada. |

4.3. **Tipos de resposta:**
- **Plena** — direito atendido.
- **Parcial fundamentada** — atendido no possível; justificativa para o não atendido (ex.: retenção fiscal/ISO).
- **Negativa fundamentada** — base legal autônoma impede atendimento; orientação para recurso à ANPD.

4.4. **Registro obrigatório:** correlation_id, identidade verificada (modo), tipo direito, decisão, justificativa, evidências.

---

## 5. Fluxo — Incidente de Segurança ANPD

5.1. **Prazo legal: 3 dias úteis** para comunicação à ANPD (Res. CD/ANPD 15/2024).

5.2. **Passos:**

| Tempo | Ação |
|---|---|
| T+0 | Detecção (alerta automático, denúncia, terceiro). |
| T+0..2h | Acionar equipe de resposta; contenção inicial. |
| T+2..24h | Avaliação: incidente confirmado? Há risco relevante a Titulares? |
| T+24h | Notificação ao Tenant afetado (Controlador) — DPA cl. 10.1. |
| T+24..72h úteis | Preparação da comunicação ANPD usando `incidente-anpd-modelo.md`. |
| T+3 dias úteis | **Envio à ANPD.** Comunicação a Titulares quando exigido. |
| T+30 dias | Relatório consolidado de causa raiz e remediação. |
| T+5 anos | Preservação do registro do incidente. |

5.3. **Decisão "quem comunica à ANPD":** Controlador, salvo acordo específico que delegue à CONTRATADA (Operador). Em SaaS típico Aferê, **Controlador (Tenant) comunica**; Aferê fornece dados técnicos.

5.4. **Modelo de comunicação:** `docs/conformidade/comum/incidente-anpd-modelo.md`.

---

## 6. Drill Anual Obrigatório

6.1. **Frequência:** mínimo 1 vez por ano + sempre após mudança material.

6.2. **Cenários a testar:**
- incidente de vazamento de dados de Cliente Final;
- pedido de eliminação Titular técnico com conflito ISO 17025;
- requisição judicial de logs de acesso;
- inclusão de novo sub-operador com objeção de Tenant;
- comprometimento de signatário A3 (INV-CER-FRAUD-A3-001).

6.3. **Saídas do drill:** relatório formal; ajustes em runbooks; ajustes em hooks; treinamento adicional se gap.

6.4. **Registro:** `docs/conformidade/comum/drills/drill-NNNN-MM.md`.

---

## 7. Contato Público

7.1. **Canal único primário:** dpo@[dominio-a-definir].
7.2. **Canal alternativo durante dogfooding:** roldao.tecnico@gmail.com.
7.3. **Divulgação:**
- rodapé do site público;
- seção contato da PoP;
- DPA assinado com cada Tenant;
- registro junto à ANPD quando aplicável.

---

## 8. Escalation

| Severidade | Quem é acionado | Prazo |
|---|---|---|
| Baixa | DPO resolve sozinho | 15 dias corridos |
| Média | DPO + tech-lead-saas-regulado | 7 dias |
| Alta | DPO + tech-lead + advogado-saas-regulado (subagente) | 48h |
| Crítica | DPO + Roldão + advogado humano OAB | 24h |

8.1. **Gatilhos automáticos de severidade alta/crítica:**
- incidente confirmado;
- requisição judicial;
- notificação ANPD recebida;
- pedido de Tenant grande (TOP-3 farma);
- vazamento alegado por mídia/terceiro.

---

## 9. Registro de Decisões

9.1. Toda decisão do DPO é registrada em trilha imutável (WORM) com:
- correlation_id;
- tipo de matéria (titular/incidente/sub-operador/PoP/outro);
- decisão;
- fundamentação;
- evidências consultadas;
- timestamp.

9.2. **Acesso:** Roldão + DPO + auditor independente sob NDA.

9.3. **Retenção:** 5 anos mínimo; estendida quando vinculada a obrigação fiscal/ISO.

---

## 10. Indicadores (KPIs)

| KPI | Meta |
|---|---|
| Tempo médio resposta titular | ≤ 10 dias corridos |
| % resposta dentro prazo legal | 100% |
| Drill anual executado | 1/ano mínimo |
| Incidentes comunicados ANPD dentro 3 dias úteis | 100% |
| Sub-operadores com DPA assinado | 100% antes 1º tenant pago |
| Revisão semestral de finalidades | 2/ano |
| Revisão trimestral de acessos administrativos | 4/ano |

---

## 11. Referências

- LGPD — Lei nº 13.709/2018
- Res. CD/ANPD 2/2022 (direitos titular)
- Res. CD/ANPD 15/2024 (incidente)
- Res. CD/ANPD 18/2024 (RIPD/DPIA)
- Res. CD/ANPD 19/2024 (encarregado)
- ISO/IEC 27001 (awareness)
- ISO/IEC 17025 cl. 8.4 (retenção registros)
- Marco Civil da Internet — Lei 12.965/2014

---

**FIM RUNBOOK DPO v1.0 — MINUTA**
