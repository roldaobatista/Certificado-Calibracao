---
owner: roldao
revisado-em: 2026-06-12
status: minuta
aguarda-corretora-susep: true
selo: "PRÉ-COTAÇÃO — REQUER CORRETORA SUSEP CREDENCIADA (Lei 4.594/64 + Res. CNSP)"
finalidade: briefing técnico completo pra corretora SUSEP humana cotar 7 modalidades Wave A
audiencia: corretora de seguros SUSEP credenciada (perfil tech E&O + cyber + RC consequente)
---

> ❄️ **CONGELADO (decisão Roldão 2026-06-12, auditoria de cerimônia R19):** emendas de escopo/cobertura por módulo estão suspensas até os gates GATE-SEG-* correspondentes. Subagente `corretora-seguros-saas` atua no P2 SOMENTE para risco de DESIGN — não para atualizar este briefing que será revisado por corretora SUSEP credenciada pré-produção.

# Briefing técnico — corretora SUSEP

## 1. Sumário executivo

O **Aferê** (nome provisório) é um SaaS multi-tenant brasileiro voltado a empresas de assistência técnica + laboratórios de calibração metrológica acreditados ISO/IEC 17025 pelo CGCRE/RBC. Está em fase pré-produção (Foundation técnica fechada; primeiro tenant externo previsto pra Wave A, sem data definida). O **modelo operacional é 100% código gerado por agentes IA** com 3 pilares de controles compensatórios (ADR-0019) — não há programadores humanos no ciclo de produção. Esta corretora é convidada a cotar **7 modalidades de seguro complementares**, descritas na planilha anexa.

## 2. Identidade do produto

- **Nome comercial:** "Aferê" (provisório — não comprar domínio ainda)
- **Modelo de negócio:** SaaS multi-tenant — assinatura mensal por tenant (faixa estimada R$ 500-3.000/mês por tenant)
- **Cliente piloto:** Balanças Solution (empresa do Roldão Batista — dogfooding)
- **Primeiro tenant externo:** sem data; depende fechamento Wave A + portões ADR-0001
- **Concorrência direta:** Calibre.Software (mystery shopping documental realizado)
- **Diferencial:** módulo de calibração ISO 17025 com regra de decisão 7.8.6, validação software 7.11, OS com atividades multi-tipo, certificados longa custódia (~25 anos)

## 3. Escopo funcional (módulos)

Mínimo 6 módulos confirmados, totalizando ~48 módulos catalogados em `faseamento-modulos.md`:

| Módulo | Wave | Risco-chave |
|---|---|---|
| Foundation F-A (multi-tenant + RLS + audit) | Fechado | Vazamento cross-tenant |
| Foundation F-B (authz + feature flags + IP hash) | Fechado | Bypass de autorização |
| Clientes (Marco 1) | Fechado | LGPD eliminação/anonimização |
| Equipamentos (Marco 2) | Fechado | Imutabilidade pós-INSERT + QR HMAC |
| OS (Marco 3) | Em spec | Custódia física, BPT, transferência mid-OS, vistoria |
| Calibração (Marco 4) | Pendente | Regra de decisão 7.8.6, validação SW 7.11, 2ª conferência |
| Certificados | Pendente | Long-tail 25 anos, A3 ICP-Brasil, contestação |
| Fiscal / NFS-e | Pendente (deadline 01/09/2026 nacional) | Erro fiscal → SEFAZ |
| Financeiro (CR/CP) | Pendente | Cobrança indevida, conciliação OFX |
| Billing-saas | Pendente | Wrongful billing > R$ 50k |
| Chamados, Orçamentos, BPM, BI, app-técnico | Pendentes | Diversos |

## 4. Stack técnica

- **Backend:** Python 3.12 + Django 5.0 + DRF + procrastinate (filas sobre PG)
- **Banco:** PostgreSQL 16 — schema-shared + RLS + middleware tenant_id (ADR-0002)
- **Frontend web:** HTMX sobre Django templates + 4 SPAs isoladas (ADR-0010)
- **Mobile:** Flutter (planejado — Wave A) com offline-first + sync por atividade (ADR-0027)
- **Assinatura A3 ICP-Brasil:** Web PKI Lacuna client-side (ADR-0009) — Aferê NUNCA toca chave privada
- **KMS:** AWS KMS Multi-Region Key (sa-east-1 ↔ us-east-1 réplica)
- **Storage WORM:** Backblaze B2 (datacenters US) — trilha imutável certificados + NFS-e ~25 anos
- **Hospedagem:** Hostinger VPS KVM 4 (São Paulo/BR) — DR provedor B a definir
- **Observabilidade:** Grafana Cloud + Axiom
- **PSP fiscal:** PlugNotas (provider NFS-e)
- **LLM:** Anthropic API (Claude) — geração de código e operação agentes

## 5. Modelo de operação 100% agentes IA (CRÍTICO PARA SUBSCRIÇÃO)

A ADR-0019 documenta exaustivamente. Resumo pra subscritor:

- **Nenhum programador humano commitando código em produção.**
- **3 pilares de controles compensatórios:**
  1. **10 auditores Família 5** (segurança, qualidade, produto, drift, LLM, performance, observabilidade, idempotência, supplychain, LGPD) — bloqueiam commit/merge antes de chegar em main. MÉDIO+ é bloqueante DURO (INV-RITUAL-001).
  2. **4 subagentes humanos-substitutos** especialistas (tech-lead, advogado, corretora — você —, consultor RBC) — revisam plan + spec antes de implementação.
  3. **Ritual Spec Kit obrigatório** (spec FORWARD → plan + 4 reviews → matriz reconciliação → tasks → implement → 10 auditores) — pular ritual é proibido por hook.
- **25 hooks ativos** (207/207 casos verdes em `_test-runner`) bloqueiam: comandos destrutivos, secrets, vazamento de tenant_id, mascaramento de teste, envelope inválido, falta de policy RLS, imutabilidade quebrada, etc.
- **Humano licenciado SUSEP/OAB/CREA** entra apenas em 5 casos-limite: apólice (você), parecer OAB, dossiê CGCRE, RT credenciado físico, decisões legais públicas.

**Por que isso importa pra subscrição:** o subscritor deve REJEITAR exclusão genérica "código gerado por IA sem revisão humana" — os controles compensatórios são objetivos, versionados, auditáveis e mais rigorosos do que ciclo dev humano padrão. Documentação à disposição pra due diligence: `ADR-0019`, `controles-compensatorios-codigo-ia.md`, `governanca/catalogo-auditores.md`.

## 6. Regulatório aplicável

| Norma | Impacto seguros |
|---|---|
| **LGPD (Lei 13.709/18)** | Multa até 2% faturamento tenant; notificação ANPD 72h; direitos titular art. 18 (portabilidade/eliminação/anonimização) implementados em Marco 1 |
| **ISO/IEC 17025** | Tenants acreditados CGCRE/RBC — certificado errado = recall + suspensão escopo (motivo Modalidade 7) |
| **NIT-DICLA-021** | Requisitos RT credenciado por grandeza — ADR-0022 |
| **Receita Federal / SEFAZ municipais** | NFS-e nacional deadline 01/09/2026 (módulo fiscal pendente) |
| **INMETRO** | Verificação metrológica (Portaria 157/2022) |
| **CC art. 627 (Depositário)** | Custódia física instrumento — base BPT |
| **ICP-Brasil A3** | MP 2.200-2/01 + Res ITI — assinatura RT lab |
| **CNSP / SUSEP** | Esta apólice em si — base legal Lei 4.594/64 |

## 7. Exposição agregada multi-tenant (ATENÇÃO ESPECIAL)

Risco assimétrico característico SaaS multi-tenant: **1 bug em código compartilhado afeta N tenants simultaneamente**. Implicações pra subscrição:

- **Capital agregado anual > sublimite por evento** — corretora deve dimensionar agregado pensando em incidente que dispare 50+ claims simultâneos.
- **Cláusula `aggregate reinstatement`** (Cyber) é crítica — 1º sinistro pode esgotar capital; reinstatement automático garante cobertura pro restante do ano.
- **`Multi-claim aggregate`** (E&O+Cyber consolidado) ≥ R$ 10M — evita disputa de imputação claim-a-claim.
- **CBI sub-operador** (Modalidade 6) é cascata: AWS KMS down → 100% tenants param simultaneamente.

## 8. Riscos por fase (mapa)

| Fase / Marco | Janela | Risco-chave seguro |
|---|---|---|
| **Hoje — dogfooding Balanças Solution** | Já ocorrendo | **BPT IMEDIATO** — instrumentos físicos em custódia (GATE-SEG-BPT-1) |
| **Pré-1º tenant externo pago** | Wave A | Cyber R$ 5M + reinstatement; E&O R$ 5-10M; D&O; CBI; ACR |
| **1º tenant externo** | Wave A | Todas as 7 modalidades emitidas; DPA cap 12x mensalidade ou R$ 500k |
| **1º tenant farma/alimento** | Wave A condicional | E&O com sublimite recall ativo + apólice complementar do tenant exigida |
| **1º tenant RBC acreditado** | Wave A | Accreditation Loss Extension obrigatória |
| **Marco 3 OS — vistoria habilitada** | Wave A | E&O `pareceres técnicos` ativa |
| **V2 — RT vendor próprio** | V2 | RC profissional individual RT (`RC-RT-vendor-v2.md`) |

## 9. Controles existentes (mitigantes pra prêmio)

- RLS no banco (multi-tenancy bloqueia vazamento cross-tenant em DB).
- Audit trail imutável (hook `audit-immutability-check`).
- IP hash HMAC anti-PII em logs (F-B).
- A3 client-side (Aferê não custodia chave privada — defesa anti-replay nonce + signing-time server).
- KMS MRK (ciclo de chave PII GATE).
- WORM B2 (trilha eventos imutável).
- Crypto-shredding por tenant (LGPD direito esquecimento).
- 25 hooks pré-commit + 10 auditores pré-merge.
- DPA modelo + DPAs sub-operadores (7 sub-operadores nomeados).
- Drill anual incidente cyber+ANPD (GATE-SEG-DRILL-1).

## 10. Pedido formal de cotação

Solicitamos cotação SUSEP-credenciada para **7 modalidades** descritas na planilha anexa (`planilha-cotacao-wave-a.md`):

1. E&O ampliado (R$ 5-10M agregado)
2. Cyber (R$ 5M + reinstatement)
3. D&O (R$ 1M)
4. **BPT (EMERGENCIAL — antes da próxima recepção física)**
5. Extensão veicular UMC
6. Dependent Service BI (R$ 1M agregado)
7. Accreditation Loss Extension (R$ 2M agregado)

**Cláusulas críticas a NEGOCIAR:** 12 cláusulas nomeadas listadas na planilha.
**Cláusulas a REJEITAR:** exclusão "código IA sem revisão humana"; exclusão "depositário"; exclusão multas regulatórias LGPD/CGCRE/INMETRO/ANPD; franquia > 5% (exceto BPT fixo).

**Janela:**
- BPT: **imediato** (dogfooding em curso).
- Demais 6: antes do 1º tenant externo pago (sem data fixa).
- Modalidade RC RT vendor: V2 (gatilho em `RC-RT-vendor-v2.md`).

**Corretoras candidatas paralelas:** Marsh Brasil, AON Tech, Howden Brasil.

## 11. Documentação à disposição pra due diligence

- `ADR-0019` (responsabilidade civil + segurabilidade código IA)
- `ADR-0022` (RT do tenant)
- `ADR-0023` (OS com atividades)
- `ADR-0025` (validação software ISO 17025 cl. 7.11)
- `ADR-0028` (este mapa)
- `controles-compensatorios-codigo-ia.md` (se existir; senão referenciado em ADR-0019)
- `governanca/catalogo-auditores.md` (10 auditores)
- `REGRAS-INEGOCIAVEIS.md`
- `dpa-modelo.md` (com cap responsabilidade)
- `retencao-matriz.md` (Receita 5y × ISO 8.4 ~25y × LGPD)

## 12. Contato

Roldão Batista — roldao.tecnico@gmail.com — Balanças Solution.

---

**Selo:** este briefing é pré-cotação. Apólice válida exige corretora SUSEP credenciada (Lei 4.594/64 + Resoluções CNSP). Subagente IA `corretora-seguros-saas` produziu este documento sob ritual Spec Kit — não substitui parecer humano licenciado.
