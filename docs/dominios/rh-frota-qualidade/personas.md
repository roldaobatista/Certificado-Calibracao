---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas do domínio RH + Frota + Qualidade

---

## P-RFQ-01 — Motorista UMC (compliance Lei 13.103/2015)

**Quem é:** Técnico de campo que dirige UMC profissionalmente. Cadastrado tanto como técnico (P-OP-01) quanto como motorista (compliance jornada).

**Goals:**
- Saber se posso pegar a próxima OS sem violar Lei 13.103
- Registrar descanso obrigatório de 30 min a cada 5h30
- Não dirigir > 11h ininterruptas
- Comprovante de jornada em caso de fiscalização

**Frustrations:**
- "Gerente marca OS sem ver minha jornada"
- Lei muda + sem alerta no app
- Fiscalização rodoviária pede caderneta — eu não tenho

**Permissões:** Mesmas do técnico de campo + visualização da própria jornada legal.

**Compliance:** INV-020 — hook valida agenda do tenant; bloqueia OS que infringe.

---

## P-RFQ-02 — Responsável pela qualidade

**Quem é:** 30-50 anos. Em tenant grande, dedicado; em tenant pequeno, acumula com signatário técnico. Trata NC, prepara auditorias internas, mantém manual da qualidade ISO 17025.

**Goals:**
- Registrar NC em < 2 min (sem retrabalho)
- Acompanhar plano de ação até fechamento
- Preparar dossiê pra auditoria CGCRE em < 1 dia (V2)
- Identificar tendência de NC (cartas de controle — MVP-2)

**Frustrations:**
- NC em Excel separado, não consigo correlacionar com OS
- Auditor CGCRE quer evidência — eu não tenho rastro
- "Causa raiz?" registrada em uma frase e some

**Permissões:** Qualidade — qualidade (CRUD) + auditor read-only em Metrologia + Operação + acesso ao audit trail.

---

## P-RFQ-03 — Gerente / dono (aprovação RH + frota)

Já listadas em personas transversais. Tocam este domínio ao:
- Aprovar colaborador novo (Dono)
- Aprovar adiantamento de técnico (Gerente — JTBD-063)
- Designar responsável por veículo (Dono)
- Fechar NC após plano de ação concluído (Gerente)

---

## P-RFQ-04 — Andréia (CS L1)

**Quem é:** Persona 16 do discovery. Suporte Level 1 contratada pelo tenant (não pela Aferê) que atende cliente final em primeira chamada. Em tenant pequeno, papel acumulado.

**Goals (tangenciam RH/qualidade):**
- Saber o que CS L2 precisa fazer (escalonamento)
- Registrar reclamação que vira NC
- Ver SLA do cliente reclamante

Detalhes em `docs/discovery/personas-detalhadas.md` Persona 16.

---

## P-RFQ-05 — Auditor CGCRE (V2)

Persona já listada em outros domínios. Toca RH+Qualidade pela **auditoria de manual da qualidade** + verificação de NC + plano de ação + ações corretivas (cláusulas 7.10, 8.5, 8.6, 8.7 ISO 17025).

---

## P-RFQ-06 — DPO (V2 quando designado)

**Quem é:** Encarregado de proteção de dados (LGPD art. 41). Diferido V2 — subagent `advogado-saas-regulado` faz por enquanto.

**Goals:**
- Aprovar RIPD/DPIA antes de release
- Responder solicitação de titular em 15 dias
- Comunicar ANPD em 72h se incidente

Detalhes em `docs/conformidade/comum/lgpd-rat.md`.

---

## Anti-personas

- **Tenant que recusa registrar jornada motorista** → INV-020 não-negociável (bloqueio + alerta)
- **Tenant que ignora NC** → INV-012 bloqueia emissão até resolução

---

## Referências

- `docs/discovery/personas-detalhadas.md` (Persona 9 motorista UMC; Persona 16 Andréia CS L1)
- `docs/discovery/jobs-to-be-done.md` (BIG-08 frota+UMC, BIG-11 automações)
- `REGRAS-INEGOCIAVEIS.md` INV-012, INV-020
- `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` (NC + qualidade)
