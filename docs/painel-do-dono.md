# Painel do dono

> **Status atual da fase, do escopo, das decisões pendentes — em PT-BR pra o Roldão.**
>
> Atualizado por agente toda sessão produtiva. **Este é o único lugar onde você precisa olhar pra saber "o que está acontecendo no meu projeto agora".**

---

## ⏱️ Estado em 2026-05-16 (atualizado pós Rodada 0 batch 1)

**Fase:** **Rodada 0 Discovery — batch 1 CONCLUÍDO** (4 de 15 artefatos)
**Última atividade:** pesquisa de concorrentes (24 mapeados — 16 BR + 8 internacionais), normas/regulação (15 municípios + ISO 17025 + LGPD 2024-26 + Bacen/PIX 2025 + PCI-DSS 4.0.1), domínio de negócio (mapa preliminar de domínios → módulos), riscos (11 novos adicionados).
**Bloqueio:** nenhum — pronto pra você revisar batch 1 ou autorizar batch 2.
**Próximo passo recomendado pelo agente:** **decidir 9 itens estratégicos pendentes** (lista abaixo) antes de autorizar batch 2. Auditoria interna de 4 agentes já aplicou todas as correções factuais — só decisões de produto/escopo precisam de você.

### ✨ 3 achados estratégicos pra você ler primeiro

1. **GAP CONFIRMADO** — "OS + calibração ISO 17025 + NFS-e municipal multi-prefeitura" não existe no mercado BR de forma nacional. Único concorrente que combina (FP2 Tecnologia) cobre só Santa Maria/RS. **Sua tese de produto está sustentada por evidência**. Detalhe em `docs/discovery/concorrentes.md` §4.
2. **Risco mais grave que apareceu (R18, score 25)** — NIT-DICLA-030 rev. 15 (Cgcre dez/2024) item 8.2.6: **certificado de calibração sem resultado de medição + incerteza é rejeitado**. Vira regra de bloqueio no sistema (não deixa nem emitir). Detalhe em `docs/discovery/riscos.md`.
3. **Concorrente nacional mais perigoso = Cali LAB/WEB** (Canoas/RS, desde 2000, homologado pela Fundação CERTI). Vantagem nossa: Cali ainda é desktop-first e não tem fiscal/NFS-e. **Janela competitiva é estreita** — se Cali fechar parceria com Bling/Omie pra fiscal, perdemos diferencial #1.

---

## 🚨 Decisões pendentes que SÓ VOCÊ pode tomar

### Decisões da auditoria interna (9 itens — pra você decidir 1 a 1)

| # | Decisão | Recomendação do agente | Status |
|---|---|---|---|
| **D-aud-1** | Subir piso de preço de R$ 300/mês pra R$ 500-1.000/mês com 1 mês grátis | **Aceitar** — Auditor 1 mostrou que volume de lab calibrador é menor que e-commerce; R$ 300 cria expectativa de "barato" difícil de reverter | ⏳ |
| **D-aud-2** | Adicionar fichas dedicadas de TOTVS Protheus + Qualyteam + SAP Business One BR | **Aceitar** — TOTVS é gigante adjacente que aparece em todo prospect; Qualyteam ficou só nas fontes; SAP B1 é referência | ⏳ |
| **D-aud-3** | Refinar invariante #4 ("software validado") em 3 sub-regras testáveis (aprovação do responsável técnico antes de prod; revalidação de cálculo de incerteza; versão do software gravada em cada certificado) | **Aceitar** — Auditor 2 alertou que está vago demais pra virar hook bloqueante | ⏳ |
| **D-aud-4** | Mover invariante #7 (BaaS fiscal único) pra ADR + adicionar invariantes #11-#15 (retenção 17025, padrão vencido bloqueia emissão, NC bloqueia emissão, confidencialidade 4.2 com log, versão do software em cada certificado) | **Aceitar** — BaaS é arquitetura, não regra de conformidade. Os 5 novos invariantes fecham lacunas críticas | ⏳ |
| **D-aud-5** | Subdividir domínio Metrologia em 3 sub-domínios (Execução de calibração / Padrões e rastreabilidade / Garantia da validade) | **Aceitar com ressalva** — só fazer quando o módulo Calibração entrar no faseamento; até lá é só nota | ⏳ |
| **D-aud-6** | Mover Gestão de Competências e Autorizações pra dentro do MVP-1 (não esperar pós-MVP) | **Aceitar** — Auditor 3 alertou que 17025 6.2 exige autorização documentada do signatário. Sem isso o sistema NÃO PODE emitir certificado válido. Escopo magro: matriz competência × grandeza + validade + autorização por escopo | ⏳ |
| **D-aud-7** | Adicionar metrologia legal (IPEMs/RBMLQ-I, Portarias INMETRO 157/2022 balanças + 227/2022 bombas) como sub-domínio ou flag dentro de Metrologia | **Decidir baseado em escopo** — se você atende cliente de balança comercial ou bomba de combustível, é obrigatório. Se foca só em RBC voluntária, pode ficar fora. **Você responde isso** | ⏳ |
| **D-aud-8** | Padronizar IDs de risco como R-001 a R-NNN sequencial único (eliminar mistura R1/R27/RC-01) | **Aceitar** — Auditor 4 alertou que migração depois é dor. Fazer agora enquanto a lista tem 30, não 300 | ⏳ |
| **D-aud-9** | Criar **ADR-IA** agora (mesmo sem stack escolhida) com 5 pontos: (1) abstração obrigatória de provider, (2) dados de cliente final não vão pra API por padrão, (3) IP do output é do Roldão, (4) hard cap de gasto por tenant, (5) suite de eval baseline | **Aceitar** — Auditor 4 mostra que mitiga 5 riscos novos (R27-R31, R32) em um único movimento | ⏳ |

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
