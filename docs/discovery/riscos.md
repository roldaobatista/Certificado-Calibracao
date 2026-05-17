# Discovery — Riscos

> **Artefato Rodada 0** (agente + Roldão). Inventário do que pode dar errado. Categorizado por tipo + probabilidade × impacto.
> **Atualizado:** 2026-05-16 — padronização de IDs pós-auditoria (Auditor 4). Todos os riscos agora em formato R-NNN sequencial único; coluna "Origem" rastreia de onde veio cada um. Total: 38 riscos consolidados (29 originais + 9 importados de `concorrentes.md` §7).

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

## Matriz Probabilidade × Impacto (38 riscos)

| ID | Risco (resumo) | Categoria | P | I | Score | Mitigação | Owner | Origem |
|---|---|---|---|---|---|---|---|---|
| **R-001** | Customização disfarçada (founder is customer) | Cliente | 4 | 5 | **20** | Discovery rigorosa com 5-10 OUTRAS empresas | Roldão | original |
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
| **R-034** | Fundação CERTI homologa só Cali e cria barreira política | Mercado | 1 | 4 | **4** | Buscar homologação CERTI cedo; caso de uso comparativo técnico | Roldão | concorrentes (era RC-05) |
| **R-035** | Visma (dona da Conta Azul desde 08/2025) compra Cali/Metroex | Mercado | 3 | 5 | **15** | Monitorar M&A Visma na BR; ir a mercado rápido; lockar com integração bancária mais profunda | Roldão | concorrentes (era RC-06) |
| **R-036** | TOTVS lança vertical de calibração via SIGAMNT/SIGAQMT melhorado | Mercado | 2 | 4 | **8** | Profundidade técnica RBC + UX moderna SaaS que TOTVS Protheus não consegue replicar | Roldão | concorrentes (era RC-07) |
| **R-037** | CGCRE muda paradigma pra acreditação baseada em riscos | Mercado/Regulatório | 3 | 3 | **9** | Modelar audit trail extensível ao novo modelo desde dia 0; acompanhar discussões CGCRE | Auditor Conformidade | concorrentes (era RC-08) |
| **R-038** | INMETRO/CGCRE oferece plataforma estatal grátis pra labs acreditados | Mercado | 1 | 5 | **5** | Sem ação ativa; gatilho seria comunicado oficial | Roldão | concorrentes (era RC-09) |
| **R-039** ⭐ | **Tenant declara perfil A (ISO 17025 acreditado) sem ter acreditação Cgcre real e emite certificados com selo RBC falso.** Fraude regulatória. Roldão (como vendor do SaaS) pode responder solidariamente | Jurídico/Regulatório | 3 | 5 | **15** | INV-015 (bloqueio por perfil); upgrade pra perfil A exige prova documental (certificado Cgcre + escopo de acreditação); revisão periódica automática consultando portal Cgcre (web scraping ou API se houver); cláusula contratual de responsabilização do tenant | Auditor Conformidade | decisão Roldão perfis 16/05/2026 |
| **R-040** | **Balança comercial calibrada pelo tenant tem verificação INMETRO/IPEM vencida** (perfil de uso comercial) e mesmo assim cliente final usa pra cobrar. Lacre INMETRO vence anualmente; calibração interna não substitui verificação legal. Cliente é multado e culpa o software | Regulatório/Mercado | 3 | 4 | **12** | Sistema diferencia explicitamente "calibração" (rastreabilidade) de "verificação metrológica legal" (selo INMETRO); calendário de verificação IPEM por instrumento; alerta 90/60/30 dias antes; certificado de calibração comercial leva nota "ESTA CALIBRAÇÃO NÃO SUBSTITUI A VERIFICAÇÃO INMETRO OBRIGATÓRIA — Portaria 157/2022" | Auditor Conformidade | decisão Roldão tipos de balança 16/05/2026 |

---

## Top 15 prioritários (Score ≥ 12) — atualizado pós-padronização

> R-018 e R-027 empatam em 25; **R-027 fica no #1** porque NÃO tem mitigação implementada ainda (ADR-0000 escrita mas hooks pendentes); R-018 já tem hook planejado em `REGRAS-INEGOCIAVEIS.md` (INV-002).

1. **R-027** — Prompt injection cliente final — 25
2. **R-018** — Certificado sem cadeia rejeitado por Cgcre — 25
3. **R-001** — Customização disfarçada (founder is customer) — 20
4. **R-002** — Família 5 vaporware — 20
5. **R-005** — ERP N módulos com 1 pessoa = anos — 20
6. **R-007** — Conflito tríplice retenção — 20
7. **R-016** — Cutover NFS-e Padrão Nacional 01/09/2026 — 20
8. **R-006** — NFS-e em município com padrão próprio — 16
9. **R-028** — Soberania de dados Anthropic — 16
10. **R-003** — Multi-tenant vazamento — 15
11. **R-004** — TAM ridículo — 15
12. **R-011** — Roldão burnout — 15
13. **R-014** — LGPD: vazamento → multa ANPD — 15
14. **R-015** — Signatário técnico indisponível — 15
15. **R-023** — Stack incapaz de validar software metrológico — 15
16. **R-029** — Bus factor Roldão — 15
17. **R-035** — Visma compra Cali/Metroex — 15
18. **R-039** — Tenant declara perfil A sem acreditação real (fraude) — 15
19. **R-040** — Verificação INMETRO vencida em balança comercial — 12

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
