---
owner: roldao
revisado-em: 2026-06-13
status: stable
finalidade: Catálogo único e vivo de todos os GATEs Wave A do projeto Aferê. Substitui as listas dispersas em 6 arquivos diferentes (F-A/auditoria-familia5.md, F-B/auditoria-familia5.md, M1-clientes/auditoria-familia5.md, M2-equipamentos/auditoria-familia5.md, OS-CAL-RESOLUCAO-rodada-1.md, OS-CAL-RESOLUCAO-rodada-2.md).
fonte: auditoria projeto-inteiro 10 lentes 2026-05-23 (lente 9 — Foundation gaps + auditoria-familia5 dos marcos fechados)
---

# GATEs Wave A — consolidado vivo

> Atualizar este arquivo quando GATE fechar (mover linha para tabela "FECHADOS") ou abrir GATE novo.
> Severidade segue INV-RITUAL-001: GATE bloqueante aberto = Wave A não pode arrancar produtivamente para o item correspondente.

---

## Resumo por categoria (estado em 2026-06-13 pós P8 precificacao)

| Categoria | Total | Abertos | Fechados | Em andamento |
|---|---|---|---|---|
| Seguros (SEG-*) | 13 | 12 | 0 | 1 (CAP-1 — DPA Onda 7) |
| LGPD / Jurídico (LGPD-*) | 13 | 11 | 0 | 2 (minutas + cap DPA) |
| Foundation F-A (1-7) | 7 | 7 | 0 | 0 |
| Foundation F-B (FB-1..4) | 4 | 4 | 0 | 0 |
| Marco 1 clientes (CLI-1..8) | 8 | 8 | 0 | 0 |
| Marco 2 equipamentos (EQP-*) | 18 | 17 | 1 | 0 (CVE-WeasyPrint mitigado) |
| ISO 17025 / CGCRE (RBC-*) | 8 | 8 | 0 | 0 |
| Modelo dados / convenções (DOM-*) | 5 | 0 | 5 | 0 (Onda 2 fechou) |
| Bus / integração (BUS-*) | 5 | 4 | 1 | 0 (envelope retrofit Onda 3) |
| Operação / Drill (OPS-*) | 6 | 6 | 0 | 0 |
| Precificacao (PRC-* + WIREIN) | 8 | 8 | 0 | 0 |
| **TOTAL** | **94** | **84** | **7** | **3** |

> Adicionados em 2026-06-12 (auditoria de cerimônia R17/R18): GATE-LGPD-RAT-CONSOLIDACAO + GATE-CGCRE-DOSSIE-PROSA.
> Adicionados em 2026-06-13 (P8 precificacao): GATE-PRC-CUSTEIO-REAL + GATE-PRC-HISTORICO-ORCAMENTOS + GATE-PRC-ALERTA-GESTOR + GATE-PRC-NOTIFICACAO + GATE-PRC-COMISSAO-REAL + GATE-PRC-TABELA-CONTRATO + GATE-PPS-WIREIN-OS (movido da seção PPS para cá, onde o contexto do consumidor `precificacao` está completo).

---

## GATEs ABERTOS

### Seguros (12) — exigem corretora SUSEP humana

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-SEG-BPT-1 | 🔴 EMERGENCIAL | Dogfooding Balanças Solution em curso (CC art. 627) | Roldão + corretora SUSEP | IMEDIATO |
| GATE-SEG-CAP-1 | 🟡 em andamento | 1º tenant externo pago | Roldão + advogado | Onda 7 (quase fechado) |
| GATE-SEG-CYBER-1 | 🔴 | 1º tenant externo pago | Roldão + corretora SUSEP | Pré-Wave A externa |
| GATE-SEG-EO-1 | 🔴 | Aceite tenant farma/alimento | Roldão + corretora SUSEP | Pré-1º tenant farma |
| GATE-SEG-DBI-1 | 🔴 | 1º tenant externo pago | Roldão + corretora SUSEP | Pré-Wave A externa |
| GATE-SEG-ACR-1 | 🔴 | 1º tenant RBC acreditado | Roldão + corretora SUSEP | Pré-1º tenant RBC |
| GATE-SEG-VIST-1 | 🟡 | Habilitar `tipo=vistoria` ADR-0023 | Roldão + corretora | Junto GATE-SEG-EO-1 |
| GATE-SEG-META-1 | 🟡 | Cláusula `consequential regulatory damages` ativa | Roldão + corretora | Junto GATE-SEG-EO-1 |
| GATE-SEG-A3-1 | 🟡 | Cláusula `third-party credential abuse` ativa | Roldão + corretora | Junto GATE-SEG-CYBER-1 |
| GATE-SEG-BPT-2 | 🟡 | Cláusula `named insured by date of loss` + DPA tenant | Roldão + corretora | Junto GATE-SEG-CAP-1 |
| GATE-SEG-VEIC-1 | 🟡 | OS campo com padrão em trânsito | Roldão + corretora | Pré-OS campo |
| GATE-SEG-DRILL-1 | 🔴 | Aderência ANPD 3 dias úteis | DPO + Roldão | Anual — antes 1º tenant externo |

### LGPD / Jurídico (11)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-LGPD-DPO-1 | 🔴 | 1º tenant externo pago | Roldão (designar) | Pré-Wave A externa |
| GATE-LGPD-TOU-1 | 🔴 | Publicação produto | Advogado OAB | Pré-1º tenant externo |
| GATE-LGPD-POP-1 | 🔴 | Publicação produto | Advogado OAB | Pré-1º tenant externo |
| GATE-LGPD-DPA-MASTER-1 | 🔴 | 1º tenant externo pago | Advogado OAB | Pré-1º tenant externo |
| GATE-LGPD-SUB-AWS | 🔴 | 1º tenant externo pago | Aferê com AWS | Pré-Wave A externa |
| GATE-LGPD-SUB-B2 | 🔴 | 1º tenant externo pago | Aferê com Backblaze | Pré-Wave A externa |
| GATE-LGPD-SUB-PLUGNOTAS | 🔴 | Emissão NFS-e produção | Aferê com PlugNotas | Pré-1º NFS-e externa |
| GATE-LGPD-SUB-LACUNA | 🔴 | Assinatura A3 produção | Aferê com Lacuna | Pré-1º certificado A3 externo |
| GATE-LGPD-SUB-OUTROS | 🟡 | Wave A completa | Aferê com Anthropic/Grafana/Axiom | Pré-Wave A externa |
| GATE-LGPD-DRILL | 🔴 | Aderência ANPD | DPO designado | Anual — pré-1º tenant externo |
| GATE-LGPD-ART18-MODULOS | 🔴 | Tenant externo em módulo cobre titular | Tech-lead + DPO | Por módulo (equipamentos/OS/cal/cert/billing) |
| **GATE-LGPD-RAT-CONSOLIDACAO** | 🔴 | **Deploy do dogfooding com dados reais** (1º titular real = clientes da Balanças Solution — gatilho correto, não o 1º tenant externo) | Tech-lead + advogado-saas-regulado + DPO | Antes do 1º dado real de pessoa física entrar em produção |
| **GATE-CGCRE-DOSSIE-PROSA** | 🟡 | Tenant perfil A real OU auditoria CGCRE marcada | Consultor RBC + tech-lead | Disparado por evento externo (não por módulo) |

> **GATE-LGPD-RAT-CONSOLIDACAO (novo — R17 auditoria cerimônia 2026-06-12):** 1 passe consolidado de RAT LGPD + DPIA + censo de retenção por entidade. Insumo: apontadores-PII de 1 linha mantidos nas specs de cada módulo ("PII: campos X,Y — base legal Z"). Linha de retenção por módulo continua SÓ quando o módulo codifica retenção (job/trigger). Specs novas mantêm o apontador-PII de 1 linha mas NÃO emitem RAT/DPIA completo por módulo até este GATE.
>
> **GATE-CGCRE-DOSSIE-PROSA (novo — R18 auditoria cerimônia 2026-06-12):** redação consolidada dos dossiês/URS cl. 7.11 (parte narrativa IQ/OQ/PQ). A EVIDÊNCIA executável (replay fixtures, `versao_motor`, marcadores OQ em migrations) **continua obrigatória por módulo durante a construção** — essa é irrecuperável depois. O que vai pra este GATE é só a prosa narrativa do dossiê consolidado.

### Foundation F-A (7)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-1 | 🔴 | 1º tenant externo pago | DevOps + DPO | Verificação periódica B2 WORM + ciclo chave PII + hash AcessoDadosCliente |
| GATE-2 | 🟡 | Wave A completa | Sysadmin | Provisionamento B2 WORM segundo cluster |
| GATE-3 | 🟡 | Wave A completa | Sysadmin | NTP sincronizado + monitorado |
| GATE-4 | 🔴 | 1º tenant externo pago | DevOps | Ciclo de chave PII anual (rotação KMS) |
| GATE-5 | 🟡 | Auditoria CGCRE | DevOps | Hash chain `AcessoDadosCliente` em produção |
| GATE-6 | ✅ | — | — | ADR-0020 aceita (REGRAS>orçamento + CODEOWNERS) |
| GATE-7 | 🟡 | Wave A | Tech-lead | Higiene `::uuid` em policies RLS |

### Foundation F-B (4)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-FB-1 | 🔴 | Primeiro perfil tenant-specific | Tech-lead | Regenerar policy `authz_perfil_acao_select` (INV-AUTHZ-004) |
| GATE-FB-2 | 🟡 | Auditoria CGCRE | DevOps | Retenção `authz_decisions` + `ip_hash` |
| GATE-FB-3 | 🟡 | Auditoria LGPD | Tech-lead | Redator escopo PII em logs |
| GATE-FB-4 | 🟡 | Texto INV-AUTHZ-002 via ADR | Tech-lead | ADR documentando texto canônico |

### Marco 1 clientes (8)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-CLI-1 | 🔴 | 1º tenant externo | DevOps | Retenção stable + B2 WORM |
| GATE-CLI-2 | 🟡 | Wave A completa | Tech-lead | EventoTimeline consumers ativos |
| GATE-CLI-3 | 🟡 | UX produto Wave A | Tech-lead | p95 visão-360 ≤ 200ms |
| GATE-CLI-4 | 🟡 | Auditoria interna | DevOps | Dashboard regularização (cliente bloqueado/reativado) |
| GATE-CLI-5 | 🔴 | Habilitar bloqueio automático inadimplência | Comercial | Régua D+30/60/89 ativa (depende `comunicacao-omnichannel`) |
| GATE-CLI-6 | 🔴 | Reativação automática `ContasReceber.Pago` | Tech-lead | Consumer + teste E2E |
| GATE-CLI-7 | 🔴 | Wave A | Tech-lead | Consumer `operacao/agenda` reage a `Cliente.Bloqueado` |
| GATE-CLI-8 | 🔴 | Wave A | Tech-lead | Consumer `metrologia/certificados` reage a `Cliente.Bloqueado` |

### Marco 2 equipamentos (17 abertos + 1 fechado)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-EQP-1 | 🔴 | Wave A | Tech-lead + Lacuna | A3 Lacuna integrado pra signing |
| GATE-EQP-KMS | 🔴 | 1º tenant externo | DevOps | AWS KMS MRK real (`GenerateMac`/`VerifyMac`) substitui HMAC PG |
| GATE-EQP-PENTEST | 🔴 | 1º tenant externo | Security | Pentest timing-oracle Mann-Whitney 1000 amostras |
| GATE-EQP-RT | 🔴 | Tenant RBC acreditado | Consultor RBC humano | Carta competência RT credenciado (NIT-DICLA-021) |
| GATE-EQP-RT-NOTIF | 🔴 | Conformidade NIT-DICLA-021 | Tech-lead | Consumer ANPD/CGCRE em desligamento RT |
| GATE-EQP-DEP-WEASYPRINT-UPGRADE | 🟡 | Pós-upgrade WeasyPrint | DevOps | Quando WeasyPrint 68+ corrigir CVE-2025-68616 nativo |
| GATE-EQP-PWA-ADR | 🟡 | US-EQP-003 fase 4 | Tech-lead | Aceite formal ADR-0018 (PWA QR scanner) |
| GATE-EQP-FOTO-EXIF | 🟡 | Wave A | Tech-lead | EXIF strip obrigatório no upload (paridade INV-EQP-ANOM-001) |
| GATE-EQP-FOTO-BLUR | 🟡 | Wave A | Tech-lead | Blur automático de rostos em fotos de evidência |
| GATE-EQP-INVAL-PROV | 🟡 | Wave A | Tech-lead | Trigger PG bloqueia FK `Certificado.equipamento` provisório (INV-EQP-PROV-001) |
| GATE-EQP-IMPORT | 🟡 | Wave A | Tech-lead | Import CSV com validação cross-tenant + dedup |
| GATE-EQP-PORTAL | 🟡 | Wave A | Tech-lead | Portal cliente para histórico próprio do equipamento |
| GATE-EQP-COMPAT-MIGRATION | 🟡 | Migration retrofit | Tech-lead | Migration de `data_*_vigencia` → `vigencia_*` (ADR-0030) |
| GATE-EQP-FK-ANON | 🟡 | Migration retrofit | Tech-lead | Migration `Certificado.cliente_*_referencia_hash` (ADR-0032) |
| GATE-EQP-SD-PADRAO | 🟡 | Wave A | Tech-lead | Soft-delete declarado por entidade (ADR-0031) |
| GATE-EQP-RECALL | 🟡 | Wave A | Tech-lead | Mecanismo recall por versão `EquipamentoVersao` |
| GATE-EQP-TIMING-EXP | 🟡 | Pós GATE-EQP-PENTEST | Security | Expor relatório pentest a tenants sob NDA |
| ~~GATE-EQP-CVE-WEASYPRINT~~ | ✅ FECHADO | — | — | Mitigado in-app via `url_fetcher` custom em `services_etiqueta.py` |

### ISO 17025 / CGCRE (RBC-*) (8)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-RBC-IMPARC-1 | 🔴 | Tenant RBC + Marco 4 | Tech-lead + RBC | cl. 4.1 imparcialidade declarada |
| GATE-RBC-ANAL-PEDIDOS-1 | 🔴 | Marco 3 OS + Marco 4 | Tech-lead | cl. 7.1 análise crítica pedidos em orçamentos |
| GATE-RBC-VAL-METODO-1 | 🔴 | Marco 4 calibração | Tech-lead | cl. 7.2 entidade MetodoCalibracao versionada |
| GATE-RBC-RAST-1 | 🔴 | Tenant RBC + Marco 4 | Tech-lead | cl. 6.5 cadeia rastreabilidade padrão→INMETRO/BIPM |
| GATE-RBC-RT-METODO-1 | 🟡 | Tenant RBC sofisticado | Consultor RBC + Tech | NIT-DICLA-021 competência por método (não só grandeza) |
| GATE-RBC-RT-SUBST-1 | 🟡 | Tenant RBC + Marco 3 OS | Tech-lead | Substituto RT / afastamento temporário |
| GATE-RBC-NC-RECONC-1 | 🔴 | Marco 4 calibração + qualidade | Tech-lead | Reconciliar `calibracao.NaoConformidade` vs `qualidade.NC` (ADR transversal) |
| GATE-RBC-CL-8-1 | 🔴 | Tenant RBC | Tech-lead + Consultor | cl. 8.5/8.8/8.9 audit interna + revisão direção |
| GATE-RBC-ESCOPO-1 (NOVO M3 P-OS-R3) | 🔴 | 1º tenant perfil A/RBC | Tech-lead + Consultor RBC | NIT-DICLA-030: predicate `tenant_dentro_escopo_acreditado` + consumer `Acreditacao.Vencida/Suspensa` ativos |
| GATE-RBC-CAPA-1 (NOVO M3 P-OS-R5) | 🟡 | Módulo qualidade Wave B | Tech-lead | `RegistroCAPA` consume `AtividadeNaoConforme`/`AtividadeNCResolvida` + FK reversa `NaoConformidadeAtividade.registro_capa_id` |

### Marco 3 OS (NOVOS — pós-P3 ritual 2026-05-23)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-OS-TENANT-SUSPENSO (P-OS-T6) | 🔴 | 1º tenant pago | Tech-lead + Roldão | ADR-0035 aceita + matriz operações M3 × estado tenant em `docs/dominios/operacao/modulos/os/operacao-suspenso-matriz.md` |
| GATE-OS-FOTO-NOSHOW-BLUR (P-OS-A5) | 🟡 | Wave A2 | Tech-lead | Blur automático de rostos antes do upload (modelo on-device) — até lá, aviso UX |
| GATE-OS-SUCESSAO-EVIDENCIA (P-OS-A7) | 🟡 | Reabertura cross-cliente em produção | Tech-lead + Advogado | Entidade `SucessaoSocietaria` + PDF ato societário + A3 admin |
| GATE-OS-CONSBIO-TEXTO-OAB (P-OS-A1) | 🔴 | 1º tenant externo pago | OAB humana | Texto canônico `consentimento-biometria-touch.md` validado OAB |
| GATE-OS-DPIA-OAB (já existia em spec) | 🔴 | 1º tenant externo pago | OAB humana | DPIA-OS revisada por OAB humana |
| GATE-OS-CAL-LINK-WATCHDOG (P-OS-R6) | 🟡 | Marco 3 P4 | Tech-lead | Janela parametrizável por-tenant: 72h alerta / 15 dias úteis NC (defaults perfil A) |
| GATE-OS-PERF-N+1 (P-OS-T4) | 🟡 | Wave A — antes 1º tenant pago | Tech-lead | `OSVisao360QueryService` + p95 budget + teste assertNumQueries ≤5 |

### Seguros (cláusulas adicionais pós Marco 3 P3 — ADR-0028 rev 2)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-SEG-INMETRO-PRAZO-1 (NOVO M3 P-OS-S6) | 🟡 | 1º tenant com equipamento INMETRO obrigatório | Roldão + corretora SUSEP | Cláusula `consequential regulatory damages` cobre prazo INMETRO de cliente final do tenant |
| GATE-SEG-CYBER-1 (atualizado M3 P-OS-S2) | 🔴 | 1º tenant externo pago | Roldão + corretora SUSEP | Cláusula afirmativa `sensitive personal data art. 11` SEM sublimite separado + `image rights` incidental (P-OS-S5) |
| GATE-SEG-EO-1 (atualizado M3 P-OS-S3/S4/S5) | 🔴 | Aceite tenant farma/alimento | Roldão + corretora SUSEP | Franquia R$ 5k wrongful billing (sem gatilho R$ 50k) + tax penalty exposure (Receita+SEFAZ) + software validation defect upstream M3 + vicarious admin decision via platform |

### Bus / integração (4 abertos + 1 fechado)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-BUS-CONSUMER-IDEMP | 🔴 | Marco 3 OS | Tech-lead | Migration tabela `consumer_idempotencia` + retrofit consumers |
| GATE-BUS-HANDLERS | 🔴 | Wave A | Tech-lead | Registry de consumers real (zerado hoje) |
| GATE-BUS-DEAD-LETTER | 🟡 | Wave A | Tech-lead | Tabela `dead_letter_events` + notificação SEV-2 |
| GATE-BUS-ANON-PROPAG | 🔴 | Wave A | Tech-lead | Evento `Cliente.Anonimizado` + handlers cross-módulo |
| ~~GATE-BUS-ENVELOPE-V10~~ | ✅ FECHADO | — | — | Onda 3 saneamento — envelope canônico em event_helpers.py |

### Operação / Drill (6)

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-OPS-DRILL-ANPD | 🔴 | Aderência ANPD | DPO | Anual |
| GATE-OPS-DRILL-CYBER | 🔴 | Aderência cyber | Security + DPO | Anual |
| GATE-OPS-DRILL-DR | 🔴 | DR funcional | DevOps | Trimestral |
| GATE-OPS-RUNBOOK | 🔴 | 1º tenant externo | DevOps | Runbook + DR + observabilidade |
| GATE-OPS-OBSERV | 🔴 | 1º tenant externo | DevOps | Grafana + Axiom + alertas SLO |
| GATE-OPS-CCREATE-FAR | 🟡 | Marco 4 cal | DevOps | DR provedor B (Magalu/Oracle/AWS) |

### Frente `precificacao` (#3 cadeia de preço)

> Adicionados em 2026-06-13 (P8 precificacao). Nenhum bloqueia o fechamento do núcleo da frente; cada um destrava um módulo futuro específico.

| GATE | Severidade | Bloqueia | Owner | Prazo |
|---|---|---|---|---|
| GATE-PRC-CUSTEIO-REAL | 🟡 | Publicar modo `COST_PLUS` + preço mínimo real + alerta de staleness do `custo_referencia_em` | Tech-lead | Quando `custeio-real` (N7) implementar `CustoProvider` real |
| GATE-PRC-HISTORICO-ORCAMENTOS | 🟡 | Materialização de `Precificacao.PrecoPraticado` / `HistoricoPrecoPraticado` — **pré-condição: LIA art. 7º IX documentada** | Tech-lead + Advogado (OAB) | Quando frente `orcamentos` (#5) existir |
| GATE-PRC-ALERTA-GESTOR | 🟡 | Alerta ativo + dashboard de margem (US-PRC-007 parte 2) | Tech-lead | Wave A / frente de telas |
| GATE-PRC-NOTIFICACAO | 🟡 | Push/e-mail de pedido de aprovação (ADR-0060); resolve contexto na ENTREGA, margem só com `ver_margem` (ADV-PRC-02) | Tech-lead | Quando `comunicacao-omnichannel` (ADR-0060) estiver disponível |
| GATE-PRC-COMISSAO-REAL | 🟡 | Comissão real (módulo `comissoes` próprio); hoje só simulação por % parâmetro | Tech-lead | Wave B / módulo `comissoes` |
| GATE-PRC-TABELA-CONTRATO | 🟡 | Precedência contrato/segmento/região (AC-005-4 completo); Wave A só cliente-específico > padrão | Tech-lead | Wave B |
| GATE-PPS-WIREIN-OS | 🔴 **bloqueante pré-1º tenant externo** | Preço da OS avulsa hoje é client-supplied (`ordens_servico/views.py:507`); conserto via porta `preco_para_os` fail-closed **consome a frente `precificacao`** (resolução de tabela por cliente via `VinculoTabelaPrecoCliente` + `_resolver_preco_com_fallback`). Porta pronta e testada — o wire-in é da frente OS | Tech-lead | Antes do 1º tenant externo pago |
| GATE-PRC-CALCULAR-BATCH-FULL | 🟡 | Batch completo de `preco_para_os` para a cesta — hoje ~3 q/item intrínsecas (item_catalogo + item_catalogo_versao + linha_tabela_preco). Otimização requer redesign do `preco_para_os` para resolver múltiplos itens em queries batch. Aceitável no dogfooding com cesta pequena. `obter_padrao` já é 1x/request (PERF-MÉDIO-3 P9 consertado). | Tech-lead | Wave B / antes de cesta com N>50 itens |
| GATE-PRC-ANONIMIZACAO-CONSUMER | 🟡 | `apps.py ready()` precisa `registrar_consumer("Cliente.Anonimizado", ...)` que revoga o `VinculoTabelaPrecoCliente` vigente do cliente anonimizado (repo `revogar` pronto; estrutura ADR-0032 correta; só falta o wiring do consumer no bus). Achado BAIXO LGPD P9. Sem ele, o `cliente_id` pseudônimo permanece no vínculo pós-anonimização. | Tech-lead | Junto do wiring de eventos cross-módulo (integração OS) |

---

## GATEs FECHADOS (Onda 1-3 saneamento + histórico)

| GATE | Fechamento | Como fechou |
|---|---|---|
| GATE-DOM-VIGENCIA | 2026-05-23 (Onda 2) | ADR-0030 aceita + VO `JanelaVigencia` + INV-VIG-001..004 + hook `vigencia-canonica-check.sh` |
| GATE-DOM-SOFT-DELETE | 2026-05-23 (Onda 2) | ADR-0031 aceita + tabela entidade→padrão + INV-SOFT-001..003 + hook `soft-delete-padrao-check.sh` |
| GATE-DOM-FK-ANON | 2026-05-23 (Onda 2) | ADR-0032 aceita + VO `ReferenciaPIIAnonimizavel` + INV-ANON-001..004 + hook `fk-pii-anonimizavel-check.sh` |
| GATE-DOM-VOS-METROLOG | 2026-05-23 (Onda 2) | VOs `Grandeza`, `FaixaMedicao`, `IncertezaExpandida`, `NumeroCertificado` em `src/domain/metrologia/value_objects.py` |
| GATE-DOM-VOS-BASE | 2026-05-23 (Onda 2) | VOs `Telefone` (E.164+DDD-BR), `UF`, `PaisISO3166`, `Dinheiro` em `src/domain/shared/value_objects.py` |
| GATE-BUS-ENVELOPE-V10 | 2026-05-23 (Onda 3) | Retrofit `event_helpers.py` injeta `event_id`, `_schema_version`, `occurred_at`, `correlation_id`, `actor` automaticamente |
| GATE-EQP-CVE-WEASYPRINT | 2026-05-23 (Marco 2 P5) | Mitigação in-app `url_fetcher` custom em `services_etiqueta.py` (CVE-2025-68616 SSRF) |

---

## Política de manutenção deste catálogo

1. **Abrir GATE novo:** acrescentar linha na categoria correta; severidade conforme INV-RITUAL-001.
2. **Fechar GATE:** mover linha para "FECHADOS" com data + descrição de como fechou.
3. **Severidade:**
   - 🔴 = bloqueia 1º tenant externo OU bloqueia módulo/marco específico
   - 🟡 = bloqueia uma fase futura específica, mas Wave A pode arrancar parcial
   - ✅ = fechado
4. **Owner:** sempre nomear quem fecha (tech-lead, DevOps, advogado OAB, corretora SUSEP, consultor RBC, DPO, Roldão).
5. **Prazo:** absoluto quando possível; relativo quando dependente de evento (ex: "pré-1º tenant externo").

---

## Pendências de origem (referências dispersas a consolidar — backlog interno)

- F-A/auditoria-familia5.md — GATEs 1..7
- F-B/auditoria-familia5.md — GATEs FB-1..4
- M1-clientes/auditoria-familia5.md — GATEs CLI-1..8
- M2-equipamentos/auditoria-familia5.md — GATEs EQP-*
- OS-CAL-RESOLUCAO-rodada-1.md — 51 GATEs Wave A
- OS-CAL-RESOLUCAO-rodada-2.md — 28 GATEs Wave A
- AGENTS.md §12 — referência consolidada

Quando este catálogo `gates-wave-a-consolidado.md` virar fonte única, os arquivos acima devem citá-lo e não duplicar.
