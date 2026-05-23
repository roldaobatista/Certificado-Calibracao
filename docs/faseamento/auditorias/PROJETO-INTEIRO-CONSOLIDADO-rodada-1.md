---
owner: roldao
revisado-em: 2026-05-23
status: stable
escopo: projeto inteiro (F-A, F-B, M1, M2, pre-M3, módulos não implementados)
agentes: 10 lentes paralelas (tech-lead, advogado, RBC, corretora, auditor-produto, auditor-drift-docs, integrações, fases-futuras, foundation-gaps, modelo-dados)
---

# Auditoria projeto inteiro — Rodada 1 (10 lentes)

Data: 2026-05-23. Solicitada por Roldão: "gaps de PRD/modelo de domínio/integrações em TODO PROJETO, desde Foundation F-A/F-B, domínios já implementados, e que ainda não foi implementado".

## Resumo executivo

10 agentes em paralelo, cada um com lente distinta. **Mapeados ~150 achados** distribuídos em:

- **22 CRÍTICOS** (bloqueiam 1º tenant externo OU produzem decisão errada agora)
- **51 ALTOS** (NC alta probabilidade, retrabalho garantido se ignorados)
- **48 MÉDIOS** (drift documental, convenção a unificar)

**Veredito geral:** Foundation+M1+M2 estão **tecnicamente sólidos** (ritual Spec Kit aplicado, 10 auditores Família 5 PASS, hooks 207/207 verdes). Mas o **casco LGPD/contratual está nu** (sem DPA assinado, sem PoP/ToU, sem DPO designado), os **fundamentos transversais não foram consolidados** (vigência temporal com 3 nomes diferentes, soft-delete com 5 padrões, VOs metrológicos ausentes, anonimização sem propagação cross-módulo), e **48 GATEs Wave A** estão dispersos em 6 docs sem owner/prazo. O **bus de eventos publica, mas ninguém consome** (consumer registry zerado, envelope diverge do canônico).

Antes de arrancar Marco 3 OS, recomenda-se 1 onda de saneamento focada em **fechar TOP-15 CRÍTICOS** abaixo (estimativa: 1-2 semanas de trabalho doc + 5 dias código).

---

## TOP 15 CRÍTICOS (priorizados pra fechar antes de Marco 3 P4)

### Bloco A — bloqueia ir a produção / 1º tenant externo

1. **[Jurídico C1+C2+C3] Termo de Uso + Política de Privacidade do Aferê não existem; DPA Aferê↔tenant em draft diferido; DPAs com 7 sub-operadores (AWS/B2/PlugNotas/Lacuna/Anthropic/Grafana/Axiom) não assinados.** Sem isso, mesmo dogfooding Balanças Solution está exposto. Ação: contratar consulta pontual com advogado LGPD/SaaS BR (R$ 8-20k) antes de Wave A vender. [lente 2]

2. **[Jurídico C4] Direitos do titular (LGPD art. 18) só existem em `clientes`.** `equipamentos`, OS futuro, calibração, certificados, billing-saas não têm endpoint/fluxo de portabilidade/eliminação/anonimização. Prazo ANPD = 15 dias corridos. [lente 2]

3. **[Seguros C1+C8] Cláusula contratual de limite de responsabilidade do Aferê AUSENTE no DPA + cobertura BI/RC consequente "perda de acreditação CGCRE do tenant" não negociada.** Cap contratual = ação mais barata e maior impacto financeiro. ADR-0028 trata 5 modalidades; precisa de 7 (acrescentar `Dependent Service BI` + `Accreditation Loss Extension`). [lente 4]

4. **[Foundation gap #1] GATE-SEG-BPT-1 EMERGENCIAL** — apólice BPT (Bens de Terceiros) pra Balanças Solution dogfooding sem owner SUSEP nem prazo. Marco 3 OS começa recebendo equipamentos físicos. [lente 9]

5. **[Foundation gap #2] GATE-EQP-KMS** — AWS KMS MRK real substituindo HMAC versionado em Postgres. Sem isso, comprometimento do DB = comprometimento de TODOS os QRs de TODOS os tenants. [lente 9]

### Bloco B — gera retrabalho garantido se Marco 3+ codar antes

6. **[Modelo C-DT-01] Convenção de vigência temporal é cacofonia:** RT usa `data_inicio_vigencia/data_fim_vigencia/encerrado_em`; RTCompetencia usa `declarado_em/vigente_ate`; Certificado usa `emitido_em/revogado_em`; AGENTS §3 prescreve `(vigencia_inicio, vigencia_fim, revogado_em, motivo_revogacao)` que **nenhuma entidade usa**. Cravar VO `JanelaVigencia` + ADR antes de M3/M4/Cert/Procedimento/Padrão replicarem variantes. [lente 10]

7. **[Modelo C-DT-03] Soft-delete inconsistente** entre clientes (`deletado_em`), equipamentos (estado-máquina), certificados (`revogado_em`), RT (`encerrado_em`). M3 OS vai criar 5ª variante. ADR ditando 3 padrões aceitos + tabela "entidade→padrão" + hook validador. [lente 10]

8. **[Modelo C-DT-04 + Domínio gap #1] FK cross-módulo + anonimização não modelada.** Matriz retenção prevê `cliente_id_original_hash` em Equipamento/Certificado/OS pra cenário B/C ADR-0021, mas **nenhuma migration cria esse campo**. PROTECT na FK vai impedir hard-delete Zona A. Cravar VO `ReferenciaPIIAnonimizavel` agora. [lentes 1, 10]

9. **[Integrações C7-01+C7-02] Envelope do outbox real diverge do envelope canônico documentado.** Real tem `acao, payload, causation_id, tenant_id, usuario_id, resource_summary`; doc v10 exige `event_id, event_name, _schema_version, occurred_at, correlation_id, causation_id, actor, payload`. Hook `bus-envelope-validator.sh` só checa `tenant_id`. Marco 3 não consegue consumir eventos M1/M2 sem refactor. [lente 7]

10. **[Integrações C7-03] Consumer registry zerado.** Marco 1 publicou `Cliente.Bloqueado` (consumer agenda/certificados é GATE-CLI-7/8), Marco 2 publicou 4 eventos de equipamento. **ZERO handlers registrados** → tudo cai em `_noop`. Outbox marca `processado_em` mesmo no _noop, mascarando o gap. [lente 7]

### Bloco C — ISO 17025 / regulatório

11. **[RBC C1+C2+C3] Cláusulas 4.1 (Imparcialidade), 7.1 (Análise crítica de pedidos), 7.2 (Seleção/validação de métodos) AUSENTES** em todo PRD/ADR. CGCRE pergunta na 1ª pergunta de supervisão. Marco 4 calibração ainda não iniciou — momento ideal pra incluir no spec FORWARD. [lente 3]

12. **[RBC C6 + Foundation gap #4] GATE-EQP-RT (carta competência RT humano credenciado NIT-DICLA-021) + dossiê URS/IQ/OQ/PQ ISO 17025 cl. 7.11 ADR-0025 ainda proposta.** Sem isso, tenant RBC NÃO PODE usar Aferê pra emissão acreditada. [lentes 3, 9]

### Bloco D — drift documental que envenena decisão

13. **[Drift C1+C2+C3] ADR-0029 existe mas não está na tabela §11 de AGENTS.md; AGENTS §3 enumera 22 hooks mas existem 25; INDICE.md v8 (17/05) diz "17 ADRs ativas — 0000 a 0017" quando hoje são 30 (0000..0029).** Agente lendo qualquer um desses pode tomar decisão baseada em fact desatualizado. [lente 6]

14. **[Drift C4+C5] PRD raiz + faseamento-modulos.md ambos `status: draft` desde 2026-05-17** apesar de F-A/F-B/M1/M2 fechados em cima. Marco 3 spec FORWARD vai partir de quê? INV-RITUAL-001 exige base estável. [lente 6]

### Bloco E — fases futuras com PRD inviável

15. **[Fases A1 + Produto C1] `fiscal/prd.md` tem 0 US e 0 AC** — só descrição narrativa, mas deadline regulatório 01/09/2026 NFS-e nacional. Marco 3 OS sem `docs/faseamento/M3-os/` (PRD `os` está stable mas spec FORWARD não foi escrita). [lentes 5, 8]

---

## ALTOS agrupados por área (51 achados)

### Modelo de domínio (lente 1) — 5 ALTOS
- `Cliente.deletado_em` não tem `zona_anonimizacao` (ADR-0021); cascade em certificado emitido quebra INV-025.
- Vigência ausente em tarifa/plano, procedimento de calibração, incerteza de padrão.
- Idempotência cross-módulo conceitual: `event_id` + causation explícito sem entidade que persista.
- 3 papéis distintos (técnico_executor, revisor RT, conferente 2ª, signatário A3) viram `Usuario` genérico; sem `DelegacaoExecucao`.
- `certificados/models.py` é stub Marco 2 e precisa 6 campos críticos em Wave A (numero_nit_dicla, regra_decisao, snapshot_acreditacao, signatario_a3_hash, padroes_usados, versao_motor_calculo).

### LGPD/contratual (lente 2) — 6 ALTOS
- Base legal do RT ambígua (obrigação legal vs execução contrato).
- Signatário do certificado não cabe nas 4 finalidades do catálogo.
- Matriz retenção `bus_outbox` só pra Marco 1; M3/M4 vão usar mesmo outbox.
- Transferência internacional AWS us-east-1: "decisão de adequação em construção" sem cláusulas-padrão formalizadas.
- PCI-DSS RAT-16 "delegado a gateway SAQ-A" sem gateway escolhido nem DPA.
- Runbook incidente ANPD existe; drill anual pendente; INV-005 fala "3 dias úteis" mas doc fala "T+72h corridos".

### ISO 17025/RBC (lente 3) — 8 ALTOS
- NIT-DICLA-021 competência por método específico (não só grandeza).
- Substituto do RT / afastamento temporário inexistente.
- Cláusula 7.3 amostragem: zero menção (non-goal não declarado).
- 6.4 equipamentos do lab vs equipamentos do cliente (Marco 2) sem distinção formal.
- 7.4 manuseio: só recepção mapeada; armazenamento durante calibração ausente.
- 7.10 trabalho não conforme: duplicação calibracao.NaoConformidade vs qualidade.NC.
- 7.8.6 regra de decisão "Banded" / Modo W ausente em ADR-0024.
- 8.5/8.8/8.9 auditoria interna + revisão pela direção diferidas pra MVP-2 = NC mínima.

### Seguros (lente 4) — 6 ALTOS
- Cyber R$ 2M agregado para 50+ tenants = abaixo do padrão LGPD.
- Franquia BPT 2% (R$ 40k/evento) alta pra instrumentos.
- D&O cobre Roldão PF mas não cobre RT vendor V2 (ADR-0022).
- Falha NTP/timestamp A3 sem cláusula `time-source integrity defect`.
- E&O `consequential regulatory damages` não nomeia SEFAZ/Receita.
- Billing-saas cobrança indevida sem sublimite `wrongful billing`.

### Produto/AC (lente 5) — 4 ALTOS
- 46/48 PRDs presos em `status: draft` indefinidamente (cravam decisão sem ADR).
- Frontmatter inconsistente em 33/49 PRDs (sem `revisado-em`, owner alterna case).
- AC vs teste mapeado: M1/M2 ótimos; OS/calibração/certificados sem mapeamento TXXX.
- Persona "signatário A3" não declarada.

### Drift docs (lente 6) — 4 ALTOS
- AGENTS.md cabeçalho diz "≤ 250 linhas"; tem 254.
- CURRENT.md prioridade #1 (GATE-SEG-BPT-1) não espelhada em AGENTS §12.
- ADR-0017 vigência jul/2026 sem urgência (janela <2 meses real).
- MEMORY.md `project_session_state` congelado em 2026-05-18 (cita F-B em saneamento; hoje fechado).

### Integrações (lente 7) — 4 ALTOS
- `consumer_idempotencia` documentada no docstring, sem migration.
- Anonimização LGPD NÃO propaga via evento (sem `Cliente.Anonimizado`).
- M3 OS→M4 Cal→Cert sem `_schema_version` declarada; aliases sem registry.
- Saga/compensação "OS cancelada após cert emitido" não modelada.

### Fases futuras (lente 8) — 5 ALTOS
- `financeiro/fiscal` (0 AC; deadline 01/09/2026).
- `financeiro/contas-receber` (0 AC; gateway pagamento gate aberto).
- `financeiro/contas-pagar` (0 AC; sem ADR conciliação OFX).
- `operacao/chamados` (0 AC; relação Chamado→OS indefinida).
- `comercial/orcamentos` (0 AC; conversão Orçamento→OS sem máquina estados).

### Foundation gaps (lente 9) — 8 ALTOS
- INV-CLI-002/SEC-CSV-001 marcados "a criar" em REGRAS mas hooks já existem (drift).
- INV-OS-* (10 INVs) sem hook nenhum; M3 P4 começa sem barreira.
- INV-CAL-* (12 INVs) + INV-CER-FRAUD-A3-001 sem hook.
- CODEOWNERS gap D5: lista `financeiro/auth/tenant/kms/migrations` mas código real está em `src/infrastructure/{authz,multitenant,equipamentos,clientes}` — **nenhum path real está coberto**.
- TODO removível em produção: `clientes/predicates_authz.py:59` aguardando ADR-0015.
- F-B testes específicos (predicate binding, ip_hash HMAC, allowlist anti-PII, rollback-órfão) sem `test_inv_fb_*.py` rastreável.
- GATE-1..5 F-A (B2/WORM, verificação periódica, NTP, ciclo chave PII, hash chain) sem owner/prazo.
- GATE-CLI-7/8 consumers `Cliente.Bloqueado` Wave A — bloqueio só meio-implementado.

### Modelo dados (lente 10) — 5 ALTOS
- VO `Telefone` E.164 inexistente.
- VOs metrológicos ausentes (FaixaMedicao, IncertezaExpandida, Grandeza).
- Matriz retenção sem coluna estruturada `eliminacao_efetiva` vs `anonimizacao_em_lugar` × Zona ADR-0021.
- Ciclo de chave PII por tenant sem job/runbook/dono.
- Timezone do laboratório vs servidor sem regra (lab em fuso diferente quebra cl.7.7).

---

## MÉDIOS (48 achados) — resumo

Drift de número (contagem hooks/auditores/ADRs), VOs faltando (CNPJ alfanumérico, UF, PaisISO, UUIDv7), moeda hardcoded BRL implícito, idioma do certificado (pt vs bilíngue), `unique_doc_ativo` cliente vs cliente_canonico, 18 portas ACL com 15 só doc, dead-letter sem tabela formal, `bus_outbox` worker sem trigger anti-mutation justificado em INV, dispersão de GATEs em 6 arquivos sem dashboard consolidado, suite 621 passed sem cobertura por módulo, `metricas-sucesso.md` não citada nas US dos specs, persona "operador metrologista júnior" não modelada (cl. 6.2), `revisado-em` ausente no template `_TEMPLATE`, `documentos-do-projeto.md` defasado, `validar_*` drills isolados sem cross-fase, "XXX" como ícone em management commands confunde varredura dívida. (Detalhes nos relatórios individuais de cada lente — salvar se necessário em arquivos separados.)

---

## Recomendação de ondas de remediação

### Onda 1 — Saneamento crítico antes de Marco 3 (1 semana doc + 5 dias código)

1. **Doc/legal (paralelo):** abrir DPA + PoP + ToU + designar DPO (consulta paga R$ 8-20k); cravar cap contratual responsabilidade no DPA.
2. **Convenções transversais:** ADR de vigência (`JanelaVigencia` VO + `vigencia_inicio/vigencia_fim/revogado_em/motivo_revogacao` canônico) + ADR de soft-delete (3 padrões) + VO `ReferenciaPIIAnonimizavel` + retrofit RT/Cert/RTCompetencia.
3. **Bus de eventos:** retrofit envelope canônico (event_id, _schema_version, correlation_id, actor, occurred_at); criar tabela `consumer_idempotencia` (migration); estender `bus-envelope-validator.sh`; registrar handler dummy logado em cada consumer GATE-CLI-7/8.
4. **Drift docs:** atualizar AGENTS §11 com ADR-0029; corrigir §3 enumeração de hooks; promover PRD raiz + faseamento-modulos pra `stable`; atualizar INDICE.md + documentos-do-projeto.md + MEMORY.md (`project_session_state`).
5. **CODEOWNERS:** retrofit pra cobrir `src/infrastructure/{authz,multitenant,equipamentos,clientes,certificados,responsavel_tecnico}/` reais.

### Onda 2 — Marco 3 OS pode arrancar com base sã (paralelo a P1-P2 de M3)

6. Criar hooks INV-OS-* (5 hooks): `os-conclusao-todas-terminais-check`, `biometria-key-validator`, `os-geo-precision-check`, `termo-canonicalizacao-check`, `enum-tipo-atividade-fechado`.
7. Preencher US/AC do `fiscal/prd.md` (deadline 01/09/2026 ≈ 14 semanas).
8. Decidir gateway pagamento (Asaas/Iugu/Gerencianet) → ADR.
9. Spec FORWARD do M3 OS deve referenciar `JanelaVigencia` + `ReferenciaPIIAnonimizavel` + envelope canônico v10.
10. ADR-0021 (anonimização) sair de proposta → aceito; matriz retenção retrofitada com coluna Zona A/B/C.

### Onda 3 — Pré-Marco 4 calibração (antes de codar)

11. ADR-0024/0025/0026 sair de proposta → aceito.
12. Incluir cl. 4.1 (imparcialidade), 7.1 (análise crítica), 7.2 (validação métodos), 7.3 (amostragem non-goal), 7.4 (manuseio durante cal), 8.5/8.8/8.9 (audit interna + revisão direção) no spec FORWARD M4.
13. Reconciliar `calibracao.NaoConformidade` vs `qualidade.NC` (ADR transversal).
14. Cravar VOs metrológicos (`FaixaMedicao`, `IncertezaExpandida(k,nivel_conf)`, `Grandeza`).
15. Contratar carta competência RT humano CGCRE (GATE-EQP-RT).

### Onda 4 — Pré-1º tenant externo pago

16. Reanalisar ADR-0028: expandir pra 7 modalidades (acrescentar `Dependent Service BI` + `Accreditation Loss Extension`); subir Cyber pra R$ 5M agregado + reinstatement.
17. Implementar AWS KMS MRK real (GATE-EQP-KMS).
18. Pentest timing-oracle Mann-Whitney 1000 amostras (GATE-EQP-PENTEST).
19. Drill ANPD anual (drill obrigatório).
20. Job rotação chave PII por tenant + runbook + dono.

---

## Lentes individuais (referências)

Cada agente produziu relatório próprio. Para detalhe, ver:

| # | Lente | Achados (C/A/M) | Agente |
|---|-------|-----------------|--------|
| 1 | Modelo domínio cross-fase | 4 / 5 / 5 | tech-lead-saas-regulado |
| 2 | LGPD + contratual | 4 / 6 / 8 | advogado-saas-regulado |
| 3 | ISO 17025 / NIT-DICLA / RBC / VIM | 6 / 8 / 7 | consultor-rbc-iso17025 |
| 4 | Risco/seguro coberto | 8 / 6 / 5 | corretora-seguros-saas |
| 5 | AC binários + scope + glossário | 3 / 4 / 4 | auditor-produto |
| 6 | Drift entre docs canônicos | 5 / 4 / 6 | auditor-drift-docs |
| 7 | Integrações inter-modulares | 3 / 4 / 4 | general-purpose |
| 8 | Fases não implementadas | 0 / 5 / 4 | general-purpose |
| 9 | Foundation gaps + GATEs + INVs | 5 / 8 / 5 | general-purpose |
| 10 | Modelo de dados transversal | 4 / 5 / 4 | general-purpose |
| **Total** | | **42 / 55 / 52** | 10 agentes |

(Diferença vs total no resumo: alguns achados se sobrepõem entre lentes — agregados por causa-raiz.)
