# .agent/SESSION.md — handoff entre sessões

> **Pra quê:** capturar "onde paramos / próximo passo / bloqueio" entre sessões de agente. Mais confiável que só auto-memory.
>
> **Quem mantém:** o próprio agente atualiza no final de cada sessão produtiva.
> **Hierarquia:** CURRENT.md (agora) > SESSION.md (histórico curto) > auto-memory do Claude Code (preferências do humano).

---

## Última sessão

**Data:** 2026-05-17 (sessão Rodada 0 batch 2 + auditoria 10 agentes + 4 decisões fundadoras do Roldão)
**Agente:** Claude Code (Opus 4.7) + 4 subagentes auditores
**Roldão presente:** sim, ativo — contribuiu com:
- Lista de 6 concorrentes adicionais (CalibraFácil, ABC71, SoftExpert, myLIMS, AutoLab×3, ConfLab)
- Auvo como concorrente (1 dossiê extra)
- Promoção de Estoque a domínio próprio (porque empresa fornece peças usadas no reparo de balanças)
- Pediu auditoria interna ("lançar 1 agente por ponto importante")

### Onde paramos
**Rodada 0 batch 1 EXECUTADA + auditoria interna interna concluída + correções factuais aplicadas.**

**Artefatos do batch 1 (todos atualizados pós-auditoria):**
1. ✅ `docs/discovery/concorrentes.md` — 17 concorrentes BR (16 + Auvo) + 8 internacionais + 5 ERPs horizontais BR. Gap confirmado em 3 ondas (pesquisa+lista do Roldão+revisão auditor). **Correções aplicadas:** data Qualer/MasterControl, valor Conta Azul, evidência FP2 regional. **RC-06 a RC-09 adicionados.**
2. ✅ `docs/discovery/normas-e-regulacao.md` — 15 municípios, ISO 17025, RBC/CGCRE, LGPD 2024-2026, Bacen/PIX, MOC NF-e 7.0, PCI-DSS 4.0.1. **Correções aplicadas:** NIT-DICLA-021 Rev. 10; DOQ-008 jun/2020; VIM JCGM 200:2012; SVC CE/PA→RS; Brasília ISSnet.
3. ✅ `docs/discovery/dominio-de-negocio.md` — visão geral + mapa de domínios. **Correções aplicadas:** Cgcre = 4 anos com supervisões; CB-25 corrigido; IPEMs adicionados; **Estoque promovido a domínio próprio** (decisão Roldão).
4. ✅ `docs/discovery/riscos.md` — 29 riscos (R1-R29). **R27 (prompt injection cliente final, score 25) + R28 (soberania dados, score 16) + R29 (bus factor Roldão, score 15) adicionados.** Top 15 reorganizado com R27 no #1.
5. ✅ `docs/discovery/proximos-artefatos.md` — **NOVO.** Checklist consolidada dos 29 documentos referenciados mas ainda inexistentes (inclui ADR-IA recomendado).
6. ✅ `docs/governanca/auditoria-decisoes-autonomas.md` — entrada nova com auditoria + correções aplicadas + 9 decisões pendentes pro Roldão.

### Onde paramos (17/05/2026 — fim do dia)

**✅ MUITA coisa entregue. Resumo executivo:**

1. **Batch 2 do Discovery executado** (3 artefatos: personas, JTBDs, jornada — ~2.400 linhas)
2. **10 auditores rodaram em paralelo** sobre batch 2 — 10 relatórios densos com erros factuais + lacunas + sugestões estratégicas
3. **Roldão aprovou "ACEITO TUDO"** das 27 decisões consolidadas dos auditores
4. **Aplicação em lote**: 11 correções factuais + 27 decisões estratégicas (5 personas novas + reescrita 5 Big Jobs + Job Map 8 fases + 8 jobs emocionais + 5 anti-jobs + recalibração empresa-modelo + 3 fluxos comerciais + 6 etapas metrológicas + glossário roldao 227 termos + INV-016 WCAG + R-035 elevado + R-042 transferência risco)
5. **4 decisões fundadoras do Roldão** no `dominio-de-negocio.md` (texto canônico dele):
   - **Controle de Técnico em Campo, Despesas, Frota e UMC** (caminhão com pesos-padrão, modalidades de transporte do técnico, caixa do técnico, prestação de contas)
   - **Módulo de Comissões Configuráveis** (8 formas de cálculo, múltiplos participantes na OS, gatilho por recebimento, fechamento bloqueado com auditoria)
   - **Cliente 360°, CRM Contínuo, Automações** (cliente nunca "morre", engine gatilho→condição→ação configurável)
   - **Módulo de Estoque Completo** (multi-local: central/técnico/motorista/UMC; transferência 2 etapas com aceite; controle individual de lacre + selo INMETRO com rastreabilidade + foto obrigatória)

**Artefatos do Discovery agora:**
- ✅ `concorrentes.md` (atualizado: 2 frases novas posicionamento + coluna Big Jobs cobertos)
- ✅ `normas-e-regulacao.md` (16 invariantes: INV-016 WCAG novo)
- ✅ `dominio-de-negocio.md` (4 seções canônicas novas escritas pelo Roldão)
- ✅ `riscos.md` (57 riscos: R-001..R-057; R-035 elevado pra score 20)
- ✅ `personas-detalhadas.md` (14 personas: 13 ativas + 1 quase-persona, incluindo Carlos motorista UMC)
- ✅ `jobs-to-be-done.md` (~109 JTBDs + 12 Big Jobs; ~2.139 linhas)
- ✅ `jornada-atual-sem-produto.md` (4 ciclos detalhados, ~800 linhas)
- ✅ `proximos-artefatos.md` (consolidação)
- ✅ `docs/comum/glossario-roldao.md` (NOVO — 227 termos traduzidos PT-BR)
- ✅ `painel-do-dono.md` (incluindo D-aud7-1 ação pendente com terceiros: advogado+seguro+DPA+dossiê = R$ 18-60k)
- ✅ `governanca/auditoria-decisoes-autonomas.md` (entradas atualizadas)

### Próximo passo lógico

**Aguardando Roldão revisar:**
1. As 4 seções canônicas novas em `dominio-de-negocio.md` (texto dele — só conferir se ficou bem encaixado)
2. Glossário `docs/comum/glossario-roldao.md` (227 termos — se algum tá errado)
3. Decisão sobre D-aud7-1 (ação com advogado+corretora+consultor — não é trabalho de agente)

**Depois disso, batch 3:**
- `dores-mapeadas.md`, `opportunity-solution-tree.md`, `assumption-map.md` — agente faz sozinho

---

### Detalhe do batch 2 original (mantido pra histórico)
**✅ Batch 2 do Discovery EXECUTADO.** 3 artefatos novos preenchidos por subagentes em paralelo:
- ✅ `personas-detalhadas.md` (~780 linhas) — 8 personas (Roldão dono + Sandra RT/Qualidade + Letícia atendente + Bruno técnico campo + Marcos metrologista + Cláudia financeiro + Rogério comercial + João cliente final) com identidade, goals, frustrations, ferramentas atuais, variações por perfil A/B/C/D, perguntas pra entrevista
- ✅ `jobs-to-be-done.md` (~830 linhas) — 45 jobs individuais (JTBD-001 a JTBD-045) + 7 Big Jobs + 6 Anti-jobs; cortes por perfil e por tipo de instrumento
- ✅ `jornada-atual-sem-produto.md` (~800 linhas) — 4 ciclos detalhados (comercial / operacional / metrológico / financeiro) com 8-12 etapas cada; top 10 dores; 16 ferramentas BR mapeadas; estimativas quantitativas

**Achados-chave do batch 2:**
- **5 gaps de mercado defensáveis simultaneamente** identificados nos Big Jobs: BIG-01 ciclo completo + BIG-03 perfis A/B/C/D + BIG-04 NFS-e multi-município + BIG-06 Metrologia Legal + BIG-07 Portal do cliente
- **3 dores mais graves** (input pra `dores-mapeadas.md`): D-007 certificado sem campo obrigatório NIT-DICLA-030 (R-018 score 25), D-002 esquecimento de recalibração (R$ 3-8k/mês de receita perdida), D-010 dono operando no nível diário (R-011 + R-029)
- **Ferramentas BR onipresentes** (a confirmar): WhatsApp Business (~100%), Excel/Sheets (~95%), Cali+Metroex (~65-90%), Bling+Conta Azul+Omie (~65-95%), caderno+celular (~80-100%)
- **Variações por perfil** materializadas em todas as personas + jobs

### Próximo passo lógico
Bloco que era esperado pós-batch-2: `dores-mapeadas.md` (input pra priorização do MVP-1) + posteriormente `opportunity-solution-tree.md` + `assumption-map.md` (todos do batch 3 do Discovery).

**Antes:** Roldão precisa decidir se autoriza batch 3 OU se quer revisar os 3 artefatos do batch 2 primeiro.

---

### Histórico anterior — batch 1 + auditoria (16/05/2026)
**✅ Todas as 9 decisões da auditoria + decisão fundadora de perfis + 3 correções aplicadas em 16/05/2026.**

**Decisão fundadora nova (pós-auditoria):**
- **4 perfis de empresa no setup do tenant** (A acreditada / B com padrão RBC / C em preparação / D comercial básica) com regras configuráveis/absolutas por perfil
- **Tipos de balança calibrada** mapeados (comercial, industrial, rodoviária, processos, analítica, etc.) — confirma Metrologia Legal no MVP
- **INV-015 novo** — separa os perfis (bloqueio de emissão de tipo superior ao perfil declarado)
- **R-039 + R-040 novos** — fraude por perfil declarado + verificação INMETRO vencida

Resumo das outras 9 decisões aplicadas:
- D-aud-1: pricing R$ 500-1.000 com 1 mês grátis (era R$ 300)
- D-aud-2: 3 fichas novas (TOTVS Protheus + Qualyteam + SAP B1)
- D-aud-3+4: 14 invariantes (era 10); INV-004 dividido em a/b/c; INV-007 movido pra ADR; INV-010 a INV-014 novos
- D-aud-5+6+7: Metrologia subdividida em 3; Gestão de Competências promovida ao MVP-1; Metrologia Legal adicionada
- D-aud-8: 38 riscos consolidados em R-001..R-038 (formato único)
- D-aud-9: ADR-0000 (Uso de IA) criada

**Próximo: Rodada 0 batch 2** — agente sozinho ainda consegue:
- `docs/discovery/personas-detalhadas.md` (6 papéis identificados em `dominio-de-negocio.md`)
- `docs/discovery/jobs-to-be-done.md`
- `docs/discovery/jornada-atual-sem-produto.md` (status quo — planilha + WhatsApp + Bling)

Depois Roldão precisa entrar em cena para:
- Revisar os 4 artefatos do batch 1 (especialmente os itens marcados `[a confirmar]` e `[Roldão validar]`)
- Receber e revisar `docs/discovery/treinamento-entrevista-roldao.md` (a criar)
- Fazer 2 entrevistas piloto (revisadas por auditor)
- Marcar onda 1: 3 entrevistas com donos de OUTRAS empresas

### Bloqueio atual
Nenhum técnico. Próxima decisão é do Roldão (autorizar batch 2 vs revisar batch 1 primeiro).

### Decisões tomadas nesta sessão
- Pesquisa via 4 subagentes paralelos (3 iniciais + 1 follow-up após lista do Roldão).
- Reconhecimento de gaps em fontes: itens `[a confirmar]` marcados explicitamente, não inventados.
- Correções factuais: SCAN morto desde 2014, RIR/99 revogado pelo RIR/2018, mito "72h GDPR" derrubado (3 dias úteis), ILAC G8 ≠ validação de software, myLIMS ≠ PerkinElmer, 3 produtos chamados "AutoLab" no Brasil.
- Estrutura de `concorrentes.md` segmentada em: internacionais → nacionais → ERPs horizontais BR → bônus do gap.

### Achados estratégicos pra Roldão olhar
- **GAP CONFIRMADO** "OS + calibração ISO 17025 + NFS-e municipal multi-prefeitura" — único player com NFS-e nativa é FP2 (regional, Santa Maria/RS). Tese central do produto sustentada.
- **R18 = risco mais grave** (score 25): NIT-DICLA-030 rev. 15 item 8.2.6 rejeita certificado sem cadeia de rastreabilidade + incerteza. Vira INV-CALIB-001.
- **Concorrente nacional mais perigoso:** Cali LAB/WEB (homologado CERTI, base RBC instalada). Vantagem: ainda é desktop-first sem fiscal.
- **Janela competitiva:** se Cali/Metroex fechar parceria com Bling/Omie pra fiscal, perdemos diferencial #1.

---

## Histórico (últimas sessões, ordem cronológica reversa)

### Sessão 2026-05-16 (Rodada 0 batch 1) — esta
4 artefatos do Discovery preenchidos. 16 concorrentes BR + 8 internacionais mapeados. 15 municípios cobertos. 11 riscos novos. Gap central do produto confirmado em 2 ondas.

### Sessão 2026-05-16 (estrutura inicial)
Criada estrutura de documentação seguindo v5: ~30 arquivos de fundação + 15 cabeçalhos de Discovery prontos pra preencher.

### Sessão 2026-05-16 (discussão de docs)
Passou por v3 → v4 → v5. Auditorias com 10 agentes (rodada 1 sobre v2 e rodada 2 sobre v4). Revelações grandes: founder is customer, N módulos a descobrir, escopo é ERP completo (não só calibração).

### Sessão 2026-05-16 (anterior, mesmo dia)
Ambiente Claude Code blindado, hooks reescritos com perl/JSON::PP + 23 testes verdes.

### Sessão 2026-04-19
Renomeação Kalibrium → Aferê.
