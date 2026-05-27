---
owner: roldao
revisado-em: 2026-05-27
status: stable
escopo: pré-Wave A — 14 módulos pendentes + 28 ADRs propostas + F-C2/F-C3 + TRACKs Wave A M1-M4 + drift docs pós-SAN-PERFIL-TENANT
agentes: 10 lentes paralelas (tech-lead, advogado, RBC, corretora, auditor-produto, auditor-drift-docs, integrações, foundation-gaps F-C, TRACKs Wave A, ADRs propostas)
gatilho: Roldão pediu escopo "Amplo — gaps + dívidas + estado" via AskUserQuestion 2026-05-27 (pós-SAN-PERFIL-TENANT Sprints 1-4 fechados)
---

# Auditoria pré-Wave A — Rodada 1 (10 lentes)

Data: 2026-05-27. Solicitada por Roldão imediatamente após SAN-PERFIL-TENANT Sprints 1-4 fechados, ANTES de arrancar Wave A propriamente. Objetivo: detectar lacunas estruturais (tipo FAIL L6 do SAN-PERFIL-TENANT — predicate lendo payload, snapshot no nível errado, INV nunca codada) ANTES de codar mais 14 módulos.

## Estado inicial (entrada da auditoria)

- **Foundation+Marcos fechados:** F-A (2026-05-18), F-B (2026-05-18), M1 clientes (2026-05-21), M2 equipamentos (2026-05-23), F-C1 (2026-05-24), M3 OS (2026-05-25), M4 calibração (2026-05-27).
- **SAN-PERFIL-TENANT:** Sprints 1-4 FECHADOS 2026-05-27 (schema multi-step, predicate `tenant_perfil_e`, provisionar_tenant, snapshot `perfil_no_evento` WORM). Sprints 5-6 = Wave A.
- **ADRs:** 68 totais (0000-0067). Aceitas: 39. Propostas: 29.
- **Hooks:** 51 ativos / 414 casos verdes no `_test-runner.sh`.
- **Suite:** M4 chave 629/629 PASS, suite ampla regression+audit+M3+M4 exit 0 pós-saneamento.
- **F-C2 e F-C3:** NÃO fechadas (entregáveis listados em `docs/faseamento-foundation-waves.md` §4.2/§4.3).

## Lentes desta rodada

| # | Lente | Agente |
|---|-------|--------|
| L1 | Modelo de domínio + transversais | `tech-lead-saas-regulado` |
| L2 | LGPD / contratos Aferê↔tenant + sub-operadores | `advogado-saas-regulado` |
| L3 | ISO 17025 / RBC CGCRE | `consultor-rbc-iso17025` |
| L4 | Seguros + responsabilidade civil | `corretora-seguros-saas` |
| L5 | Produto / AC binário PRDs 14 módulos Wave A | `auditor-produto` |
| L6 | Drift docs entre AGENTS/CURRENT/MEMORY/ADRs | `auditor-drift-docs` |
| L7 | Integrações inter-modulares Wave A | `general-purpose` |
| L8 | Foundation gaps F-C2/F-C3 + pré-requisitos Wave A | `general-purpose` |
| L9 | Saneamento residual M1-M4 (TRACKs Wave A) | `general-purpose` |
| L10 | ADRs propostas — coerência cruzada com ADR-0067 | `general-purpose` |

## Veredito por lente

> A preencher conforme cada agente retorna. Cada bloco terá:
> - Achados CRÍTICO (bloqueia Wave A)
> - Achados ALTO (retrabalho garantido se Wave A começar)
> - Achados MÉDIO (drift/convenção)
> - Achados BAIXO/INFO
> - Lacunas-tipo L6 (predicate lê payload / snapshot nível errado / INV nunca codada)

### L1 — Modelo de domínio

**Resumo:** 6 lacunas-tipo L6 detectadas (fraude documental viável via payload, snapshot no nível errado, regra de negócio ignorando perfil persistido). 6 CRÍTICO + 9 ALTO + 6 MÉDIO = 21 achados acionáveis. Se Wave A começar sem fechar TOP-1..10, cada um dos 14 módulos cravará variante do FAIL L6 e auditoria pós-Wave-A repetirá retrofit pesado (4 sprints SAN-PERFIL-TENANT).

#### TOP críticos (lacuna-tipo L6 — mesmo padrão estrutural do SAN)
1. **[CRÍTICO L6 — CER-RBC-PAYLOAD] Template lê `cert.tipo_acreditacao` em vez de `Tenant.perfil_regulatorio`** — `certificados/prd.md:317` §6.1. Operador marca cert como RBC no payload e ganha selo CGCRE+ILAC-MRA no PDF sem tenant ser perfil A. **Ação:** AC-CER-010-2 cita predicate `tenant_perfil_e({"A"})`.
2. **[CRÍTICO L6 — LIC-001-3] Licença CGCRE marcada como bloqueante por padrão sem checar perfil** — `licencas-acreditacoes:66`. Tenant perfil D cadastra licença CGCRE de outro lab + marca bloqueante; INV-032 nunca encontra → emissão segue solta. **Ação:** AC-LIC-001-3 + US-LIC-010..012 pré-condição `tenant_perfil_e({"A","C"})`.
3. **[CRÍTICO L6 — FIS-001 OCSP] Predicate `verificar_status` A3 não vinculado a `Tenant.cert_digital_id`** — `fiscal` AC-FIS-001-1/6. Abre vector pra emitir NF-e com A3 de outro CNPJ. **Ação:** FK NOT NULL `Tenant.cert_a3_e_cnpj_id` + INV-A3-OCSP-001 pré-condição "cert verificado == cert persistido".
4. **[CRÍTICO L6 — ACS-006 FILIAL] Filial-ativa lida do seletor do usuário sem persistir em sessão server-side** — `acesso-seguranca:138`. Atendente filial A passa `filial_id=B` no payload e enxerga filial B. **Ação:** ContextVar `filial_atual_context` populada por middleware + bloqueio de `filial_id` no payload.
5. **[CRÍTICO L6 — TRE-007 BYPASS] AC-TRE-007-3 permite bypass de competência com justificativa+aprovação sem ADR objetiva** — `treinamentos:132`. ISO 17025 cl. 6.2 não admite bypass arbitrário (análogo ADR-0026). **Ação:** ADR-0069 "bypass competência cl. 6.2" com matriz objetiva.
6. **[CRÍTICO L6 — SST-004 NR-* PERFIL] AC-SST-004 não diferencia perfil tenant** — `seguranca-trabalho:104`. Perfil A vs D têm obrigações NR diferentes. **Ação:** matriz "perfil tenant × NR exigida" via `matriz-feature-perfil.md`.

#### CRÍTICOS gerais (bloqueia Wave A começar)
7. **[CRÍTICO — RT SUBSTITUTO] Persona "RT substituto/sucessor" ausente em 14 PRDs.** ADR-0022 trata vigência+competência mas NÃO trata substituição. **Ação:** ADR-0068 "Sucessão/substituição RT" antes de Wave A.
8. **[CRÍTICO — EST-002 LOTE-VENCIDO-EM-VEÍCULO] Lote em trânsito ou no veículo do técnico continua usável após `validade < now()`** — `estoque:58,64-67`. ADR-0030 `JanelaVigencia` declarada mas não aplicada em `LoteEstoque`. **Ação:** AC-EST-002-2 cita `JanelaVigencia` + job diário `bloquear_lote_vencido`.
9. **[CRÍTICO — EQP CLIENTE-ATUAL] `Equipamento.cliente_atual_id` FK pura quando ADR-0032 prescreve `ReferenciaPIIAnonimizavel`** — `certificados` AC-CER-013. Quando cliente anonimizado, Equipamento aponta pra registro vazio. **Ação:** retrofit antes de `app-tecnico` cravar no mobile (US-APP-001-2).
10. **[CRÍTICO — PROC-VIGENTE FAIL-OPEN PERMANENTE] US-PROC-002 não cita plug `AtividadeDaOS.procedimento_versao_id`** — `procedimentos/prd.md:60` + ADR-0066. Sem GATE-CAL-PROC-VIGENTE-PREDICATE acionado, fail-open vira default permanente. **Ação:** US explícita em `procedimentos` + tarefa Wave A bloqueante.

#### ALTOS (retrabalho garantido)
11. INV-026 PREÇO-NÃO-RETROATIVO duplicado em 3 PRDs sem VO `Preco`
12. EXIF-strip duplicado em `app-tecnico` e `certificados` sem VO `FotoComExifSegregado` + INV-FOTO-EXIF-001 transversal
13. AGE-INV-020 Lei 13.103 sem consultar perfil (tenant D sem técnico CNH)
14. CHM-003 SLA sem entrada `perfil_regulatorio` na tabela
15. BCN base-conhecimento busca sem citar INV-TENANT-001 no GIN/tsvector
16. APP-003 GPS LGPD-consentimento autodeclarado em payload (não em `Colaborador.consente_gps_em`)
17. CT-002 caixa-técnico offline não cita IDEMP-001 (`client_offline_id` UUID4)
18. **`perfil_no_evento` falta em `contas-receber` + `fiscal`** — Sprint 4 SAN-PERFIL incompleto. Retrofit migrations adicionando coluna `GENERATED ALWAYS AS`.
19. TRE-004 certificado treinamento duplica padrão Certificado calibração

#### MÉDIOS
20. `JanelaVigencia` ADR-0030 não citada em 10 PRDs (estoque/lote, agenda/feriado, treinamentos, licenças)
21. Soft-delete ADR-0031 não citado em chamados, orcamentos, agenda
22. `revisado-em` vs `revisado_em` inconsistente entre 10 PRDs (hook quebra)
23. Cache offline `app-tecnico` sem `ReferenciaPIIAnonimizavel` no payload `Cliente.Anonimizado`
24. INV-AGENT-001 prompt injection só em `app-tecnico` (falta em `chamados`/`base-conhecimento`)
25. `caixa-tecnico` US-CT-005 sem citar trigger PG anti-mutação análogo a `auditoria_anti_*`

#### Veredito agregado
- 6 lacunas-tipo L6 (mesma família do SAN-PERFIL-TENANT) — REPETE o erro estrutural se Wave A começar sem fechar
- Personas ausentes: RT substituto/sucessor (item 7) — ADR-0068 nova
- VOs duplicados/inexistentes: `Preco`, `FotoComExifSegregado`, `LoteEstoqueVigente`
- Retrofit Sprint 4 SAN-PERFIL incompleto (CR + Fiscal sem `perfil_no_evento`)
- **Recomendação:** consertar TOP-1..10 ANTES de Wave A; itens 11-19 em saneamento paralelo Sprint 5; itens 20-25 em pass drift final.

### L2 — LGPD / contratos Aferê↔tenant

**Resumo:** 5 CRÍTICOS LGPD + 3 CRÍTICOS contratuais + 4 ALTOS + 5 MÉDIOS. Minutas existem (`termo-de-uso-afere-v1.0.md`, `politica-de-privacidade-afere-v1.0.md`, `dpa-modelo-cap-responsabilidade.md`, runbook DPO, subprocessadores) mas TODAS `aguarda-revisao-oab: true`. **0 de 7 sub-operadores com DPA assinado.** ADR-0067 perfil regulatório não reflete no DPA.

#### TOP críticos (bloqueia 1º dogfooding com dados reais)
1. **[CRÍTICO LGPD-001] PP não publicada — sem aviso ao titular.** Campos `[a definir]` em razão social/CNPJ/DPO. Mesmo dogfooding coleta CPF de clientes finais da Balanças. LGPD art. 9º exige informação clara antes da coleta. Sanção até R$ 50M.
2. **[CRÍTICO LGPD-002] DPO não designado formalmente.** Roldão acumula informalmente. Art. 41 §1º exige canal indicado. ANPD fiscaliza MPE também. **Ação:** designação formal (Roldão interino OU DPO-as-Service R$ 800-2.5k/mês — Privacy Tools, Opice Blum). Promover ADR-0061.
3. **[CRÍTICO LGPD-003] DPAs com 7 sub-operadores: 0/7 assinados.** Prioridade: PlugNotas/Lacuna (BR-BR) → Hostinger → AWS (DPA addendum) → Backblaze (confirmar EU vs EUA — `transferencia-internacional.md` diz EU, `subprocessadores.md` diz EUA) → Anthropic ZDR → Grafana/Axiom V2. **Recomendação:** migrar réplica AWS KMS de us-east-1 pra sa-east-1b+1c (mesma região = sem transferência internacional).
4. **[CRÍTICO LGPD-004] ADR-0067 perfil regulatório não reflete no DPA.** Cap R$ 500k uniforme para perfil D (R$ 300/mês) viola CDC art. 39 V. Addendum "Anexo I — Especificidades por Perfil Regulatório" com 4 tabelas (cap, retenção, direitos, SLA, cláusulas ISO).
5. **[CRÍTICO LGPD-005] Direitos do titular Wave A — 12 dos 17 módulos sem fluxo real.** Só `clientes` ✅; outros 16 são 🛠 fan-out dependendo de endpoint inexistente. Prazo ANPD 15 dias úteis. **Ação:** promover ADR-0061 e priorizar como 1º item Wave A. Mitigação interim: canal `dpo@…` responde manual com SLA em planilha.

#### CRÍTICOS contratuais
6. **[CRÍTICO CTR-001] Decisão Aferê PJ separada vs interno Balanças.** Recomendo manter dentro da Balanças Solution durante dogfooding (zero custo, sem complexidade tributária). PJ separada só quando aparecer 2º tenant externo.
7. **[CRÍTICO CTR-002] Subcontratação ISO cl. 6.6 — DPA encadeado não existe.** US-CAL-017 M4 entregue, mas Aferê→Tenant→Lab subcontratado sem cadeia documentada (LGPD art. 39 §4º).
8. **[CRÍTICO CTR-003] ToU placeholder `[RAZÃO SOCIAL]`** impede aceite válido (CC art. 104 — objeto indeterminado).

#### ALTOS por módulo Wave A
- `contas-receber` e `acesso-seguranca` PRDs zero ocorrências de "direitos titular" / "anonimizacao"
- GATE-DIR-TIT-1 (Marco 3 OS Fase 5) precisa estender aos 14 módulos Wave A; hook `prd-direitos-titular-check.sh` criar
- `app-tecnico` biometria touch + foto+EXIF: OK estrutural (DPIA existe) mas fan-out endpoint não existe
- `fiscal` NFS-e: PlugNotas DPA pendente (já citado)
- `contas-receber` Wave A NÃO toca cartão (PCI ⚪ lazy correto); Wave B Asaas DPA pré-req

#### MÉDIOS
- Backblaze EU vs EUA inconsistência interna
- Anthropic — confirmar ZDR via console
- Hostinger — verificar DPA nos T&C
- Foro arbitral CAM-CCBC (R$ 20-40k instauração) desproporcional pra perfil D (R$ 300/mês — abusiva CDC art. 51 IV); usar arbitragem só >R$ 50k, abaixo JEC/foro Cuiabá-MT

#### Veredito agregado
- 17 itens canônicos auditados; 12 bloqueia dogfooding profundo / externo
- **Recomendação OAB Tier 1 (próximos 30 dias):** R$ 8-15k pacote — PP+ToU+DPA+addendum perfil+subprocessadores
- **Tier 2 (antes 1º tenant externo):** R$ 3-5k DPO formal + DPA subcontratação + apólice
- **Tier 3 (farma TOP-3 / 1ª supervisão CGCRE):** R$ 8-20k/ano dedicado
- **Material pronto pra OAB:** esta auditoria + minutas + ADR-0067 + matriz feature×perfil + 17 finalidades + matriz direitos titular + retenção

### L3 — ISO 17025 / RBC

**Resumo:** 5 CRÍTICOS + 2 CRÍTICOS gerais + 16 ALTOS + 6 MÉDIOS. 6 cláusulas ISO com gap CRÍTICO. **Tenant Balanças NÃO está pronta pra 1ª supervisão CGCRE com config atual.**

#### TOP críticos (CGCRE pergunta na 1ª pergunta de supervisão)
1. **[CRÍTICO RBC-4.1] Imparcialidade ausente em TODO o repo.** Grep `imparcialidade|4\.1|comitê.*imparcialidade` zero arquivos. CGCRE para na 1ª hora sem política + comitê + análise de risco + declaração conflito. **Ação:** módulo `governanca-laboratorial` ou expandir `qualidade` com US-IMP-001..004 + ADR transversal.
2. **[CRÍTICO RBC-7.1] Análise crítica de pedidos ausente em `orcamentos` e `chamados`.** Hoje orçamento vira OS sem gate técnico-metrológico (CMC? padrão disponível? RT competente?). **Ação:** US-ORC-NNN consultando `cmc_cobre` + `procedimento_vigente_para` + `rt_competencia_cobre` + `padrao_disponivel`.
3. **[CRÍTICO RBC-7.11] ADR-0025 só pra calibração** — `certificados`, `procedimentos`, `padroes`, `licencas-acreditacoes` SEM URS/IQ/OQ/PQ. Auditor CGCRE pede dossiê do software que emite o cert, não só do que calcula incerteza.
4. **[CRÍTICO RBC-NIT-DICLA-021] Competência RT por GRANDEZA, não por método.** ADR-0022 `RTCompetencia` só tem `grandeza` (massa/comprimento/etc.); NIT exige "Massa **classe E2 OIML R111 método de subdivisão**". RT "massa balança comum" hoje pode assinar cert RBC de massa E1 sem barreira. **Ação:** ADR-0022 v2 com `(grandeza, metodo_id, faixa_min, faixa_max)`.
5. **[CRÍTICO RBC-PREDICATES] Fail-open ADR-0063/0066 sem GATE-WAVE-A-PREDICATES-FAIL-CLOSED.** Balanças vira perfil A com 3 predicates retornando True → NC documental certa. **Ação:** adicionar 8º gate em ADR-0067 bloqueando 1º perfil A produtivo.

#### CRÍTICOS gerais
6. **[CRÍTICO RBC-6.6] Subcontratação — `certificados` NÃO marca trabalho subcontratado.** US-CAL-017 M4 entregue mas PDF não declara "calibração realizada por [subcontratado]" (cl. 6.6.2).
7. **[CRÍTICO RBC-6.4.5] Equipamentos auxiliares do lab (termo-higrômetro de sala, fonte de tensão, banho) NÃO modelados.** Só `PadraoMetrologico` e `Equipamento` do cliente. CGCRE pergunta "qual termo-higrômetro mediu T=20°C dessa cal?" e tenant não responde.

#### ALTOS (16 itens)
- Cl. 4.1: auditoria interna anual + cadastro vínculos comerciais auto-calibração proibida
- Cl. 7.1: discordâncias lab/cliente + registro de exceção
- Cl. 7.2: validação de método quando lab modifica norma (não só catálogo)
- Cl. 7.3: amostragem não-declarada como non-goal em PRD canônico
- Cl. 7.4: armazenamento durante calibração ausente; dano em trânsito sem registro técnico
- Cl. 7.7: cartas de controle MVP-2 → adiantar pra MVP-1 (perfil A exige desde 1ª supervisão)
- Cl. 7.8.6: PDF não imprime obrigatoriamente regra+PFA/PRA+zona ILAC (ADR-0024 entregou mas template incompleto)
- Cl. 7.10: duplicação `calibracao.NaoConformidade` vs `qualidade.NC` sem ADR reconciliando
- Cl. 7.11: replay determinístico não cobre geração do PDF (WeasyPrint sem `SOURCE_DATE_EPOCH`)
- Cl. 8.5/8.8/8.9: congelados MVP-2; Balanças vira perfil A em MVP-1 = NC mínima certa
- NIT-DICLA-016/021: afastamento/substituto do RT inexistente
- Cl. 6.2.5: matriz `(pessoa × atividade × supervisor exigido)` ausente

#### MÉDIOS
- Glossário VIM 3 / ISO 17025 incompleto (faltam CMC, rastreabilidade, U)
- Idioma certificado (PT vs bilíngue PT+EN) sem ADR
- Timezone lab vs servidor sem INV (MT UTC-4 vs SP UTC-3 → "data calibração 23:30 dia anterior")
- Drift export dossiê CGCRE entre `licencas-acreditacoes` e `padroes`
- ADR-0046/0047 propostas — sem PAdES-LTV cert perde validade em ≤5a quando cert RT expira (cl. 8.4 exige 25a)
- ADR-0014 imparcialidade ainda proposta (crítico 1)

#### Veredito agregado
- **6 cláusulas com gap CRÍTICO** (4.1, 7.1, 7.11 estendida, 6.2.5/NIT-021, predicates fail-open, 6.4.5)
- Fail-open Wave A NÃO TRAVA hoje — criar gate AGORA
- ADR-0025 cobertura: M4 sim; 4 módulos Wave A NÃO
- **Estimativa 12 semanas pra ficar pronto pra 1ª supervisão.** Contratar consultor RBC humano credenciado 4-8 semanas antes (R$ 8-15k pontual).

### L9 — Saneamento residual M1-M4 TRACKs

**Resumo:** ~80 TRACKs catalogados (9 FECHADOS, 71 abertos). 7 BLOQ-WA-START, 30 BLOQ-WA-FECHA, 25 BLOQ-EXTERNO, 9 TECH-DEBT. Estimativa total: ~80d dev + 10-12 semanas calendário paralelo.

#### TOP críticos (BLOQ-WA-START — fechar antes do 1º commit Wave A — ~9d ≈ 2 semanas)
1. **[CRÍTICO TRACK-CAL-VIEWSETS] T-CAL-124..133 — 10 ViewSets REST restantes** (5d). Hoje só CalibracaoViewSet 3 actions: produto invisível. Ordem 1.
2. **[CRÍTICO TRACK-OS-GRANDEZA] GATE-OS-GRANDEZA-EM-ATIVIDADE** (1.5d). M4 fechou sem retrofit do campo `grandeza` em AtividadeDaOS. ADR-0063 fail-open ainda ativo. Ordem 3.
3. **[CRÍTICO TRACK-IDEMP-HOOK] GATE-IDEMP-HOOK-DETECT-ACTION** (0.5d). Hook não detecta `@action(methods=POST)`. Ordem 2.
4. **[ALTO LIMPA-MESA]** GATE-FB-4 + GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA + GATE-EQP-RT-AUTHZ + GATE-DEP-001/002 + GATE-EQP-DEP-WEASYPRINT-UPGRADE — 5 itens baratos (~2.5d total).

#### Categorias consolidadas
- **Bateria drills PG real** (M3 + M4 + SAN-PERFIL): consolidar em 1 drill-day Balanças (2d)
- **Bateria perf** (N+1 visão-360 + assertNumQueries + p95<1.5s): perf-week (4d)
- **Sagas + consumers** (CLI-2/5/6/7/8 + sucessão + sync mobile): 8.5d à medida que módulos Wave A destravam
- **Storage real** (B2 WORM + Object Lock + retenção 25a): consolidar GATE-1+2+4+CLI-1+EQP-2+T-CAL-114+GATE-CAL-BACKUP-METROLOGICO em frente única (5d)
- **KMS real** (AWS KMS MRK + RFC 3161 TSA-ITI): consolidar GATE-CAL-KMS+EQP-KMS+EQP-5 (6d)
- **Notificações regulatórias** (consumers ANPD/CGCRE + retry anonimização): 5d
- **Dependências humano OAB** (6 frentes consolidadas em 1 contratação): 3-5 semanas calendário
- **Dependências humano RBC** (carta competência RT NIT-DICLA-021): 2 semanas + R$3-5k
- **Dependências corretora SUSEP** (apólice E&O+Cyber+BPT+Property): 4-6 semanas
- **Pentest externo**: 2-3 semanas + contratação

#### ADRs fail-open status
- **ADR-0063 (M3 OS)** — M4 fechou sem retrofit `AtividadeDaOS.grandeza`. Fail-open ATIVO. Fechar em Sub-onda A.
- **ADR-0066 (M4)** — aguarda módulos novos Wave A `metrologia/escopos-cmc` + `procedimentos-calibracao` (6d cada).
- **ADR-0067** — Sprints 1-4 fechados; 5-6 são Wave A.

#### Veredito agregado
**Onda de saneamento em 3 sub-ondas:**
- **Sub-onda A (2 semanas — pré-Wave A start)** — 7 BLOQ-WA-START + limpa-mesa = ~9d dev
- **Sub-onda B (durante Wave A, paralela)** — 30 BLOQ-WA-FECHA = ~55d distribuídos em 6-8 semanas
- **Sub-onda C (calendário paralelo — disparar JÁ no Wave A start)** — 3 contratações externas (OAB+RBC+Corretora) + B2/KMS provisioning + pentest = 5-8 semanas

**Bloqueador conceitual:** Roldão decidir disparar as 3 contratações externas. Sem isso, BLOQ-EXTERNO não fecha. Recomendação: disparar JÁ no Wave A start.

### L4 — Seguros + responsabilidade civil

**Resumo:** 4 CRÍTICOS + 6 ALTOS + 5 MÉDIOS. GATE-SEG-BPT-1 emergencial (4 dias parado, risco R$ 800-2.400/mês). Pacote 7 modalidades dimensionado corretamente em ADR-0028 rev 2; falta calibração de capital + cláusulas afirmativas IA + DPA cap.

#### TOP críticos
1. **[CRÍTICO SEG-001] GATE-SEG-BPT-1 parado** — Balanças já recebe equipamento de cliente em dogfooding; sem BPT, queda de balança de R$ 50-200k vira saída de caixa direta. **Ação:** Roldão contata corretora SUSEP esta semana só pra BPT isolado (R$ 4-8k/ano, emissão 5-10 dias úteis).
2. **[CRÍTICO SEG-002] DPA cap responsabilidade em minuta sem integração** — `dpa-modelo-cap-responsabilidade.md` cláusula 11.2 (cap 12 mensalidades ou R$ 500k) é a peça de MAIOR retorno e MAIS BARATA (só redação OAB R$ 2-4k). Sem cap, ação judicial pode pedir lucros cessantes ilimitados.
3. **[CRÍTICO SEG-003] Apólice modular por perfil ADR-0067 não dimensionada** — perfil A aciona Modalidade 7 (Accreditation Loss); perfil D nunca. Mod 7 em standby R$ 500k até 1º perfil A externo economiza R$ 8-15k/ano.
4. **[CRÍTICO SEG-004] D&O Roldão PF + ADR-0019 sem cláusula afirmativa IA** — risco seguradora negar sinistro citando "código IA sem revisão humana" como neglect. Plano B: cosseguro Lloyd's via Marsh com cláusula AI-affirmative.

#### CRÍTICOS por modalidade
- **E&O:** lista `consequential regulatory damages` sem ANEEL/ANATEL/ANP; `continuity of coverage` 25y precisa cravar como obrigatório Mod 1.
- **Cyber:** capital R$ 5M subdimensionado (ANPD multa por infração; 50 tenants × 200 titulares = R$ 50M cenário-pior); subir R$ 5M→R$ 10M + 2 reinstatements (+R$ 8-15k/ano); adicionar `OCSP/CRL fallback gap coverage` ADR-0046.
- **BPT:** franquia escalonada (R$ 5k até R$ 50k bem / R$ 15k acima); estender trânsito tenant↔Aferê (ou seguro cargas separado).

#### ALTOS
5. Dependent Service BI (Mod 6) — waiting period 4h tight (us-east-1 já caiu 6h; Anthropic 8h); negociar 2h ou `regulatory deadline missed coverage` independente.
6. Wrongful billing rev 2 — `contas-receber` Wave A já gera fatura antes de billing-saas Wave B; cravar cláusula "billing-agnóstica".
7. D&O exclusão fraude — definir como "sentença transitada em julgado" + `advancement of defense costs`.
8. Cyber × Mod 7 — overlap não resolvido; cláusula `priority of coverage` (Mod 2 → Mod 6 → Mod 7).
9. GATE-SEG-DRILL-1 (drill anual ANPD) aberto — drill reduz prêmio Cyber 10-20%. Executar junho/2026 antes da cotação.
10. Cláusula RC IA do ADR-0019 pilar 1 não está no DPA cap — integrar.

#### MÉDIOS
11. Mod 5 (extensão veicular UMC) — Wave A é bancada-only; deferir Mod 5 pra Wave B (economiza R$ 2-4k/ano).
12. Estimativa R$ 60-120k/ano = 5-17% receita (acima benchmark SaaS regulado 3-8%); franquias mais altas ano 1 baixa 25%.
13. Cosseguro internacional não plotado — pedir Marsh/AON cotação BR-only + cosseguro 60/40 Lloyd's.
14. `Notice of circumstances` ampla — Aferê detecta circunstância antes de claim chegar; padrão Lloyd's, mercado BR resiste mas negociável.
15. DPO formal não nomeado — Cyber cota +15-25% sem DPO; Roldão se auto-nomeia interino até pós-1º tenant externo.

#### Veredito agregado
- ADR-0028 rev 2 com 7 modalidades está dimensionada corretamente; 2 precisam calibração (Cyber capital + Mod 7 standby).
- Estimativa pacote ano 1 dogfooding: R$ 35-55k/ano (sem receita externa). Pós-escala 5-10 tenants: R$ 60-120k/ano.
- **Sequenciamento próximas 4 semanas:**
  1. Esta semana: BPT isolado via Marsh/Howden.
  2. Semana 2: advogado OAB valida DPA cap (cláusulas 11.2-11.4 + ADR-0019 pilar 1).
  3. Semana 3: drill ANPD interno + relatório arquivado.
  4. Semana 4: pacote completo pra corretora escolhida (Fase 2).
- **Limite legal:** corretora SUSEP humana é obrigatória; tudo acima é briefing.

### L5 — Produto / AC PRDs Wave A

**Resumo:** 16 PRDs auditados (4 op + 4 metr + 2 rh + 2 supp + 1 com + 3 fin). **1/16 PRONTO** (`fin/fiscal` stable). 5 CRÍTICOS + 6 ALTOS + 9 MÉDIOS. Estimativa retrofit: ~130h ≈ 4 semanas paralelas. Bloqueia início Wave A em código.

#### TOP críticos
1. **[CRÍTICO PROD-PERFIL-001] 14/16 PRDs não declaram perfil ADR-0067.** Só `metr/padroes` (e parcial `rh/treinamentos`) mencionam A/B/C/D. Replica gap estrutural SAN-PERFIL.
2. **[CRÍTICO PROD-AC-001] `op/base-conhecimento` 100% sem AC binário** — 10 US sem GIVEN-WHEN-THEN. Reescrita completa (6h).
3. **[CRÍTICO PROD-ESCOPO-001] `supp/estoque` declara Wave B mas é Wave A** — conflito direto AGENTS §12.
4. **[CRÍTICO PROD-AC-002] `op/chamados`, `op/agenda`, `fin/caixa-tecnico`, `fin/contas-receber` — US sem GIVEN-WHEN-THEN** (~20h paralelo).
5. **[CRÍTICO PROD-PII-001] `fin/caixa-tecnico` GPS opcional sem matriz LGPD** — frase única "GPS opcional (com consentimento — LGPD)" sem base legal/retenção/DPIA.

#### ALTOS
6. `metr/certificados` §6.1 lê `cert.tipo_acreditacao` (payload) — mesmo padrão L6 fraude documental
7. `metr/licencas-acreditacoes` US-LIC-010 cadastra acreditação CGCRE sem `tenant_perfil_e([A,B,C])`
8. `fin/fiscal` INV-INT-001 mistura calibração e perfil sem separar (perfil A obriga RBC; D só declaração)
9. `fin/contas-receber` US-CR-006 ignora perfil em régua/retenção
10. 13/16 PRDs `revisado-em` ≥ 4 dias atrasado em relação a ADR-0067
11. 5/16 PRDs com frontmatter incompleto (sem `proximo-review`, `diataxis`, `audiencia`)

#### MÉDIOS (9 itens)
Personas inline ausentes em 11/16; dependências ADR não listadas em 14/16; lacuna L6 em chamados/agenda/treinamentos/seguranca-trabalho; non-goals usa "MVP-2" em vez de "Wave B"; `fin/caixa-tecnico` sem glossário; `owner` inconsistente roldao vs Roldão; `contas-receber` sem retenção Receita 5a; vocab "MVP-1/Wave A" em 4 estilos; 12/16 métricas só link sem inline.

#### Sequenciamento sugerido (4 batches)
- **Batch 1 (semana 1):** caminho crítico fiscal (33h) — `fin/fiscal` + `metr/certificados` + `fin/contas-receber` + `metr/licencas-acreditacoes`
- **Batch 2 (semana 2):** operação dogfooding (48h) — `op/app-tecnico` + `chamados` + `agenda` + `caixa-tecnico` + `base-conhecimento`
- **Batch 3 (semana 3):** metrologia + RH (24h) — `procedimentos` + `padroes` + `treinamentos` + `seguranca-trabalho`
- **Batch 4 (semana 4):** comercial + plataforma (~25h) — `orcamentos` + `acesso-seguranca` + `estoque` (após decisão Wave A vs B)

### L6 — Drift docs

**Resumo:** 5 CRÍTICOS + 5 ALTOS + 14 MÉDIOS. **AGENTS.md se contradiz 4× sobre hooks/casos.** INDICE faltando ADR-0067. CLAUDE.md congelado em 2026-05-17 (10 dias velho). MEMORY/session-state desatualizada.

#### Contagens reais vs declaradas
| Métrica | Real | AGENTS | CURRENT | MEMORY/session | INDICE | Drift |
|---|---|---|---|---|---|---|
| Hooks ativos | **51** | 48 (4 lugares) / 51 (1 lugar) | 51 | 48 | 48 | +3 em 4 lugares |
| Casos test-runner | **414** | 379 (4) / 414 (1) | 414 | 379 | 379 | +35 em 4 lugares |
| ADRs aceitas | **65 arquivos** | 68 §11 (inclui 59-61 reservadas) | OK | OK | **falta 0067** | INDICE -1 |
| AGENTS.md linhas | 297 | limite 300 | — | — | — | folga crítica |

#### TOP críticos
1. **[CRÍTICO DRIFT-001] AGENTS.md contradiz a si mesmo 4× sobre hooks/casos** — linhas 8/59/266/275 dizem 48/379; linha 126 diz 51/414 (correto)
2. **[CRÍTICO DRIFT-002] INDICE.md desatualizado em 3 fatos simultâneos** — falta ADR-0067; "48 hooks"; sitemap sem SAN-PERFIL-TENANT
3. **[CRÍTICO DRIFT-003] CLAUDE.md:5 cabeçalho congelado em 2026-05-17** — "Decisões fundadoras D1–D5 + ADRs 0000, 0001, 0002, 0007, 0008, 0009 ativas" quando hoje são 65 ADRs
4. **[CRÍTICO DRIFT-004] documentos-do-projeto.md zero menções a SAN-PERFIL/ADR-0067**
5. **[CRÍTICO DRIFT-005] memory/project_session_state.md:56 ainda diz 379/48** — fonte canônica de boot de outros agentes

#### ALTOS
- AGENTS.md:5 cabeçalho não cita SAN-PERFIL nem ADR-0067 (só §11/§12)
- AGENTS.md:8 drills sem `validar_san_perfil_tenant_*` (17/17 + 6/6 PASS PG real)
- AGENTS.md:9 GATEs Wave A omite 7 GATE-TENANT-PERFIL-*
- AGENTS.md:59 §3 lista de hooks omite tenant-perfil-imutavel + payload-tipo-acreditacao + feature-perfil-matriz (Sprints 1-3) + 4 hooks pré-existentes
- faseamento-foundation-waves §11 sem entrada SAN-PERFIL-TENANT 2026-05-27

#### 38 PRDs em `draft` ≥10 dias
- `comercial/clientes/prd.md` em draft mas M1 fechado 2026-05-21 (deve ser stable)
- 11 PRDs revisados 2026-05-23 (4 dias atrasado de ADR-0067)
- 25+ PRDs revisados 2026-05-17 (10 dias)
- Apenas 4 PRDs stable: os, fiscal, calibracao, equipamentos

#### Ondas de drift fix (~40 min total)
- DRIFT-A (números, 10min): 5 lugares com `48→51` e `379→414`
- DRIFT-B (ADR-0067+SAN-PERFIL em canônicos, 20min): INDICE + AGENTS:5 + AGENTS:9 + faseamento-FW §11 + documentos-do-projeto
- DRIFT-C (CLAUDE.md status, 5min)
- DRIFT-D (lista §3 hooks AGENTS, 5min): adicionar 4-7 hooks omitidos
- DRIFT-E (clientes/prd.md status draft→stable, 2min)
- DRIFT-F (cosméticos): typo "continui"; "tenant-id-validator ainda a criar"

### L7 — Integrações inter-modulares

**Resumo:** 4 CRÍTICOS + 6 ALTOS + 5 MÉDIOS. Críticos da rodada anterior (envelope, registry) resolvidos. **NOVA classe de gap:** M3/M4 gravam timeline LOCAL e nunca cruzam o `bus_outbox`. Snapshot `perfil_no_evento` Sprint 4 não propaga no envelope cross-módulo. Wave A vai amplificar 14×.

#### TOP críticos
1. **[CRÍTICO INT-2026-01] M3 OS publica `EventoDeOS` local mas nunca cruza o bus** — 18 use cases gravam timeline; nenhum chama `audit.event_helpers.publicar_evento`. Saga 1 (Orçamento→OS→Cert→NF→CR→Pgto) quebra no passo 2-3. Saga LGPD nunca dispara. 9 dos 18 consumers M3 estão dormindo aguardando publisher.
2. **[CRÍTICO INT-2026-02] M4 calibração tem mesmo padrão** — `EventoDeCalibracao` local sem ponte. `metrologia/certificados` Wave A não recebe `Calibracao.Aprovada`. ADR-0066 presume bus mas origem nunca acende.
3. **[CRÍTICO INT-2026-03] `perfil_no_evento` Sprint 4 NÃO propaga no envelope bus** — só preenche tabelas LOCAIS (auditoria/calibracao/os). Quando Wave A retrofitar, consumer cross-módulo opera **cego** ao perfil. Auditor CGCRE pergunta perfil no momento da emissão; certificado emitido não saberá.
4. **[CRÍTICO INT-2026-04] Hook `bus-envelope-validator.sh` é teatro** — valida só 4 regras pontuais (`tenant_id`, Fiscal+certificado_id, BillingSaas+modo, Cliente+zona). Não valida `event_id/_schema_version/occurred_at/correlation_id/actor`. Permite envelope incompleto se desenvolvedor pular helper canônico.

#### ALTOS (6)
- Sagas ADR-0034 documentadas mas apenas 3 stub-consumers em M3 (saga 1+3+4 incompletas; saga 2 inexistente)
- 5 eventos M1 críticos sem consumer (cliente.bloqueado em 3 lugares, consentimento_revogado, pii.incidente — ANPD ≤24h não dispara)
- ADR-0036 (replay schema) proposta — `_schema_version=1` fixo; janela 90d não implementada
- Hook `feature-perfil-matriz-validator` (Sprint 3) protege code local, não consumer Wave A
- Catálogo `automacoes-catalogo.md` declara 15 automações Wave A+B — engine ADR-0005 diferida; **nenhuma registrada em `_REGISTRY`**
- IDEMP-001 (`Idempotency-Key` em POST crítico) não rastreado por hook — Wave A fiscal/CR/CT recebem POST com risco duplicação

#### MÉDIOS
- `event_name` é `acao` (snake_case) em vez de PascalCase canônica catálogo
- `src/infrastructure/bus/` quase vazio; registry mora em `audit/outbox_worker.py`
- `dead_letter_events` existe (migration 0016) mas sem drill envenenamento (GATE-FC3-DLQ-DRILL)
- `integracoes-inter-modulos.md` revisado-em 2026-05-22 anterior a M3/M4/SAN-PERFIL
- Categorização Domain/Integration/Notification sem mecânica que separe

#### Eventos Wave A planejados
~150 publishers novos × 14 módulos. **Sem retrofit INT-01/02/03/04, cada um dos 14 módulos vai entregar publishers que ninguém consome.**

#### Onda pré-Wave A (3-5 dias dev + drill)
1. Retrofit M3 (INT-01): 18 use cases → `publicar_evento_bus` na mesma transaction.atomic
2. Retrofit M4 (INT-02): mesmo padrão calibração
3. Envelope perfil_no_evento (INT-03): `_inserir_no_outbox` lê `current_setting('app.perfil_tenant')`
4. Hook robusto (INT-04): exige envelope canônico inteiro
5. Sagas mínimas Wave A (INT-05): 4 sagas críticas com stubs + state-machine
6. Schema versioning (INT-07): `_schema_version` por evento + janela 90d
7. Consumer GATE-CLI-7/8 (INT-06): consumer-dummy logado pros 5 eventos M1

### L8 — Foundation gaps F-C2/F-C3 + pré-reqs Wave A

**Resumo:** F-C1 ✅ FECHADA. F-C2 0/5 prontos. F-C3 2/8 prontos (Redis + DLQ estrutura). **8 ADRs propostas críticas bloqueando Wave A.** Hooks Wave A 3/3 prontos. F-C2/F-C3 são bloqueantes pra deploy EXTERNO (memória `project_deploy_so_quando_roldao_quiser` → dogfooding pode codar em paralelo).

#### F-C2 (Observabilidade infra) — 0/5
- structlog real (base.py:441-462 placeholder)
- INV-LOG-001..003 não declaradas em REGRAS
- `/health` + `/ready` + `/health/deep` separados (só `/healthz/` trivial)
- SIGTERM procrastinate worker não implementado
- contextvar `correlation_id` 4 pontos não implementado

#### F-C3 (Instrumentação) — 2/8
- ✅ Redis em docker-compose.yml
- ✅ DLQ estrutura (migration 0016 + consumers/orcamento.py)
- ❌ DEFAULT_PAGINATION_CLASS + hook + retrofit 621 testes (cresce com tempo)
- ❌ DEFAULT_THROTTLE_CLASSES + INV-RATE-001..003
- ❌ circuitbreaker em chamadas externas (Lacuna/KMS/Asaas)
- ❌ prometheus-client + opentelemetry-sdk + dashboard 10 métricas
- ❌ Pin SHA Docker + 3 actions + dependabot.yml

#### TOP críticos (bloqueia Wave A começar)
1. **[CRÍTICO PRE-WAVE-A-01] ADRs 0014, 0015, 0016 propostas há > 6 meses** — sem promoção, INV-INT-001..013 não exigíveis em Wave A
2. **[CRÍTICO PRE-WAVE-A-02] ADR-0010 estratégia tela proposta** — 1ª tela vira precedente acidental
3. **[CRÍTICO PRE-WAVE-A-03] ADR-0008 fiscal com deadline 01/09/2026** (NFS-e nacional)
4. **[CRÍTICO PRE-WAVE-A-04] 9 PRDs Wave A em draft** — agente codador inventa AC

#### ALTOS
- F-C2 inteiro não iniciado (dogfooding tolera; externo NÃO)
- F-C3 paginação ausente — retrofit cresce com cada Marco (621 hoje, pode ser 1500 daqui 2 meses)
- Supply-chain `dependabot.yml` inexistente + actions/Docker sem pin SHA
- ADR-0009 A3 Lacuna proposta
- **Drift: `clientes/prd.md` draft mas Marco 1 fechado 2026-05-21** (cross-check L6)

#### MÉDIOS
- ADR-0034 saga compensação proposta; código já existe sem decisão formalizada
- ADRs 0059/0060/0061 reservadas mas sem arquivo físico (drift estrutural §11)
- `circuitbreaker` ausente

#### Recomendação — 4 ondas pré-Wave A
- **Onda PRE-A.1** (Promoção ADRs — sessões Roldão+tech-lead): promover 0014/0015/0016 + 0010 + 0008 + 0009 + 0003 + 0004; resolver drift 0059-0061
- **Onda PRE-A.2** (Saneamento PRDs paralelo): promover ~9 PRDs draft→stable
- **Onda PRE-A.3** (CODAR antes 1º módulo): paginação + retrofit 621 + dependabot + pin SHA + throttle
- **Onda PRE-A.4** (paralela aos primeiros módulos): F-C2 completa (structlog + INV-LOG + endpoints + SIGTERM + correlation_id)
- F-C3 Prometheus + circuit breaker: final Wave A ou Wave B

### L10 — ADRs propostas — coerência cruzada

**Resumo:** 29 ADRs propostas auditadas vs ADR-0067. **3 superadas/housekeeping**, **6 conflitam direto** (exigem emenda), **5 com prazo regulatório duro**, **4 adiar Wave B/V2**, **15 prontas pra promover**. Custo: ~3 sessões emendar + 1 batch promover + 1 housekeeping. 3 decisões Roldão necessárias.

#### TOP críticos (BLOQ-WA-START)
1. **[CRÍTICO ADR-0008]** Fiscal pluggable — **deadline duro 01/09/2026** NFS-e Padrão Nacional (14 semanas)
2. **[CRÍTICO ADR-0010]** Estratégia tela (HTMX + 5 SPAs) — decisão Roldão via AskUserQuestion
3. **[CRÍTICO ADR-0015]** Lifecycle tenant — JÁ EMENDADA Sprint 3, só trocar `status: aceito`
4. **[CRÍTICO ADR-0009]** A3 cliente-side — emenda perfil A obrigatório
5. **[CRÍTICO ADR-0028]** Mapa coberturas seguro — decisão financeira Roldão + cotação SUSEP
6. **[CRÍTICO ADR-0013]** Pricing composicional — sem componente `perfil_regulatorio` modelo billing-saas quebra

#### ALTOS (BLOQ-WA-FECHA — 6 conflitos com ADR-0067)
- ADR-0009 A3 (trata como opcional; matriz exige A3 obrigatório em perfil A)
- ADR-0013 pricing (sem componente perfil)
- ADR-0035 tenant suspenso (matriz "param/continuam" igual pra todos; A suspenso perde CGCRE)
- ADR-0043 bloqueio inadimplência (igual pra todos; A com grace period maior)
- ADR-0044 export ANVISA (não consulta perfil; perfil A único válido com selo CGCRE)
- ADR-0045 recall cert (recall+notificação CGCRE só perfil A)

#### MÉDIOS
- ADR-0004 vs 0027 — verificar superseded-by
- ADR-0049/0050/0052/0053 cluster fiscal/pagamento — promover em batch
- ADR-0037 glossário, ADR-0018 QR (housekeeping)
- ADR-0019 → marcar `superseded-by: 0028`
- ADR-0003 stub vazio (escrever conteúdo)

#### Sequenciamento (4 sprints)
- **Sprint A (esta semana):** 0008 + 0049 (deadline) + 0015 (só status) + 0009 + bloco A3 (0046/0047/0048)
- **Sprint B (próxima):** 0010 UI (AskUserQuestion Roldão) + 0035/0043 + 0044/0045
- **Sprint C (até 1º externo):** 0028 (corretora) + 0019 superseded + batch limpo (0014/0016/0034/0036/0037/0038/0039/0050/0051/0052/0053)
- **Sprint D (adiados):** 0005, 0011, 0013 (emenda), 0055

#### Achado-bonus
ADR-0067 introduziu `perfil_regulatorio` mas apenas 3 ADRs entre as 29 mencionam perfil. **Hook `feature-perfil-matriz-validator` deveria varrer ADRs em status proposta também**, não só PRDs, pra evitar ADRs nascerem em drift.

## TOP CRÍTICOS consolidados

### Família A — Lacunas-tipo L6 (fraude documental viável — mesmo padrão do SAN-PERFIL-TENANT)

Achados que repetem em escala 14× o gap estrutural que o saneamento de hoje consertou. Cada um deixa o sistema ler **fonte não-confiável** (payload da request) em vez de fato persistido. **Se Wave A começar sem fechar, o saneamento Sprint 5-6 vai precisar refazer o que SAN-PERFIL-TENANT 1-4 fez — só que para 14 módulos.**

1. **CER-RBC-PAYLOAD** — Template lê `cert.tipo_acreditacao` em vez de `Tenant.perfil_regulatorio`. (L1#1 + L5#6)
2. **LIC-001-3 BLOQUEANTE-RBC** — Acreditação CGCRE bloqueante sem checar perfil. (L1#2 + L5#7)
3. **FIS-001 OCSP-A3** — Predicate verifica A3 sem amarrar a `Tenant.cert_a3_e_cnpj_id`. (L1#3)
4. **ACS-006 FILIAL-NO-PAYLOAD** — Filial-ativa do seletor sem persistir em sessão server-side. (L1#4)
5. **TRE-007 BYPASS-COMPETÊNCIA** — Bypass com justificativa sem ADR objetiva (análogo ADR-0026). (L1#5)
6. **SST-004 NR-PERFIL** — NR-* sem diferenciar perfil tenant. (L1#6)

### Família B — Bloqueia Wave A COMEÇAR (urgência máxima)

7. **ADR-0008 fiscal pluggable — DEADLINE REGULATÓRIO DURO 01/09/2026** (14 semanas). NFS-e Padrão Nacional vira obrigatória. Mesmo dogfooding precisa emitir NFS-e válida. (L8#3 + L10#1)
8. **ADRs 0014/0015/0016 propostas há > 6 meses** — `docs/faseamento-foundation-waves.md` §5 exige aceitas antes Wave A começar. ADR-0015 já EMENDADA Sprint 3 — só trocar status. (L8#1 + L10#3)
9. **Bus M3/M4 grava timeline LOCAL e nunca cruza outbox** — saga 1 (Orçamento→OS→Cert→NF→CR) quebra no passo 2-3; 9 dos 18 consumers M3 dormem aguardando publisher; Saga LGPD anonimização nunca dispara. (L7#1, #2)
10. **`perfil_no_evento` Sprint 4 NÃO propaga no envelope bus cross-módulo** — consumer Wave A vai operar cego ao perfil. Quando `Calibracao.Aprovada` cruzar pra `metrologia/certificados`, certificado emitido não saberá perfil sem nova consulta. (L7#3)
11. **T-CAL-124..133 — 10 ViewSets REST restantes M4** (5d). Só CalibracaoViewSet 3 actions. **Produto invisível pro usuário** — qualquer dogfooding profundo trava. (L9#1)
12. **14/16 PRDs Wave A sem declaração de perfil ADR-0067** — só `metr/padroes` e parcial `rh/treinamentos`. (L5#1)
13. **GATE-SEG-BPT-1 EMERGENCIAL** — 4 dias parado; Balanças já recebe equipamento de cliente em dogfooding; risco R$ 800-2.400/mês expectância. (L4#1)
14. **ADR-0010 estratégia tela em proposta** — 1ª tela Wave A vira precedente acidental se decisão HTMX-vs-SPA não cravada. Decisão Roldão via AskUserQuestion. (L8#2 + L10#2)
15. **6 PRDs Wave A sem AC binário GIVEN-WHEN-THEN** — `op/base-conhecimento` (zero), `op/chamados`, `op/agenda`, `fin/caixa-tecnico`, `fin/contas-receber`, `rh/treinamentos` (parcial). (L5#2, #4)
16. **GATE-OS-GRANDEZA-EM-ATIVIDADE** — M4 fechou sem retrofit `AtividadeDaOS.grandeza`. ADR-0063 fail-open ATIVO. (L9#2)

### Família C — Bloqueia 1º dogfooding profundo (LGPD + ISO + cláusulas)

17. **Política de Privacidade + ToU não publicados** — campos `[a definir]` em razão social/CNPJ/DPO; LGPD art. 9º exige aviso ao titular antes da coleta. (L2#1)
18. **DPO não designado formalmente** — art. 41 §1º exige canal indicado. ANPD fiscaliza MPE. (L2#2)
19. **DPAs com 7 sub-operadores: 0/7 assinados** — incluindo AWS us-east-1 (transferência internacional sem cláusulas-padrão). Recomendação: migrar réplica KMS pra sa-east-1b+1c. (L2#3)
20. **ADR-0067 perfil não reflete no DPA** — cap R$ 500k uniforme viola CDC art. 39 V para perfil D R$ 300/mês. (L2#4)
21. **Direitos do titular Wave A — 12/17 módulos sem fluxo real** — ADR-0061 reservada. Mitigação interim: canal manual com SLA 15 dias em planilha. (L2#5)
22. **RBC 4.1 Imparcialidade ausente em TODO o repositório** — política + comitê + análise risco + declaração conflito. CGCRE para na 1ª hora. (L3#1)
23. **RBC 7.1 Análise crítica de pedidos ausente em `orcamentos`/`chamados`** — orçamento vira OS sem gate técnico-metrológico. (L3#2)
24. **ADR-0025 só pra calibração** — `certificados`, `procedimentos`, `padroes`, `licencas-acreditacoes` sem URS/IQ/OQ/PQ. (L3#3)
25. **NIT-DICLA-021 — competência RT por GRANDEZA, não por método** — RT "massa balança comum" assina cert RBC de massa E1 sem barreira. ADR-0022 v2 necessária. (L3#4)
26. **Predicates fail-open sem `GATE-WAVE-A-PREDICATES-FAIL-CLOSED`** — Balanças vira perfil A com 3 predicates retornando True → NC documental certa. (L3#5)

### Família D — Drift cross-doc (envenena decisão Wave A)

27. **AGENTS.md contradiz a si mesmo 4× sobre hooks/casos** (48 vs 51 / 379 vs 414). (L6#1)
28. **INDICE.md faltando ADR-0067 + cabeçalho sem SAN-PERFIL-TENANT** — auditor externo CGCRE/advogado lendo sitemap NÃO encontra o saneamento que fechou L6. (L6#2)
29. **CLAUDE.md:5 congelado em 2026-05-17** (10 dias velho). (L6#3)
30. **memory/project_session_state.md desatualizada** — fonte canônica de boot de outros agentes. (L6#5)
31. **`comercial/clientes/prd.md` em draft mas Marco 1 fechado 2026-05-21** — drift óbvio entre AGENTS §12 e PRD canônico. (L6 + L8#9)

### Família E — Bloqueia 1º cliente externo pago (Portão 1 ADR-0001)

32. **ADR-0028 + 5 críticos seguros** — pacote 7 modalidades + cap DPA + Cyber R$5M→R$10M + cláusula afirmativa IA + apólice modular por perfil. (L4#2-#4)
33. **6 ADRs conflitam direto com ADR-0067 — exigem emenda** — 0009/0013/0035/0043/0044/0045. (L10)
34. **F-C2 inteiro NÃO INICIADO** — structlog placeholder, sem INV-LOG, sem /health vs /ready, sem SIGTERM, sem correlation_id contextvar. (L8#5)
35. **F-C3 paginação ausente + retrofit cresce com tempo** — 621 testes hoje; daqui 2 meses pode ser 1500. Custo amplifica. (L8#6)
36. **Supply-chain: `dependabot.yml` inexistente, actions sem pin SHA, Dockerfile com tag mutável**. (L8#7)
37. **38 PRDs em draft ≥10 dias** (incluindo clientes). (L6 + L5#10)

---

## Plano de saneamento — 5 ondas

> **Premissa:** Roldão escolheu auditoria 10 lentes ANTES de codar Wave A pra evitar repetir o gap estrutural do SAN-PERFIL-TENANT em 14 módulos. Plano abaixo respeita essa decisão — todas as ondas A-D fecham ANTES do 1º commit de módulo novo Wave A. Onda E pode rodar em paralelo com Wave A inicial.

### Onda PRE-A.1 — Drift docs + housekeeping (1-2h, ZERO bloqueio)

Itens baratos que destravam tudo. **Antes de qualquer outra coisa.**

| # | Item | Tempo | Lente |
|---|------|-------|-------|
| 1.1 | DRIFT-A: corrigir 5 lugares com 48→51 e 379→414 | 10min | L6 |
| 1.2 | DRIFT-B: INDICE + AGENTS:5 + AGENTS:9 (GATE-TENANT-PERFIL-*) + faseamento-FW §11 + documentos-do-projeto | 20min | L6 |
| 1.3 | DRIFT-C: CLAUDE.md:5 cabeçalho | 5min | L6 |
| 1.4 | DRIFT-D: lista §3 hooks AGENTS — adicionar 4-7 hooks omitidos | 5min | L6 |
| 1.5 | DRIFT-E: `clientes/prd.md` draft→stable (M1 fechou há 6 dias) | 2min | L6, L8 |
| 1.6 | DRIFT-F: typo ADR-0067 ("continui"); "tenant-id-validator ainda a criar" AGENTS:160 | 5min | L6 |
| 1.7 | `supp/estoque/prd.md` — decidir Wave A vs B e atualizar §1 e §4 | 1h | L5#3 |

### Onda PRE-A.2 — Promoção ADRs + emendas (sessões Roldão + Claude — ~1 semana)

| # | Item | Tempo | Bloqueia | Lente |
|---|------|-------|----------|-------|
| 2.1 | Promover **ADR-0008 fiscal** (deadline 01/09/2026 — start hoje) | 1h | fiscal Wave A | L8, L10 |
| 2.2 | Promover **ADR-0015 lifecycle tenant** (só trocar status — já emendada Sprint 3) | 5min | onboarding | L8, L10 |
| 2.3 | Promover **ADR-0014 transições regulatórias + ADR-0016 operação consistente** | 2h | INV-INT-001..013 | L8, L10 |
| 2.4 | Promover **ADR-0009 A3 cliente-side** + emenda perfil A obrigatório | 1h | certificados | L8, L10 |
| 2.5 | Promover bloco **ADR-0046 + 0047 + 0048** A3/TSA/OCSP em batch | 2h | certificados | L10 |
| 2.6 | **ADR-0010 estratégia tela** — AskUserQuestion Roldão (HTMX núcleo + 5 SPAs) | 30min decisão | 1ª tela Wave A | L8, L10 |
| 2.7 | Emendar 6 ADRs conflitantes c/ ADR-0067: **0009, 0013, 0035, 0043, 0044, 0045** | 3h | 6 módulos Wave A | L10 |
| 2.8 | Promover ADRs 0003/0004 mobile (verificar superseded-by ADR-0027) | 2h | app-tecnico | L8, L10 |
| 2.9 | ADR-0019 marcar `superseded-by: 0028` (fundir) | 5min | housekeeping | L10 |
| 2.10 | ADR-0003 stub — escrever conteúdo ou marcar deprecated | 1h | app-tecnico | L10 |
| 2.11 | Resolver drift ADR-0059/0060/0061 (criar esqueletos `reservada` ou tirar §11) | 30min | drift §11 | L8 |
| 2.12 | Batch limpo: promover 0034/0036/0037/0038/0039/0049/0050/0051/0052/0053 | 4h | múltiplos Wave A | L10 |
| 2.13 | **ADR-0068 nova — Sucessão/substituição RT** (persona ausente em 14 PRDs) | 2h | agenda, app-tecnico, certificados | L1#7, L3#15 |
| 2.14 | **ADR-0069 nova — Bypass competência cl. 6.2 (objetiva, análogo ADR-0026)** | 2h | treinamentos | L1#5, L3#A1 |
| 2.15 | **ADR-0022 v2 — RTCompetencia por método específico** (não só grandeza) | 3h | certificados, calibracao | L3#4 |
| 2.16 | **ADR-0025 estender** aos 4 módulos metrologia Wave A (`certificados`, `procedimentos`, `padroes`, `licencas-acreditacoes`) | 2h | metrologia Wave A | L3#3 |

### Onda PRE-A.3 — Saneamento PRDs Wave A (4 batches paralelos — ~4 semanas)

Reescrita orientada por perfil ADR-0067 + AC binário BDD + frontmatter completo. **Bloqueia início Wave A em código.** Estimativa ~130h em 4 frentes paralelas.

| Batch | PRDs | Tempo |
|-------|------|-------|
| **B1** (semana 1 — caminho crítico fiscal) | `fin/fiscal` + `metr/certificados` + `fin/contas-receber` + `metr/licencas-acreditacoes` | 33h |
| **B2** (semana 2 — operação dogfooding) | `op/app-tecnico` + `op/chamados` + `op/agenda` + `fin/caixa-tecnico` + `op/base-conhecimento` | 48h |
| **B3** (semana 3 — metrologia + RH) | `metr/procedimentos` + `metr/padroes` (revisão final) + `rh/treinamentos` + `rh/seguranca-trabalho` | 24h |
| **B4** (semana 4 — comercial + plataforma) | `com/orcamentos` + `supp/acesso-seguranca` + `supp/estoque` (após decisão) | 25h |

**Em cada PRD aplicar 21 lacunas L1 + 17 achados L5** (perfil declarado, AC BDD, persona inline, ADRs dependentes, glossário, frontmatter completo, vocab Wave A).

### Onda PRE-A.4 — Bus M3/M4 retrofit causa-raiz + sub-onda A TRACKs (~3 semanas dev)

| # | Item | Tempo | Lente |
|---|------|-------|-------|
| 4.1 | **INT-01: Retrofit M3 OS** — 18 use cases publicam em `bus_outbox` na mesma transaction.atomic | 2d | L7 |
| 4.2 | **INT-02: Retrofit M4 calibração** — use cases publicam Integration Events | 1.5d | L7 |
| 4.3 | **INT-03: `perfil_no_evento` no envelope bus** — `_inserir_no_outbox` lê `app.perfil_tenant` | 0.5d | L7 |
| 4.4 | **INT-04: Hook `bus-envelope-validator` robusto** — envelope canônico inteiro | 0.5d | L7 |
| 4.5 | **INT-06: Consumer-dummy GATE-CLI-7/8** — 5 eventos M1 críticos | 0.5d | L7 |
| 4.6 | **INT-07: Schema versioning por evento + janela 90d** | 1d | L7 |
| 4.7 | T-CAL-124..133 — **10 ViewSets REST M4** restantes | 5d | L9 |
| 4.8 | GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` (fecha ADR-0063 fail-open) | 1.5d | L9 |
| 4.9 | GATE-IDEMP-HOOK-DETECT-ACTION — hook detecta `@action(methods=POST)` | 0.5d | L9 |
| 4.10 | Limpa-mesa: GATE-FB-4 + GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA + GATE-EQP-RT-AUTHZ + GATE-DEP-001/002 + GATE-EQP-DEP-WEASYPRINT | 2.5d | L9 |
| 4.11 | **F-C3 paginação + retrofit 621 testes + hook** (mais barato hoje que daqui 2 meses) | 3d | L8 |
| 4.12 | **F-C3 supply-chain** — `dependabot.yml` + pin SHA Docker + 3 actions | 1d | L8 |
| 4.13 | **Retrofit Sprint 4 incompleto** — `perfil_no_evento` em `contas-receber` + `fiscal` | 1d | L1#18 |

### Onda PRE-A.5 — F-C2 + drills internos (~10d)

**Sem contratações externas** (memória `project_sem_contratacoes_externas_ate_producao` — Roldão decidiu 2026-05-27 que zero gasto com OAB/RBC/SUSEP/B2 pago/KMS pago/pentest enquanto sistema estiver em desenvolvimento). Itens que dependem de humano externo viram **GATE-EXTERNO-PRODUCAO** (executar somente em pré-produção real). Minutas continuam escritas (preparação defensiva), revisão OAB diferida.

| # | Item | Tempo | Custo | Lente |
|---|------|-------|-------|-------|
| 5.1 | F-C2 entregável 1 — substituir placeholder `config/settings/base.py:441-462` por structlog real + processor canônico injetando `tenant_id`+`correlation_id`+`request_id` | 1d | — | L8 |
| 5.2 | F-C2 entregável 2 — INV-LOG-001..003 em REGRAS-INEGOCIÁVEIS + retrofit 29 call sites com `extra=` manual (13 arquivos) | 1d | — | L8 |
| 5.3 | F-C2 entregável 3 — endpoints separados `/health` (liveness) + `/ready` (DB) + `/health/deep` (DB+B2+KMS+outbox) | 0.5d | — | L8 |
| 5.4 | F-C2 entregável 4 — SIGTERM handler em procrastinate worker (drena fila, termina job em voo) | 0.5d | — | L8 |
| 5.5 | F-C2 entregável 5 — contextvar `correlation_id` propagado 4 pontos (middleware HTTP → DRF view → EventEnvelope.publicar() → consumer enter) | 1d | — | L8 |
| 5.6 | Drills internos estruturais (sem provisioning real): GATE-FC1-ROTACAO simulada + GATE-CYBER-BREAKGLASS-DRILL estrutural + DR drill anual estrutural + 90d QR HMAC simulado | 2d setup + ~30min/mês execução | — | L9 |
| 5.7 | **GATEs externos rastreados como `GATE-EXTERNO-PRODUCAO`** (não executar): B2 WORM real, AWS KMS MRK real, pacote OAB Tier 1/2/3, carta RT credenciado NIT-DICLA-021, SUSEP 7 modalidades, pentest externo. Documentar em `docs/conformidade/comum/gates-externos-pre-producao.md`. | 1d doc | — | L2/L3/L4/L9 |

**Minutas/preparação defensiva (CONTINUAM escritas pelo subagente `advogado-saas-regulado` em `minuta + aguarda-revisao-oab: true`):**
- ToU + PP do Aferê (campos `[a definir]` → preencher Balanças Solution agora; Aferê PJ depois)
- DPA Aferê↔tenant + addendum perfil A/B/C/D
- DPA encadeado subcontratação ISO cl. 6.6
- DPIA (assinatura touch, GPS, biometria)
- RIPD
- Consentimento biométrico texto
- Cláusula afirmativa IA + cap responsabilidade

**Roldão executa quando decidir ir pra produção real** — então sim aciona pacote OAB Tier 1/2/3 + corretora SUSEP + B2/KMS reais + pentest.

---

## Estimativa total

| Onda | Esforço | Calendário | Bloqueia |
|------|---------|-----------|----------|
| PRE-A.1 (drift) | 2h Claude | mesmo dia | nada — destrava todas |
| PRE-A.2 (ADRs) | ~25h Claude + 2-3 sessões Roldão | 1 semana | Wave A começar |
| PRE-A.3 (PRDs) | ~130h paralelo (4 frentes) | 4 semanas | 1º commit módulo Wave A |
| PRE-A.4 (bus + TRACKs + F-C3) | ~20d dev | 3 semanas | 1º commit módulo Wave A |
| PRE-A.5 (contratações + F-C2) | ~30d dev + calendário externo | 6-8 semanas paralelo | 1º cliente externo pago |

**Total efetivo pré-Wave A em código:** ~4-5 semanas calendário (Ondas 1+2+3+4 em paralelo onde possível).
**Total até 1º cliente externo pago:** +6-8 semanas (Onda 5 paralela).

---

## Decisões Roldão TOMADAS (2026-05-27 noite)

1. ✅ **ADR-0010 estratégia tela** — HTMX núcleo + 5 SPAs isoladas (Editor BPM, Portal Cliente, Marketplace, BI, Omnichannel).
2. ✅ **Sem contratações externas até produção real** — ADR-0028 cotação SUSEP / OAB Tier 1/2/3 / Carta RT / B2 KMS reais / Pentest = **DIFERIDOS** pra pré-produção. Memória `project_sem_contratacoes_externas_ate_producao`.
3. ✅ **Aferê PJ separada DEPOIS** — por enquanto tudo Balanças Solution. PJ separada quando aparecer 2º tenant externo (futuro).
4. ✅ **Onda 3 saneamento PRDs com 4 agentes paralelos** (máximo paralelismo — memória `feedback_max_parallelism`).

## Decisões Roldão ainda pendentes (menores)

5. **`supp/estoque` é Wave A ou Wave B?** — PRD declara B mas AGENTS lista A. (Resolver em Onda 1.7 / Onda 3 B4)
6. **Migrar réplica AWS KMS de us-east-1 pra sa-east-1b+1c?** — elimina transferência internacional. (Decisão deferida pra pré-produção)
7. **`metr/padroes` é Wave A?** — PRD existe e é avançado; faseamento-FW §5 não lista nominalmente. Aparenta ser pré-req calibração. (Onda 3 B3)
8. **DPO interino Roldão** — auto-nomeação informal continua até pré-produção (sem custo R$ 0).

---

## Recomendação de execução

**Não codar nenhum módulo Wave A novo enquanto Ondas 1-4 não fecharem.** Risco = repetir o gap estrutural SAN-PERFIL-TENANT em escala 14× (1 saneamento de 4 sprints virou exemplo; 14 retrabalhos é projeto de meses).

**Sequenciamento sugerido pra próxima sessão Claude:**

1. **Onda 1 inteira em 1 sessão** (2h Claude) — destrava drift e dá visão limpa pros agentes seguintes.
2. **Onda 2.1 + 2.2 + 2.3 + 2.6 (AskUserQuestion Roldão)** — destrava fiscal/lifecycle/operação consistente + decisão UI. Sessão única ~3h.
3. **Disparar Onda 5.1 (BPT emergencial — Roldão liga Marsh/Howden esta semana)** + **Onda 5.2 (pacote OAB Tier 1)** em paralelo.
4. **Onda 4.1 + 4.2 + 4.3 + 4.4 (bus M3/M4 causa-raiz)** — fecha gap estrutural antes de Wave A amplificar. ~4.5 dias.
5. **Onda 3 Batch 1 (caminho crítico fiscal)** — 33h paralelo destrava `fin/fiscal` que tem deadline duro.
6. Demais ondas em paralelo conforme capacidade.

## Histórico

| Data | Mudança |
|------|---------|
| 2026-05-27 noite | Auditoria disparada. 10 agentes em paralelo. Esqueleto criado. |
| 2026-05-27 madrugada | 10/10 lentes retornaram. Consolidado fechado. Roldão decidiu "resolver TUDO — críticos, altos, médios, baixos". Auditoria promovida `draft→stable` como insumo da execução em 5 ondas. |
| 2026-05-27 madrugada (Onda 1) | **Onda PRE-A.1 concluída.** Drift resolvido: AGENTS.md (cabeçalho + §3 lista hooks + §6 título + §9 hook tenant-id-validator + §12 contagens + §12 Hooks header), CLAUDE.md:5 status, INDICE.md cabeçalho + §ADRs, documentos-do-projeto.md cabeçalho, faseamento-foundation-waves §11 (entradas SAN-PERFIL + auditoria 10 lentes), memory/project_session_state.md (description + suite + próxima ação), memory/project_perfil_regulatorio_tenant.md, .agent/CURRENT.md, clientes/prd.md draft→stable, ADR-0067 typo "continui"→"continua". Suite hooks `_test-runner.sh` verificada: **413/413 verdes / 51 ativos** (L6 declarou 414 mas suite reporta 413 — correção propagada). Memória nova `project_sem_contratacoes_externas_ate_producao`. |
