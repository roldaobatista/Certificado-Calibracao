---
owner: claude-code
revisado-em: 2026-05-22
status: stable
escopo: módulo equipamentos — aviso UX ao atendente quando aceite de transferência é presencial (US-EQP-004 AC-EQP-004-1 / P-EQP-A2)
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md (US-EQP-004)
  - docs/faseamento/M2-equipamentos/plan.md (P-EQP-A2)
  - docs/conformidade/equipamentos/transferencia-termo.md
versao_canonica: v1.0-2026-05-22
fundamento_legal: Lei 14.063/2020 art. 4º + CP arts. 299 (falsidade ideológica) e 171 (estelionato) + CLT art. 482 alínea "a" (improbidade) + CC art. 462 (responsabilidade objetiva)
---

# Aviso UX — aceite presencial de transferência via atendente v1.0

> **Pra quê:** quando o aceite de transferência de equipamento
> (US-EQP-004) acontece presencialmente via atendente (ViaAceiteTransferencia
> `presencial_atendente`), o atendente do laboratório se TORNA fiador
> do aceite — afirma sob as cominações penais e trabalhistas que (a)
> identificou corretamente cedente e cessionário, (b) leu o termo, e
> (c) registrou aceite consciente. Esta via é classificada como
> **fraca** (corretora RAT-EQP-ACEITE — sem MFA do titular) e exige
> cap de risco no contrato tenant (GATE-EQP-S5 Wave A).
>
> Este doc define:
>
> 1. **Aviso UX** exibido ao ATENDENTE antes de marcar `presencial_atendente`.
> 2. **Allowlist semântica** anti-CTA / anti-promocional.
> 3. **3 camadas de mitigação** (UX + auditoria + contrato).
>
> Mudar texto exige PR + bump `versao_canonica` no frontmatter +
> revisão `advogado-saas-regulado`.

---

## 1) Aviso UX ao ATENDENTE (exibido ANTES de marcar via=presencial_atendente)

```
ANTES DE CONFIRMAR ACEITE PRESENCIAL:

[ ] Identifiquei DOCUMENTALMENTE o cedente (RG/CPF ou contrato social)
    e o cessionário (RG/CPF ou procuração) — sem assumir que "é
    sempre a mesma pessoa".

[ ] LI integralmente o termo de transferência (v1.1-2026-05-22, 4
    cláusulas) para ambas as partes e confirmei verbalmente que
    entenderam:
    - LGPD art. 18 (titularidade preservada do cedente)
    - Lei 14.063/2020 art. 4º (aceite eletrônico tem valor)
    - Não-cessão de garantia / contrato / certificado ISO 17025
    - Titularidade do dado pessoal NÃO é cedida

[ ] Não há SOB AMEAÇA / SOB COAÇÃO / VÍCIO DE VONTADE evidente
    (cessionário relutante, cedente forçado, terceiros pressionando).
    Se houver dúvida — RECUSE o aceite e escale ao supervisor.

[ ] A foto do equipamento foi tirada PRESENCIALMENTE no ato do
    aceite (não recuperada de upload anterior) — defesa contra
    troca de item entre solicitação e formalização.

[ ] Declaração: ao confirmar o aceite presencial, atesto sob as
    cominações dos arts. 299 (falsidade ideológica) e 171
    (estelionato) do Código Penal, do art. 482 alínea "a" da CLT
    (justa causa por ato de improbidade) e do art. 462 do Código
    Civil (responsabilidade objetiva) que cumpri integralmente os
    4 passos acima e que o aceite reflete vontade livre e informada
    de cedente e cessionário.

[Cancelar — recusar aceite]      [Confirmar aceite presencial]
```

**Constantes (a criar em Wave A `validators.py`):**
`AVISO_ACEITE_PRESENCIAL_VERSAO_CANONICA`, `AVISO_ACEITE_PRESENCIAL`.
Marco 2 expõe apenas o doc canônico — gerador do contrato tenant↔cliente
em Wave A (`comunicacao-contratual`) lerá daqui.

---

## 2) Allowlist semântica — o que o aviso NÃO pode incluir

Aviso NÃO pode conter:

- CTA promocional ("aproveite", "desconto", "garantia estendida").
- Termos que ATENUEM a responsabilidade do atendente
  ("simples conferência", "rapidamente", "se possível").
- Referência a métricas operacionais que pressionem o atendente
  ("tempo médio de atendimento", "metas", "performance").
- Promessa de "validade jurídica plena" sem qualificação da via
  fraca (aceite presencial é via fraca por design — Wave A
  introduzirá portal-cliente OTP via forte).

---

## 3) Três camadas de mitigação

### Camada A — UX (este aviso)
Forçar atendente a CONFIRMAR cada item antes de marcar a via.
Atendente vira fiador documental do aceite.

### Camada B — Auditoria estrutural
`Aceite.usuario_id_atendente` é OBRIGATÓRIO quando
`via=presencial_atendente` (P-EQP-A2). Cadeia auditável WORM 25a
liga o aceite ao usuário do atendente — defesa probatória em caso
de contestação.

### Camada C — Contratual
Contrato tenant↔Aferê (Wave A `comunicacao-contratual`) inclui
cap de risco GATE-EQP-S5: aceite presencial fica limitado a
operações de baixo valor (transferência de equipamento usado entre
clientes do mesmo tenant, sem cessão de dados sensíveis). Cessão
de dados pessoais sensíveis SÓ via portal-cliente OTP (Wave B Q2-2027).

---

## 4) Versionamento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| v1.0-2026-05-22 | 2026-05-22 | advogado-saas-regulado | Criação inicial. Aviso UX + allowlist + 3 camadas (UX/auditoria/contrato). |

Bump exige PR + revisão `advogado-saas-regulado` + alteração de
`AVISO_ACEITE_PRESENCIAL_VERSAO_CANONICA` (Wave A) com teste
anti-drift versão↔frontmatter.
