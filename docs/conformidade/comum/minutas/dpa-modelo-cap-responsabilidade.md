---
owner: roldao
revisado-em: 2026-06-12
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/ASSINATURA"
finalidade: extensão do dpa-modelo.md original com cláusulas de cap de responsabilidade + cláusula penal específica de vazamento + foro arbitral
relacao-com: dpa-modelo.md (versão draft anterior) — esta extensão deve ser integrada quando dpa-modelo.md sair de draft para stable na próxima rodada
---

# Extensão DPA — Cláusulas 11, 13 e adendos

> ❄️ **CONGELADO (decisão Roldão 2026-06-12, auditoria de cerimônia R19):** emendas de cláusulas por módulo estão suspensas até o gate GATE-LGPD-DPA-MASTER-1. O subagente `advogado-saas-regulado` atua no P2 SOMENTE para risco de DESIGN — não para polir prosa que será reescrita por OAB humana pré-assinatura.

> Esta minuta consolida as cláusulas críticas (Cap de Responsabilidade + Penal de Vazamento + Foro Arbitral) que devem ser integradas ao `dpa-modelo.md` quando promovido a `stable`. Documento separado para facilitar revisão OAB focada.

---

## Cláusula 11 — Responsabilidade

### 11.1. Responsabilidade do Operador

11.1.1. A CONTRATADA (Operador) responde pelos danos diretos causados ao CONTRATANTE (Controlador) em razão de descumprimento comprovado dos deveres assumidos neste DPA e na legislação aplicável (LGPD art. 42 e seguintes).

11.1.2. A responsabilidade da CONTRATADA é solidária com o CONTRATANTE perante o titular do dado quando aplicável (LGPD art. 42 §1º II), preservado o direito de regresso entre as Partes conforme cada qual deu causa.

### 11.2. Limites do CAP de Responsabilidade

11.2.1. **CAP por evento gerador:** a responsabilidade da CONTRATADA, em qualquer hipótese (contratual, extracontratual, indenizatória, regressiva), por evento gerador, fica limitada ao MAIOR entre:

(a) **R$ 500.000,00** (quinhentos mil reais); ou
(b) o equivalente a **12 (doze) mensalidades** efetivamente pagas pelo CONTRATANTE à CONTRATADA nos 12 (doze) meses anteriores à data do evento gerador.

11.2.2. **CAP agregado anual:** o limite agregado anual de responsabilidade da CONTRATADA, somando todos os eventos no período de 12 meses, fica limitado a **36 (trinta e seis) mensalidades** efetivamente pagas no mesmo período.

11.2.3. **Reinstatement contratual:** o CAP agregado anual pode ser recomposto 1 (uma) vez por ano, mediante anuência expressa por escrito da CONTRATADA e ajuste correspondente em apólice de seguro de RC Profissional (E&O) — ver ADR-0028.

### 11.3. Cláusula Penal Específica — Vazamento de Dados

11.3.1. Em caso de vazamento confirmado de dados pessoais por culpa exclusiva da CONTRATADA (excluídos casos de força maior, ato de terceiro, comprometimento de credencial do CONTRATANTE ou de seus usuários, e demais hipóteses excludentes de responsabilidade), aplica-se cláusula penal contratual no valor de **6 (seis) mensalidades** efetivamente pagas pelo CONTRATANTE nos 6 meses anteriores ao incidente.

11.3.2. A cláusula penal acima é cumulativa com as demais sanções (administrativas, civis e criminais) eventualmente cabíveis, e não substitui a indenização por dano efetivo, observado o CAP do item 11.2.

11.3.3. **Atenuação:** o valor da cláusula penal pode ser reduzido pelo juiz quando manifestamente excessivo (CC art. 413), respeitada a função de incentivo ao cumprimento.

### 11.4. Excluídos do escopo de responsabilidade

A responsabilidade da CONTRATADA não abrange:

(a) danos indiretos, lucros cessantes ou perda de chance que ultrapassem o CAP de 11.2;
(b) danos decorrentes de uso indevido da Plataforma pelo CONTRATANTE ou seus usuários;
(c) danos por força maior, caso fortuito ou ação de terceiro;
(d) danos por indisponibilidade de sub-operador (sujeitos a coberturas próprias do sub-operador e/ou apólice CBI — ver ADR-0028);
(e) danos resultantes de dados inseridos pelo CONTRATANTE que violem direito de terceiro;
(f) sanções aplicadas ao CONTRATANTE em razão de descumprimento próprio independente da CONTRATADA;
(g) hipóteses de dolo ou culpa grave do CONTRATANTE.

---

## Cláusula 13 — Foro e Resolução de Conflitos

### 13.1. Cláusula Arbitral

13.1.1. **As disputas decorrentes deste DPA serão resolvidas por arbitragem**, com renúncia expressa das Partes ao foro judicial estatal, salvo para tutela cautelar urgente e execução do laudo arbitral.

13.1.2. **Câmara:** Câmara de Arbitragem do Mercado de São Paulo — **CAM-CCBC** (Centro de Arbitragem e Mediação da Câmara de Comércio Brasil-Canadá).

13.1.3. **Sede:** Cidade de São Paulo, Estado de São Paulo, Brasil.

13.1.4. **Idioma:** Português (Brasil).

13.1.5. **Regulamento:** vigente na data da instauração do procedimento arbitral.

13.1.6. **Número de árbitros:** 1 (um) árbitro único quando o valor em disputa for até R$ 500.000,00; 3 (três) árbitros para valores superiores.

13.1.7. **Lei aplicável:** legislação brasileira, com observância especial à LGPD, Marco Civil da Internet, Código Civil e demais normas regulatórias setoriais (ISO/IEC 17025, NIT-DICLA, Receita Federal) quando pertinentes.

13.1.8. **Confidencialidade:** o procedimento arbitral é confidencial, ressalvada a publicidade exigida por lei ou para defesa em outras esferas.

13.1.9. **Custos:** rateados conforme regulamento da CAM-CCBC; vencido suporta integralmente conforme decisão final.

### 13.2. Tutela cautelar urgente

13.2.1. Qualquer das Partes pode pleitear tutela cautelar urgente perante o **foro da Comarca de São Paulo/SP** antes da instauração da arbitragem ou em paralelo a esta, exclusivamente para:

(a) proteger evidências em risco de perecimento;
(b) impedir continuidade de vazamento de dados;
(c) garantir cumprimento de ordem da ANPD ou de outro órgão regulador;
(d) outras hipóteses de urgência incompatíveis com o tempo da arbitragem.

13.2.2. A medida cautelar não suspende nem prejudica a competência arbitral para o mérito.

---

## Adendos relevantes

### A. Drill Anual ANPD

A CONTRATADA obriga-se a executar drill anual de incidente de segurança simulado, com produção de relatório arquivado. Resultado é compartilhado com o CONTRATANTE mediante solicitação formal, observada confidencialidade dos demais Tenants.

### B. Inserção no DPA Master

Estas cláusulas 11, 13 e adendos devem ser integradas ao `dpa-modelo.md` quando este sair de `draft` para `stable`, substituindo qualquer cláusula equivalente anterior.

### C. Pendências bloqueantes pré-assinatura

- [ ] Razão social e CNPJ da CONTRATADA definidos
- [ ] DPO formalmente designado e nomeado neste DPA
- [ ] Validação OAB destas cláusulas (especialmente 11.2 — cap quantitativo e 11.3 — penal específica)
- [ ] Apólice de E&O contratada com capital compatível (ADR-0028 Modalidade 1 — R$ 5-10M agregado)
- [ ] Apólice Cyber contratada (ADR-0028 Modalidade 2 — R$ 5M + reinstatement)

---

**FIM Extensão DPA v1.0 — MINUTA — REQUER VALIDAÇÃO OAB**
