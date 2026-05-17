# Auditoria de decisões autônomas dos agentes

> **Lista do que os agentes decidiram SEM consultar o Roldão** (dentro dos `limites-autonomia.md`). Roldão lê pra estar informado; pode discordar (vira ADR de reversão).
>
> Auditor 2 v2 alertou: sem essa filtragem dedicada, autonomia vira caixa-preta.

---

## Formato de cada entrada

```markdown
### YYYY-MM-DD — [Resumo em PT-BR de 1 linha]
- **Decisão:** [o que foi decidido]
- **Por quê:** [razão objetiva]
- **Quem decidiu:** [agente Claude Code / Codex CLI / Auditor X]
- **Sessão:** [hash ou link pra `.agent/SESSION.md` da época]
- **Impacto:** [reversível / irreversível / parcialmente reversível]
- **Caso-limite (do limites-autonomia)?** [Caso N — sim/não] (se sim, deveria ter escalado — bug do agente)
- **Link pra ADR (se criado):** [path]
- **Roldão revisou?** ⏳ pendente / ✅ aprovou / ❌ discordou (ver ADR-NNNN de reversão)
```

---

## Entradas (cronológico reverso)

### 2026-05-17 NOITE — Auditoria de 12 agentes sobre batch 3 + 24 correções aplicadas em lote
- **Decisão:** Roldão pediu "auditoria com 12 agentes em ângulos novos (diferente de batches 1 e 2)". Disparei 12 auditores independentes em paralelo cobrindo: (11) Pricing & Unit Economics, (12) Sequenciamento MVP, (13) Calibração de scores/RICE, (14) Defensibilidade competitiva/moats, (15) Testabilidade de premissas, (16) Filtros de ICP, (17) Riscos legais/trabalhistas, (18) Go-to-market/canal aquisição, (19) Founder-customer deep dive R-001, (20) Conflitos internos cross-doc, (21) Blind spots, (22) Defesa LEAP #1 modelo agentes.
- **24 achados consolidados** (12 críticos + 12 altos). Os 5 mais graves:
  - **Modelo 100% agentes (LEAP F-1) sem critério de mortalidade** (Aud-22)
  - **OP1 não pode ser primeiro do MVP-1** — OP7 NFS-e tem deadline 01/09/2026 (Aud-12, Aud-20)
  - **Foundation invisível no OST** — multi-tenant/RBAC/RLS/auth escondidos como premissas (Aud-12)
  - **4 das 8 OPs do MVP-1 viraram canon antes de entrevistas** — founder bias materializado (Aud-13, Aud-19)
  - **Apenas 3 dos 9 "gaps defensáveis" são moats reais** (Aud-14); Auvo > Visma como ameaça #1
- **Roldão aprovou "ACEITAR TUDO".**
- **Aplicado em lote por 4 subagentes paralelos:**
  - Subagente A: OST → 12 OPs (era 8); Foundation pré-MVP; Wave A (OP7+OP2+OP10) → Wave B (OP1+OP4+OP5+OP8+OP3); Confidence dual-axis; IDs canônicos R-049..R-057; pricing reconciliado; OP4 simplificado (1 fórmula no MVP-1); BIG-03 + BIG-06 ganham OP dedicada
  - Subagente B: dores-mapeadas → Top 5 corrigido (#05 promovida; #19 desce); 8 scores recalibrados; segunda deflação em DAPs de DFs; 4 marcações [INFERÊNCIA] novas; seção "Imunização contra founder bias"
  - Subagente C: assumption-map → 61 premissas (+V-15, F-17, F-18, F-19); F-1 com 10 kill switches + planos B/C/D; Van Westendorp N=30→5-8. riscos → 65 riscos (8 novos R-058..R-065); R-001 elevado pra 20; R-034 4→12; R-046 10→15
  - Subagente D: normas (20 INVs com INV-017 ICP-Brasil + INV-018 RT vendor + INV-019 dossiê 7.11 + INV-020 Lei 13.103/2015); personas (16 com Persona 15 Diego Consultor RBC + Persona 16 Andréia CS L1); concorrentes (Auvo #1 ameaça); domínio (desambiguação "decisão fundadora"); glossário (236 termos)
- **Total delta:** ~3.500 linhas alteradas em 9 docs do Discovery + glossário
- **Quem decidiu:** Roldão (aprovou em bloco) + Claude Code (orquestrador) + 12 subagentes auditores + 4 subagentes de aplicação
- **Impacto:** MUITO ALTO — reescreveu MVP-1 (era 8 OPs, virou 12 com Foundation explícita), promoveu 2 riscos críticos (R-001 + R-034), criou 4 invariantes legais (INV-017..INV-020), adicionou 2 personas (Consultor RBC + CS L1)
- **Caso-limite?** Não — todas as 24 decisões tiveram veredito explícito do Roldão "ACEITAR TUDO"
- **Próximas ações:** (1) Listar 20 telefones quentes Roldão antes de codar; (2) ADR-0001 stack antes do spike F-1; (3) Preparar Onda 1 com 5 entrevistas "anti-Roldão"; (4) D-aud7-1 em paralelo
- **Roldão revisou?** ✅ aprovou em bloco; revisão de qualidade da aplicação pendente

---

### 2026-05-17 — 4 decisões fundadoras do Roldão (Frota/UMC + Comissões + CRM 360° + Estoque)
- **Decisão:** Roldão registrou 4 grandes blocos de especificação como textos canônicos diretamente em `dominio-de-negocio.md`:
  1. **Controle de Técnico em Campo, Despesas, Frota e UMC** — operação de campo (OS multi-equipamento, 3 modalidades de transporte do técnico, caixa do técnico com adiantamento+prestação de contas, UMC com motorista próprio + pesos-padrão, controle total de frota carros+UMC)
  2. **Módulo de Comissões Configuráveis** — 8 formas de cálculo (bruto, mão de obra, peças+serviços com %, produtos, líquido, fixo, por tipo de serviço, por equipamento), múltiplos participantes na mesma OS, períodos configuráveis, gatilho por recebimento, controle de descontos/margem, aprovação/auditoria, integração com todos os módulos
  3. **Cliente 360°, CRM Contínuo, Automações** — filosofia integrada (cliente nunca "morre"), visão 360°, engine de automação configurável (gatilho→condição→ação), múltiplos funis (venda/calibração/manutenção/contratos/pós-venda/renovação/inativos/recuperação)
  4. **Módulo de Estoque Completo** — multi-local (central, filial, técnico, veículo, caminhão, UMC, motorista, sucata, RMA), transferência 2 etapas com aceite, controle individual de lacre e selo INMETRO com rastreabilidade + foto obrigatória, app mobile pra técnico+motorista, integração com OS, alertas de reposição
- **Aplicado em:**
  - `dominio-de-negocio.md` — 4 seções canônicas novas (texto do Roldão preservado integralmente como fonte de verdade)
  - `jobs-to-be-done.md` — 5 Big Jobs novos (BIG-08 Frota/UMC + BIG-09 Comissões + BIG-10 CRM 360° + BIG-11 Automações + BIG-12 Estoque); ~40 JTBDs novos (JTBD-060..109); top 10 re-rankeado 4ª vez
  - `riscos.md` — 15 riscos novos (R-042 a R-057) cobrindo: transferência risco vendor↔tenant (CRÍTICO), caixa do técnico, frota, UMC, acessibilidade, automação errada, LGPD spam, selo INMETRO perdido, lacre fraude, inventário divergente, comissão errada/fraude
  - `concorrentes.md` — coluna "Big Jobs cobertos" na matriz §5 + 2 frases novas posicionamento (vs Auvo + vs ERPs horizontais) + posicionamento atualizado com mention de Frota/UMC + Comissões + CRM 360°
  - `painel-do-dono.md` — D-aud7-1 destacado (ação com terceiros: advogado+seguro+DPA+dossiê = R$ 18-60k); 9 gaps defensáveis listados (era 5)
- **Por quê:** Roldão é o decisor de produto + dono do setor. Texto dele = fonte de verdade. Agente apenas executou aplicação técnica + desdobramentos pra arquitetura/concorrentes/riscos.
- **Quem decidiu:** Roldão (produto) + Claude Code (executor) + subagentes (reescrita de JTBDs)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-17
- **Impacto:** **DECISÕES FUNDADORAS** — afetam todo o produto. Reverter exige ADR.
- **Caso-limite?** Não — foi decisão direta do decisor de produto
- **Achados:**
  - Gaps de mercado defensáveis subiram de 5 pra **9** — Aferê propõe cobrir 12/12 Big Jobs onde concorrentes cobrem no máximo 5/12
  - **9º gap defensável** (Estoque multi-local com lacre/selo INMETRO) é nicho regulatório intocado por todos
  - R-035 (Visma) elevado pra score 20 — janela competitiva confirmada estreita
  - R-042 (transferência risco vendor↔tenant) é existencial — Roldão precisa contratar advogado+seguro+DPA+consultor (R$ 18-60k)
- **Roldão revisou?** ✅ ele é o decisor; revisão da aplicação técnica pendente

---

### 2026-05-17 — Auditoria interna de 10 agentes sobre batch 2 + correções aplicadas
- **Decisão:** Roldão pediu "lance 10 agentes auditando batch 2". Disparei 10 auditores independentes em paralelo cobrindo: (1) fidelidade BR personas, (2) inclusão/acessibilidade, (3) framework JTBD, (4) priorização/MVP fit, (5) anti-jobs/scope creep, (6) realismo operacional BR, (7) regulatório nas jornadas, (8) cross-check entre 7 artefatos, (9) gap competitivo reforçado, (10) linguagem pro Roldão não-técnico.
- **Achados consolidados (5 mais sérios):** transferência risco vendor↔tenant não mapeada (Aud-7); acessibilidade ausente nas personas (Aud-2); custo do status quo subestimado 2-3x (Aud-6); janela competitiva curta — Visma+Cali em 18 meses (Aud-9); Roldão não consegue ler os 3 docs (Aud-10).
- **Roldão aprovou "ACEITO TUDO"** das 27 decisões consolidadas.
- **Aplicado** (alguns por mim, outros por subagentes em paralelo):
  - 11 correções factuais (data, NIT-DICLA-021→016+019, instituições formação, salários CBO 2026, calibradores, Cláudia/Bling SP, Bruno caderno 70-80%, Marcos Cali resistência, contagem personas, ferramentas, recalibração 30-50%)
  - 5 personas novas (Carlos motorista UMC, Auditor Cgcre, Patrícia farma, João-Sênior, Bruna, Roldão Sênior — total 14)
  - 5 Big Jobs reescritos (BIG-01/03/05/06/07) + Job Map de 8 fases por Big Job + 8 jobs emocionais/sociais
  - JTBDs novos (Sandra RT, JTBD-046/047 + 8 emocionais + 12 frota/UMC/caixa + 12 comissões + 15 CRM/automação + 12 estoque/lacre/selo)
  - Anti-jobs novos (ANTI-07 a ANTI-11) + princípios "vertical thin" + "produto não plataforma"
  - Top 10 re-rankeado com BIG-08/09/10/11/12 + JTBD-044 (alerta renovação) no top 3
  - Reescrita §1 dos 3 docs do batch 2 (PT-BR humano sem jargão)
  - Títulos PT-BR (Goals→"O que quer", Frustrations→"O que deixa louca", Reluctance→"O que vai resistir")
  - Tradução inline de códigos cifrados (R-NNN, INV-NNN, ADR-NNN)
  - Costura nominal persona ↔ JTBD ↔ dor
  - INV-016 (WCAG 2.1 AA + PDF/UA) absoluto pra todos perfis
  - R-035 (Visma) elevado pra score 20
  - R-042 (transferência risco vendor↔tenant) novo score 20
  - `docs/comum/glossario-roldao.md` criado com 227 termos traduzidos PT-BR
  - Empresa-modelo recalibrada pra 5-10 funcionários (era 10-20)
  - 3 fluxos comerciais novos (licitação pública, contrato anual, atestado capacidade técnica)
  - 6 etapas metrológicas faltantes (aceitabilidade, estabilização, condições ambientais, revisão 2º signatário, selo, as found/as left)
  - Custo do status quo corrigido pra R$ 35-50k/mês
- **Itens pendentes pra terceiros (D-aud7-1):** advogado (contrato + DPA), corretora de seguros (RC profissional + cibernética), consultor de qualidade (dossiê de validação 17025). Custo total R$ 18-60k. Registrado em destaque no `painel-do-dono.md`.
- **Quem decidiu:** Roldão (aprovou em bloco) + Claude Code (orquestrador) + 10 subagentes auditores + 4 subagentes de reescrita
- **Impacto:** alta — reescreveu/expandiu 7 docs (~6.000+ linhas de delta), criou 1 doc novo (glossário), aplicou 4 decisões fundadoras
- **Caso-limite?** Não — todas as 27 decisões tinham veredito explícito do Roldão "ACEITO TUDO"
- **Roldão revisou?** ✅ aprovou em bloco; revisão de qualidade da aplicação pendente

---

### 2026-05-17 — Rodada 0 batch 2 executado (3 artefatos novos)
- **Decisão:** Roldão autorizou execução do batch 2. Disparei 3 subagentes em paralelo, cada um responsável por 1 artefato:
  - `personas-detalhadas.md` (~780 linhas) — 8 personas com identidade, goals, frustrations, ferramentas atuais, variações por perfil A/B/C/D
  - `jobs-to-be-done.md` (~830 linhas) — 45 jobs individuais + 7 Big Jobs + 6 Anti-jobs; corte por perfil e tipo de instrumento
  - `jornada-atual-sem-produto.md` (~800 linhas) — 4 ciclos detalhados + top 10 dores + 16 ferramentas BR mapeadas
- **Total:** ~2.400 linhas geradas em paralelo (~30 min de trabalho de agente).
- **Por quê:** Roldão autorizou ("SIM"). Pesquisa secundária sem entrevista está dentro da autonomia. Base usada: os 4 artefatos do batch 1 + decisões posteriores (perfis A/B/C/D + tipos configuráveis + selo INMETRO sem vencimento).
- **Quem decidiu:** Claude Code (orquestrador) + 3 subagentes general-purpose (executores)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-17
- **Impacto:** reversível (todos versionados); decisões fundadoras não tocadas
- **Caso-limite?** Não — pesquisa secundária sem mudança de stack/invariante
- **Achados estratégicos:**
  - **5 gaps de mercado defensáveis simultaneamente** confirmados nos Big Jobs (BIG-01, BIG-03, BIG-04, BIG-06, BIG-07). Nenhum concorrente cobre mais de 2.
  - **Receita escondida quantificada:** esquecimento de recalibração custa R$ 3-8k/mês pra empresa-modelo (input forte pra pitch comercial)
  - **WhatsApp Business é universal (~100% das empresas BR do setor):** entra como requisito obrigatório do MVP, não como feature opcional
  - **D-007 (certificado sem campo NIT-DICLA-030) materializa R-018 score 25:** confirma que INV-002 (hook bloqueia emissão) é diferencial crítico
  - **8ª persona criada (João, cliente final do tenant):** quase-persona usada só pra design do Portal do Cliente (BIG-07)
- **Itens deixados pra entrevistas (validação primária):**
  - Salários BR de 2026 por persona (faixas inferidas; precisa amostra de 3+ por papel)
  - Decisor de compra real em perfil A (dono ou metrologista?)
  - Adoção real de calibrador documentador (Beamex/Fluke) — define se integração é MVP ou pós
  - Disposição a pagar real por perfil (teto mental de R$ 500/mês foi inferência)
- **Próximo:** Roldão decide se vai pro batch 3 (`dores-mapeadas.md` + `opportunity-solution-tree.md` + `assumption-map.md`) ou se revisa batch 2 primeiro
- **Roldão revisou?** ⏳ pendente

---

### 2026-05-16 — 3 correções do Roldão sobre perfis + selo INMETRO + tipos configuráveis
- **Decisão (correção da decisão anterior):**
  1. **Selo INMETRO/IPEM em balança comercial NÃO tem vencimento estampado** — o que vence é a obrigação legal de verificação periódica (anual). Risco R-040 corrigido pra refletir isso (era "selo vencido", virou "verificação periódica não feita pelo cliente final").
  2. **Perfil B tem regras 17025 TOTALMENTE configuráveis** (não absolutas como eu havia descrito). Empresa B com ambição de acreditação pode ativar tudo; empresa B "leve" pode desativar quase tudo. Apenas perfil A tem regras absolutamente travadas. Tabela "Escopo por perfil" das 14 invariantes corrigida.
  3. **Tipos de instrumento atendidos** (balança comercial / industrial / rodoviária / processo / analítica / bancada / contadora / gancho / plataforma / outros) **são configuráveis no setup do tenant** — empresa marca 1, alguns ou todos; pode adicionar tipos novos depois (self-service). UI/filtros/dashboards mostram só tipos marcados.
- **Aplicado em:**
  - `dominio-de-negocio.md` — perfil B reescrito (configurável); seção "Regras configuráveis" simplificada (só A é absoluto); seção "Tipos de instrumento" agora começa com configurabilidade explícita do setup
  - `normas-e-regulacao.md` §8.1 — 7 invariantes mudaram "Escopo por perfil" pra "Absoluta em A; configurável em B, C, D" (era "Absoluta em A e B" ou "recomendada em B")
  - `riscos.md` — R-040 reformulado (não é "selo vencido"; é "verificação periódica obrigatória não feita pelo cliente final"); **R-041 novo** (tenant marca tipo no setup que não atende tecnicamente; operação falha no campo)
- **Por quê:** Roldão é dono do setor e corrigiu 3 erros conceituais que eu havia introduzido. Aplicação direta sem auditor — ele é fonte de verdade do domínio.
- **Quem decidiu:** Roldão (decisor + know-how do setor)
- **Sessão:** ver `.agent/SESSION.md` (2026-05-16 batch 1 + decisão de perfis + 3 correções)
- **Impacto:** alta — afeta tabela de invariantes (7 mudanças) + descrição do perfil B + introduz config de "tipos atendidos" no setup como decisão fundadora separada
- **Caso-limite?** Não — foi correção direta do decisor de produto
- **Achados:**
  - **Perfil B mais flexível que eu havia desenhado** — vira "B-leve" ou "B-rigoroso" conforme o dono escolher; sistema deve nomear essas variantes no setup
  - **Setup tem 3 dimensões de configuração principais:** (1) perfil (A/B/C/D), (2) tipos de instrumento atendidos (checklist multi), (3) regras 17025 ativadas (quando perfil ≠ A)
  - **R-041 introduz risco operacional:** sistema permite operação que tenant não tem capacidade técnica — wizard de setup precisa pedir prova de capacidade por tipo marcado
- **Roldão revisou?** ✅ ele é o decisor desta decisão

---

### 2026-05-16 — Decisão fundadora: 4 perfis de empresa + tipos de balança + 2 riscos novos
- **Decisão:** Roldão definiu que o **setup do tenant** precisa suportar 4 perfis distintos (A acreditada / B com padrão RBC / C em preparação / D comercial básica) com **regras configuráveis por perfil**. Também confirmou escopo de calibração de balanças (todos os tipos: comercial, industrial, rodoviária, processos), o que confirma D-aud-7 (Metrologia Legal no MVP).
- **Aplicado em:**
  - `dominio-de-negocio.md` — nova seção "Perfis de empresa (setup)" com 4 perfis A/B/C/D + tabela de regras absolutas/condicionais + implicações pra arquitetura
  - `dominio-de-negocio.md` — nova seção "Tipos de balança calibrada" com 9+ tipos mapeados + regulamentação aplicável + implicações pro produto
  - `normas-e-regulacao.md` §8.1 — coluna "Escopo por perfil" adicionada em todas as invariantes (algumas viraram condicionais); **INV-015 novo** (bloqueio por perfil: tenant não pode emitir certificado de tipo superior ao perfil declarado)
  - `riscos.md` — **R-039 novo** (tenant declara perfil A sem acreditação real e emite com selo RBC falso; score 15); **R-040 novo** (verificação INMETRO/IPEM vencida em balança comercial; score 12)
  - `painel-do-dono.md` — D-aud-7 marcado RESOLVIDO; decisão de perfis registrada
- **Por quê:** Roldão é dono de empresa do setor; viu durante a aplicação que o produto precisa atender mais que só perfil A (que é o que TODOS os concorrentes nacionais assumem). Perfis B+C+D são o GAP REAL não atendido por Cali/Metroex/Calibre — eles assumem que cliente é lab acreditado. Perfil C como "trilha de evolução" é diferencial único no mercado.
- **Quem decidiu:** Roldão (decisor de produto + know-how do setor) + Claude Code (executor)
- **Sessão:** ver `.agent/SESSION.md` (2026-05-16 batch 1 + decisão de perfis)
- **Impacto:** **DECISÃO FUNDADORA DO PRODUTO** — afeta setup, modelo de dados (campo `perfil` em tenant), modelo do certificado (template por perfil), hooks de validação (INV-015), marketing (mensagem segmentada por perfil), pricing (talvez perfil C/D precise de tier menor). Reversível só com ADR.
- **Caso-limite?** **Sim** — é decisão de produto/escopo, NÃO faz parte da autonomia operacional. Mas Roldão deu a decisão direta (não foi agente decidindo sozinho). Por isso registrado como decisão DELE com agente como executor.
- **Achados estratégicos:**
  - Perfil C ("trilha de evolução") é diferencial competitivo único — nenhum concorrente (Cali/Metroex/Calibre/CalibraFácil/AUTOLAB) oferece isso
  - INV-015 é o invariante que **separa os perfis** — sem ele, perfil B podia emitir certificado falso com selo RBC e configurar fraude regulatória
  - Tipos de balança expandido confirma que **Metrologia Legal** vira módulo importante (não apenas flag)
  - R-039 (fraude por perfil mal-declarado) tem implicação jurídica — Roldão (vendor) pode responder solidariamente. Cláusula contratual obrigatória
- **Roldão revisou?** ✅ ele é o decisor desta decisão

---

### 2026-05-16 — Roldão aprovou as 9 decisões da auditoria; aplicadas autonomamente
- **Decisão:** Roldão respondeu "ACEITO TUDO" pras 9 decisões pendentes da auditoria do batch 1. Aplicadas em sequência:
  - **D-aud-1** Pricing: R$ 300 → **R$ 500-1.000/mês** com 1 mês grátis. Faixas crescimento (R$ 1.500-3.000) e Pro (R$ 3.000-6.500) também subiram.
  - **D-aud-2** 3 fichas novas em `concorrentes.md` §14: **TOTVS Protheus** (SIGAMNT + SIGATEC + SIGAQMT/Metrologia descoberto), **Qualyteam** (Joinville/SC desde 2008, QMS BR com 400+ clientes), **SAP Business One BR** (via parceiros, R$ 50k-150k implementação).
  - **D-aud-3** Invariante #4 ("software validado") quebrado em INV-004a (deploy só com aprovação RT), INV-004b (revalidação de cálculo de incerteza), INV-004c (versão do software gravada em cada certificado).
  - **D-aud-4** INV-007 (BaaS único) movido pra ADR fiscal (não é invariante); INV-010 a INV-014 novos: retenção 17025, padrão vencido bloqueia emissão, NC bloqueia emissão, confidencialidade 4.2 com log, certificado externo sem incerteza bloqueia. **Total: 14 invariantes** (era 10).
  - **D-aud-5** Domínio Metrologia subdividido em 3: (a) Execução de calibração, (b) Padrões e rastreabilidade, (c) Garantia da validade.
  - **D-aud-6** "Gestão de Competências e Autorizações" promovido ao MVP-1 obrigatório (17025 6.2). Escopo magro: matriz competência × grandeza + validade + autorização por escopo. RH completo (folha, ponto, holerite) fica lazy.
  - **D-aud-7** Domínio "Metrologia Legal" adicionado (IPEMs/RBMLQ-I, Portarias INMETRO 157/2022 balanças + 227/2022 bombas). Confirmar se está no escopo do MVP nas entrevistas (depende se Roldão atende balança comercial / bomba combustível).
  - **D-aud-8** Padronização de IDs de risco aplicada: **R-001 a R-038** sequencial único, coluna Origem adicionada. R-021 marcado DEPRECATED (consolidado com R-033). Tabela completa de mapeamento RC-* → R-* em `riscos.md` e `concorrentes.md` §7.
  - **D-aud-9** **ADR-0000 (Uso de IA) criada** em `docs/adr/0000-uso-de-ia.md` com 5 princípios fundadores: (1) abstração obrigatória de provider, (2) dados de cliente final não vão pra API por padrão, (3) IP do output é do Roldão, (4) hard cap por tenant, (5) sanitização e segregação de input não-confiável.
- **Por quê:** Roldão deu autorização explícita ("ACEITO TUDO"). Aplicação direta sem aguardar item-a-item.
- **Quem decidiu:** Roldão (decisor) + Claude Code (executor) + 4 subagentes auditores (insumo)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (auditoria batch 1)
- **Impacto:** reversível (todas as edições versionadas); ADR-0000 é fundadora — reabrir só com ADR de reversão.
- **Caso-limite?** Não — todas as decisões já tinham veredito do Roldão "aceito"
- **Itens deixados em aberto pra entrevista:**
  - D-aud-7 — confirmar se Metrologia Legal está no escopo do MVP (depende se Roldão atende balança/bomba)
  - D-aud-5 — subdivisão de Metrologia em 3 sub-domínios materializa quando o módulo entrar no faseamento (até lá é só nota no mapa)
- **Roldão revisou?** ✅ aprovou em bloco

---

### 2026-05-16 — Auditoria interna do batch 1 + correções factuais aplicadas
- **Decisão:** Roldão pediu "lançar 1 agente por ponto importante pra revisar". Disparei 4 auditores independentes em paralelo:
  - **Auditor 1** — concorrentes.md (achou 2 erros factuais + sugeriu 3 concorrentes ausentes + 5 frases de posicionamento frágeis)
  - **Auditor 2** — normas-e-regulacao.md (achou 4 erros factuais: NIT-DICLA-021 é Rev. 10 e não Rev. 03; DOQ-008 é jun/2020; VIM ainda é JCGM 200:2012; SVC CE/PA → SVC-RS)
  - **Auditor 3** — dominio-de-negocio.md (apontou auditoria Cgcre = 4 anos não 2; CB-25 é Qualidade e não Calibração; glossário só cobre 30%; estoque deveria ser domínio próprio)
  - **Auditor 4** — riscos.md + cross-check (apontou 10 riscos faltando; padronização de IDs; 21 documentos referenciados mas inexistentes)
- **Aplicadas autonomamente (correções factuais confirmadas por fonte):**
  - `concorrentes.md`: data Qualer/MasterControl (03/03/2025); valor Conta Azul (US$ 300 mi/~R$ 1,7 bi, não R$ 2 bi); evidência FP2 regional (4 clientes em Santa Maria/RS); RC-06, RC-07, RC-08, RC-09 adicionados; **Auvo adicionado** (indicação Roldão); **Estoque promovido a domínio próprio** (indicação Roldão + sugestão Auditor 3)
  - `normas-e-regulacao.md`: NIT-DICLA-021 Rev. 10; DOQ-008 jun/2020; VIM JCGM 200:2012; SVC CE/PA → SVC-RS; Brasília = emissor próprio ISSnet + ADN
  - `dominio-de-negocio.md`: Cgcre = ciclo 4 anos com supervisões; CB-25 corrigido (Qualidade, não Calibração) + adicionado IPEMs/RBMLQ-I; estoque promovido a domínio próprio com escopo de WMS
  - `riscos.md`: R27 (prompt injection cliente final, score 25) + R28 (soberania dados Anthropic EUA, score 16) + R29 (bus factor Roldão, score 15); top 12 reorganizado pra top 15 com R27 no #1
  - **Criado `docs/discovery/proximos-artefatos.md`** consolidando os 29 artefatos referenciados pelos 4 docs mas ainda inexistentes (inclui ADR-IA novo recomendado pelo Auditor 4)
- **NÃO aplicadas (ficam pra decisão do Roldão):**
  - Subir piso de pricing R$ 300→R$ 500-1.000 (Auditor 1)
  - Adicionar fichas TOTVS Protheus, Qualyteam, SAP B1 BR (Auditor 1) — mais 3 dossiês
  - Refinar invariante #4 em 3 sub-regras testáveis (Auditor 2)
  - Mover invariante #7 (BaaS único) pra ADR e adicionar invariantes #11-#15 (Auditor 2)
  - Subdividir domínio Metrologia em 3 sub-domínios (Auditor 3)
  - Mover Gestão de Competências pra MVP-1 (Auditor 3 — conflito real com 17025 6.2)
  - Padronizar IDs (R-001 a R-NNN sequencial) (Auditor 4)
  - Criar ADR-IA hoje (Auditor 4)
  - Substituir mitigações "monitorar" por owner + cadência + gatilho (Auditor 4)
  - Adicionar metrologia legal (IPEMs/Portarias 157/2022 e 227/2022) como sub-domínio ou flag (Auditor 3)
- **Por quê:** itens factuais são erros objetivos com fonte — aplicar não muda direção estratégica. Itens não-aplicados envolvem decisões de produto/escopo onde Roldão é o decisor.
- **Quem decidiu:** Claude Code (orquestrador) + 4 subagentes auditores (general-purpose) + Roldão (intervenções: Auvo + estoque domínio próprio)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (auditoria batch 1)
- **Impacto:** reversível (todas as edições versionadas no git); não toca decisões fundadoras
- **Caso-limite?** Não — correção de erro factual e adição de risco com mitigação documentada estão dentro da autonomia
- **Achados que viram entrada futura em REGRAS-INEGOCIAVEIS:**
  - R27 → INV-AGENT-001 (input não-confiável de cliente final precisa de hook)
  - R18 (já citado em entrada anterior) → INV-CALIB-001
  - Invariantes propostas em `normas-e-regulacao.md` §8.1 (10 candidatos, 5 mais sugeridos pelo Auditor 2)
- **Roldão revisou?** ⏳ pendente — Roldão precisa decidir os 9 itens não-aplicados acima

---

### 2026-05-16 — Rodada 0 Discovery batch 1 executada (4 artefatos)
- **Decisão:** preencher `concorrentes.md`, `normas-e-regulacao.md`, `dominio-de-negocio.md`, `riscos.md` com conteúdo denso a partir de pesquisa pública. Disparados 3 subagentes paralelos (concorrentes ERP horizontal BR, concorrentes calibração ISO 17025, normas/regulação BR) + 1 subagente extra após Roldão acrescentar 6 nomes novos (CalibraFácil, ABC71, SoftExpert, myLIMS, AutoLab×3, ConfLab). Total: 16 concorrentes brasileiros + 8 internacionais mapeados; 15 municípios prioritários cobertos para NFS-e; 11 riscos novos adicionados (R16–R26).
- **Por quê:** Roldão autorizou início da Rodada 0 e pediu o primeiro batch (artefatos que o agente faz sozinho). Pesquisa pública sem entrevista de cliente está dentro da autonomia. Lista adicional do Roldão veio durante a execução — incorporada em append.
- **Quem decidiu:** Claude Code (Opus 4.7) — orquestrador; subagentes general-purpose pra pesquisa.
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (Rodada 0 batch 1)
- **Impacto:** reversível (arquivos podem ser reescritos); decisões fundadoras NÃO foram tocadas
- **Caso-limite?** Não — pesquisa secundária sem mudança de stack ou de invariante
- **Achados estratégicos que podem virar ADR/INV:**
  - **Gap "OS + calibração ISO 17025 + NFS-e municipal" confirmado** em 2 ondas de pesquisa independentes (16 nacionais + 8 internacionais). Único com NFS-e nativo é FP2 Tecnologia (Santa Maria/RS regional). Tese central do produto sustentada.
  - **NIT-DICLA-030 rev. 15 item 8.2.6:** Cgcre não aceita certificado sem resultado de medição + incerteza → vira invariante INV-CALIB-001 (bloqueio na emissão).
  - **Mito "72h GDPR" derrubado:** ANPD Res. 15/2024 é **3 dias úteis**, não 72h corridas. Toda documentação interna precisa usar o termo correto.
  - **Decreto 3000/99 (RIR/99) está REVOGADO desde 2018** (substituído pelo Decreto 9.580/2018 — RIR/2018). Draft anterior do `normas-e-regulacao.md` citava norma morta — corrigido.
  - **SCAN está morto desde 30/09/2014** — só SVC-AN/SVC-RS + EPEC. Quem cita SCAN está com base antiga.
  - **Cutover NFS-e Padrão Nacional:** MEI desde set/2023; municípios desde 01/01/2026; ME/EPP Simples obrigatório em 01/09/2026 (CGSN 189/2026). SP mantém próprio integrado ao ADN; POA desliga DANFSe local em 01/07/2026.
  - **PCI-DSS 4.0.1** vigente desde 31/03/2025 (sem carência). Recomendação: usar PSP/gateway tokenizado → SAQ A.
  - **ILAC G8 trata de regras de decisão, não validação de software** — referências corretas são WELMEC 7.2 / OIML D 31. Roldão precisa confirmar qual quer.
  - **Confusão derrubada:** myLIMS NÃO é PerkinElmer (é Confience/STG Partners); 3 produtos chamados "AutoLab" no Brasil (Arkade, Automa, MRI); ABC71 não compete com lab calibrador (compete com metrologista interno de indústria).
- **Itens [a confirmar] pra Roldão:** Brasília NFS-e modelo de adesão, NIT-DICLA-021 revisão vigente, Enunciado CD/ANPD nº 4, número da IN BCB do PIX, VIM 4ª ed., ILAC G8 vs WELMEC 7.2.
- **Roldão revisou?** ⏳ pendente — Roldão já contribuiu durante a execução com lista de 6 concorrentes adicionais; revisão final dos 4 artefatos pendente.

---

### 2026-05-16 — Estrutura inicial de documentação criada
- **Decisão:** criação de ~33 arquivos de fundação + estrutura de pastas seguindo `documentos-do-projeto.md` v5; ~100 arquivos lazy do v5 NÃO foram criados conforme regra do próprio doc.
- **Por quê:** Roldão autorizou "criar toda estrutura"; agente seguiu regra do doc "não criar template vazio pra preencher depois".
- **Quem decidiu:** Claude Code (Opus 4.7)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16
- **Impacto:** reversível (arquivos podem ser deletados)
- **Caso-limite?** Não — está dentro da autonomia
- **Link pra ADR:** N/A
- **Roldão revisou?** ⏳ pendente (este é o primeiro item da lista)

---

## Como agente atualiza esta lista

A cada decisão autônoma significativa (que valha registrar):
1. Adiciona entrada NO TOPO (cronológico reverso).
2. Atualiza `status-semanal.md` referenciando esta entrada.
3. Atualiza `trilha-auditoria-agentes.md` com detalhe técnico.

## Critério "significativa" pra registrar

- Mudança em arquivo de `REGRAS-INEGOCIAVEIS.md`, `governanca/`, `conformidade/`, `adr/`, `comum/`.
- Mudança em > 5 arquivos numa única sessão.
- Adoção/descontinuação de ferramenta, biblioteca, padrão.
- Decisão arquitetural não-trivial.
- Tudo que poderia ter escalado mas foi decidido autonomamente.

**Não registrar:** correção de typo, atualização de status, edição de comentário.
