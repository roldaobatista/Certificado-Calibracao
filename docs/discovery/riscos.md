# Discovery — Riscos

> **Artefato Rodada 0** (agente + Roldão). Inventário do que pode dar errado. Categorizado por tipo + probabilidade × impacto.
> **Atualizado:** 2026-05-16 — padronização de IDs pós-auditoria (Auditor 4). Todos os riscos agora em formato R-NNN sequencial único; coluna "Origem" rastreia de onde veio cada um. Total: 38 riscos consolidados (29 originais + 9 importados de `concorrentes.md` §7).
>
> **Versão pós-auditoria 12 agentes (17/05/2026 noite).** 8 riscos novos (R-058..R-065) + 2 promoções (R-034 score 4→12, R-046 score 10→15). **Total: 65 riscos.**
>
> **Versão pós-validação externa documental (17/05/2026 noite tarde).** 1 risco rebaixado: R-001 de score 20 → 12 (P 4→3) com evidência de 4 buckets independentes confirmando 13 das 20 dores externamente. Ver `validacao-externa-documental.md`.

---

## Convenção de IDs (Auditor 4 — aplicada 16/05/2026)

- **Formato:** `R-NNN` sequencial único (sem reuso, sem buracos).
- **Sem prefixos por categoria** (RC-*, RT-*, etc.) — categoria fica em coluna.
- **Sem reuso de número** — se um risco for desativado, ID fica reservado eternamente (entrada vira "DEPRECATED" + motivo).
- **Origem** rastreia onde o risco foi proposto pela primeira vez.

---

## Categorias de risco

- **Regulatório:** ANPD/LGPD, INMETRO/CGCRE, Receita Federal, Bacen, ANS, etc.
- **Técnico:** stack inviável, integração impossível, performance, segurança
- **Mercado:** TAM pequeno, concorrência forte, demanda baixa
- **Operacional / Time:** 1 pessoa + IA = bottleneck, agente vira inviável, burnout do Roldão
- **Financeiro:** investimento insuficiente, custos crescendo desproporcionalmente
- **Cliente:** "founder is customer" → produto não generaliza, primeiro cliente externo recusa
- **Jurídico:** responsabilidade por dado vazado, IA emitindo certificado regulado
- **Concorrencial:** movimentos de mercado que afetam diferenciação

---

## Matriz Probabilidade × Impacto (65 riscos)

| ID | Risco (resumo) | Categoria | P | I | Score | Mitigação | Owner | Origem |
|---|---|---|---|---|---|---|---|---|
| **R-001** ⭐ REBAIXADO | Customização disfarçada (founder is customer) — **score 20 → 12 em 17/05/2026** após validação documental: 4 buckets independentes (reviews, social, marketing concorrentes, regulatório/acadêmico) confirmaram 13 das 20 dores externamente; 0 refutadas. P reduzida de 4 → 3. **Não cai pra ≤9** porque dores #15 (comissões) e #16 (UMC específica) continuam suspeitas de halo founder + clientes Cali/Metroex são silenciosos publicamente (Onda 1 ou cliente piloto sob NDA ainda insubstituíveis). | Cliente | 3 | 4 | **12** | Validação documental concluída (ver `validacao-externa-documental.md`); continuar com mystery shopping + cliente piloto sob NDA quando aparecer; **NÃO cair pra ≤9** sem validar bandeiras amarelas (#15 comissões + UMC específica em #16) | Roldão | original (rebaixado pós-validação documental 17/05/2026) |
| **R-002** | Família 5 (3 auditores) virar vaporware | Operacional | 4 | 5 | **20** | Materializar prompts + triggers + veto na Rodada 4 | Agente | original |
| **R-003** | Multi-tenant vazamento entre tenants | Técnico/Regulatório | 3 | 5 | **15** | INV-TENANT-001 + RLS + hook + drill | Auditor Segurança | original |
| **R-004** | TAM ridículo (poucos prospects ICP) | Mercado | 3 | 5 | **15** | Validação ativa antes de comprometer | Roldão | original |
| **R-005** | ERP de N módulos com 1 pessoa = anos sem MVP | Operacional | 5 | 4 | **20** | Faseamento por módulo + MVP-1 enxuto | Roldão | original |
| **R-006** | NFS-e em município com padrão próprio (SP, Goiânia) | Regulatório/Técnico | 4 | 4 | **16** | Matriz município × padrão + BaaS fiscal | Auditor Conformidade | original |
| **R-007** | Conflito tríplice retenção (Receita × ISO × LGPD) | Regulatório | 4 | 5 | **20** | `retencao-matriz.md` + base legal explícita | Auditor Conformidade | original |
| **R-008** | Prompt injection via MCP GitHub (input dev/repo) | Técnico/Segurança | 3 | 4 | **12** | `mcp-policy.md` + `agente-input-nao-confiavel.md` | Auditor Segurança | original |
| **R-009** | Hostinger SPOF (provedor inteiro fora) | Operacional | 2 | 5 | **10** | `dr-plan.md` 3 cenários + IaC pra provedor B | Auditor Operação | original |
| **R-010** | Token cost explosion (>R$ 50/dia) | Financeiro | 3 | 3 | **9** | Hard cap por tenant + alerta no painel + circuit breaker (ADR-0000) | Roldão | original |
| **R-011** | Roldão burnout (dono não-técnico sozinho) | Operacional/Humano | 3 | 5 | **15** | Limites de autonomia + status semanal forçando foco | Roldão | original |
| **R-012** | Stack escolhida se mostra inviável após MVP-1 | Técnico | 2 | 4 | **8** | Spikes técnicos em discovery + ADR-0001 conservadora | Auditor Arquitetura | original |
| **R-013** | Concorrente generalista lança features ISO 17025 | Mercado | 2 | 4 | **8** | Foco em diferencial + nicho fiel. **Consolidado com R-033** | Roldão | original |
| **R-014** | LGPD: incidente de vazamento → multa ANPD | Regulatório/Financeiro | 3 | 5 | **15** | `seguranca-dados.md` + 3-dias-úteis playbook + DPO | Auditor Conformidade | original (re-scored Auditor 4: era 10) |
| **R-015** | Signatário técnico não-disponível (RBC NIT-DICLA-021) | Regulatório | 3 | 5 | **15** | Identificar signatário ANTES de emitir 1º certificado | Roldão | original |
| **R-016** | NFS-e cutover Padrão Nacional 01/09/2026 (ME/EPP) — Res. CGSN 189/2026 | Regulatório/Técnico | 4 | 5 | **20** | BaaS fiscal único (Focus/PlugNotas/TecnoSpeed); ADR fiscal pós-stack | Auditor Conformidade | normas-e-regulacao |
| **R-017** | Porto Alegre desliga DANFSe local em 01/07/2026 | Regulatório/Técnico | 3 | 4 | **12** | Mapear municípios dos primeiros 5 clientes; integração ADN pronta antes de jul/26 | Auditor Conformidade | normas-e-regulacao |
| **R-018** | NIT-DICLA-030 rev. 15 item 8.2.6 — certificado sem cadeia + incerteza rejeitado | Regulatório | 5 | 5 | **25** | Hook bloqueia emissão sem cadeia completa (INV-002); validar em mock antes do 1º cliente | Auditor Conformidade | normas-e-regulacao |
| **R-019** | Concorrente nacional (Cali/Metroex) lança fiscal/NFS-e antes do nosso MVP | Mercado | 3 | 4 | **12** | Ir a mercado rápido (módulo metrologia + fiscal juntos); integração bancária mais profunda | Roldão | concorrentes (era RC-01) |
| **R-020** | FP2 Tecnologia expande NFS-e multi-município pra cobertura nacional | Mercado | 2 | 4 | **8** | Monitorar M&A/expansão; vantagem por UX SaaS + capilaridade | Roldão | concorrentes (era RC-02) |
| **R-021** | DEPRECATED — consolidado com R-033 (ERP horizontal lança vertical calibração). | — | — | — | — | Ver R-033 | — | original |
| **R-022** | Mito "72h GDPR" virar invariante errada — ANPD é **3 dias úteis** | Regulatório/Operacional | 3 | 4 | **12** | Doc `lgpd-incidente-3-dias-uteis.md`; revisar runbooks; treinar agentes | Auditor Conformidade | normas-e-regulacao |
| **R-023** | Stack não suporta validação de software metrológico (cláusula 7.11) | Técnico/Regulatório | 3 | 5 | **15** | ADR-0001 com critério "WORM + audit trail + replay determinístico"; spike antes de cravar | Auditor Arquitetura | concorrentes/normas |
| **R-024** | Anvisa RDC 658/2022 ou RDC 786/2023 atinge cliente farma | Regulatório/Mercado | 2 | 4 | **8** | Documentar quais clientes farma exigem; "perfil regulado farma" como add-on, não MVP-1 | Auditor Conformidade | normas-e-regulacao |
| **R-025** | PCI-DSS 4.0.1 ativada se aceitarmos pagamento online direto | Regulatório/Operacional | 3 | 4 | **12** | Não processar cartão direto; PSP/gateway com tokenização → SAQ A | Auditor Segurança | normas-e-regulacao |
| **R-026** | Confusão entre 3 empresas chamadas "AutoLab" | Operacional/Marketing | 2 | 2 | **4** | Padronizar referência interna (Automa/Arkade/MRI) em `concorrentes.md` §3.16 | Agente | concorrentes |
| **R-027** | **Prompt injection via cliente final do tenant** | Técnico/Segurança/Multi-tenant | 5 | 5 | **25** | ADR-0000 + `agente-input-nao-confiavel.md`: input externo = "regulado-untrusted"; agentes não executam ações sensíveis sem aprovação humana; sanitização; red team trimestral | Auditor Segurança | auditoria batch 1 |
| **R-028** | Soberania de dados — Anthropic processa em EUA | Regulatório/Mercado | 4 | 4 | **16** | ADR-0000: DPA + opt-out por tenant; roadmap modelo BR (Maritaca/Sabiá) | Auditor Conformidade | auditoria batch 1 |
| **R-029** | Bus factor Roldão (saúde/incapacidade súbita) | Operacional/Humano | 3 | 5 | **15** | Runbook continuidade; procurador técnico em cartório; cofre digital com sucessor; sucessor treinado em `painel-do-dono.md` | Roldão | auditoria batch 1 |
| **R-030** | Cali lança fiscal/NFS-e via parceria (variante específica de R-019) | Mercado | 3 | 4 | **12** | Ver R-019. **Considerar fundir com R-019 numa próxima revisão** | Roldão | concorrentes (era RC-01) |
| **R-031** | FP2 expande nacional (variante de R-020) | Mercado | 2 | 4 | **8** | Ver R-020 | Roldão | concorrentes (era RC-02) |
| **R-032** | Qualer/MasterControl lança versão pt-BR + fiscal | Mercado | 1 | 3 | **3** | Foco em PME BR; gigantes entram pelo enterprise primeiro | Roldão | concorrentes (era RC-03) |
| **R-033** | ERP horizontal (Omie/Bling/Conta Azul/Tiny) lança vertical calibração ISO 17025 | Mercado | 2 | 5 | **10** | Profundidade técnica ISO 17025 (incerteza GUM, rastreabilidade, ILAC G8) que generalistas não dominam; foco em RBC | Roldão | concorrentes (era RC-04) + original R-021 |
| **R-034** ⭐ PROMOVIDO | **Homologação CERTI/INMETRO não obtida → barreira de entrada legal vs Cali** — processo de homologação leva 18-36 meses pra obter; sem isso, perdemos diferencial em concorrência com cliente regulado/grande. Promovido de score 4 → 12 pós-auditoria 12 agentes (17/05/2026). | Mercado/Regulatório | 4 | 3 | **12** | Iniciar processo de homologação ainda no ano 1 (paralelo ao MVP-1); buscar homologação CERTI cedo; caso de uso comparativo técnico; ver F-19 em assumption-map | Roldão | concorrentes (era RC-05) + promoção Aud-12 agentes batch 3 |
| **R-035** ⭐ ELEVADO | Visma (dona da Conta Azul desde 08/2025) compra Cali/Metroex — **score elevado pra 20 em 17/05/2026** (Auditor 9): Visma tem 140+ aquisições, ARR enterprise, Conta Azul+Cali = BIG-01+BIG-04 em 18 meses | Mercado | 4 | 5 | **20** | Monitorar M&A Visma na BR (alerta mensal); ir a mercado rápido (chegar a 50+ clientes antes da próxima aquisição); lockar com integração bancária mais profunda + Frota/UMC + CRM 360° (que Visma+Cali não fariam em 12 meses) | Roldão | concorrentes (era RC-06) + Auditor 9 batch 2 |
| **R-036** | TOTVS lança vertical de calibração via SIGAMNT/SIGAQMT melhorado | Mercado | 2 | 4 | **8** | Profundidade técnica RBC + UX moderna SaaS que TOTVS Protheus não consegue replicar | Roldão | concorrentes (era RC-07) |
| **R-037** | CGCRE muda paradigma pra acreditação baseada em riscos | Mercado/Regulatório | 3 | 3 | **9** | Modelar audit trail extensível ao novo modelo desde dia 0; acompanhar discussões CGCRE | Auditor Conformidade | concorrentes (era RC-08) |
| **R-038** | INMETRO/CGCRE oferece plataforma estatal grátis pra labs acreditados | Mercado | 1 | 5 | **5** | Sem ação ativa; gatilho seria comunicado oficial | Roldão | concorrentes (era RC-09) |
| **R-039** ⭐ | **Tenant declara perfil A (ISO 17025 acreditado) sem ter acreditação Cgcre real e emite certificados com selo RBC falso.** Fraude regulatória. Roldão (como vendor do SaaS) pode responder solidariamente | Jurídico/Regulatório | 3 | 5 | **15** | INV-015 (bloqueio por perfil); upgrade pra perfil A exige prova documental (certificado Cgcre + escopo de acreditação); revisão periódica automática consultando portal Cgcre (web scraping ou API se houver); cláusula contratual de responsabilização do tenant | Auditor Conformidade | decisão Roldão perfis 16/05/2026 |
| **R-040** | **Cliente final do tenant esquece de fazer verificação periódica INMETRO obrigatória** (balança comercial — anual via IPEM). Marca/selo INMETRO em si não tem prazo, mas a obrigação legal de verificação periódica continua. Cliente leva multa do IPEM e culpa o software | Regulatório/Mercado | 3 | 4 | **12** | Sistema diferencia explicitamente "calibração" (rastreabilidade) de "verificação metrológica legal" (IPEM); calendário de obrigação de verificação por instrumento; alerta 90/60/30 dias antes; certificado de calibração comercial leva nota "ESTA CALIBRAÇÃO NÃO SUBSTITUI A VERIFICAÇÃO INMETRO OBRIGATÓRIA — Portaria 157/2022" | Auditor Conformidade | decisão Roldão tipos de balança 16/05/2026 (corrigido: selo não tem vencimento, a obrigação periódica é que precisa cumprir) |
| **R-041** ⭐ | **Tenant configura no setup tipos de instrumento que não atende** (ex: marca "rodoviária" sem ter cargas-padrão grandes) e tenta criar OS desses tipos. Sistema permite mas operação falha no campo (técnico não tem padrão pra calibrar). | Operacional/UX | 3 | 3 | **9** | Setup pede confirmação de capacidade técnica por tipo marcado (ter padrão rastreado da grandeza/faixa); alerta no momento de criar 1ª OS daquele tipo; permitir desmarcar tipo a qualquer momento; trilha de auditoria das mudanças | Auditor Produto | decisão Roldão tipos configuráveis 16/05/2026 |
| **R-042** ⭐ CRÍTICO | **Transferência de risco vendor↔tenant não tratada contratualmente.** Aferê embute cálculo de incerteza, assinatura digital, NFS-e — falha em qualquer um pode tirar acreditação do tenant. Sem contrato com limitação de responsabilidade + seguro RC profissional + dossiê de validação 17025 + DPA-modelo, **Roldão (vendor) responde solidariamente em cada bug**. | Jurídico/Operacional | 4 | 5 | **20** | Pré-requisito MVP-1: contrato vendor↔tenant com limitação de responsabilidade; seguro RC profissional + cibernético; dossiê de validação 17025 do próprio software; DPA-modelo; cláusula penal pra fraude do tenant | Roldão + advogado + corretora | Auditor 7 batch 2 (17/05/2026) |
| **R-043** | Caixa do técnico não prestada (técnico sumiu com adiantamento R$ 500-5.000) | Financeiro/Operacional | 3 | 3 | **9** | Limite de adiantamento + workflow de prestação de contas em N dias + alerta gerente | Cláudia financeiro | decisão Roldão Frota/UMC 17/05/2026 |
| **R-044** | Manutenção de frota atrasada (carro quebra na viagem, cliente perde dia, OS atrasa) | Operacional | 4 | 3 | **12** | Alerta de manutenção próxima por KM/data + bloqueio de uso se documento vencido | Gerente frota | decisão Roldão Frota/UMC 17/05/2026 |
| **R-045** | Multa não paga vira protesto + CNH suspensa do condutor → técnico não pode dirigir | Operacional/Jurídico | 3 | 3 | **9** | Alerta de vencimento de multa + integração com SENATRAN (a confirmar) | Gerente frota | decisão Roldão Frota/UMC 17/05/2026 |
| **R-046** ⭐ ELEVADO | **UMC com peso-padrão roubado ou batido** = perda de R$ 100-300 mil em massas + parada operacional por semanas + contratos perdidos. Score elevado de 10 → 15 pós-auditoria 12 agentes (Brasil teve 22 mil roubos de carga em 2024 — NTC&Logística; probabilidade real 3, não 2). | Operacional/Financeiro | 3 | 5 | **15** | Seguro de carga + rastreamento veicular + protocolo de segurança em viagem + plano de UMC reserva | Roldão | decisão Roldão Frota/UMC 17/05/2026 + elevação Aud-12 agentes batch 3 |
| **R-047** | Motorista UMC perde validade CNH/MOPP/toxicológico → UMC parada → contratos perdidos | Operacional/Regulatório | 3 | 4 | **12** | Alerta de vencimento + plano de motorista substituto + acordo com motorista freelance pra emergência | RH/Cláudia | decisão Roldão Frota/UMC 17/05/2026 |
| **R-048** ⭐ | **Acessibilidade WCAG 2.1 AA ausente** — portal cliente / app mobile / PDF de certificado violam Lei 13.146/2015 art. 63. Multa MP + responsabilidade solidária Aferê/tenant + reprovação em licitação pública (Lei 14.133/2021) | Regulatório/Jurídico | 3 | 4 | **12** | INV-016 absoluta (WCAG 2.1 AA + PDF/UA); auditoria axe-core em CI; revisão manual em cada release; selo de conformidade no site | Auditor Acessibilidade | Auditor 2 batch 2 (17/05/2026) |
| **R-049** | Automação dispara mensagem indevida em massa pro cliente errado → reclamação Reclame Aqui + LGPD oposição art. 18 | Operacional/Regulatório | 3 | 4 | **12** | Sandbox de teste antes de ativar regra; aprovação humana antes de mass-send; opt-out granular por tipo de mensagem; rate limiting | Auditor Segurança | decisão Roldão CRM/Automações 17/05/2026 |
| **R-050** | Cliente reclama de spam (LGPD art. 18 oposição) — sistema mandou mensagem automática sem opt-in | Regulatório | 3 | 4 | **12** | Opt-in granular obrigatório por tipo de mensagem (cobrança vs comercial vs notificação vs marketing); canal de unsubscribe em cada mensagem; log de opt-out | Auditor Conformidade | decisão Roldão CRM/Automações 17/05/2026 |
| **R-051** | **Selo INMETRO perdido** → fiscalização IPEM exige justificativa formal + pode multar lab | Regulatório | 3 | 4 | **12** | Rastreabilidade individual por número + foto obrigatória + workflow de perda com aprovação gestor + comunicação proativa ao IPEM | Sandra/Marcos | decisão Roldão Estoque 17/05/2026 |
| **R-052** | Lacre/selo aplicado em equipamento errado → fraude metrológica | Regulatório/Jurídico | 2 | 5 | **10** | Confirmação dupla (técnico + cliente assina foto) + foto obrigatória com QR code do equipamento | Auditor Conformidade | decisão Roldão Estoque 17/05/2026 |
| **R-053** | Técnico recusa peça que recebeu (alega "não veio") → sumiço de peça cara | Operacional/Financeiro | 3 | 3 | **9** | Transferência 2 etapas obrigatória + foto da peça na origem + auditoria de divergências por técnico | Almoxarife | decisão Roldão Estoque 17/05/2026 |
| **R-054** | Inventário com divergência sistemática em técnico X → sinal de fraude interna | Operacional/Financeiro | 3 | 4 | **12** | Relatório de divergência por técnico ao gestor; bloqueio de novas transferências se padrão suspeito | Gerente | decisão Roldão Estoque 17/05/2026 |
| **R-055** | Erro de configuração de regra de comissão (% errado, regra duplicada) → cálculo errado em escala → reclamação trabalhista | Operacional/Financeiro | 3 | 4 | **12** | Simulador "se rodasse hoje" antes de ativar; auditoria de toda mudança de regra; revisão por gerente antes de fechamento | Cláudia/Roldão | decisão Roldão Comissões 17/05/2026 |
| **R-056** | Vendedor descobre brecha (desconto pra elevar margem aparente + ganhar mais comissão sobre líquido) → fraude interna | Operacional/Financeiro | 3 | 3 | **9** | Bloqueio de desconto acima de N% sem aprovação; alerta de padrão suspeito; auditoria por vendedor | Auditor Interno | decisão Roldão Comissões 17/05/2026 |
| **R-057** | Comissão paga sobre fatura que cliente depois não pagou (inadimplência) | Financeiro | 3 | 3 | **9** | Regra "comissão só sobre recebido" + estorno automático em caso de cancelamento + provisão financeira | Cláudia | decisão Roldão Comissões 17/05/2026 |
| **R-058** ⭐ NOVO | **Jornada do motorista UMC (Lei 13.103/2015) não modelada no sistema.** Logs do Aferê viram prova contra o tenant em ação trabalhista (tempo-espera = sobreaviso 1/3; jornada > 11h sem pausa = adicional). Roldão arrolado como réu solidário (vendor que forneceu a ferramenta de controle). | Jurídico/Regulatório/Operacional | 4 | 4 | **16** | Criar INV-020 (módulo Frota+UMC contém ponto eletrônico + cálculo tempo-espera = sobreaviso 1/3 + alerta de violação de jornada antes do fim do turno) | Auditor Conformidade + jurídico | Aud-17 batch 3 (17/05/2026 noite) |
| **R-059** ⭐ NOVO | **Caixa do técnico vira "salário-utilidade" (Receita Federal + INSS).** "Adiantamento genérico do mês" sem prestação de contas vinculada a viagem é gatilho de autuação (Súmula 367 TST). Vira passivo trabalhista + tributário no tenant. | Jurídico/Regulatório/Financeiro | 4 | 4 | **16** | Prazo máximo de prestação de contas: 5 dias úteis após retorno; vedação a adiantamento sem viagem vinculada; devolução de saldo positivo registrada no caixa; relatório mensal por técnico | Cláudia + jurídico | Aud-17 batch 3 (17/05/2026 noite) |
| **R-060** ⭐ NOVO | **Signatário descredenciado individualmente pela Cgcre sem bloqueio automático.** Cgcre pode suspender signatário (não o lab inteiro) — certificados emitidos APÓS o descredenciamento são nulos. Sem alerta automático, tenant continua emitindo e descobre meses depois. | Regulatório | 3 | 5 | **15** | Scraping/API diária do portal Cgcre; rebaixamento automático do signatário no Aferê quando suspenso; alerta imediato ao RT do tenant; bloqueio de novas emissões com aquele signatário | Auditor Conformidade | Aud-17 batch 3 (17/05/2026 noite) |
| **R-061** ⭐ NOVO | **Inadimplência SaaS > 12% sangra caixa.** Tenant não paga assinatura do Aferê; sem política de bloqueio gradual, vira sangria silenciosa (CS L1 não monitora). | Financeiro | 4 | 3 | **12** | ADR-0004 a criar: política de cobrança + dunning automatizado (lembrete D-3, D+1, D+7) + read-only no dia D+15 + apagar conforme LGPD após retenção legal | Cláudia/Roldão | Aud-21 batch 3 (17/05/2026 noite) |
| **R-062** ⭐ NOVO CRÍTICO | **CS L1 (suporte ao tenant) inexistente = churn 90 dias > 40%.** 1º cliente abre ticket sexta 22h, ninguém responde, churna mês 2. Modelo SaaS sem CS L1 (mesmo que seja bot) não fecha. | Operacional/Cliente | 5 | 4 | **20** | Persona 16 (Operador CS) a criar; playbook de CS L1; SLA escrito por categoria de ticket; bot com FAQ + escalonamento; Roldão como fallback humano até primeiros 20 clientes; ver F-18 em assumption-map | Roldão | Aud-21 batch 3 (17/05/2026 noite) |
| **R-063** ⭐ NOVO | **Migração de dados Cali/Bling/Excel vira consultoria escondida.** Cada onboarding = 40h custom; mata margem SaaS (LTV não sustenta R$ 8k+ de implementação grátis). | Operacional/Financeiro | 4 | 4 | **16** | Spike F-16 promovido a Top 8 LEAP; importador padronizado pra Cali (XML/Access) + Bling (API) + planilha (CSV template); ver F-17 (onboarding ≤ 8h) | Roldão | Aud-21 batch 3 (17/05/2026 noite) |
| **R-064** ⭐ NOVO | **Auvo expande pra Frota + Caixa em 9-12 meses (não Visma em 18 meses).** Auvo já tem GPS + OS + app + base PME de assistência técnica; cobrir OP3 (Operação de Campo) inteira é incremento natural. Mata diferencial #1 do Aferê. | Mercado | 4 | 4 | **16** | Integrar Frota com cadeia de rastreabilidade RBC (Auvo nunca vai fazer — não é metrologia); vender "Frota com rastreabilidade RBC" como bundle; chegar a 50 clientes antes da expansão deles | Roldão | Aud-14 batch 3 (17/05/2026 noite) |
| **R-065** ⭐ NOVO CRÍTICO | **Vendor (Roldão) não tem RT registrado com formação metrológica.** Cliente farma audita o lab (tenant) e pede o RT do vendor da plataforma; Roldão não tem CREA + competência metrológica registrada → fornecedor reprovado em qualificação. | Regulatório/Jurídico/Mercado | 5 | 4 | **20** | Contratar RT (engenheiro com CREA + competência metrológica comprovada via cursos INMETRO/RBC); criar INV-018 (RT obrigatório no Aferê); ADR documentando a contratação | Roldão + RH | Aud-17 batch 3 (17/05/2026 noite) |

---

## Top 15 prioritários (Score ≥ 12) — atualizado pós-auditoria 12 agentes (17/05/2026 noite)

> R-018 e R-027 empatam em 25; **R-027 fica no #1** porque NÃO tem mitigação implementada ainda (ADR-0000 escrita mas hooks pendentes); R-018 já tem hook planejado em `REGRAS-INEGOCIAVEIS.md` (INV-002).
> **R-001 REBAIXADO de 20 → 12 em 17/05/2026** após validação documental confirmar 13/20 dores externamente; ver `validacao-externa-documental.md`. Não cai pra ≤9 sem validar bandeiras amarelas (#15 comissões, UMC específica em #16).

**Score 25:**
1. **R-027** — Prompt injection cliente final — 25
2. **R-018** — Certificado sem cadeia rejeitado por Cgcre — 25

**Score 20:**
3. **R-002** — Família 5 vaporware — 20
4. **R-005** — ERP N módulos com 1 pessoa = anos — 20
5. **R-007** — Conflito tríplice retenção — 20
6. **R-016** — Cutover NFS-e Padrão Nacional 01/09/2026 — 20
7. **R-035** — Visma compra Cali/Metroex — 20
8. **R-042** — Transferência risco vendor↔tenant não tratada contratualmente — 20
9. **R-062** ⭐ NOVO — CS L1 inexistente = churn 90 dias > 40% — 20
10. **R-065** ⭐ NOVO — Vendor sem RT registrado — 20

**Score 16:**
12. **R-006** — NFS-e em município com padrão próprio — 16
13. **R-028** — Soberania de dados Anthropic — 16
14. **R-058** ⭐ NOVO — Jornada motorista UMC (Lei 13.103/2015) não modelada — 16
15. **R-059** ⭐ NOVO — Caixa do técnico vira salário-utilidade — 16
16. **R-063** ⭐ NOVO — Migração Cali/Bling/Excel vira consultoria escondida — 16
17. **R-064** ⭐ NOVO — Auvo expande pra Frota+Caixa em 9-12 meses — 16

**Score 15:**
18. **R-003** — Multi-tenant vazamento — 15
19. **R-004** — TAM ridículo — 15
20. **R-011** — Roldão burnout — 15
21. **R-014** — LGPD: vazamento → multa ANPD — 15
22. **R-015** — Signatário técnico indisponível — 15
23. **R-023** — Stack incapaz de validar software metrológico — 15
24. **R-029** — Bus factor Roldão — 15
25. **R-039** — Tenant declara perfil A sem acreditação real (fraude) — 15
26. **R-046** ⭐ ELEVADO (era 10) — UMC com peso-padrão roubado/batido — 15
27. **R-060** ⭐ NOVO — Signatário descredenciado pela Cgcre sem bloqueio automático — 15

**Score 12:**
28. **R-001** ⭐ REBAIXADO (era 20) — Customização disfarçada (founder is customer) — 12 (após validação documental 17/05/2026)
29. **R-008** — Prompt injection via MCP GitHub — 12
29. **R-017** — Porto Alegre desliga DANFSe local 01/07/2026 — 12
30. **R-019** — Cali lança fiscal/NFS-e antes do MVP — 12
31. **R-022** — Mito 72h GDPR vs 3 dias úteis ANPD — 12
32. **R-025** — PCI-DSS 4.0.1 se aceitar cartão direto — 12
33. **R-030** — Cali lança fiscal via parceria — 12
34. **R-034** ⭐ PROMOVIDO (era 4) — Homologação CERTI/INMETRO não obtida — 12
35. **R-040** — Cliente final esquece verificação periódica INMETRO — 12
36. **R-044** — Manutenção de frota atrasada — 12
37. **R-047** — Motorista UMC perde CNH/MOPP/toxicológico — 12
38. **R-048** — Acessibilidade WCAG 2.1 AA ausente — 12
39. **R-049** — Automação dispara mensagem indevida em massa — 12
40. **R-050** — Cliente reclama de spam (LGPD art. 18) — 12
41. **R-051** — Selo INMETRO perdido — 12
42. **R-054** — Inventário com divergência sistemática (fraude interna) — 12
43. **R-055** — Erro de regra de comissão em escala — 12
44. **R-061** ⭐ NOVO — Inadimplência SaaS > 12% sangra caixa — 12

---

## Riscos "cisnes negros" (P baixa, I catastrófico)

- Anthropic descontinua API (todo agente para) — coberto pela ADR-0000 (abstração de provider obrigatória).
- Hostinger BR sai do ar permanentemente — coberto por R-009.
- ANPD multa milionária em SaaS multi-tenant similar (precedente) — observar.
- INMETRO mudar política sobre software de calibração com IA — coberto por R-037.

**Mitigação:** observar; sem ação ativa AGORA mas plano de contingência mental.

---

## Como esta lista evolui

- Risco novo descoberto → adicionar imediatamente como R-NNN (próximo número disponível).
- Mitigação implementada → marcar ✅ + reduzir score residual.
- Risco materializou → mover pra postmortem + atualizar invariante.
- Risco descontinuado → marcar como DEPRECATED + razão (não remover linha, não reusar ID).
- Revisão obrigatória a cada milestone (síntese, MVP-1, 1º deploy, etc.).
- **Coluna Origem é imutável** — preserva história mesmo se risco for re-categorizado.
