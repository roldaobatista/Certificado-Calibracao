---
owner: roldao
revisado-em: 2026-05-23
status: stable
finalidade: Catálogo único e vivo de todos os GATEs Wave A do projeto Aferê. Substitui as listas dispersas em 6 arquivos diferentes (F-A/auditoria-familia5.md, F-B/auditoria-familia5.md, M1-clientes/auditoria-familia5.md, M2-equipamentos/auditoria-familia5.md, OS-CAL-RESOLUCAO-rodada-1.md, OS-CAL-RESOLUCAO-rodada-2.md).
fonte: auditoria projeto-inteiro 10 lentes 2026-05-23 (lente 9 — Foundation gaps + auditoria-familia5 dos marcos fechados)
---

# GATEs Wave A — consolidado vivo

> Atualizar este arquivo quando GATE fechar (mover linha para tabela "FECHADOS") ou abrir GATE novo.
> Severidade segue INV-RITUAL-001: GATE bloqueante aberto = Wave A não pode arrancar produtivamente para o item correspondente.

---

## Resumo por categoria (estado em 2026-05-23 pós Onda 1-8 saneamento)

| Categoria | Total | Abertos | Fechados | Em andamento |
|---|---|---|---|---|
| Seguros (SEG-*) | 13 | 12 | 0 | 1 (CAP-1 — DPA Onda 7) |
| LGPD / Jurídico (LGPD-*) | 11 | 9 | 0 | 2 (minutas + cap DPA) |
| Foundation F-A (1-7) | 7 | 7 | 0 | 0 |
| Foundation F-B (FB-1..4) | 4 | 4 | 0 | 0 |
| Marco 1 clientes (CLI-1..8) | 8 | 8 | 0 | 0 |
| Marco 2 equipamentos (EQP-*) | 18 | 17 | 1 | 0 (CVE-WeasyPrint mitigado) |
| ISO 17025 / CGCRE (RBC-*) | 8 | 8 | 0 | 0 |
| Modelo dados / convenções (DOM-*) | 5 | 0 | 5 | 0 (Onda 2 fechou) |
| Bus / integração (BUS-*) | 5 | 4 | 1 | 0 (envelope retrofit Onda 3) |
| Operação / Drill (OPS-*) | 6 | 6 | 0 | 0 |
| **TOTAL** | **85** | **75** | **7** | **3** |

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

### LGPD / Jurídico (9)

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
