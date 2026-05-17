---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Responsabilidade técnica — signatário do certificado

> **Pra quê:** RBC NIT-DICLA-021 exige **signatário técnico humano** com qualificação demonstrada por certificado emitido. Aferê NÃO substitui o signatário — o software apenas viabiliza, audita e protege a assinatura.
>
> **Origem:** Cláusula 6.2 ISO 17025 (pessoal) + NIT-DICLA-021 (qualificação) + INV-018 + R-065 da auditoria 12 agentes.

---

## 1. Princípio

**O signatário técnico é uma pessoa física qualificada**, não o software. O Aferê:
1. Identifica o signatário no certificado (nome + CREA + competência + qualificação)
2. Coleta assinatura digital ICP-Brasil A3 cliente-side (ADR-0009)
3. Carimbo de tempo de origem confiável
4. Audit log da emissão (quem, quando, qual cliente)
5. Não permite emissão sem signatário identificado e assinatura válida

---

## 2. Cargos / papéis

| Papel | Quem | Responsabilidade |
|-------|------|------------------|
| **Signatário técnico** (lab usuário) | Pessoa física qualificada do tenant, listada em escopo CGCRE/RBC | Assinar certificado; responde por valor metrológico |
| **Responsável pela qualidade** (lab usuário) | Pessoa física do tenant | Aprovar/auditar processos do lab |
| **RT do vendor** (Aferê) | Pessoa física com CREA + competência metrológica + escopo registrado | Responde tecnicamente pelo software perante CGCRE quando tenant é acreditado |
| **DPO formal** (Aferê) | Pessoa física qualificada em LGPD | Responde pela proteção de dados |

---

## 3. RT do vendor — diferido V2 (R-065)

**Decisão Roldão (2026-05-17):** RT do vendor (Aferê) **diferido pra V2-V3** (ver `discovery/sintese-final.md` §7). Implicações:

- Aferê **NÃO atende cliente farma TOP ou tenant RBC acreditado no MVP-1** (R-065 score 20 aceito conscientemente)
- INV-018 (dossiê 7.11) fica como pendência V2
- Quando 1º tenant RBC acreditado quiser usar Aferê, RT humano deve ser contratado primeiro

**Mitigação na janela atual:** subagent `consultor-rbc-iso17025` prepara minutas, simula auditoria, gera URS/IQ/OQ/PQ. Humano credenciado contratado pontual quando preciso (R$ 5-15k consulta).

---

## 4. Como Aferê implementa qualificação do signatário (tenant)

Cadastro de signatário pelo tenant requer:
- Nome completo + CPF
- CREA (ou outro conselho aplicável)
- Competência declarada (escopo metrológico em que pode assinar)
- Anexo: documento de qualificação (diploma, certificado curso, registro CGCRE)
- Vinculação a certificado A3 ICP-Brasil (verificação de chain of trust)

Validações:
- **Auditor Segurança** verifica que `signatario.competencia` cobre o `tipo_de_calibracao` do certificado em emissão
- **Auditor Produto** verifica que template do certificado tem campo "signatário" preenchido + AC binário "certificado assinado por humano qualificado"

---

## 5. ICP-Brasil A3 — implementação

Ver ADR-0009 detalhada. Resumo:
- A3 (token físico ou cartão) **sempre cliente-side** via Web PKI Lacuna (desktop) ou Flutter FFI (mobile)
- Defesa anti-replay: nonce + signing-time server-controlled + one-shot
- A1 (arquivo P12) server-side com KMS — exceção; só pra signatários do vendor (RT V2)
- Carimbo de tempo: PSS Brasil ou Lacuna LTV

---

## 6. Hooks que enforce

| Hook / Auditor | Função |
|----------------|--------|
| `INV-checker.sh` | Bloqueia commit que adiciona INV de signatário sem teste correspondente |
| Auditor Segurança | Bloqueia merge que permite emissão sem signatário válido |
| Auditor Produto | Bloqueia merge se template não tem campo `signatario_qualificado` |
| Hook de emissão (a criar) | Pre-emissão: rejeita certificado sem assinatura A3 válida + chain of trust válida |

---

## 7. Reconciliação com LGPD

PII do signatário (CPF, CREA) é coberto por:
- Base legal: art. 7º II (obrigação regulatória — exige nome no certificado)
- Retenção: enquanto signatário ativo + 5 anos após desligamento
- Anonimização não-aplicável (norma exige nome real)

---

## 8. Drill / auditoria

- **Trimestral (V2):** simular auditoria CGCRE — tenant RBC tem signatário válido pra todos certificados ativos
- **Pre-merge:** Auditor Produto verifica AC de emissão sempre incluem signatário
- **Anual (V2):** revisão escopo de signatários pelo RT do vendor (quando contratado)

---

## 9. Pendências

- [ ] URS detalhado do módulo de signatário
- [ ] Hook pre-emissão (a criar quando Wave A começar)
- [ ] Fluxo de troca de signatário (e.g., desligamento) — UI + audit log
- [ ] Revogação de chain of trust (signatário perdeu credenciamento)
- [ ] Integração com Receita Federal pra validar CPF + CGCRE pra validar credenciamento (V2)
- [ ] Contratação RT do vendor (V2 — quando 1º tenant RBC pago aparecer)

---

## 10. Referências

- NIT-DICLA-021 (RBC — qualificação do signatário)
- ABNT NBR ISO/IEC 17025:2017 cláusula 6.2 (pessoal)
- ADR-0009 (onde A3 assina)
- `REGRAS-INEGOCIAVEIS.md` INV-002, INV-018
- `discovery/sintese-final.md` §7 (RT do vendor diferido)
- `conformidade-iso-17025.md`
