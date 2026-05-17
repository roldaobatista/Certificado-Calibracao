# Painel do dono

> **Status atual da fase, do escopo, das decisões pendentes — em PT-BR pra o Roldão.**
>
> Atualizado por agente toda sessão produtiva. **Este é o único lugar onde você precisa olhar pra saber "o que está acontecendo no meu projeto agora".**

---

## ⏸️ AÇÃO COM TERCEIROS — DIFERIDA PRA V2 (2026-05-17)

**Decisão Roldão (2026-05-17):** não haverá busca de cliente externo pago na janela atual. **Os 4 itens abaixo ficam diferidos** — só viram crítico quando 1º cliente externo aparecer. Ver memória [[sem-cliente-externo-na-janela-atual]] + `docs/adr/0001-stack.md` (Portão 1 diferido).

**Janela atual:** MVP-1 sai como **dogfooding em Balanças Solution** (própria empresa do Roldão). Risco aceito conscientemente.

| Item | Quando contratar | Custo estimado | Por que vira crítico (V2) |
|---|---|---|---|
| Contrato vendor↔tenant com limitação de responsabilidade | Antes do 1º externo | R$ 5-15k (one-time) | R-042 score 20 vira ativo |
| Seguro RC profissional + RC cibernética | Antes do 1º externo | R$ 3-15k/ano | R-042 + R-014 |
| DPA-modelo pra tenant repassar ao cliente | Antes do 1º externo | R$ 2-5k (one-time) | R-024 + R-028 |
| Dossiê de validação 17025 do próprio software | Antes do 1º externo (consultor RBC humano) | R$ 8-25k | NC do tenant cai na conta do vendor |

**Total diferido:** R$ 18-60k. Não gastar agora.

**Próxima ação sua na janela atual:** começar Foundation F-A (multi-tenant + RLS + audit, 4-6 semanas) com critérios da ADR-0001 Portão 3 aplicados — sem spike descartável; ver [[nao-construir-codigo-descartavel]]. R-042 fica como risco aceito enquanto não há cliente externo.

---

## ⏱️ Estado em 2026-05-17 NOITE (pós-auditoria 12 agentes + 24 correções aplicadas)

**Fase:** **Rodada 0 Discovery — batch 3 EXECUTADO + auditoria 12 agentes + 24 achados aplicados em lote**
**Última atividade:** sessão da noite 17/05/2026 — Roldão pediu auditoria com 12 agentes em ângulos novos (sem repetir batches 1+2). Disparados 12 auditores em paralelo cobrindo: Pricing, Sequenciamento MVP, Calibração scores, Defensibilidade, Testabilidade, ICP, Legal/trabalhista, GTM, Founder bias, Cross-doc, Blind spots, LEAP #1. **24 achados (12 críticos + 12 altos).** Roldão aprovou ACEITAR TUDO. 4 subagentes em paralelo aplicaram as 24 correções em 9 docs do Discovery.

**O que mudou nos docs (delta total: ~3.500 linhas):**
- **OST:** 12 Opportunities (era 8); Foundation explícita pré-MVP; re-sequenciamento Wave A (OP7+OP2+OP10) → Wave B (OP1+OP4+OP5+OP8+OP3); 4 OPs novas (OP9 BIG-03 + OP10 BIG-06 + OP11 cobrança + OP12 painel); Confidence dual-axis (dono × mercado); pricing reconciliado mix A=10%/B=55%/C=25%/D=10%; IDs canônicos R-049..R-057
- **Dores:** Top 5 corrigido removendo halo founder-customer: #10 NFS-e → #02 recalibração (15k era 28,5k) → #04 NIT-DICLA-030 → #01 cadastro → #05 status OS (promovida). Dor #19 frota desceu pra top 8. 8 scores recalibrados.
- **Assumption-map:** 61 premissas (+ V-15 CAC, F-17 onboarding, F-18 CS, F-19 CERTI). F-1 com 10 kill switches + planos B/C/D explícitos. Van Westendorp N=30 → N=5-8.
- **Riscos:** 65 riscos (8 novos R-058..R-065). R-001 elevado pra 20 (severidade reforçada por 3 auditores). R-034 promovido 4→12 (CERTI). R-046 elevado 10→15 (UMC roubo).
- **Normas:** 20 invariantes (+INV-017 ICP-Brasil + INV-018 RT vendor + INV-019 dossiê 7.11 + INV-020 Lei 13.103/2015)
- **Personas:** 16 personas (+ Persona 15 Diego Consultor RBC = canal #1 + Persona 16 Andréia/CS L1)
- **Concorrentes:** Auvo virou ameaça #1 (9-12 meses), não Visma (18 meses). Pricing reconciliado. 3 dos 9 gaps reclassificados como backlog.
- **Domínio:** "decisão fundadora" desambiguada (PRODUTO Roldão 17/05 vs ENGENHARIA D1-D6)
- **Glossário:** 236 termos (+9: RICE, Van Westendorp, fake door, smoke test, ride-along, time-trial, leap-of-faith, conjoint analysis, decisão fundadora)

**Bloqueio atualizado (2026-05-17 noite final):** Foundation F-A → F-H (4-6 semanas pra F-A; resto em paralelo onde possível) + Wave A em Balanças Solution. **Entrevistas externas e D-aud7-1 diferidos pra V2** — Roldão decidiu não buscar cliente externo na janela atual ([[sem-cliente-externo-na-janela-atual]]).

**Próximo passo recomendado pelo agente:**
1. ADR-0001 stack — **candidata aprovada via Portões 2+3** (Portão 1 diferido pra V2)
2. Foundation F-A (multi-tenant + RLS + audit) — 4-6 semanas com critérios da ADR-0001 Portão 3, **construída em ambiente local (Docker compose)**; deploy a servidor remoto só quando Roldão autorizar ([[deploy-so-quando-roldao-decidir]])

**Estado da documentação após v7 (2026-05-17 noite +6h):**
- **Documentação estrutural completa.** 5 domínios + 19 módulos com 8 docs cada (~152 arquivos).
- **5 OPs novas (OP13/14/15/16/17)**, **7 INVs novos (INV-021..027)**, **3 ADRs reais (0004/0005/0006)** adicionadas.
- **Total ~270 docs** distribuídos em 8 famílias.
- **O que falta:** specs por feature (`specs/<NNN>/{spec,plan,tasks}.md`) — só criar quando feature entrar em desenvolvimento.
- **Próximo bloqueio real:** Roldão autorizar início de Foundation F-A em ambiente local.
3. Wave A em Balanças Solution (NFS-e + Certificado + OS) por ≥ 3 meses
4. Família 6 calibração ISO 17025 (`docs/dominios/metrologia/modulos/calibracao/`) — gap regulatório técnico

### ✨ Achados consolidados pós-auditoria + 4 decisões fundadoras

1. **9 gaps defensáveis simultâneos** (era 5 — agora 9 após decisões fundadoras): BIG-01 ciclo completo + BIG-03 perfis A/B/C/D + BIG-04 NFS-e multi-município + BIG-06 Metrologia Legal + BIG-07 portal cliente + **BIG-08 Frota+UMC+Caixa** + **BIG-09 Comissões configuráveis** + **BIG-10 CRM 360°+Automações** + **BIG-12 Estoque multi-local com lacre/selo INMETRO**. Nenhum concorrente cobre mais de 5/12.
2. **Custo do status quo corrigido pra R$ 35-50k/mês** (era R$ 10-22k subestimado). Esse é o número que vende.
3. **WhatsApp Business universal (~100%):** integração obrigatória no MVP.
4. **Janela competitiva curta:** R-035 (Visma compra Cali/Metroex) elevado pra score 20. Chegar a 50+ clientes antes da próxima aquisição da Visma.
5. **Acessibilidade INV-016 obrigatória** (LBI Lei 13.146/2015). Sem WCAG 2.1 AA, ação MP + reprovação em licitação.
6. **Transferência de risco vendor↔tenant** (R-042 score 20) é existencial — sem contrato/seguro/DPA/dossiê, qualquer bug pode falir o vendor.

### ✨ 3 achados estratégicos pra você ler primeiro

1. **GAP CONFIRMADO** — "OS + calibração ISO 17025 + NFS-e municipal multi-prefeitura" não existe no mercado BR de forma nacional. Único concorrente que combina (FP2 Tecnologia) cobre só Santa Maria/RS. **Sua tese de produto está sustentada por evidência**. Detalhe em `docs/discovery/concorrentes.md` §4.
2. **Risco mais grave que apareceu (R18, score 25)** — NIT-DICLA-030 rev. 15 (Cgcre dez/2024) item 8.2.6: **certificado de calibração sem resultado de medição + incerteza é rejeitado**. Vira regra de bloqueio no sistema (não deixa nem emitir). Detalhe em `docs/discovery/riscos.md`.
3. **Concorrente nacional mais perigoso = Cali LAB/WEB** (Canoas/RS, desde 2000, homologado pela Fundação CERTI). Vantagem nossa: Cali ainda é desktop-first e não tem fiscal/NFS-e. **Janela competitiva é estreita** — se Cali fechar parceria com Bling/Omie pra fiscal, perdemos diferencial #1.

---

## 🚨 Decisões pendentes que SÓ VOCÊ pode tomar

### ✅ Decisões da auditoria — todas aplicadas (16/05/2026)

> Roldão aprovou todas as 9 decisões da auditoria. Aplicadas em sequência. Resumo do que mudou:

| # | Decisão | Status |
|---|---|---|
| **D-aud-1** | Piso de preço subido: R$ 500-1.000/mês com 1 mês grátis (era R$ 300) | ✅ aplicado em `concorrentes.md` §9 |
| **D-aud-2** | Fichas TOTVS Protheus + Qualyteam + SAP B1 adicionadas | ✅ aplicado em `concorrentes.md` §14 |
| **D-aud-3** | Invariante #4 quebrado em INV-004a, INV-004b, INV-004c | ✅ aplicado em `normas-e-regulacao.md` §8.1 |
| **D-aud-4** | Invariante #7 (BaaS) movido pra ADR fiscal; INV-010 a INV-014 adicionados | ✅ aplicado em `normas-e-regulacao.md` §8.1 (total 14 invariantes) |
| **D-aud-5** | Domínio Metrologia subdividido em 3 (Execução / Padrões / Garantia) | ✅ aplicado em `dominio-de-negocio.md` §Mapa |
| **D-aud-6** | "Gestão de Competências e Autorizações" promovido pra MVP-1 obrigatório | ✅ aplicado em `dominio-de-negocio.md` §Mapa |
| **D-aud-7** | Metrologia Legal (IPEMs, balanças, bombas) adicionado como domínio novo | ✅ **CONFIRMADO NO MVP** — Roldão confirmou em 16/05/2026 que calibra TODOS os tipos de balança (comercial, industrial, rodoviária, processos), portanto Metrologia Legal entra obrigatoriamente |
| **D-aud-8** | IDs de risco padronizados pra R-001..R-038 (38 riscos consolidados) | ✅ aplicado em `riscos.md` + `concorrentes.md` §7 |
| **D-aud-9** | ADR-0000 (Uso de IA) criada com 5 princípios fundadores | ✅ aplicado em `docs/adr/0000-uso-de-ia.md` |

### 🆕 Decisão fundadora de produto (16/05/2026)

**Perfis de empresa no setup do tenant** — Roldão definiu que o sistema precisa suportar **4 perfis** distintos:
- **A** — Acreditada ISO 17025 + RBC (selo Cgcre + ILAC MRA)
- **B** — Não-acreditada, mas usa padrões RBC (certificado "rastreável ao RBC")
- **C** — Quer migrar pra ISO/acreditação no futuro (regras editáveis, trilha de evolução)
- **D** — Calibração comercial básica (sem rastreabilidade RBC)

Aplicado em `dominio-de-negocio.md` §Perfis de empresa + `normas-e-regulacao.md` §8.1 (invariantes ganharam coluna "Escopo por perfil"; INV-015 novo bloqueia emissão de certificado de tipo superior ao perfil declarado).

**Tipos de balança calibrada** — comercial, industrial, rodoviária, processos, analítica, bancada, contadora, gancho, plataforma + outros instrumentos (manômetro, termômetro, paquímetro etc.). Confirmou Metrologia Legal no MVP.

**3 riscos novos:**
- **R-039** — Tenant declara perfil A sem acreditação real (fraude; score 15)
- **R-040** — Cliente final esquece verificação periódica INMETRO obrigatória (score 12) — **selo INMETRO em si não vence; o que vence é a obrigação de verificação anual**
- **R-041** — Tenant marca tipo de instrumento no setup que não atende tecnicamente (score 9)

**3 correções aplicadas em 16/05/2026 (Roldão corrigiu o agente):**
1. Selo INMETRO/IPEM **não tem vencimento estampado** — o que vence é a obrigação de verificação periódica anual
2. **Perfil B** tem regras 17025 **totalmente configuráveis** (não absolutas) — empresa B com ambição de acreditação pode ativar tudo; "B-leve" pode desativar quase tudo
3. **Tipos de instrumento atendidos** são **configuráveis no setup** — empresa marca 1, alguns ou todos; pode adicionar depois (self-service)

### Decisões anteriores que continuam pendentes

| Decisão | Por quê preciso | Status |
|---|---|---|
| **Autorizar batch 2** (personas + JTBD + jornada-atual) — só depois das 9 acima | Agente pode tocar sozinho | ⏳ aguardando |
| **Nome final do produto** | "Aferê" é provisório; decidir antes de comprar domínio | ⏳ aguardando |
| **Licença (LICENSE)** | MIT, Apache, proprietária, etc. Necessário antes de 1º release público | ⏳ aguardando |
| **Quem é o signatário técnico** dos certificados de calibração (RBC NIT-DICLA-021 exige metrologista PF responsável) | ⏳ você ou contratar | ⏳ aguardando |
| **Confirmar referência: ILAC G8 vs WELMEC 7.2 / OIML D 31** | Você pediu ILAC G8 pra "validação de software" mas G8 é regra de decisão. Referências corretas pra validação de software são WELMEC 7.2 e OIML D 31 | ⏳ aguardando |

---

## 📋 Últimas decisões dos agentes (sem consultar você)

> Lista do que agente decidiu sozinho. Detalhes em `governanca/auditoria-decisoes-autonomas.md` (a criar). Tudo aqui foi feito dentro dos `limites-autonomia.md`.

- **2026-05-16:** D5 (CODEOWNERS) expandida de 5 → 10 paths após Auditor 1 v2 alertar que 5 paths é fraco demais pra ERP financeiro. Você confirmou.
- **2026-05-16:** Estrutura criada não inclui ~100 docs lazy do v5 — segue regra do próprio documento. Agente pode criar conforme rodadas avançarem.
- **2026-05-16:** Rodada 0 batch 1 executada autonomamente — 4 artefatos preenchidos via pesquisa pública (24 concorrentes mapeados, 15 municípios cobertos para NFS-e, 11 riscos novos identificados). Detalhe em `governanca/auditoria-decisoes-autonomas.md`.

---

## ⚠️ Alertas (vermelhos)

> Coisas que o agente quer chamar sua atenção AGORA.

1. **Nome "Aferê" provisório.** Não compre domínio ainda.
2. **Risco "founder is customer".** Discovery PRECISA incluir 5–10 OUTRAS empresas pra evitar customização disfarçada. Você terá que entrevistar.
3. **Família 5 (3 auditores-agentes) ainda é vaporware.** Prompts dos auditores precisam ser escritos pra "governança IA" não ser PowerPoint. Saí da Rodada 4.

---

## 📊 Métricas (vai preencher conforme rodadas avançam)

- Documentos criados: ~33 de ~140 previstos (24%)
- Documentos preenchidos com conteúdo real: 4 da Rodada 0 (concorrentes, normas, domínio, riscos)
- Rodadas concluídas: 0 de 9 (Rodada 0: 4/15 artefatos)
- Concorrentes mapeados: 24 (16 BR + 8 internacionais)
- Municípios cobertos para NFS-e: 15 prioritários
- Riscos catalogados: 26 (top 12 com score ≥ 12)
- Invariantes candidatos identificados: 10 (entrada para `REGRAS-INEGOCIAVEIS.md`)
- Features do MVP-1 entregues: 0
- Auditorias rodadas: 2 (rodada 1 sobre v2, rodada 2 sobre v4)
- Memórias salvas: 14 entradas em `MEMORY.md`

---

## 🗓️ Próximas 3 ações (do agente)

1. ⏳ Aguardar você revisar batch 1 ou autorizar batch 2.
2. Batch 2 (sozinho): `personas-detalhadas.md` + `jobs-to-be-done.md` + `jornada-atual-sem-produto.md`.
3. Preparar `treinamento-entrevista-roldao.md` pra você revisar antes das entrevistas piloto.

---

## Como ler este painel

- 🚨 Pendente que precisa de você AGORA
- 📋 Histórico do que aconteceu (sem ação pra você)
- ⚠️ Alerta — leia mas não precisa agir agora
- 📊 Métrica
- 🗓️ Próximo passo do agente (sem precisar de você)
