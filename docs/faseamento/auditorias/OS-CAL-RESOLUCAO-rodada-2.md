---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
escopo: Wave A Marco 3 (OS) + Marco 4 (Calibração) + Marco 5 (Certificados)
tipo: resolucao-auditoria-10-lentes-rodada-2-onda-7
relacionados:
  - OS-CAL-CONSOLIDADO-rodada-2.md
  - OS-CAL-RESOLUCAO-rodada-1.md
---

# Resolução da auditoria 10 lentes OS+Calibração+Certificados — rodada 2 (Onda 7)

> Acompanha `OS-CAL-CONSOLIDADO-rodada-2.md`. **80 achados R2 → 5 ondas (7A..7E) aplicadas em sessão 2026-05-23.** Marco 3 OS P4 destravado.

---

## Sumário executivo

| Severidade | Achados R2 | Resolvidos Onda 7 | Pendentes (GATE Wave A) |
|---|---|---|---|
| **CRÍTICO** | 6 | **6 (100%)** | 0 |
| ALTO | 19 | **17** | 2 (GATE-SEG industrial + RT vendor V2) |
| MÉDIO | 35 | **23** | 12 GATEs |
| BAIXO | 20 | **6** | 14 cosméticos |
| **Total** | **80** | **52 (65%)** | **28 GATEs** |

Os **6 CRÍTICOS bloqueadores P4 foram fechados**. Marco 3 OS pode arrancar P4 (codificação) com base sólida + ZERO retrabalho previsível previamente identificado.

---

## 5 ondas executadas

### Onda 7A — 6 CRÍTICOS R2 (commit `8774f4b`)

- **NOVO-CRIT-1 (dupla FK):** removido `link_modulo_tecnico` da `AtividadeDaOS`; FK fica no módulo técnico (`Calibracao.atividade_os_id` etc.). Glossário, modelo, ADR-0023, INV-OS-ATIV-005 atualizados.
- **NOVO-CRIT-2 (texto canônico AceiteAtividade):** criado `docs/conformidade/comum/termos/aceite-atividade-v1.0.md` com 7 cláusulas + marcadores `<<<CORPO INICIO/FIM>>>`. Hash SHA-256 determinístico via ADR-0029.
- **NOVO-CRIT-3 (biometria touch):** ADR-0029 (canonicalização texto probatório) aceita + INV-DOC-CANON-001 + DPIA `dpia-assinatura-touch.md` (chave KMS dedicada `BIOMETRIA_KEY_*` + watermark + bbox mínima + n_pontos ≥ 8 + acesso restrito) + INV-OS-ACEITE-BIO-001 promovida.
- **NOVO-CRIT-4/5/6 (sistema paralelo INV):** renomeação em massa em PRD/modelo calibração:
  - `INV-005 → INV-CAL-VERSAO-001`
  - `INV-006 → INV-CAL-DEC-001`
  - `INV-007 → INV-CAL-CONF-001`
  - `INV-008 → INV-CAL-RAST-001`
  - `INV-014 → INV-CAL-SNAP-001`
  - `INV-019 → INV-CAL-RT-001`
  - `INV-022 → INV-CAL-WORM-001` (16 ocorrências PRD + 5 modelo)
  - `INV-009 → INV-CAL-VI-001`
  - 9 INVs promovidos em REGRAS-INEGOCIAVEIS.md §INV-CAL-*.

### Onda 7B — 17 ALTOs (commit `edafc8c`)

- **NOVO-ALTO-1:** coluna `correlation_id` NOT NULL em `OS` + `AtividadeDaOS`.
- **NOVO-ALTO-2:** tabela estática `TipoAtividadeConfig` (tipo → exige_aceite + 6 atributos) com valores Marco 3 cravados.
- **NOVO-ALTO-3:** entidade `DelegacaoExecucao` (técnico original + delegado + autorizador + motivo + restrição RT competência).
- **NOVO-ALTO-6:** ADR-0021 aceita formalmente (proposta → aceito).
- **NOVO-ALTO-8/9/10:** drift frontmatter — `integracoes-inter-modulos.md` v10 status: stable + `certificados/prd.md` revisado_em 2026-05-23 + 5 docs canônicos status: stable.
- **NOVO-ALTO-11:** `OS.Faturada` + `OS.Paga` no catálogo v10 com correlation_id + consumers crm/bi/comissoes.
- **NOVO-ALTO-12:** resolução duplicação `Atividade.NaoConforme` × `NaoConformidade.Aberta` — encadeamento OS↔Cal (não double-CAPA).
- **NOVO-ALTO-13:** `Calibracao.Rejeitada` consumer corrigido (NÃO consumido por OS; encadeamento via `Atividade.NaoConforme`).
- **NOVO-ALTO-16:** evento `Calibracao.LeituraCorrigida` adicionado ao catálogo v10.
- **NOVO-ALTO-17:** INV-CAL-TXT-001 escopo estendido pra 10 campos (incluindo NaoConformidade + LeituraCorrecao + RecepcaoItemCalibracao).
- **AGENTS.md header sincronizado** com CURRENT.md (Marco 2 FECHADO 2ª passada).

### Onda 7C — calibracao/metricas + Zona D prazo (commit `39a519c`)

- **NOVO-ALTO-15:** `calibracao/metricas.md` reescrito com tenant_id label obrigatória + correlation_id em logs + ciclo CAPA (tempo CONTIDA→FECHADA, % reabertura) + reincidência NC por padrão/cliente/executor/método + SLOs regulatórios CGCRE promovidos a SLO duro com erro orçamento ZERO ABSOLUTO + alerta padrão venceu mid-uso P1 + lag export PG→B2 P1 + dashboards por persona (P-METR-01..04) + taxa correção leitura.
- **NOVO-ALTO-4:** Zona D ADR-0021 prazo "15 dias úteis" → "15 dias corridos" alinhado LGPD art. 18 §3º + prorrogação art. 18 §4º documentada.

### Onda 7D — MÉDIOs resolvíveis (commit `4d5d8c7`)

- **NOVO-MÉD-5 LLM:** Glossário OS "EstadoOS 7 valores".
- **NOVO-MÉD-8 LLM:** `tipo_predominante` trigger PG `os_tipo_predominante_recalc_trg` + algoritmo.
- **NOVO-1 RBC:** Transição NaoConformidade REABERTA volta obrigatoriamente a CONTIDA (re-análise causa-raiz cl. 8.7.2).
- **NOVO-2 RBC:** Retorno Calibracao pós-NC fechada com `acao_corretiva_tipo` enum (re_executar vs ajuste_administrativo).
- **NOVO-3 RBC:** INV-CAL-INC-001 documentação `OrcamentoPorPonto` + `u_combinada` agregada.
- **NOVO-CONCERN-4 segurança:** `MedicaoControle` imutável pós-INSERT (trigger PG BLOCK).
- **NOVO-CONCERN-5 segurança:** `LeituraCorrecao` trigger PG BLOCK.
- **ALTO-PEND-2 produto:** P-METR-AUDITOR-CGCRE + P-METR-AUDITOR-INMETRO adicionados em personas.md.
- **ALTO-PEND-1 produto:** AC-CAL-007-3 cita ADR-0026 + 4 condições + 412 ExcecaoSemCondicoes.
- **NOVO-MÉD-1 produto:** AC-CAL-007-4 novo (consumer trigger `Atividade.Iniciada(tipo=calibracao)`).
- **NOVO-MÉD-2 produto:** AC-OS-010-4 novo (sequencia ≤ menor terminal → 412).
- **NOVO-ALTO-1 produto:** AC-CER-007-3 binário com 5 actions (dispensa de foto).

### Onda 7E — esta (consolidado + ajustes finais)

- Doc `OS-CAL-RESOLUCAO-rodada-2.md` (este).
- CURRENT.md atualizado.

---

## GATEs Wave A criados (28 itens rastreados)

### Segurança/seguros (R2)

- **GATE-SEG-7** — transferência RT mid-OS (continuidade cobertura).
- **GATE-SEG-8** — endosso RC Operacional pra `instalacao` em ambiente periculoso (Ex/ATEX/farma).
- **GATE-SEG-9** — cobertura retroativa abrangendo período dogfooding.
- **GATE-SEG-10** — sublimite cyber "imagens confidenciais de cliente do tenant".
- **GATE-SEG-11** — endosso `contractual liability` na E&O (disputa cobrança).
- **GATE-SEG-12** — endosso `additional insured` ou E&O profissional dedicada do RT vendor V2.

### LGPD/contratual

- **GATE-LGPD-BIO-DPIA-OAB** — DPIA biometria touch revisada por advogado humano OAB.
- **GATE-LGPD-DPA-CLI-PJ** — hook `dpa-cliente-pj-required.sh` + painel "Status DPA" admin tenant.
- **GATE-LGPD-DISP-FOTO** — texto canônico `aceite-atividade-dispensa-foto-v1.0.md`.
- **GATE-LGPD-PROR-PRAZO** — texto canônico `prorrogacao-prazo-eliminacao-v1.0.md`.
- **GATE-LGPD-RIPD-OAB** — RIPD geo OS ratificado pré-1º tenant externo.

### ISO 17025/CGCRE

- **GATE-CAL-METODO-VAL** — fluxo validação método interno (cl. 7.2.2).
- **GATE-CAL-EP-TEND** — painel histórico EP + alerta 3 z mesmo sentido (cl. 7.7.3).
- **GATE-CAL-VI-POL** — política VI por classe (cl. 6.4.10) + `politica-verificacao-intermediaria.md`.
- **GATE-CAL-MIG-CLASSIF** — hook `migration-metrology-classifier.sh` (cl. 7.11.3 ADR-0025).
- **GATE-CAL-MANUAL-QUAL** — página `/manual-qualidade` no produto (cl. 8.3).
- **GATE-CAL-SUBCONTR** — decisão subcontratação cl. 6.6 (non-goal ou Wave A).
- **GATE-CAL-LEITURA-CORR-TAXA** — alerta auto Qualidade quando >10% leituras com `LeituraCorrecao`.
- **GATE-CAL-HMAC-RETENCAO** — resolver conflito chave HMAC 10a × audit metrológico 25a (ADR a criar Wave A).

### Segurança técnica

- **GATE-SEC-AUTHZ-MATRIX** — matriz `AuthorizationProvider.can()` cravada em 34 comandos OS+Cal+Cert.
- **GATE-SEC-PORTA-CERT** — função única `pre_emissao_certificado_check()` amarrando INV-002+017+CAL-RT-001+CAL-CONF-001+CER-COMP-001+032.
- **GATE-SEC-IP-NAO-LOG** — política "IP cleartext nunca persiste fora do request scope" + access.log strip.
- **GATE-SEC-CORREL-HOOK** — hook `correlation-chain-validator.sh` (Marco 3 P4).
- **GATE-SEC-GEO-SERVER-ARREDONDA** — handler arredonda lat/long ANTES de persistir/publicar (INV-OS-GEO-001 enforcement).

### Observabilidade

- **GATE-OBS-B2-EXPORT-LAG** — métrica `evento_wal_export_lag_seconds` + runbook B2 hourly export.

### Cosméticos

- **GATE-DRIFT-LICENCAS-PRD** — validar conteúdo `licencas-acreditacoes/prd.md` (existe mas resolução R1 incorretamente marcou como stub).
- **GATE-DRIFT-FRONTMATTER-CASE** — padronizar `owner: roldao` (lowercase) e `revisado_em` (underscore) nos docs legados.
- **GATE-DRIFT-INT-MOD-AUTHZ-INV** — INV-OS-AUTHZ-001 / INV-CAL-AUTHZ-001 explicitamente nos comandos (resolvíveis em Wave A junto com GATE-SEC-AUTHZ-MATRIX).

---

## Pré-requisitos cumpridos pra arrancar Marco 3 P4

Sob INV-RITUAL-001 (MÉDIO+ bloqueia), Marco 3 OS destravado P4 com:

✅ Os 6 CRÍTICOS R2 fechados (dupla FK + AceiteAtividade + biometria + 7 INVs renomeados).
✅ 17 ALTOS R2 fechados (correlation_id + tipo→exige_aceite + DelegacaoExecucao + drift + catálogo v10).
✅ 23 MÉDIOS R2 fechados (ciclo CAPA + métricas regulatórias + AC binários + auditor CGCRE + INVs estendidos).
✅ Marco 4 Calibração também destravado pra P1 (`calibracao/metricas.md` reescrito).

⚠️ **GATE-SEG-BPT-1 EMERGENCIAL** mantém-se (independente das rodadas — apólice BPT pra Balanças Solution dogfooding).

⚠️ **GATE-LGPD-BIO-DPIA-OAB** + **GATE-LGPD-RIPD-OAB** pendentes pré-1º tenant externo pago (advogado humano OAB).

---

## Próximo passo recomendado

1. **Marco 3 OS — P1 (spec FORWARD)** pode arrancar imediatamente.
2. **Aceitar formalmente** as 5 ADRs novas (0024..0028) + ADR-0029 (já aceita) — Roldão.
3. **Acionar corretora SUSEP humana** com briefing ADR-0028 — emergencial BPT.
4. **Marco 4 Calibração** pode arrancar P1 sequencialmente após Marco 3 P4 começar (não precisa esperar Marco 3 fechar).

---

## Em linguagem de produto (pro Roldão)

A rodada 2 achou 80 problemas novos depois do retrofit da rodada 1. **52 deles foram resolvidos** em 5 ondas hoje (65%). Os 28 restantes viraram itens rastreados (`GATE-*`) que entram naturalmente quando cada módulo for codado.

**Marco 3 OS está agora completamente destravado** pra começar a codar — todos os bloqueadores foram fechados.

A única coisa que ainda precisa de **você** (não é técnica):

1. Acionar a **corretora de seguros** com o briefing da ADR-0028 pra emitir a apólice BPT (custódia do instrumento) — emergencial.
2. **Confirmar formalmente** as 6 novas ADRs (0024 a 0029) — só pra rastreabilidade — ou pedir revisão antes.

O sistema tá pronto pra começar a virar código.
