---
owner: Roldão
revisado-em: 2026-05-23
status: stable
---

# PRD — Aferê (provisório)

> **Pra quê:** visão consolidada do produto. Saída da síntese final do discovery (`docs/discovery/sintese-final.md` DRAFT v3). Documento vivo — atualizar quando ICP/MVP-1/faseamento mudarem.
>
> **Nome:** Aferê é **PROVISÓRIO**. Não comprar domínio nem registrar INPI sem decisão final. Em código, usar slug neutro (`afere_app` ou similar) até bater o martelo.

---

## 1. O que é

ERP completo SaaS multi-tenant para **empresas de assistência técnica + calibração metrológica** (laboratório ISO 17025 + atendimento de campo). Substitui o stack patchwork que essas empresas usam hoje (Bling + Cali/Metroquality + Excel + WhatsApp).

Diferencial central: **calibração ISO 17025 com cálculo de incerteza nativo + emissão de NFS-e municipal funcional + trilha de auditoria WORM + recalibração proativa**, num único produto, com preço público e trial self-service de 30 dias — coisa que nenhum concorrente brasileiro oferece hoje.

---

## 2. Pra quem (ICP)

**4 perfis configuráveis** — cada tenant escolhe o seu na ativação:

| Perfil | Descrição | % do ICP | DAP hipótese |
|---|---|---|---|
| **A** | Laboratório acreditado RBC/CGCRE com escopo formal | 5-10% | R$ 1.500-3.000/mês |
| **B** ⭐ | Lab rastreável (não-acreditado), com clientes regulados ocasionais — **Roldão é deste perfil; é o núcleo do MVP-1** | 20-30% | R$ 700-1.500/mês |
| **C** | Lab em preparação pra acreditar (trilha D→A) | ~30% | R$ 500-800/mês |
| **D** | Calibração comercial pura (sem rituais 17025) | Raro nuclear | R$ 300-500/mês |

**Geografia núcleo MVP-1:** SP + RS + MG + SC (eixo industrial onde Roldão opera).
**TAM ICP convertível estimado:** 1.500-2.000 empresas (não os 5.000 brutos do setor).

### Sinais de "ESTE é o ICP" (validados documentalmente)
- Mantém 3+ sistemas paralelos (Bling + Cali + Excel + WhatsApp)
- Perde 30-50% das renovações por esquecimento
- Sofre com NFS-e municipal (cutover 09/2026)
- Atende cliente farma ocasionalmente (BPF RDC 658/972)
- Tem ≥1 técnico de campo com UMC ou veículo dedicado
- Conhece pressão regulatória ENIQ 2025-2026

### Sinais de "este NÃO é o ICP"
- Lab que não atende a clientes externos (calibração interna corporativa pura) — TOTVS/SIGAMNT atende melhor
- Empresa que cobra calibração avulsa sem rastreabilidade
- Lab de bancada-only sem campo nem UMC — anti-perfil (testa halo founder)

---

## 3. Dores que resolve (top 5 do MVP-1)

| # | Dor | Origem | Evidência |
|---|-----|--------|-----------|
| 1 | **NFS-e municipal cutover 09/2026** — emissão funcional em qualquer município | Dor #10 | 4 buckets validação documental |
| 2 | **Esquecimento de recalibração** — perde 30-50% das renovações por não lembrar cliente | Dor #02 | Validado externamente |
| 3 | **Word/Excel para cálculo de incerteza** — sem rastreabilidade, sem audit trail | Dor #04 | Pitch metrológico defensável |
| 4 | **Cadastro duplicado 4-6x entre sistemas** | Dor #01 | Foundation |
| 5 | **"Cadê minha OS?" perguntado 10-30x/dia** | Dor #05 | Quick win |

Lista completa de dores em `docs/discovery/dores-mapeadas.md` (32 dores mapeadas).

---

## 4. Tese central do MVP-1

> **Em 12 meses, antes do cutover NFS-e 01/09/2026 + janela ENIQ fechar, entregar emissor NFS-e + cálculo de incerteza NIT-DICLA-030 rev. 15 + trilha de auditoria 17025 + recalibração proativa, capturando mercado em onda de pressão regulatória forçada.**

### Escopo mínimo do MVP-1 (top 3 features)

1. **Cadastro único cliente + emissão de OS + certificado de calibração** (BIG-07 + BIG-02)
2. **Emissão NFS-e via BaaS pluggable** (PlugNotas como 1ª implementação — ver ADR-0008) (BIG-04)
3. **Lembrete de recalibração via WhatsApp BSP** (BIG-10 + BIG-11)

### Funcionalidades de suporte (Foundation, pré-MVP-1)
- Multi-tenant + RLS + audit trail (F-A)
- Auth + RBAC + cadastros (F-B)
- Cliente master (F-C — BIG-07)
- Mobile shell offline-first (F-D)
- WhatsApp BSP integrado (F-E)
- F-G hooks + auditores Família 5 + CI (cobre validação do modelo 100% agentes)
- Hooks + CI (F-G)
- ADR-0001 stack candidata fechada (F-H)

---

## 5. Non-goals do MVP-1

O que **NÃO** entra na primeira versão (alinhado com ANTI-01..ANTI-11 da discovery):

- ❌ Folha de pagamento / RH completo
- ❌ Pagamento direto com cartão (PCI-DSS fora do escopo)
- ❌ BI sofisticado / dashboards customizáveis
- ❌ Mensageria interna entre técnicos
- ❌ **Customização individual por tenant** (ANTI-11 — CRÍTICO; defesa contra "founder is customer")
- ❌ Hardware proprietário (somos software, não fabricante)
- ❌ 7 das 8 fórmulas de comissão (deixar 1 no MVP-1, expandir em MVP-2)
- ❌ Frota TCO completo (deixar caixa do técnico no MVP-1; frota move pra MVP-2)
- ❌ Cliente farma TOP (RT diferido pra V2-V3; ver `docs/adr/0008-fiscal-pluggable.md` + RDC 658/972)
- ❌ Assinatura 21 CFR Part 11 (V2-V3)
- ❌ API pública (decisão consciente — fora do mapa até decisão explícita)

---

## 6. Modelo de negócio

- **SaaS multi-tenant** em Hostinger SP/BR + Backblaze B2 EU + AWS KMS sa-east-1 (Multi-Region Key).
- **Pricing público** (vs setor 100% venda consultiva — diferencial defensável real).
- **Trial self-service de 30 dias** (vs setor 100% demo agendada — pioneiro estrutural).
- **Sem fidelidade abusiva**, sem reajuste acima do IPCA (anti-padrão do setor identificado em validação).

### Faixas hipotéticas (LEAP V-2 a validar)

| Perfil | Mensal | Setup |
|---|---|---|
| A | R$ 1.500-3.000 | R$ 0 |
| B | R$ 700-1.500 | R$ 0 |
| C | R$ 500-800 | R$ 0 |
| D | R$ 300-500 | R$ 0 |

**Meta operacional 12 meses:** 50 clientes pagantes (SOM).

---

## 7. Métricas de sucesso do MVP-1

| Métrica | Meta | Como medir |
|---|------|------------|
| Tenants pagantes em 12 meses | ≥ 50 | Painel do dono |
| NFS-e emitidas sem erro fatal | ≥ 95% | Log fiscal |
| Certificados de calibração gerados sem retrabalho | ≥ 90% | Auditor de Produto + NPS |
| Tempo médio "cadastro → 1ª OS emitida" | ≤ 15 min | Telemetria onboarding |
| Churn 90 dias | ≤ 15% | Cobrança + CS |
| Lembretes de recalibração com resposta | ≥ 40% | Métricas WhatsApp |
| CAC blended | ≤ R$ 4.500 | Marketing + venda |
| LTV/CAC | ≥ 4:1 | Cobrança + CAC |
| **Auditor de Segurança em 3 portões da ADR-0001** | passou | `governanca/trilha-auditoria-agentes.md` |
| R-001 (founder is customer) | ≤ 9 | `discovery/riscos.md` |

---

## 8. Concorrência (resumo)

| Ranking | Concorrente | Ameaça real |
|---|---|---|
| #1 | **Metroex / ForLogic** | Estruturado, cross-sell Qualiex, +500 INMETRO, API pública, MSA/SPC/IATF |
| #2 | **Cali** | 28 anos, homologação CERTI declarada, Cali LAB Mobile com QR offline |
| #3 | **Calibre.Software** | Player nicho menor que esperado (2-10 pessoas, marketing fraco, docs incompletas) |
| #4 | **FP2 Tecnologia** | Adjacente — atende análises, não RBC puro. Vale como prova de viabilidade técnica |

Detalhe em `docs/discovery/concorrentes.md` + `docs/discovery/validacao-externa/mystery-shopping-documental.md` + `docs/discovery/validacao-externa/estudo-calibre-software.md`.

---

## 9. Riscos remanescentes (score 20+)

- **R-027** — Prompt injection cliente final (ADR-0000 + hooks pendentes)
- **R-018** — Certificado sem cadeia rastreável rejeitado por CGCRE (INV-002 hook pendente)
- **R-001** — Founder is customer (atualmente 12; cai pra ≤9 só com cliente externo pago sob NDA — Portão 1 ADR-0001)
- **R-065** — Vendor sem RT (diferido pra V2-V3; aceito conscientemente)
- **R-062** — CS L1 inexistente (LEAP F-18 a validar)
- **R-042** — Transferência de risco vendor↔tenant

Lista completa em `docs/discovery/riscos.md` (65 riscos catalogados).

---

## 10. O que falta pra MVP-1 sair do papel

> **Atualizado 2026-05-17:** cliente externo pago **diferido pra V2**. MVP-1 sai dogfooding-only em Balanças Solution. Ver memória [[sem-cliente-externo-na-janela-atual]].

1. **Síntese final discovery** sair de DRAFT v3 → STABLE via **caminho B** (dogfooding, ver `discovery/sintese-final.md` §critério)
2. **Portão 3 ADR-0001** — F-A real construída em 4-6 semanas com critérios aprovados (sem spike descartável; ver [[nao-construir-codigo-descartavel]])
3. **Base de conformidade MVP-1:** ✅ `lgpd-rat.md`, ✅ `seguranca-dados.md`, ✅ `isolamento-multi-tenant.md`, ✅ `retencao-matriz.md`, ⏳ `conformidade-iso-17025.md`, ⏳ `responsabilidade-tecnica.md`
4. **3 prompts dos auditores Família 5** ✅ materializados (camada A subagent + camada B GitHub Action)
5. **5 hooks adicionais** ✅ criados (anti-mascaramento, context-budget, INV-checker, tenant-id-validator, paths-frontmatter-validator)
6. **Devcontainer + .env.example** (após ADR-0001 fechar definitiva)
7. **Wave A em produção real na Balanças Solution** por ≥ 3 meses sem SEV-0; ≤ 2 SEV-1 — gate substituto pra "MVP-1 entregue"

**Diferidos pra V2 (quando 1º cliente externo aparecer):**
- Portão 1 ADR-0001 (R-001 ≤ 9)
- Apólice cyber + RC profissional + DPO formal
- DPA-modelo + termos jurídicos pra contrato externo
- Dossiê de validação 17025 do software (consultor RBC)
- Bloco D do `go-live-checklist.md` (3 cartas, sintese STABLE caminho A, etc.)

Veja também: `docs/documentos-do-projeto.md` v6 (mapa completo de docs) + `docs/faseamento-modulos.md` (ordem dos módulos em produção).
