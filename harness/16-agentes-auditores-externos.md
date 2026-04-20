# 16 — Agentes auditores externos (substituem humanos contratados)

> **P0-12**: três agentes especializados com papel de auditor externo, substituindo os especialistas humanos previstos anteriormente (consultor metrológico, advogado LGPD, engenheiro sênior de review).

## Racional

Usuário é não-técnico e optou por operar sem contratação pontual de humanos especialistas. Solução: três agentes atuam como **primeira linha de auditoria externa**, com:
- Parecer vinculante no release-norm (podem bloquear).
- Separação de funções preservada por arquitetura (auditor nunca é executor).
- Limitações honestamente declaradas (não substituem humano em 5 casos-limite).

O mesmo princípio que o **produto** aplica ao laboratório — "quem executa não aprova" (ISO 17025 §5.4) — vale no harness: quem escreve a regra não a audita; quem escreve o código não faz o review crítico.

---

## Limitações honestamente declaradas

**Estes 3 agentes NÃO fazem:**
- Parecer jurídico legalmente vinculante em contencioso.
- Substituir auditor CGCRE no dia da auditoria real de acreditação.
- Assinar laudo técnico regulamentar.
- Substituir signatário humano de documento que a norma exige assinatura de pessoa física competente.
- Representar o produto em processo judicial ou administrativo.

Nesses casos, sistema faz **fail-closed** e escala ao usuário com briefing pronto para contratar humano. Esses são os "bloqueios reais" que chegam a ele.

### 5 casos-limite que exigem humano real

1. **Auditoria CGCRE agendada** (cliente pediu acreditação formal).
2. **Processo judicial aberto** contra o produto ou contra cliente que usou certificado.
3. **Incidente LGPD com dados vazados** em produção.
4. **Acidente metrológico**: cliente tomou decisão crítica com base em certificado e houve dano.
5. **Reclamação formal em órgão regulador** (Inmetro, Cgcre, ANPD).

Nesses 5: agentes preparam briefing e *case file*, sistema para emissão (fail-closed) e escala ao usuário.

---

## Os 3 agentes auditores

### 11. `metrology-auditor`

**Mandato**: pré-auditoria ISO 17025 / CGCRE / NIT-DICLA antes de cada release.

**Enfoque**: "Se fosse auditoria real amanhã, este release passaria?"

**Escopo**:
- Revisa escopo acreditado, CMC, rastreabilidade ponta a ponta.
- Valida templates A/B/C contra DOQ-CGCRE-028.
- Simula bateria de 40+ perguntas típicas de auditoria CGCRE.
- Testa cenários de não-conformidade comuns (padrão vencido, signatário sem competência, ambiente fora da faixa).
- Emite parecer em `compliance/audits/metrology/<release>.md` com veredito PASS/FAIL + lista de achados.
- **BLOQUEIA release** se encontra não-conformidade grave.

**Modelo**: Opus.
**Paths permitidos (escrita)**: `compliance/audits/metrology/**`.
**Paths bloqueados**: qualquer código; o agente não edita o que audita.
**Frequência**: antes de cada release de fatia vertical + após mudança em `packages/normative-rules/**`.
**Relação com `regulator`**: `regulator` projeta e interpreta; `metrology-auditor` audita o conjunto.

### 12. `legal-counsel`

**Mandato**: parecer jurídico-regulatório pré-release e por claim/contrato novo.

**Enfoque**: LGPD, claims comerciais, contratos padrão (ToS / Política de Privacidade / DPA), bases jurídicas de tratamento, retenção, DSAR, regulação aplicável (Marco Civil, CDC, Lei de Acesso, etc.).

**Escopo**:
- Revisa cada claim em `compliance/approved-claims.md` — base fática, risco de processo, alternativas defensáveis.
- Valida base jurídica de cada tratamento em `compliance/legal-opinions/`.
- Analisa contratos padrão antes de cliente assinar (ToS, DPA, NDA padrão).
- Avalia risco em incidentes LGPD (severidade, obrigação de notificação ANPD/titular).
- Emite parecer em `compliance/audits/legal/<tópico>.md`.
- **BLOQUEIA release** se detecta risco jurídico alto não mitigado.

**Modelo**: Opus.
**Paths permitidos (escrita)**: `compliance/audits/legal/**`, `compliance/legal-opinions/**` (co-autoria com `lgpd-security`).
**Paths bloqueados**: qualquer código.
**Frequência**: antes de cada release + a cada claim novo + a cada contrato novo + em incidente.
**Relação com `lgpd-security`**: `lgpd-security` implementa controles técnicos de segurança/privacidade; `legal-counsel` opina sobre risco jurídico das decisões.

### 13. `senior-reviewer`

**Mandato**: code review sênior independente em áreas blocker (lista fechada em `14-verification-cascade.md` L4).

**Enfoque**: arquitetura, manutenibilidade, performance, edge cases, segurança de código (OWASP top 10), clareza, testabilidade.

**Escopo**:
- Revisa PRs em áreas críticas como segundo par de olhos (separado do agente dono do path — dupla checagem §15).
- Participa de ADRs arquiteturais.
- Emite review formal como comentários de PR + arquivo `compliance/audits/code/<PR>.md` em áreas críticas.
- **BLOQUEIA merge** se detecta risco arquitetural ou de segurança de código.
- Flaga código que parece correto mas é frágil (*implicit coupling*, *hidden state*, *race conditions* sutis).

**Modelo**: Opus.
**Paths permitidos (escrita)**: `compliance/audits/code/**` + comentários de PR.
**Paths bloqueados**: código-fonte (nunca edita o que revisa).
**Frequência**: todo PR em área crítica; opcional em áreas não-críticas.
**Relação com agentes donos**: donos implementam; `senior-reviewer` é segunda opinião sênior externa.

---

## Diferenciação vs executores internos

| Domínio | Executor (já existia) | Auditor (novo) | Princípio |
|---------|------------------------|----------------|-----------|
| Normativa | `regulator` | `metrology-auditor` | Quem interpreta norma não audita aplicação dela |
| Jurídica | `lgpd-security` | `legal-counsel` | Quem implementa controle não opina sobre risco jurídico |
| Código crítico | dono do path (`backend-api` etc.) | `senior-reviewer` | Quem escreve não aprova |

**Regra dura**: auditor **nunca** edita o artefato que audita. Se o auditor identifica problema, emite parecer; executor corrige e resubmete para nova auditoria. Esse ciclo preserva separação de funções mesmo em harness 100% autônomo.

---

## Nova divergência na matriz de escalonamento

**D9** (adicionado a `12-escalation-matrix.md`): auditor bloqueia, executor discorda.

Precedência:
- Em risco regulatório: `metrology-auditor` prevalece.
- Em risco jurídico: `legal-counsel` prevalece.
- Em risco de código/arquitetura crítica: `senior-reviewer` prevalece.
- Override exige: ADR expressa + aprovação do **usuário** ciente do risco (isso é um dos raros casos que chega a ele).

---

## Fluxo de release com os 3 auditores

Sequência obrigatória no L5 (release):

1. `qa-acceptance` confirma L4 (full regression, snapshot-diff, property tests).
2. `metrology-auditor` roda pré-auditoria → parecer em `compliance/audits/metrology/<release>.md`.
3. `legal-counsel` roda revisão jurídica → parecer em `compliance/audits/legal/<release>.md`.
4. `senior-reviewer` roda review de código crítico acumulado no release → parecer em `compliance/audits/code/<release>.md`.
5. `product-governance` consolida os 3 pareceres + pareceres dos executores (`regulator`, `lgpd-security`, etc.) + fecha `compliance/release-norm/<versao>.md`.
6. Se qualquer auditor **BLOQUEIA**: release não sai; issue automática; executor corrige; re-auditoria obrigatória.

---

## Estrutura de diretório dos pareceres

```
compliance/audits/
├─ metrology/
│  ├─ release-v1.0.md
│  └─ hotfix-2026-05-02.md
├─ legal/
│  ├─ release-v1.0.md
│  ├─ claim-<slug>.md
│  └─ contract-<slug>.md
└─ code/
   ├─ release-v1.0.md
   └─ pr-1234.md
```

Cada parecer tem frontmatter padronizado:
```yaml
---
auditor: metrology-auditor | legal-counsel | senior-reviewer
release: <versao>
verdict: PASS | FAIL | PASS_WITH_FINDINGS
findings: [<lista>]
blockers: [<lista>]
date: <ISO>
---
```

---

## Quando os 3 auditores NÃO bastam

Os 5 casos-limite listados acima. Em qualquer um deles, mesmo com os 3 auditores verdes, sistema escala ao usuário com recomendação explícita:

> "Caso X detectado. Os agentes auditores prepararam briefing em `compliance/audits/escalations/<caso>.md`. Recomendação: contratar humano especialista [tipo]. Orçamento estimado [faixa]. Aprovar?"

Usuário decide sim/não. Se sim: especialista humano entra com dossiê pronto. Se não: sistema mantém fail-closed até o risco se resolver ou usuário aceitar em ADR.

---

## Revisão periódica

A cada 3 meses, `product-governance` publica em `compliance/audits/quality-review-<data>.md`:
- Quantas não-conformidades os 3 auditores detectaram vs passaram.
- Falsos-positivos reportados pelos executores.
- Casos que exigiram humano real.
- Ajustes sugeridos nos prompts dos auditores.

Se a taxa de falsos-negativos (auditor liberou e surgiu problema depois) ficar > 2%: sistema reabre debate sobre necessidade de humano contratado, ADR obrigatória.
