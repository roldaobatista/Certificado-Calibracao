---
owner: roldao
revisado-em: 2026-05-29
status: draft
idioma: pt-BR
limite-linhas: 280
proposito: Avaliação de Impacto à Proteção de Dados Pessoais (AIPD/DPIA) — análise de risco aos titulares antes de iniciar tratamento de alto risco (LGPD Art. 38; GDPR Art. 35; EU AI Act Art. 13-14 quando há IA)
---

<!--
template: aipd.template.md
destino: docs/conformidade/lgpd/aipd-<nome-do-tratamento>.md
uso: uma AIPD por tratamento de alto risco. Não fazer uma só para o sistema todo.
quando obrigatório:
  - tratamento sistemático e em larga escala de dado pessoal
  - dado sensível (LGPD Art. 5 II) em qualquer escala
  - decisão automatizada que afeta o titular (LGPD Art. 20 / EU AI Act)
  - monitoramento de comportamento em espaço público
  - tratamento de dado de criança / adolescente
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
-->

# AIPD — Avaliação de Impacto à Proteção de Dados

> **AIPD** (também chamada **DPIA** no GDPR europeu) = relatório obrigatório que mostra **o que pode dar errado para a pessoa** cujo dado vamos tratar, e o que faremos para reduzir esse risco. Sem AIPD, a ANPD pode multar e o tratamento pode ser proibido. Quando há decisão por máquina sobre a pessoa (escore, recomendação, recusa automática), o **EU AI Act Art. 13-14** também exige supervisão humana descrita aqui.

## 1. Identificação do tratamento

| Campo | Valor |
|---|---|
| Nome do tratamento | Transcrição de áudio do WhatsApp + resposta assistida por IA ao cliente |
| Sistema/módulo responsável | Camada de IA (Agente de Transcrição → cérebro/agentes → fila de aprovação) |
| Data desta avaliação | 2026-05-29 |
| Próxima revisão obrigatória | 2027-05-29 (ou ao mudar finalidade) |
| Responsável técnico | ⚠️ a definir na fase de stack (tech-lead) |
| Encarregado (DPO) que aprovou | Roldão (encarregado inicial) — ⚠️ assinar ao fechar a descoberta |

## 2. Contexto e necessidade

Resumir em **uma única página** (alguém não-técnico precisa entender):

- **Por que** este tratamento existe? Que problema de negócio resolve?
- **O que muda** para a pessoa cujo dado é tratado, comparado à situação atual?
- **Há alternativa menos invasiva** (não coletar; coletar menos; usar dado anonimizado)? Por que foi descartada?

**Preenchido:**
- **Por que existe:** o atendimento da Balanças Solution é majoritariamente por **áudio** no WhatsApp (D-PROD-013). Para entender e responder o cliente, a IA precisa transcrever o áudio (voz→texto) e compor a resposta.
- **O que muda para a pessoa:** o cliente é atendido mais rápido; o áudio dele é convertido em texto por máquina e usado para gerar uma resposta — que **só vai ao cliente após revisão humana** (fila de aprovação). Não há decisão automatizada que afete o cliente sem um humano aprovar (D-PROD-006, NF-002).
- **Alternativa menos invasiva:** transcrever **localmente** (o áudio não sai da infraestrutura) em vez de serviço pago no exterior — é a recomendação (melhor para LGPD e custo). Não transcrever (pedir ao cliente que escreva) foi descartado: piora muito a experiência e contraria o canal real.

## 3. Dados tratados

| Categoria do dado | Item específico | É sensível? (Art. 5 II LGPD) | De onde vem | Quanto tempo guarda |
|---|---|---|---|---|
| Áudio (voz) | mensagem de voz bruta do cliente | **sim — voz pode revelar dado sensível** | WhatsApp (PTT) | **3 meses, depois descarte** |
| Conteúdo transcrito | texto do que o cliente falou | depende do conteúdo | transcrição (STT) | 2 anos |
| Identificação | telefone, nome (vínculo ao cadastro) | não | WhatsApp + Aferê | enquanto cliente + 5 anos |
| Dados de terceiros | nome/voz citados nos áudios/grupo | possível | conversas | só agregado/anonimizado (R-020) |

> **Atenção dado sensível:** se houver QUALQUER dado de saúde, biometria, origem racial/étnica, convicção religiosa, opinião política, filiação sindical, dado genético, vida sexual ou orientação sexual — esta AIPD vira **obrigatória e crítica**, e o DPO precisa aprovar explicitamente. Não tratar como rotina.

## 4. Base legal (LGPD Art. 7 ou Art. 11)

Qual hipótese da LGPD autoriza este tratamento? **Sem base legal, o tratamento é ilegal.**

| Inciso | Quando aplica | Aplica aqui? |
|---|---|---|
| Art. 7 I — consentimento | titular disse "sim" de forma livre, informada, inequívoca | <sim/não — se sim, como coleta o consentimento> |
| Art. 7 V — execução de contrato | sem o dado o contrato não é cumprido | **SIM** — sem entender o áudio não há como atender/orçar |
| Art. 7 VI — exercício regular de direito em processo | litígio | <sim/não> |
| Art. 7 IX — interesse legítimo (Art. 10) | atende interesse do controlador SEM ferir direito do titular — exige teste de balanceamento | <sim/não — se sim, anexar teste de balanceamento> |
| Art. 11 (sensível) | bases mais restritas — consentimento específico, obrigação legal, proteção da vida, tutela da saúde, etc. | <sim/não> |

## 5. Grupos vulneráveis afetados

| Grupo | Tratamos dado dele? | Cuidado adicional aplicado |
|---|---|---|
| Crianças e adolescentes (até 18) | <sim/não> | <consentimento dos pais; dados mínimos; sem perfilamento publicitário> |
| Idosos (60+) | <sim/não> | <linguagem simples nas comunicações; canal não-digital alternativo> |
| Pessoas em vulnerabilidade econômica/social | <sim/não> | <evitar perfilamento que reforce exclusão> |
| Pacientes / titulares de dado de saúde | <sim/não> | <sigilo médico; acesso restrito por papel> |
| Usuários com deficiência | <sim/não> | <acessibilidade WCAG nos canais de exercício de direito> |

## 6. Análise de risco (probabilidade × impacto)

Cada cenário ruim recebe nota de 1 (baixo) a 5 (crítico) em probabilidade e impacto. Risco = prob × impacto. Acima de 12 exige mitigação obrigatória antes de operar.

| Cenário ruim para o titular | Prob (1-5) | Impacto (1-5) | Risco (P×I) | Mitigação aplicada | Risco residual |
|---|---|---|---|---|---|
| Transcrição errada vira ação/orçamento errado (R-016) | 3 | 4 | 12 | score de confiança; confirmar em texto antes de agir; revisão na fila | 6 |
| IA inventa diagnóstico técnico sem base (R-017) | 3 | 4 | 12 | marca "lacuna"; não chuta; citação de fonte; carga do cérebro pré-requisito | 6 |
| Vazamento do áudio/dado a terceiro ou entre empresas (R-020) | 2 | 5 | 10 | STT local (áudio não sai); isolamento multi-tenant; descarte em 3 meses | 4 |
| Vazamento de conhecimento técnico restrito a cliente (R-022) | 3 | 3 | 9 | classificação de acesso por fonte + guardrail + teste de vazamento (D-PROD-016) | 4 |
| Manipulação por mensagem maliciosa (prompt injection — R-007) | 3 | 4 | 12 | nunca executar instrução do conteúdo; ação externa exige aprovação; pseudonimização | 6 |

**Tabela de leitura do risco:**

| Faixa | Significado | Ação |
|---|---|---|
| 1-4 | risco baixo | aceitar e monitorar |
| 5-9 | risco médio | mitigar antes de operar |
| 10-14 | risco alto | mitigar obrigatoriamente + reaprovação do DPO |
| 15-25 | risco crítico | NÃO operar até reduzir; consultar ANPD se mitigação inviável (LGPD Art. 38 § único) |

## 7. Medidas mitigatórias técnicas e administrativas

| Medida | Tipo | Responsável | Status (implementada / planejada) | Teste que comprova |
|---|---|---|---|---|
| <criptografia AES-256-GCM em repouso> | técnica | <segurança> | implementada | <INV-SEC-CRYPTO-01> |
| <controle de acesso por papel — RBAC> | técnica | <segurança> | implementada | <INV-SEC-AUTHZ-01> |
| <treinamento anual da equipe em LGPD> | administrativa | <DPO> | planejada — próxima turma <data> | <registro de presença> |
| <contrato de operação com bureau Serasa> | administrativa | <jurídico> | implementada | <cópia em pasta de contratos> |
| <auditoria automatizada de viés a cada release> | técnica | <ML-owner> | planejada | <pipeline `audit-bias.yml`> |

## 8. Supervisão humana (LGPD Art. 20 + EU AI Act Art. 13-14)

**Obrigatório quando há decisão automatizada que afeta a pessoa.** Se este tratamento não envolve decisão por máquina, marcar **N/A** e justificar.

> **Princípio do produto (D-PROD-006, NF-002):** NÃO há decisão automatizada que vá ao cliente sem humano. **100% do que vai ao cliente passa pela fila de aprovação (Inbox)** — a IA sugere, a pessoa aprova/edita/rejeita. Isso atende o Art. 20 por construção.

### 8.1 Direito de revisão humana
- **Como o titular pede revisão:** o cliente pode sempre pedir "falar com humano" no próprio WhatsApp; e há o canal de direitos do titular (`direitos-do-titular.md`).
- **Quem revisa:** o dono (Roldão) ou as 2 pessoas do escritório na fila de aprovação — nunca a "máquina sozinha".
- **SLA da revisão:** conforme a Inbox operacional (ver `jornadas.md`): emergência ≤5 min, orçamento ≤1h, etc.
- **Regra de bloqueio:** desconto acima do teto, valor > R$ 10 mil ou assunto regulado **travam** até revisão humana.

### 8.2 Transparência (Art. 20 §1 LGPD)
- **Informação ao titular sobre os critérios usados:** <link público + linguagem simples>.
- **O que NÃO revelamos:** <pesos exatos do modelo — segredo comercial — mas revelamos a lógica geral>.

### 8.3 Monitoramento contínuo do modelo (se há ML)
- Indicadores de drift, viés, qualidade preditiva — onde vivem: <link dashboard>.
- Frequência de reavaliação: <ex: mensal>.
- Critério para retreinar / desligar: <ex: paridade demográfica >0,8 entre grupos protegidos; AUC > 0,75>.

## 9. Consulta a partes interessadas

| Parte | Foi consultada? | Quando | Posição registrada |
|---|---|---|---|
| Encarregado (DPO) | <sim/não> | <data> | <aprovou / pediu ajuste — link da ata> |
| Equipe de segurança | <sim/não> | <data> | <link> |
| Equipe jurídica | <sim/não> | <data> | <link> |
| Representante de titulares (quando aplica — ex: associação de consumidores) | <sim/não> | <data> | <link> |
| ANPD (quando risco residual permanecer ALTO) | <sim/não> | <data> | <protocolo da consulta> |

## 10. Decisão final

Marcar uma e justificar:

- [ ] **PROSSEGUIR** — risco residual aceito pelo DPO. Operação pode iniciar.
- [x] **PROSSEGUIR COM AJUSTES** — implementar antes do piloto: (1) transcrição local; (2) score de confiança + confirmação ao cliente; (3) descarte do áudio em 3 meses com auditoria; (4) classificação de acesso do cérebro + teste de vazamento; (5) defesa contra prompt injection; (6) fila de aprovação operando. Nova revisão ao fechar a descoberta.
- [ ] **PARAR** — risco residual incompatível com LGPD/AI Act.

**Assinatura do DPO:** ⚠️ Roldão — assinar ao fechar a descoberta
**Assinatura do responsável técnico:** ⚠️ a definir na fase de stack

## 11. Vinculação

- ROPA: `docs/conformidade/lgpd/ropa.md` (linha do tratamento avaliado aqui).
- Threat model: `docs/seguranca/threat-model.md` (ameaças técnicas vinculadas).
- Direitos do titular: `docs/conformidade/lgpd/direitos-do-titular.md` (canal de revisão).
- Política de retenção: `docs/conformidade/lgpd/retencao-dados.md`.
- Runbook de incidente: `docs/operacao/runbooks/incidente-seguranca.md`.

## 12. Checklist de promoção draft → stable

- [ ] Todos os placeholders `<...>` substituídos por dados reais.
- [ ] Tabela de risco preenchida com mitigação para todo risco ≥10.
- [ ] Decisão final marcada e assinada pelo DPO.
- [ ] Linha correspondente existe e está atualizada no ROPA.
- [ ] Se há decisão automatizada, seção 8 está completa (canal de revisão funciona ponta-a-ponta).
- [ ] Frontmatter `revisado-em` atualizado; `status: stable`.
- [ ] Próxima revisão agendada (máximo 12 meses ou ao mudar finalidade).
