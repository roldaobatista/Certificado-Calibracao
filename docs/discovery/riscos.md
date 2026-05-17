# Discovery — Riscos

> **Artefato Rodada 0** (agente + Roldão). Inventário do que pode dar errado. Categorizado por tipo + probabilidade × impacto.
> **Atualizado:** 2026-05-16 — refinamento com aprendizados das pesquisas de `concorrentes.md` e `normas-e-regulacao.md`. Novos riscos R16–R22 adicionados.

---

## Categorias de risco

- **Regulatório:** ANPD/LGPD, INMETRO/CGCRE, Receita Federal, Bacen, ANS, etc.
- **Técnico:** stack inviável, integração impossível, performance, segurança
- **Mercado:** TAM pequeno, concorrência forte, demanda baixa
- **Time / operacional:** 1 pessoa + IA = bottleneck, agente vira inviável, burnout do Roldão
- **Financeiro:** investimento insuficiente, custos crescendo desproporcionalmente
- **Cliente:** "founder is customer" → produto não generaliza, primeiro cliente externo recusa
- **Jurídico:** responsabilidade por dado vazado, IA emitindo certificado regulado

---

## Matriz Probabilidade × Impacto

| Risco | Categoria | P (1–5) | I (1–5) | Score (P×I) | Mitigação | Owner |
|---|---|---|---|---|---|---|
| Customização disfarçada (founder is customer) | Cliente | 4 | 5 | **20** | Discovery rigorosa com 5–10 OUTRAS empresas | Roldão |
| Família 5 (3 auditores) virar vaporware | Operacional | 4 | 5 | **20** | Materializar prompts + triggers + veto na Rodada 4 | Agente |
| Multi-tenant vazamento entre clientes | Técnico/Regulatório | 3 | 5 | **15** | INV-TENANT-001 + RLS + hook + drill | Auditor Segurança |
| TAM ridículo (poucos prospects ICP) | Mercado | 3 | 5 | **15** | Validação ativa antes de comprometer | Roldão |
| ERP de N módulos com 1 pessoa = anos sem MVP | Operacional | 5 | 4 | **20** | Faseamento por módulo + MVP-1 enxuto | Roldão |
| NFS-e em município com padrão próprio | Regulatório/Técnico | 4 | 4 | **16** | Matriz município × padrão + Focus/NFE.io | Auditor Conformidade |
| Conflito tríplice retenção (Receita × ISO × LGPD) | Regulatório | 4 | 5 | **20** | `retencao-matriz.md` + base legal explícita | Auditor Conformidade |
| Prompt injection via MCP GitHub | Técnico/Segurança | 3 | 4 | **12** | `mcp-policy.md` + `agente-input-nao-confiavel.md` | Auditor Segurança |
| Hostinger SPOF (provedor inteiro fora) | Operacional | 2 | 5 | **10** | `dr-plan.md` 3 cenários + IaC pra provedor B | Auditor Operação |
| Token cost explosion (>R$ 50/dia) | Financeiro | 3 | 3 | **9** | Orçamento de contexto + alerta no painel | Roldão |
| Roldão burnout (dono não-técnico sozinho) | Operacional/Humano | 3 | 5 | **15** | Limites de autonomia + status semanal forçando foco | Roldão |
| Stack escolhida se mostra inviável após MVP-1 | Técnico | 2 | 4 | **8** | Spikes técnicos em discovery + ADR-0001 conservadora | Auditor Arquitetura |
| Concorrente (Bling/Tiny) lança features ISO 17025 | Mercado | 2 | 4 | **8** | Foco em diferencial + nicho fiel | Roldão |
| LGPD: incidente de vazamento → multa ANPD | Regulatório/Financeiro | 2 | 5 | **10** | `seguranca-dados.md` + 72h playbook + DPO | Auditor Conformidade |
| Signatário técnico não-disponível (RBC NIT-DICLA-021) | Regulatório | 3 | 5 | **15** | Identificar signatário ANTES de emitir 1º certificado | Roldão |
| **R16** — NFS-e cutover Padrão Nacional (ME/EPP em 01/09/2026; município SP mantém próprio + ADN) gera bug fiscal pro nosso 1º cliente | Regulatório/Técnico | 4 | 5 | **20** | Integrar BaaS fiscal único (Focus/PlugNotas/TecnoSpeed) em vez de implementar municipal-a-municipal; ADR-fiscal pós-stack | Auditor Conformidade |
| **R17** — Porto Alegre desliga DANFSe local em 01/07/2026 — se algum cliente nosso usa POA, sistema quebra na data | Regulatório/Técnico | 3 | 4 | **12** | Mapear municípios dos primeiros 5 clientes; ter integração ADN pronta antes de jul/26 | Auditor Conformidade |
| **R18** — NIT-DICLA-030 rev. 15 (item 8.2.6) — emitir certificado sem resultado de medição + incerteza é rejeitado por Cgcre | Regulatório | 5 | 5 | **25** | Hook bloqueia emissão sem cadeia completa (invariante INV-CALIB-001); validar em mock antes de 1º cliente | Auditor Conformidade |
| **R19** — Concorrente nacional (Cali/Metroex) lança fiscal/NFS-e via parceria antes do nosso MVP | Mercado | 3 | 4 | **12** | Ir a mercado rápido (faseamento prioriza módulo metrologia + fiscal juntos), lockar com integração bancária mais profunda | Roldão |
| **R20** — FP2 Tecnologia expande NFS-e multi-município pra cobertura nacional (hoje só Santa Maria/RS) | Mercado | 2 | 4 | **8** | Monitorar; vantagem competitiva por UX moderna SaaS + capilaridade | Roldão |
| **R21** — ERP horizontal (Omie/Bling/Conta Azul) lança vertical de calibração ISO 17025 | Mercado | 2 | 5 | **10** | Profundidade técnica ISO 17025 (cálculo incerteza GUM, rastreabilidade, ILAC G8) que generalistas não dominam; foco em cliente acreditado RBC | Roldão |
| **R22** — Mito "72h GDPR" virar invariante errada — ANPD Res. 15/2024 é **3 dias úteis**, não 72h corridas. Implementar errado atrai multa ou ridículo | Regulatório/Operacional | 3 | 4 | **12** | Doc `lgpd-incidente-3-dias-uteis.md` (nome correto); revisar em todos os runbooks; treinar agentes | Auditor Conformidade |
| **R23** — Stack escolhida não suportar validação de software metrológico (cláusula 7.11 da 17025) — change control + audit trail imutável + replay determinístico | Técnico/Regulatório | 3 | 5 | **15** | ADR-0001 stack deve incluir critério "permite WORM + audit trail + replay"; spike técnico antes de cravar | Auditor Arquitetura |
| **R24** — Anvisa RDC 658/2022 (BPF medicamentos) ou RDC 786/2023 (sistemas computadorizados) atinge cliente farma que pede do nosso software conformidade que não temos | Regulatório/Mercado | 2 | 4 | **8** | Documentar em Família 6 quais clientes-farma exigem; manter "perfil regulado farma" como add-on, não MVP-1 | Auditor Conformidade |
| **R25** — PCI-DSS 4.0.1 (vigente desde 31/03/2025) ativada se aceitarmos pagamento online direto | Regulatório/Operacional | 3 | 4 | **12** | Não processar cartão direto; usar PSP/gateway com tokenização (Stripe/Pagar.me/PagSeguro/Asaas) → escopo SAQ A | Auditor Segurança |
| **R26** — Confusão entre as 3 empresas com nome "AutoLab" gera erro de comunicação/posicionamento competitivo | Operacional/Marketing | 2 | 2 | **4** | Padronizar referência interna como "AutoLab/Automa" (concorrente direto), "Sistema Autolab/Arkade" (obras), "AUTOLAB/MRI" (analítico). Documentado em `concorrentes.md` §3.16 | Agente |

---

## Top riscos prioritários atualizados (≥15) — após rodada 1 de pesquisa

> Ordem reflete score P×I, com **R18 (NIT-DICLA-030 8.2.6)** no topo por probabilidade 5 e impacto 5 (rejeição direta de certificado por Cgcre).

1. **R18 — Certificado sem cadeia de rastreabilidade rejeitado por Cgcre** (NIT-DICLA-030 rev. 15, item 8.2.6) — score 25. Mitigação: hook bloqueia emissão.
2. **R16 — Cutover NFS-e Padrão Nacional 01/09/2026 (ME/EPP)** — score 20. Mitigação: BaaS fiscal único.
3. **Customização disfarçada** (founder is customer) — score 20. Discovery rigorosa OBRIGATÓRIA.
4. **Família 5 vaporware** — score 20. Materializar na Rodada 4.
5. **ERP N módulos com 1 pessoa = anos sem MVP** — score 20. Faseamento essencial.
6. **Conflito tríplice retenção** (Receita 5 anos × ISO 17025 25 anos × LGPD esquecimento) — score 20. `retencao-matriz.md` urgente.
7. **Multi-tenant vazamento entre clientes** — score 15. INV-TENANT-* + hooks + RLS PostgreSQL.
8. **TAM ridículo (poucos prospects ICP)** — score 15. Validação ativa antes de comprometer.
9. **Roldão burnout** — score 15. Limites de autonomia + status semanal forçando foco.
10. **Signatário técnico indisponível** (RBC NIT-DICLA-021) — score 15. Identificar antes do 1º certificado.
11. **R23 — Stack incapaz de validar software metrológico (cláusula 7.11)** — score 15. ADR-0001 com critério WORM+audit trail+replay.
12. **NFS-e em município com padrão próprio** (SP, Goiânia) — score 16. BaaS fiscal.

---

## Riscos "cisnes negros" (P baixa, I catastrófico)

- Anthropic descontinua API (todo agente para)
- Hostinger BR sai do ar permanentemente
- ANPD multa milionária em SaaS multi-tenant similar (precedente)
- INMETRO mudar política sobre software de calibração com IA

**Mitigação:** observar; sem ação ativa AGORA mas plano de contingência mental.

---

## Como esta lista evolui

- Risco novo descoberto → adicionar imediatamente.
- Mitigação implementada → marcar ✅ + reduzir score.
- Risco materializou → mover pra postmortem + atualizar invariante.
- Revisão obrigatória a cada milestone (síntese, MVP-1, 1º deploy, etc.).
