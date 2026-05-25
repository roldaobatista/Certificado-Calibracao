---
owner: corretora-seguros-saas
revisado_em: 2026-05-25
status: stable
tipo: review-p2-corretora
marco: Wave A Marco 4 — metrologia/calibracao
fase-ritual: P2
spec-revisada: docs/faseamento/M4-calibracao/spec.md
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/adr/0028-mapa-coberturas-wave-a.md
  - docs/adr/0019-responsabilidade-codigo-agente-ia.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
selo: "PRÉ-COTAÇÃO — NÃO EMITE APÓLICE. REQUER CORRETORA SUSEP CREDENCIADA (Lei 4.594/64 + Res. CNSP)"
---

# Parecer — Corretora Seguros (P2 ritual Spec Kit, Marco 4 `metrologia/calibracao`)

## Sumário executivo

- **Decisão geral:** **AJUSTAR.** A spec.md M4 é tecnicamente robusta sob lente de risco segurável (versão motor cravada, replay determinístico, hash-chain WORM 25a, snapshot de padrão, 2ª conferência objetiva, subcontratação cl. 6.6 com aceite assinado). Mas o M4 introduz **6 vetores de dano novos** que a ADR-0028 rev 2 NÃO cobre explicitamente, todos amarrados em modalidades 1/2/3/4/7 do mapa Wave A. Marco 4 não pode entrar em produção dogfooding-only Balanças Solution sem 3 gates seguráveis novos (GATE-SEG-EO-CAL-1 + GATE-SEG-D&O-CRIMINAL-1 + GATE-SEG-BPT-PADROES-1).
- **10 achados reais** (P-CAL-S1..S10): **0 BLOQUEANTES**, **5 ALTOS** (AJUSTADO), **4 MÉDIOS** (AJUSTADO), **1 MÉDIO** (ACEITE rastreado).
- **Não há BLOQUEANTE de fechamento M4** porque M4 sai dogfooding-only e GATE-SEG-BPT-1 já foi cravado como bloqueio do M3 (P-OS-S1). Mas há **4 cláusulas novas** que precisam entrar em ADR-0028 rev 3 antes do 1º tenant externo pago.
- **Aviso legal obrigatório:** este parecer é consultivo. Nenhuma cobertura, capital, franquia, sublimite ou cláusula constitui contrato de seguro. **Lei 4.594/64 + Resoluções CNSP exigem corretora SUSEP credenciada humana pra cotar, intermediar e emitir apólice.** Todo achado abaixo carrega `🔴 REQUER CORRETORA SUSEP` quando depende de negociação humana com seguradora.

---

## Tabela severidade

| ID | Tema | Severidade | Decisão | Modalidade ADR-0028 |
|---|---|---|---|---|
| P-CAL-S1 | Software validation defect cobre cálculo de incerteza (cl. 7.11) + vicarious cliente-final-do-tenant farma | ALTO | AJUSTAR | 1 (E&O) + 7 (Accreditation Loss) |
| P-CAL-S2 | Subcontratação cl. 6.6 — erro do laboratório subcontratado cascateia contra Aferê | ALTO | AJUSTAR | 1 (E&O) + 6 (CBI Dependent Service) |
| P-CAL-S3 | Chave HMAC corrompida em 2052 inviabiliza prova metrológica (ADR-0064) | ALTO | AJUSTAR | 2 (Cyber) + cláusula nova |
| P-CAL-S4 | Recall em massa de N certificados via proficiência UNACCEPTABLE → D&O do admin do tenant | ALTO | AJUSTAR | 3 (D&O) + 7 (Accreditation) |
| P-CAL-S5 | Fraude criminal `executor_id=user` bypass — falsidade CP art. 297 (cert metrológico tem fé pública?) | ALTO | AJUSTAR | 3 (D&O — defesa criminal) |
| P-CAL-S6 | Padrão metrológico próprio extraviado/danificado (R$ 50k-500k cada) — BPT cobre só "bens de terceiros" | MÉDIO | AJUSTAR | 4 (BPT) → modalidade nova 8 (Property — Equipamentos Metrológicos) |
| P-CAL-S7 | RecepcaoItemCalibracao foto com etiqueta de paciente farma (cliente farma do tenant) — vazamento de PII de terceiro categoria especial saúde | MÉDIO | AJUSTAR | 2 (Cyber — cláusula art. 11 já existe; estender pra third-party patient data) |
| P-CAL-S8 | AceiteSubcontratacao texto canônico OAB-pendente — cliente alega "nunca consenti" → indenização contratual | MÉDIO | AJUSTAR | 1 (E&O — wrongful consent capture) |
| P-CAL-S9 | 2ª conferência exceção abusiva (ADR-0026 5%/mês) — CGCRE suspende acreditação do tenant | MÉDIO | AJUSTAR | 3 (D&O do admin do tenant) + 7 (Accreditation Loss) |
| P-CAL-S10 | Replay determinístico divergência 0.1%-1% emite cert e depois descobre erro — recall (Marco 5) | MÉDIO | ACEITE rastreado (Marco 5 cobre via ADR-0045) | 1 (E&O) + 7 (Accreditation) |

---

## Achados

### P-CAL-S1 — Software validation defect cobre cálculo de incerteza + vicarious cliente-final-do-tenant farma [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** spec §3.2 OrcamentoIncerteza + ADR-0025 (validação software cl. 7.11) + spec §8 R-M4-01 (motor diverge entre versões) + spec §6.1 evento `Calibracao.Aprovada` → Marco 5.

**Análise.** Spec §3.2 crava `versao_motor_calculo` em `OrcamentoIncerteza` + `replay_determinismo_hash` + `segundo_caminho_calculo_divergencia_pct` (alerta 0.1%, bloqueio 1%). Tecnicamente é o melhor estado da arte ISO 17025 cl. 7.11. **Mas o vetor de dano segurável passa por cascata multi-elo:**

1. Bug no motor de cálculo passa entre 0.1% e 1% (alerta P3, não bloqueia) por meses.
2. Cert é emitido com `U_expandida` levemente errado.
3. Tenant (laboratório acreditado) entrega cert ao **cliente farma** do tenant.
4. Cliente farma usa balança calibrada errada → fabrica lote fora de spec → ANVISA recall lote → lote no mercado → consumidor lesado.
5. **Consumidor processa cliente farma → cliente farma processa tenant → tenant subroga contra Aferê.**

ADR-0028 Modalidade 1 já tem `software validation defect causing accreditation suspension` + sublimite `pharmaceutical/food recall extension` R$ 3M. **MAS:** a cláusula nomeia `accreditation suspension` como gatilho. Se o tenant **NÃO perdeu acreditação** (CGCRE não auditou ainda), mas o dano cascateou via consumidor → cliente farma → tenant, a seguradora pode argumentar "fato gerador não está coberto (accreditation suspension não ocorreu)". Lacuna de wording.

A cláusula tech do M3 P-OS-S4 (`software validation defect cobre vetores upstream`) cobre M3→M4. **Falta wording que cubra M4→cliente-final-do-tenant→consumidor-final** (4 elos de cascata, sendo o 4º elo ANVISA).

**Cláusula proposta (wording em inglês de mercado):**

```
Software measurement defect — multi-tier vicarious liability extension:
"Coverage extends to consequential damages arising from a defective
measurement, calculation, or uncertainty budget produced by the Insured's
software, irrespective of whether the Insured's tenant has had its
accreditation suspended, and including third-party claims brought by
end-customers of the Insured's tenants (B2B2C cascade), provided the
defective measurement is traceable to the Insured's software version
identifier (semver + commit hash) and replay-deterministic hash recorded
in the Insured's WORM audit trail."
```

**Modalidade:** 1 (E&O ampliado) + 7 (Accreditation Loss — wording paralelo).
**Sub-aggregate sugerida:** R$ 3M por evento (mantém pharmaceutical recall sublimit).
**Franquia sugerida:** R$ 25k por evento (mantém Modalidade 1).
**Gate:** GATE-SEG-EO-CAL-1 (NOVO) — bloqueia 1º tenant externo farma/saúde pago.

**Caso narrativo pra seguradora:**
"Em 2027, o motor de cálculo do Aferê tem regressão no termo de Welch-Satterthwaite que faz `U_expandida` sair 0,4% maior que o correto. Alerta P3 (>0,1%) é gerado mas não bloqueia. Em 6 meses, 200 certs são emitidos pra lab calibrador de farma. Em 2028, ANVISA inspeciona fábrica do cliente farma, identifica lote fora de spec, recall R$ 8M. Cliente farma processa o lab tenant (R$ 5M). Lab tenant aciona Aferê em subrogação alegando defeito de software comprovável via `replay_determinismo_hash`. Acreditação CGCRE do lab tenant **ainda não foi suspensa** (auditoria de supervisão programada pra 2029). Apólice cobre?"

🔴 REQUER CORRETORA SUSEP — wording `multi-tier vicarious` é incomum em E&O Brasil; provavelmente Marsh/AON/Howden com tradução de wording internacional.

**Ação spec.md:** §8 R-M4-01 estender mitigação com `+ cobertura E&O Modalidade 1 cláusula software measurement defect multi-tier vicarious (GATE-SEG-EO-CAL-1) + Accreditation Loss Modalidade 7`. §9.1 adicionar GATE-SEG-EO-CAL-1.

---

### P-CAL-S2 — Subcontratação cl. 6.6 — erro do laboratório subcontratado cascateia contra Aferê [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** spec §3.2 `LaboratorioSubcontratado` + `AceiteSubcontratacao` + spec §5.1 INV-CAL-SUBC-001..004 + US-CAL-017.

**Análise.** Spec inova ao cravar US-CAL-017 com 6 AC novos (1 das maiores novidades vs M3). Mas o vetor segurável é complexo:

1. Balanças Solution (tenant) recebe instrumento que excede CMC.
2. Subcontrata lab acreditado X (registrado em `LaboratorioSubcontratado`).
3. Cliente assina `AceiteSubcontratacao` (texto canônico).
4. Subcontratado calibra ERRADO (bug do subcontratado, NÃO da Aferê).
5. Subcontratado entrega cert externo → Balanças Solution embute no cert final declarando "calibrado por <subcontratado>" (cl. 6.6.2 + ILAC G18).
6. Cliente do tenant processa o tenant. **Quem responde?**
   - CC art. 932 III: responsabilidade do empregador por preposto.
   - CC art. 1023: solidariedade sociedades.
   - CDC art. 25 §1º: responsabilidade solidária na cadeia.
   - **O tenant é solidariamente responsável pelo erro do subcontratado** (cl. 6.6.4 ISO 17025 também — "the laboratory shall remain responsible").
7. Tenant subroga contra subcontratado E contra Aferê (porque o fluxo de subcontratação foi gerido pela plataforma).

**Lacuna ADR-0028:** Modalidade 1 (E&O) cobre erro do Aferê, não erro do **subcontratado do tenant** orquestrado via plataforma Aferê. A `vicarious liability — tenant operative on-site OR tenant administrative decision via platform` (rev 2) cobre **tenant on-site OU decisão administrativa do tenant**. **Não cobre subcontratado do tenant** (entidade fora do tenant).

A Modalidade 6 (CBI Dependent Service) lista AWS/B2/PlugNotas/Lacuna como sub-operadores nomeados. **Lab subcontratado** do tenant não está nessa lista — e nem deveria, pois CBI cobre indisponibilidade, não erro técnico.

**Cláusula proposta:**

```
Sub-contracted service quality liability — laboratory cl. 6.6 extension:
"Coverage extends to vicarious liability arising from measurement errors,
incorrect calibration, or improper accreditation scope coverage performed
by a third-party laboratory sub-contracted by the Insured's tenant via
the Aferê platform's subcontracting workflow (US-CAL-017), provided the
sub-contractor was selected from the tenant's registered LaboratorioSubcontratado
catalog and the AceiteSubcontratacao with biometric/A3 client signature
is on record. The Insurer's right of subrogation against the sub-contractor's
own E&O policy is preserved."
```

**Modalidade:** 1 (E&O ampliado) + 6 (CBI Dependent Service — paralelo, cobre indisponibilidade do subcontratado).
**Sub-aggregate sugerida:** R$ 1M por evento (separado do sublimite recall farma).
**Franquia sugerida:** R$ 50k por evento (alta, pra desincentivar sub-uso).
**Direito de regresso:** explicitar que seguradora SUBROGA contra apólice E&O do subcontratado.

**Caso narrativo:**
"Balanças Solution subcontrata Lab ACME pra calibrar manômetro fora do CMC. Lab ACME tem apólice E&O própria R$ 500k. Lab ACME calibra errado, cliente farma do tenant processa o tenant em R$ 2M. Tenant processa Aferê alegando que o fluxo de subcontratação não validou competência do Lab ACME corretamente. Apólice Aferê cobre R$ 2M MENOS R$ 500k (regresso contra apólice ACME)?"

🔴 REQUER CORRETORA SUSEP — cláusula de subrogação ativa contra terceiro é delicada; corretora precisa cotar.

**Ação spec.md:** §8 adicionar R-M4-18 NOVO ("erro do subcontratado cascateia → Aferê responsável solidário"). Mitigação: predicate `subcontratado_vigente_para` + INV-CAL-SUBC-002 + cobertura E&O cláusula sub-contracted quality (GATE-SEG-SUBC-1). §9.1 adicionar GATE-SEG-SUBC-1.

---

### P-CAL-S3 — Chave HMAC corrompida em 2052 inviabiliza prova metrológica (ADR-0064) [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** spec §2.2 VO `HashVersionado` + ADR-0064 + spec §3.2 `EventoDeCalibracao.evento_hash` + INV-HMAC-001..005.

**Análise.** Spec §3.2 crava `evento_hash CHAR(80)` com formato `v<NN>$<base64>` (rotação anual + KMS Multi-Region histórico 25a). ADR-0064 garante DISABLED_BUT_RETAINED por 25a + GATE-KMS-IAM-LOCK bloqueando ScheduleKeyDeletion. **Mas o vetor segurável de longuíssima cauda é:**

1. Em 2027, cert é emitido com `evento_hash` gerado por `HMAC_KEY_v07`.
2. Em 2052 (25 anos depois), CGCRE auditor pede verificação probatória.
3. **Chave `HMAC_KEY_v07` foi corrompida em 2041** (incidente AWS KMS, ransomware Aferê, erro IAM, etc.) **e não pode mais ser usada pra verificar HMAC**.
4. Cert não pode ser provado autêntico → cliente farma do tenant não pode provar conformidade lote 2027 → lote retroativamente questionado → recall histórico → indenizações cascateadas.

**Lacuna ADR-0028:** Modalidade 1 (E&O) tem `Long-tail data custody — 25 years` mas cobre **custódia do dado** (B2 WORM), não **integridade criptográfica da prova**. Cyber Modalidade 2 tem `time-source integrity defect` (NTP/timestamp A3) mas não cobre **HMAC key integrity defect**.

**Cláusula proposta:**

```
Cryptographic proof integrity defect — long-tail metrological evidence:
"Coverage extends to consequential damages arising from the inability
to cryptographically verify a previously-issued metrological certificate
due to corruption, loss, or unauthorized disablement of the HMAC key
material retained for ISO 17025 cl. 8.4 25-year evidentiary period,
provided the Insured maintained KMS Multi-Region key replication
(documented in ADR-0064) and the documented retention/rotation policy
was followed at the time of certificate issuance."
```

**Modalidade:** 2 (Cyber) + cláusula nova específica.
**Sub-aggregate sugerida:** R$ 2M por evento (compartilha sublimite Cyber).
**Franquia sugerida:** R$ 50k por evento (alta — incidente raríssimo).
**Gate:** GATE-SEG-CYBER-HMAC-1 (NOVO).

**Caso narrativo:**
"Em 2052, auditoria CGCRE pede verificação probatória de cert emitido em 2027. KMS Multi-Region da Aferê sofreu incidente em 2041 que corrompeu `HMAC_KEY_v07`. Apólice cobre danos retroativos?"

🔴 REQUER CORRETORA SUSEP — cláusula long-tail crypto é hiper-incomum; provavelmente exige Lloyd's via Marsh/AON.

**Ação spec.md:** §8 R-M4-08 estender com `+ cobertura Cyber Modalidade 2 cláusula cryptographic proof integrity defect (GATE-SEG-CYBER-HMAC-1)`. §9.1 adicionar GATE-SEG-CYBER-HMAC-1.

---

### P-CAL-S4 — Recall em massa de N certs via proficiência UNACCEPTABLE → D&O do admin do tenant [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** spec §3.2 `AnaliseImpactoNCProficiência` + spec §5.1 INV-CAL-NC-PT-001 + spec §8 R-M4-09.

**Análise.** Spec inova ao cravar `AnaliseImpactoNCProficiência` como entidade WORM imutável (cl. 7.7.2). Dispara automaticamente quando rodada PT marca UNACCEPTABLE; gestor de qualidade decide cert-a-cert (RECALL/SUSPENSAO/SEM_IMPACTO). **Vetor segurável:**

1. Tenant participa de PT, resultado UNACCEPTABLE (escore-z > 3).
2. `AnaliseImpactoNCProficiência` lista 200 certs no período afetado.
3. Gestor de qualidade decide 50 RECALL + 100 SUSPENSAO + 50 SEM_IMPACTO.
4. **Cliente farma do tenant detecta 1 cert recalled foi usado em lote em mercado** → ANVISA recall lote.
5. **Sócio/admin do tenant** é citado pessoalmente por ANVISA + processado civilmente por má gestão (CC art. 1016 — administrador responde pessoalmente por culpa).
6. Apólice D&O do tenant **não cobre Aferê** (é cobertura do tenant); apólice D&O Aferê **cobre só Roldão PF até RT vendor V2** (ADR-0028 Modalidade 3).
7. Tenant subroga contra Aferê: alega que a plataforma deveria ter bloqueado emissão se PT venceu há mais de N meses; alega falha de governança Aferê.

**Lacuna ADR-0028:** Modalidade 3 (D&O) cobre Roldão PF. Não cobre **defesa civil do admin do tenant** que está processando Aferê — isso seria coberto pela E&O Aferê (defesa contra terceiros). **Mas:** se o admin do tenant é processado **criminalmente** (CP art. 297 falsidade documento público — cert metrológico tem fé pública no SBM), apólice E&O Aferê **não cobre defesa criminal**.

Wording E&O Brasil padrão exclui criminal defense ("excluded acts: criminal, fraudulent, willful misconduct").

**Cláusula proposta:**

```
Investigation defense — tenant administrator vicarious claim:
"Coverage extends to investigation costs and civil defense fees in actions
brought by tenant administrators (sócios, diretores, RT) who allege that
defective platform governance contributed to the regulatory event
triggering their personal civil liability under CC art. 1016 or
administrative sanction by ANVISA, INMETRO, or CGCRE. Criminal defense
expressly excluded; see Modality 3 (D&O) for Insured's own administrator
criminal investigation costs."
```

**Modalidade:** 1 (E&O — investigação civil) + 3 (D&O Aferê — Roldão PF).
**Sub-aggregate sugerida:** R$ 500k por evento (defesa).
**Franquia sugerida:** R$ 15k por evento.
**Gate:** GATE-SEG-EO-INVEST-1 (NOVO).

**Caso narrativo:**
"PT 2027 do tenant Lab Beta marca UNACCEPTABLE retroativo. Aferê dispara `AnaliseImpactoNCProficiência` listando 80 certs. Gestor Lab Beta decide 30 RECALL. Cert RECALL foi usado em medicamento controlado, ANVISA recall lote, sócio Lab Beta indiciado civilmente. Sócio Lab Beta processa Aferê alegando falha de governança. Apólice cobre defesa civil + indenização?"

🔴 REQUER CORRETORA SUSEP — cláusula "investigation defense — tenant administrator vicarious" é wording híbrido E&O+D&O; corretora precisa estruturar.

**Ação spec.md:** §8 R-M4-09 estender com `+ cobertura E&O Modalidade 1 cláusula investigation defense — tenant administrator vicarious (GATE-SEG-EO-INVEST-1)`. §9.1 adicionar GATE-SEG-EO-INVEST-1.

---

### P-CAL-S5 — Fraude criminal `executor_id=user` bypass — falsidade CP art. 297 [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** spec §5.1 INV-CAL-FRAUDE-EXEC-001..COR-001 + spec §3.2 validação `executor_id == request.user.id`.

**Análise.** Spec crava 4 anti-fraude técnicos (INV-CAL-FRAUDE-EXEC/REV/CONF/COR-001). Tecnicamente é o melhor estado da arte — predicate em authz + teste E2E DRILL-FRAUDE-CAL-1..4. **Mas o vetor segurável é criminal:**

1. Técnico mal-intencionado engenha bypass (ex: explora bug em sessão MFA, social engineering, captura A3 de colega).
2. Emite cert metrológico fraudulento (cert SEM medição real ou com dado manipulado).
3. Cliente do tenant detecta a fraude (auditoria interna, denúncia anônima).
4. Cliente do tenant denuncia ao MP → MP indicia técnico **+ sócio do tenant** (responsabilização por omissão).
5. Tenant subroga contra Aferê alegando "anti-fraude técnico devia ter bloqueado" (falha de produto).
6. **Cert metrológico tem fé pública (Lei 5.966/73 — SBM)** → CP art. 297 (falsidade de doc público — 2 a 6 anos reclusão).
7. **Apólice E&O exclui willful misconduct** (ato doloso) — atendente é doloso, mas tenant alega que Aferê falhou em prevenir.

**Lacuna ADR-0028:** Modalidade 3 (D&O) cobre Roldão PF mas **não cobre defesa criminal de admin do tenant** sendo processado por omissão pós-fraude do funcionário do tenant.

**Cláusula proposta:**

```
Wrongful platform design — fraud prevention defect:
"Coverage extends to civil indemnification claims (excluding criminal
defense, which falls under Modality 3 D&O) arising from a tenant
administrator's allegation that the Insured's anti-fraud predicates
(INV-CAL-FRAUDE-EXEC/REV/CONF/COR-001) failed to prevent a fraudulent
metrological certificate issued by a tenant employee, provided the
Insured's own employees, contractors, or sub-agents did not knowingly
participate in or facilitate the fraud."
```

**Modalidade:** 1 (E&O — defesa civil) + 3 (D&O — defesa criminal Roldão PF apenas).
**Sub-aggregate sugerida:** R$ 1M por evento.
**Franquia sugerida:** R$ 25k por evento.
**Gate:** GATE-SEG-EO-FRAUDE-1 (NOVO).

**Caso narrativo:**
"Em 2028, técnico do tenant Lab Gamma captura sessão MFA do colega, emite 5 certs fraudulentos pra cliente farma. MP indicia técnico + sócio Lab Gamma. Sócio Lab Gamma processa Aferê civilmente em R$ 3M alegando que `INV-CAL-FRAUDE-EXEC-001` falhou. Apólice cobre defesa civil + indenização?"

🔴 REQUER CORRETORA SUSEP — interseção E&O × criminal × vicarious é complexa.

**Ação spec.md:** §8 adicionar R-M4-19 NOVO ("fraude criminal técnico → omissão admin tenant → subrogação Aferê"). Mitigação: 4 INV-CAL-FRAUDE-* + drill DRILL-FRAUDE-CAL-1..4 + cobertura E&O Modalidade 1 (GATE-SEG-EO-FRAUDE-1). §9.1 adicionar GATE-SEG-EO-FRAUDE-1.

---

### P-CAL-S6 — Padrão metrológico próprio (R$ 50k-500k) — BPT cobre só "bens de terceiros" [MÉDIO]

**Severidade:** MÉDIO (AJUSTADO).
**Lente:** spec §2.1 ADR-0040 (padrão metrológico entidade separada) + spec §3.2 `PadraoMetrologico`.

**Análise.** ADR-0040 separa padrão metrológico como entidade própria (módulo `padroes`). Padrões valem R$ 50k (jogo pesos OIML F1) a R$ 500k (paquímetro digital classe master, célula de carga referência). **Vetor segurável:**

1. Padrão da Balanças Solution é furtado do lab (entrada arrombada).
2. Padrão da Balanças Solution é danificado em transporte interno (queda).
3. Padrão da Balanças Solution é extraviado em recal externo (lab terceiro perde).

**Lacuna ADR-0028:** Modalidade 4 (BPT — Bens em Poder de Terceiro) cobre apenas **bens DE TERCEIROS em poder do segurado** (instrumento do cliente recebido pra calibração). **Não cobre bens próprios** do segurado.

Apólice tradicional brasileira pra **bens próprios** = Modalidade Compreensiva Empresarial (multirrisco) ou **Equipamentos Eletrônicos** (cobre eletrônica precisão). Balanças Solution pode ter apólice corporativa multirrisco que já cobre — Roldão precisa verificar.

**Cláusula proposta (modalidade NOVA 8):**

```
Modality 8 — Owned Metrological Standards Property Coverage:
Coverage: Direct physical loss or damage to metrological standards
(pesos, instrumentos de referência, padrões master) owned by the Insured
and registered in the PadraoMetrologico entity, including in-transit
loss during external recalibration cycles.
Capital per item: declared by serial number, up to R$ 500k per item.
Capital per event: R$ 1M.
Deductible: 5% of declared value, minimum R$ 5k.
Sub-clauses:
  - Transit coverage Brazil-wide (external recal at accredited laboratories)
  - Sub-rogation against carrier preserved
  - Theft requires polícia judiciária BO + tenant CFTV evidence
```

**Modalidade:** 8 NOVA (Property — Owned Metrological Standards).
**Sub-aggregate sugerida:** R$ 1M por evento.
**Franquia sugerida:** 5% valor declarado, mínimo R$ 5k.
**Gate:** GATE-SEG-BPT-PADROES-1 (NOVO).

**Caso narrativo:**
"Em 2027, padrão master célula de carga R$ 350k da Balanças Solution é danificado em queda do transportador no recal externo Inmetro Xerém. Apólice BPT atual cobre? (resposta esperada: não, é bem próprio)."

🔴 REQUER CORRETORA SUSEP — pode ser endossamento em apólice multirrisco existente da Balanças Solution; corretora consolida.

**Ação spec.md:** §8 adicionar R-M4-20 NOVO ("padrão próprio extraviado/danificado"). Mitigação: cobertura Modalidade 8 NOVA (GATE-SEG-BPT-PADROES-1) + alternativamente endosso apólice corporativa Balanças Solution. §9.1 adicionar GATE-SEG-BPT-PADROES-1.

---

### P-CAL-S7 — Foto RecepcaoItemCalibracao com etiqueta paciente farma — PII categoria especial saúde [MÉDIO]

**Severidade:** MÉDIO (AJUSTADO).
**Lente:** spec §3.2 `RecepcaoItemCalibracao.foto_evidencia_id` + spec §2.4 DPIA + spec §10 G2 (sanitizador).

**Análise.** Spec §3.2 prevê foto opcional na recepção (cliente pode recusar). DPIA pendente cita "strip EXIF obrigatório". **Mas:** instrumento de cliente farma (ex: balança analítica de farmácia hospitalar, dosador de medicamento) pode ter **etiqueta com nome de paciente, RG, leito, prontuário** (em hospital, instrumento é dedicado a setor que dosa medicamento controlado por paciente). Foto captura etiqueta → LGPD art. 11 dado especial **SAÚDE de terceiro** (paciente do hospital cliente do tenant).

**Lacuna ADR-0028:** Modalidade 2 (Cyber) rev 2 já tem `sensitive personal data — LGPD art. 11 (biometric, racial, **health**, religion) — affirmative coverage, no sub-aggregate restriction` (P-OS-S2). **Cobre.** Mas cobre **dado biométrico de profissional do tenant** (caso M3). Aqui é diferente: **dado de saúde de PACIENTE do cliente farma do tenant** (4 elos de cascata).

Wording precisa estender pra third-party patient data captured incidentally.

**Cláusula proposta:**

```
Sensitive personal data — extended third-party scope:
"Coverage under the sensitive personal data clause (LGPD art. 11)
extends to incidental capture of health, biometric, or sensitive
identifying data of patients, customers, or other third parties of
the Insured's tenants, when such capture occurs through the platform's
photo evidence, document scan, or instrument label workflows
(RecepcaoItemCalibracao, EvidenciaFotoAtividade), provided the
Insured implemented documented EXIF stripping and PII redaction
controls (INV-CAL-TXT-001 + INV-OS-FOTO-001)."
```

**Modalidade:** 2 (Cyber — estensão).
**Sub-aggregate sugerida:** R$ 1M por evento (compartilha com sensitive data Modalidade 2).
**Franquia sugerida:** R$ 15k por evento.
**Gate:** GATE-SEG-CYBER-PATIENT-1 (NOVO).

**Caso narrativo:**
"Em 2027, lab hospitalar (tenant) envia balança analítica de oncologia pra calibração na Balanças Solution. Operador fotografa instrumento sem strip etiqueta com nome paciente quimioterapia + dose. Foto é armazenada em B2. ANPD multa Aferê R$ 800k. Apólice cobre?"

🔴 REQUER CORRETORA SUSEP — extensão "third-party patient data via tenant" não é wording de mercado padrão.

**Ação spec.md:** §2.4 DPIA estender com "strip EXIF + redação OCR de etiqueta visível (preview UX 'cobrir etiquetas de paciente')". §8 adicionar R-M4-21 NOVO. §9.1 adicionar GATE-SEG-CYBER-PATIENT-1.

---

### P-CAL-S8 — AceiteSubcontratacao texto canônico OAB-pendente — cliente alega "nunca consenti" [MÉDIO]

**Severidade:** MÉDIO (AJUSTADO).
**Lente:** spec §3.2 `AceiteSubcontratacao.texto_canonico_id` + spec §2.4 GATE-CAL-CONSBIO-TEXTO-OAB-paralelo.

**Análise.** Spec crava `texto_canonico_id UUID NOT NULL FK → docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md` + `texto_hash` SHA-256 do texto exibido. **REQUER OAB** pra validar wording. **Mas:** texto OAB-pendente significa que **em dogfooding Balanças Solution o texto entra com revisão consultiva (advogado-saas-regulado IA), não OAB humana**. Se cliente Balanças Solution contesta ("o texto não dizia que vocês iam mandar pra outro lab"), risco de indenização contratual + LGPD consent invalidation.

**Lacuna ADR-0028:** Modalidade 1 (E&O) cobre `wrongful billing` mas não `wrongful consent capture` (consentimento vicioso).

**Cláusula proposta:**

```
Wrongful consent capture — informational defect:
"Coverage extends to indemnification claims arising from a third-party
allegation that the consent captured by the Insured's platform
(AceiteSubcontratacao, AceiteAtividade biometric, ConsentimentoLGPD)
was uninformed or invalidated due to deficient canonical wording,
provided the Insured can produce the canonicalized text version
identifier and SHA-256 hash from the corresponding evidence record."
```

**Modalidade:** 1 (E&O ampliado).
**Sub-aggregate sugerida:** R$ 500k por evento.
**Franquia sugerida:** R$ 10k por evento.
**Gate:** GATE-SEG-EO-CONSENT-1 (NOVO) — só fecha pós-OAB humana confirmar texto v1.0.

**Caso narrativo:**
"Em 2027, cliente Balanças Solution contesta cert subcontratado alegando 'o aceite não dizia claramente que iam mandar pra outro lab'. ANPD investiga; cliente processa civilmente R$ 200k. Apólice cobre?"

🔴 REQUER CORRETORA SUSEP — pareada com `advogado-saas-regulado` OAB humana revalidar v1.0 do texto.

**Ação spec.md:** §2.4 estender com "texto v1.0 OAB-revisado bloqueia GATE-CAL-CONSBIO-TEXTO-OAB + GATE-SEG-EO-CONSENT-1". §8 adicionar R-M4-22 NOVO. §9.1 adicionar GATE-SEG-EO-CONSENT-1.

---

### P-CAL-S9 — 2ª conferência exceção abusiva (ADR-0026 5%/mês) → CGCRE suspende acreditação tenant [MÉDIO]

**Severidade:** MÉDIO (AJUSTADO).
**Lente:** spec §2.1 ADR-0026 + spec §3.2 `Excecao2aConferencia` + spec §4.1 transição `em_revisao_1 → aguardando_2a_conferencia`.

**Análise.** ADR-0026 permite exceção 2ª conferência por 4 condições objetivas + máximo 5%/mês. Se tenant abusa (RT executor = RT revisor sistematicamente) e CGCRE auditor identifica padrão, **acreditação CGCRE do tenant é suspensa**. **Cascata:**

1. Tenant perde acreditação CGCRE.
2. Tenant perde clientes farma (perdem qualificação ANVISA por fornecedor não-acreditado).
3. Tenant processa Aferê alegando "plataforma deveria ter alertado abuso 5%/mês mais cedo".

**Lacuna ADR-0028:** Modalidade 7 (Accreditation Loss) cobre `accreditation suspension — direct loss + reaccreditation cost` + `customer churn following accreditation event`. **Cobre.** Mas o gatilho da Modalidade 7 é "tenant perde escopo CGCRE/RBC por indisponibilidade Aferê OU defeito software (ADR-0025)". **Não cobre "tenant perde acreditação por governança de exceção 2ª conferência sub-otimizada"**.

Wording precisa estender.

**Cláusula proposta:**

```
Accreditation governance defect — second-conference exception abuse:
"Coverage under Modality 7 extends to events where the tenant's
accreditation is suspended due to systemic abuse of the second-conference
exception (ADR-0026 5%/month policy), provided the Insured's platform
generated alerts at threshold N% and the tenant administrator failed
to act on documented warnings (auditable via EventoDeCalibracao chain)."
```

**Modalidade:** 7 (Accreditation Loss — estensão).
**Sub-aggregate sugerida:** R$ 500k por evento (mantém Modalidade 7).
**Franquia sugerida:** R$ 25k por evento.
**Gate:** GATE-SEG-ACR-EXCECAO-1 (NOVO).

**Ação spec.md:** §8 R-M4-03 estender com `+ cobertura Accreditation Loss Modalidade 7 cláusula governance defect (GATE-SEG-ACR-EXCECAO-1) + alerta plataforma em 3%/mês`. §9.1 adicionar GATE-SEG-ACR-EXCECAO-1. **Spec deve adicionar AC novo:** US-CAL-008 AC-novo "plataforma emite alerta P2 quando uso de exceção 2ª conferência atinge 3%/mês (1/3 do limite ADR-0026)".

🔴 REQUER CORRETORA SUSEP — extensão Modalidade 7 com gatilho governance defect é wording novo.

---

### P-CAL-S10 — Replay determinístico divergência 0.1%-1% emite cert e depois descobre erro → recall [MÉDIO — ACEITE rastreado]

**Severidade:** MÉDIO (ACEITE rastreado).
**Lente:** spec §3.2 `OrcamentoIncerteza.segundo_caminho_calculo_divergencia_pct`.

**Análise.** Spec já cobre: alerta P3 entre 0.1% e 1% (passa); bloqueio acima de 1%. Risco residual: cert emitido com erro entre 0.1% e 1%, descoberto depois → recall. **Cobertura segurável:** ADR-0045 (Marco 5) cobre recall/suspensão/errata + Modalidade 1 cláusula `software validation defect` + Modalidade 7. **Cobre.**

**Decisão:** ACEITE rastreado. Spec já mitiga e Marco 5 fará o recall via consumer `Calibracao.Aprovada`. **Não há AJUSTAR.**

**Gate:** GATE-SEG-EO-RECALL-1 (já existe via ADR-0045 → Marco 5).

🔴 REQUER CORRETORA SUSEP — apenas reconfirmação Modalidade 1 + 7 abrange divergência ≤1% reportada post-emissão.

**Ação spec.md:** §8 R-M4-01 já mitiga. Nenhuma ação adicional.

---

## Modalidades ADR-0028 afetadas (consolidação)

| Modalidade | Cláusulas novas/estendidas M4 | Achado origem |
|---|---|---|
| **1 (E&O ampliado)** | software measurement defect multi-tier vicarious + sub-contracted service quality liability + investigation defense tenant administrator + wrongful platform design fraud prevention + wrongful consent capture | P-CAL-S1, S2, S4, S5, S8 |
| **2 (Cyber)** | cryptographic proof integrity defect (long-tail 25a) + sensitive personal data extended third-party scope (patient data) | P-CAL-S3, S7 |
| **3 (D&O)** | (sem novas — já cobre Roldão PF; criminal defense Roldão preservada) | — |
| **6 (CBI Dependent Service)** | (subcontratado erro técnico NÃO entra aqui — separar de indisponibilidade) | P-CAL-S2 |
| **7 (Accreditation Loss)** | software measurement defect multi-tier vicarious (paralelo Modalidade 1) + governance defect second-conference exception abuse | P-CAL-S1, S9 |
| **8 NOVA (Property — Owned Metrological Standards)** | criada do zero — cobre padrão próprio R$ 50k-500k | P-CAL-S6 |

**Total cláusulas novas:** 8 cláusulas em 4 modalidades + 1 modalidade NOVA (8).

---

## Limite SUSEP obrigatório

Todas as 8 cláusulas novas + modalidade 8 NOVA + 7 gates novos (GATE-SEG-EO-CAL-1, GATE-SEG-SUBC-1, GATE-SEG-CYBER-HMAC-1, GATE-SEG-EO-INVEST-1, GATE-SEG-EO-FRAUDE-1, GATE-SEG-BPT-PADROES-1, GATE-SEG-CYBER-PATIENT-1, GATE-SEG-EO-CONSENT-1, GATE-SEG-ACR-EXCECAO-1) **requerem corretora SUSEP credenciada (Lei 4.594/64 + Res. CNSP) pra cotar, intermediar e emitir apólice.**

**O assistente IA `corretora-seguros-saas` NÃO emite apólice. NÃO substitui corretora humana.** Pareceres aqui são consultivos pré-cotação.

**Corretoras candidatas:** Marsh Brasil, AON Tech, Howden Brasil. Pedir 3 propostas; wordings `multi-tier vicarious` + `cryptographic proof integrity defect` provavelmente exigem tradução de wording Lloyd's / mercado internacional via Marsh ou AON.

---

## Veredicto

**AJUSTAR.**

- **Não bloqueia P2** (plan.md pode prosseguir).
- **Não bloqueia fechamento M4** (M4 sai dogfooding-only; GATE-SEG-BPT-1 já cravou bloqueio em M3 P-OS-S1 — mantém-se).
- **BLOQUEIA 1º tenant externo pago farma/saúde** via 3 gates novos (GATE-SEG-EO-CAL-1, GATE-SEG-EO-FRAUDE-1, GATE-SEG-CYBER-PATIENT-1).
- **BLOQUEIA 1º tenant externo pago qualquer** via 4 gates novos (GATE-SEG-SUBC-1, GATE-SEG-EO-INVEST-1, GATE-SEG-EO-CONSENT-1, GATE-SEG-ACR-EXCECAO-1).
- **BLOQUEIA dogfooding com padrão próprio R$ 500k** via GATE-SEG-BPT-PADROES-1 (ou endosso apólice corporativa Balanças Solution — verificar com corretora).
- **BLOQUEIA prova metrológica de longo prazo** via GATE-SEG-CYBER-HMAC-1 (não bloqueia operacional, bloqueia segurabilidade 25a).

## Próximos passos (P3 — matriz reconciliação)

1. **Agente:** integrar P-CAL-S1..S10 na matriz reconciliação P3 cruzando com pareceres tech-lead / advogado / RBC.
2. **Agente:** propor ADR-0028 rev 3 com 8 cláusulas novas + modalidade 8 + 9 gates novos.
3. **Agente:** atualizar `docs/conformidade/comum/seguros/briefing-corretora-susep.md` com novos wordings + casos narrativos + perguntas obrigatórias.
4. **Agente:** atualizar `docs/conformidade/comum/seguros/gates-seg.md` com 9 novos GATE-SEG-* M4.
5. **Agente:** propor R-M4-18 (subcontratado erro) + R-M4-19 (fraude criminal) + R-M4-20 (padrão próprio) + R-M4-21 (foto paciente) + R-M4-22 (consent vicioso) na spec.md §8.
6. **Agente:** propor AC novo US-CAL-008 (alerta P2 em 3%/mês exceção 2ª conferência) na spec.md §7 / PRD.
7. **Roldão:** contratar corretora SUSEP (Marsh/AON/Howden) — bloqueante #1 do projeto pré-1º tenant externo. Solicitar 3 propostas com wordings desta lista.

---

🔴 **REQUER CORRETORA SUSEP HUMANA** — todo capital, franquia, sublimite, cláusula e modalidade citados aqui são pré-cotação. Apólice válida só com corretora SUSEP credenciada (Lei 4.594/64 + Res. CNSP). Este parecer **não substitui** corretora humana.
