---
owner: roldao
status: stable
revisado-em: 2026-06-15
proximo_review: 2026-09-15
diataxis: reference
audiencia: agente
tipo: matriz-feature-perfil
origem: ADR-0067 §"Decisao" item 4 — Sprint 3 P5 saneamento
relacionados:
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - docs/adr/0009-onde-a3-assina.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz canônica feature × perfil regulatório

> **Origem:** ADR-0067 §"Decisão" item 4 + T-SAN-PERFIL-037 + AC-SAN-PERFIL-005-1..7.
>
> Este documento é fonte da verdade para todo predicate / use case / job que decide se uma feature está **obrigatória / parcial / opcional / desabilitada** por perfil do tenant.
>
> Hook `feature-perfil-matriz-validator.sh` (Sprint 3 — T-SAN-PERFIL-038) bloqueia commit de novo PRD/ADR que adicione US-* ou AC binário em feature listada aqui sem registrar a linha correspondente.

## Convenções

| Símbolo | Significado |
|---|---|
| `✅ OBRIGATÓRIO` | Predicate bloqueia operação se feature ausente. |
| `🟡 OBRIGATÓRIO_PARCIAL` | Versão reduzida obrigatória; versão completa opcional. |
| `🟢 OPCIONAL_RECOMENDADO` | Predicate aceita ausência mas operador recebe warning. |
| `⚪ OPCIONAL` | Sem warning; tenant decide livremente. |
| `❌ DESABILITADO` | Feature não disponível no plano; UI esconde + predicate bloqueia. |

## Matriz núcleo

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **Regra de decisão ISO 17025 cl. 7.8.6** (ADR-0024) — 3 modos + aceite cliente | ✅ OBRIGATÓRIO | ⚪ OPCIONAL | ⚪ OPCIONAL | ❌ DESABILITADO |
| **2ª conferência** (ADR-0026 + cl. 6.2.5) — segregação RT vs conferente | ✅ OBRIGATÓRIO se `regra_decisao.modo != NENHUMA` (R5 plan.md) | ⚪ OPCIONAL | ⚪ OPCIONAL | ❌ DESABILITADO |
| **Validação software 7.11** (ADR-0025) URS+IQ+OQ+PQ | ✅ OBRIGATÓRIO_FULL (URS+IQ+OQ+PQ) | 🟢 OPCIONAL_RECOMENDADO (URS apenas) | 🟡 OBRIGATÓRIO_PARCIAL (URS+OQ — gate trilha D→A, R6 plan.md) | ❌ DESABILITADO |
| **TSA-ITI qualificado PAdES-LTV** (ADR-0047) — 25a longa duração | ✅ OBRIGATÓRIO | ⚪ OPCIONAL (ICP-Brasil simples basta) | ⚪ OPCIONAL | ❌ DESABILITADO |
| **Selo ILAC-MRA no certificado** (R9 plan.md) | ✅ OBRIGATÓRIO se `tenant.ilac_mra_aderido=TRUE` / ❌ DESABILITADO se FALSE | ❌ DESABILITADO | ❌ DESABILITADO | ❌ DESABILITADO |
| **A3 ICP-Brasil obrigatório** (ADR-0009) | ✅ OBRIGATÓRIO | 🟢 OPCIONAL_RECOMENDADO (A1 aceito) | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO |
| **GUM clássico** (ADR-0067 §1 Perfil A docstring) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL |
| **Monte Carlo BIPM JCGM 101** (2º caminho de cálculo) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL | ❌ DESABILITADO |
| **Snapshot RT competência por grandeza** (ADR-0022 + ADR-0063) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL |
| **Template certificado com selo CGCRE + RBC** (Sprint 5 Wave A) | ✅ OBRIGATÓRIO | ❌ DESABILITADO (hook bloqueia) | ❌ DESABILITADO | ❌ DESABILITADO |
| **Template de orçamento com `selo_rbc`** (orcamentos — US-ORC-005 / T-ORC-039 / D-ORC-13 / INV-ORC-SELO-RBC) | ✅ PERMITIDO (perfil A) | ❌ PROIBIDO (422 `SeloRbcNaoPermitido`; gate server-side + hook `orc-template-selo-rbc-check`) | ❌ PROIBIDO | ❌ PROIBIDO |
| **Documento "Certificado de Calibração ISO 17025"** | ✅ OBRIGATÓRIO | 🟢 OPCIONAL_RECOMENDADO (com bloco "rastreabilidade declarada") | 🟢 OPCIONAL_RECOMENDADO | ❌ DESABILITADO (renomeado "Relatório de Aferição") |
| **Subcontratação cl. 6.6 (US-CAL-017)** | ✅ OBRIGATÓRIO (predicate + avaliação periódica) | ⚪ OPCIONAL | ⚪ OPCIONAL | ⚪ OPCIONAL |
| **Reclamação cliente CDC art. 26 (US-CAL-018)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Verificação periódica vigência acreditação** (S5 plan.md — job mensal) | ✅ OBRIGATÓRIO (job alerta 60d antes) | ⚪ N/A | ⚪ N/A | ⚪ N/A |
| **Escopo CGCRE `rbc_acreditado=true`** (M6 escopos-cmc — US-ECMC-001 / INV-ECMC-002 / ADR-0075) | ✅ OBRIGATÓRIO (declara escopo RBC; gate `rbc_efetivo`) | ❌ DESABILITADO (rbc forçado `false`) | ❌ DESABILITADO (rbc forçado `false`) | ❌ DESABILITADO (rbc forçado `false`) |
| **Capacidade interna declarada `rbc_acreditado=false`** (M6 — US-ECMC-007 / ADR-0075) | ⚪ OPCIONAL (além do escopo RBC) | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO |
| **Bloqueio cobertura `cobre()` na configuração** (M6 — US-ECMC-004 / INV-ECMC-004/005 / ADR-0073/0074) | ✅ OBRIGATÓRIO (412 `EscopoNaoCobreFaixa` fora do escopo) | ⚪ N/A (não é RBC — short-circuit antes da porta) | ⚪ N/A | ⚪ N/A |
| **U≥CMC na emissão** (M6 — US-ECMC-008 / INV-ECMC-009 / porta `cmc_para()` — GATE-ECMC-U-MAIOR-CMC) | ✅ OBRIGATÓRIO (412 `IncertezaAbaixoDoCMC` — consumo em `certificados` Wave A) | ⚪ N/A | ⚪ N/A | ⚪ N/A |
| **Procedimento documentado vigente** (M7 procedimentos — US-CAL-016 / INV-PROC-001/004 / ADR-0073 / cl. 7.2.1) | ✅ OBRIGATÓRIO (412 `ProcedimentoVigenteAusente` na configuração RBC; porta `cobre_procedimento()` resolve só PUBLICADO vigente que contém a faixa) | 🟢 OPCIONAL_RECOMENDADO (aviso degradante — não bloqueia) | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO |
| **Validação de método cl. 7.2.2** (M7 — INV-PROC-010 / `tipo_metodo` + `registro_validacao_id` — GATE-PROC-METODO-VALIDADO) | 🟡 OBRIGATÓRIO_PARCIAL (A + método NÃO-NORMALIZADO/MODIFICADO exige validação; **fail-open lazy** até `licencas-acreditacoes` — só AVISO hoje) | ⚪ N/A (não-acreditado nunca pende) | ⚪ N/A | ⚪ N/A |
| **NFS-e de calibração — documento metrológico exigido** (fiscal/NFS-e — US-FIS-001 / INV-FIS-001 / ADR-0008 emenda / ADR-0073) | ✅ `certificado_id` cert RBC vigente (ou NAO_RBC — D-FIS-6) | ✅ `certificado_id` cert simples (não-RBC; cert RBC → 403 AC-FIS-001-8) | ✅ `certificado_id` cert simples + flag `em_preparacao_para_rbc` (metadado interno) | ✅ `declaracao_calibracao_basica_id` (sem cert) |
| **Papel SIGNATARIO de colaborador** (colaboradores — AC-COL-03 / INV-COL-SIGNATARIO-IDENTIDADE / INV-COL-SIGNATARIO-ESCOPO / D-COL-11 / ADR-0067) — atribuição exige `usuario_id` casando com `RTCompetencia` vigente + escopo; assinatura ISO acreditada no certificado | ✅ OBRIGATÓRIO — bloqueio hard (`can_assign_signatario` fail-closed; 422 se identidade ou escopo ausentes) | 🟢 OPCIONAL_RECOMENDADO — configurável (sem bloqueio hard; warning se SIGNATARIO atribuído sem RT ativo no escopo) | 🟢 OPCIONAL_RECOMENDADO | ❌ DESABILITADO — perfil D não produz assinatura acreditada ISO (renomeado "Relatório de Aferição") |
| **NFS-e — qualificador acreditado na descrição** (fiscal — US-FIS-001 / INV-FIS-007 / cl. 8.1.3 / ADR-0075) | ⚪ PERMITIDO (pode exibir RBC/acreditada) | ❌ PROIBIDO ("RBC"/"ISO 17025"/"acreditada" na descrição) | ❌ PROIBIDO | ❌ PROIBIDO ("calibração" simples permitida — D-FIS-7) |

## Matriz de retenção em camadas (AC-SAN-PERFIL-005-5 + R10 plan.md)

> **Conflito ADR-0064 (HMAC 25a invariante) vs PII por perfil:** resolvido em 2 camadas. Hash-chain WORM sempre 25a; PII de cliente segue regra por perfil.

| Camada de dado | A | B | C | D |
|---|---|---|---|---|
| **PII cliente / titular** (ADR-0021 zonas) | 25a (ISO 8.4 obrigação legal) | 25a (recomendado — preparação para A) | 25a (mesmo) | **5a (Receita)** + anonimização agressiva |
| **Eventos WORM hash-chain** (INV-HMAC-001..005) | 25a INVARIANTE | 25a INVARIANTE | 25a INVARIANTE | **25a INVARIANTE** |
| **Job `geo_truncamento_calibracao_5a`** | NUNCA trunca | 5a (trunca preservando hash-chain) | 5a | 5a + anonimização agressiva |
| **Recebimento do item calibrando POR INSTRUMENTO** (ordens_servico — INV-OSME-RCB-001 / ADR-0082 / cl. 7.4.3) | ✅ registro de condição de recebimento por instrumento obrigatório (anormalidade por item — cl. 7.4.3); ausência = NC maior CGCRE | ⚠️ recomendado por instrumento; 1-por-OS tolerado fora de bancada | ⚠️ recomendado (em preparação) | ➖ não exigido (sem cadeia de custódia metrológica) |
| **Backup B2 WORM** (ADR-0064) | 25a | 25a | 25a | 25a (hash-chain) + 5a (PII) |
| **Escopo CMC / capacidade** (M6 — sustenta o certificado emitido; WORM Padrão B INV-ECMC-003) | 25a (lastreia cert RBC — ISO 8.4) | 25a (capacidade declarada) | 25a | 25a (nunca apaga; sem PII de cliente) |
| **Procedimento de calibração** (M7 — documento controlado que lastreia a calibração; WORM Padrão B INV-PROC-003; snapshot na calibração INV-PROC-005) | 25a (lastreia cert RBC — ISO 8.4 + cl. 7.2.1) | 25a (método declarado) | 25a | 25a (nunca apaga; sem PII de cliente) |
| **NFS-e emitida + XML probatório** (fiscal — INV-FIS-008 / zona B ADR-0021) | 5a mínimo (Receita/CTN; prudencial 10a) | 5a (prudencial 10a) | 5a | 5a | <!-- PII do tomador no payload ao provider só sob DPA (INV-FIS-009); evento WORM só hash -->

**Regra-mestre:** dados de PII de cliente podem ser anonimizados; hash-chain WORM e evento de calibração NUNCA podem ser apagados (vence INV-HMAC-001..005).

## Matriz de operações de mudança de perfil

> Quem pode disparar qual transição. Detalhe técnico em `aplicar_evento_cgcre()` (migration 0008) e `rebaixar_perfil_tenant_voluntario_cliente()` (migration 0009).

| Direção | A | B | C | D | Quem dispara |
|---|---|---|---|---|---|
| **Promoção monotônica** (D→C, C→B, B→A) | — | → A | → B | → C | Admin Aferê + A3 + PDF CGCRE (perfil A apenas) |
| **Rebaixamento voluntário cliente** (B→D, B→C, C→D) | ❌ (perda voluntária de A não permitida — use cancelamento_cgcre) | → D ou C | → D | — | Cliente com cooldown 30d + pré-aviso 7d |
| **Suspensão temporária CGCRE** | A → A (com flag) | ❌ | ❌ | ❌ | Admin Aferê em resposta a notificação CGCRE |
| **Cancelamento CGCRE** | A → B | ❌ | ❌ | ❌ | Admin Aferê em resposta a cancelamento formal CGCRE |
| **Redução de escopo CGCRE** (não muda perfil) | A → A (escopos em `licencas-acreditacoes` Wave A) | ❌ | ❌ | ❌ | Admin Aferê |
| **Correção administrativa** (qualquer direção) | qualquer | qualquer | qualquer | qualquer | Aprovação Roldão + motivo ≥100 chars + revisão jurídica |

## Cross-reference

- Predicate canônico que consulta esta matriz: `src/infrastructure/authz/perfil_tenant_helper.py::tenant_perfil_e()`.
- Função de mutação: `aplicar_evento_cgcre()` (migration 0008) + `rebaixar_perfil_tenant_voluntario_cliente()` (migration 0009).
- Hook validador desta matriz: `.claude/hooks/feature-perfil-matriz-validator.sh` (T-SAN-PERFIL-038).
- INVs: `REGRAS-INEGOCIAVEIS.md` §INV-TENANT-PERFIL-001..007.

## Como atualizar

1. Toda nova feature crítica que entrar em PRD/ADR DEVE adicionar uma linha aqui ANTES do merge (hook valida).
2. Mudança de comportamento em feature existente (ex: GUM passa de OBRIGATÓRIO para OPCIONAL em algum perfil) exige ADR de remediação + aprovação Roldão.
3. Hook `feature-perfil-matriz-validator.sh` faz grep no diff procurando `US-*` ou `AC-*-N` em paths de PRD/ADR e verifica que a feature está nesta matriz.

## Histórico

- **2026-05-27** — Documento criado em Sprint 3 P5 do saneamento ADR-0067. Cobertura inicial: 14 features-núcleo + 4 camadas de retenção + 6 direções de mudança de perfil.
- **2026-05-30 (M6 escopos-cmc P8 — T-ECMC-071)** — +4 features-núcleo (escopo RBC só A / capacidade interna B/C/D / bloqueio `cobre()` na configuração / U≥CMC na emissão) + 1 camada de retenção (escopo CMC sustenta cert 25a WORM Padrão B). ADR-0073/0074/0075.
- **2026-05-31 (M7 procedimentos P8 — T-PROC-070)** — +2 features-núcleo (procedimento documentado vigente A obrigatório / B-C-D recomendado — 412 `ProcedimentoVigenteAusente`; validação de método cl. 7.2.2 fail-open lazy A) + 1 camada de retenção (procedimento sustenta cert 25a WORM Padrão B). ADR-0073 / INV-PROC-001..010.
- **2026-06-08 (fiscal/NFS-e Fatia 3 — T-FIS-043)** — +2 features-núcleo (documento metrológico por perfil na emissão de NFS-e — A cert RBC/NAO_RBC, B/C cert simples, D declaração, AC-FIS-001-8 cert RBC em B/C → 403; qualificador acreditado na descrição PROIBIDO em B/C/D, "calibração" simples permitida D-FIS-7) + 1 camada de retenção (NFS-e+XML zona B 5a/prudencial 10a). ADR-0008 emenda / ADR-0073/0075 / INV-FIS-001/007/008/009.
- **2026-06-13 (colaboradores P8 — T-COL-060)** — +1 feature-núcleo (papel SIGNATARIO por perfil A/B/C/D: A obrigatório hard / B-C configurável/opcional-recomendado / D desabilitado). AC-COL-03 / INV-COL-SIGNATARIO-IDENTIDADE / INV-COL-SIGNATARIO-ESCOPO / D-COL-11. Achado A8 reviews-consolidado.
- **2026-06-15 (orcamentos T-ORC-039)** — +1 feature-núcleo (template de orçamento com `selo_rbc`: A permitido / B-C-D proibido 422 `SeloRbcNaoPermitido`; gate server-side + hook `orc-template-selo-rbc-check`). US-ORC-005 / D-ORC-13 / INV-ORC-SELO-RBC.
- Próximas revisões cobrirão features Wave A à medida que módulos `certificados`, `licencas-acreditacoes`, `onboarding`, `direitos-titular` forem entregues.
