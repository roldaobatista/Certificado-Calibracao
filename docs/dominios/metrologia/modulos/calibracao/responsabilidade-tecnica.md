---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
---

# Responsabilidade técnica — signatário do certificado

> **Revisado em 2026-05-23 (auditoria 10 lentes — TEMA-B.8 + TEMA-C.8 + TEMA-D.4):** adicionada política objetiva de exceção "único RT habilitado" (§3.1); consumer obrigatório `Colaborador.Desligado` (§11); INV-CER-COMP-001 (vigência RT na data execução, não emissão) referenciada.

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

## 3.1. Política objetiva de exceção revisor=executor (TEMA-B.8 / cl. 6.2.5)

> Adicionada em 2026-05-23. ISO/IEC 17025 §6.2.5 exige independência entre executor e revisor — `garantia-validade-7.7.md` permite exceção "quando único RT habilitado", mas o texto era frouxo. CGCRE em supervisão pergunta o critério objetivo. Aqui está cravado:

### Quando a exceção é aceitável

A exceção `executor == revisor` em US-CAL-007 AC-CAL-007-3 só é aceitável quando **TODAS** as condições abaixo verdadeiras:

1. **Único RT habilitado ATIVO na grandeza/faixa específica no momento da execução.** Validação automática: `count(rt_habilitado, grandeza, em_data=executada_em) == 1`.
2. **Calibração tem prazo regulatório que não pode esperar** (cert do cliente expira em ≤7 dias úteis).
3. **Tentativa documentada de subcontratar a 2ª conferência** a outro lab (e-mail registrado em audit).
4. **Justificativa registrada** com ≥100 chars + anti-PII (INV-CAL-TXT-001) explicando os 3 itens acima.

### Limite quantitativo

- Máximo **5% das calibrações/mês** podem usar a exceção. Hook `politica-excecao-revisor-check.sh` (a criar Wave A) conta e alerta gestor de qualidade quando ultrapassa.
- Excedeu 5%/mês 2 vezes consecutivas → NC automática + revisão pelo gestor de qualidade obrigatória.

### Revisão obrigatória

- **Trimestral:** gestor de qualidade revisa todas as exceções do trimestre; aprovação documentada em audit.
- **Anual:** taxa de exceção apresentada ao auditor CGCRE em supervisão.

### Audit no certificado

Todo certificado emitido sob exceção carrega no rodapé do PDF: "Conformidade ISO/IEC 17025 §6.2.5 — exceção registrada em audit ref. NC-####"

---

## 3.2. RT do vendor — diferido V2 (R-065)

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
- [ ] Hook pre-emissão (a criar quando Wave A começar) — amarra INV-002 + INV-017 + INV-019 + INV-CER-COMP-001 + INV-032 numa única função-porta `pre_emissao_certificado_check()` (TEMA-CONCERN-2 segurança)
- [ ] Fluxo de troca de signatário mid-calibração: comando `trocarRevisorOuConferente` cravado em `modelo-de-dominio.md`; UI + audit log a implementar Wave A (TEMA-D.5)
- [ ] Hook `politica-excecao-revisor-check.sh` (TEMA-B.8 — §3.1 supra)
- [ ] ADR-0026 — 2ª conferência + independência RT (TEMA-F.3) — promover decisão estrutural

---

## 10. INV-CER-COMP-001 — vigência RT na data de execução (TEMA-D.4)

> Promovido em 2026-05-23 em REGRAS-INEGOCIAVEIS.md.

**Regra:** emissão bloqueia se `signatario.competencias` não cobre `calibracao.grandeza` **NA DATA `calibracao.executada_em`** (não na data de emissão).

**Por quê:** ADR-0022 cravou `RTCompetencia` com vigência por intervalo `tstzrange`. Sem INV-CER-COMP-001, sistema permitiria emitir cert em data D2 onde RT havia perdido competência D1 < D2. Predicate `decisor_tem_competencia_para_atividade(rt_id, atividade='calibracao_grandeza_X', em_data=executada_em)` retorna false → bloqueia.

**Hook:** `pre_emissao_certificado_check()` invoca o predicate ANTES de chamar A3 sign. Sem predicate true: HTTP 412 + mensagem ao RT "Sua competência expirou em DD/MM antes da data de execução desta calibração — substituição de RT obrigatória ou ajuste de competência".

---

## 11. Consumer `Colaborador.Desligado` — INV-INT-002 (TEMA-C.8)

> Adicionado em 2026-05-23. Sem consumer, signatário fica `ativo=true` post-desligamento; pode emitir cert com A3 esquecido na máquina.

Quando módulo RH publica `Colaborador.Desligado(usuario_id, desligado_em)`:

1. **Atualiza** `signatario.status = "desligado"` + `signatario.desligado_em = desligado_em`.
2. **Bloqueia** `executar2aConferencia` e `assinar` para esse signatário (predicate retorna false).
3. **Marca** certificados em `PENDENTE_ASSINATURA` desse signatário como `pendente_designacao_rt`.
4. **Invalida** sessões ativas chamando `AuthorizationProvider.invalidar_sessoes(usuario_id)`.
5. **Audita** evento `Signatario.Desligado` em `EventoDeCalibracao` (WORM 25a).

**SLA:** ≤ 2 segundos da publicação até bloqueio efetivo (INV-INT-002 cravada).

**Hook:** `consumer-desligado-rt-check.sh` (a criar Wave A) valida que código de calibração/certificados tem subscriber registrado pra `Colaborador.Desligado`.
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
