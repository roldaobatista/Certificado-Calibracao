---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas do domínio Operação

> Detalhe rico em `docs/discovery/personas-detalhadas.md` (16 personas). Aqui ficam só as **operacionais**.

---

## P-OP-01 — Técnico de campo

**Quem é:** 25-50 anos. Motorista profissional (UMC) + executor de serviço em campo (calibração, manutenção, instalação). Maior usuário do app mobile.

**Goals:**
- Saber a agenda do dia em < 30s ao acordar
- Navegar até cliente sem digitar endereço (1 tap)
- Executar serviço offline (3G ruim ou sem sinal)
- Registrar peça consumida + foto + assinatura sem 20 cliques
- Não voltar pra empresa só pra encerrar OS

**Frustrations:**
- App que trava em local sem sinal
- Sincronização que perde foto
- Adiantamento que demora 3 dias

**Permissões:** Técnico — suas OS atribuídas + agenda própria + caixa do técnico + emitir certificado (se for signatário com competência válida).

**Compliance:** INV-020 — agenda valida 11h ininterruptas + descanso 30min/5h30.

---

## P-OP-02 — Metrologista de bancada (lab interno)

**Fonte canônica:** `docs/dominios/metrologia/personas.md` P-METR-01. A partir de 2026-05-17 a definição completa vive no domínio metrologia (persona aparece em ≥2 módulos do domínio metrologia: calibração + certificados).

Aparece em operação ao **abrir OS de calibração** e ao consumir agenda do laboratório. Demais interações estão em metrologia.

---

## P-OP-03 — Atendente (toca operação ao abrir chamado/OS)

Mesma persona do domínio Comercial (P-COM-01). Toca operação ao:
- Abrir chamado vindo de WhatsApp/telefone/portal
- Converter chamado em OS
- Agendar OS pra um técnico

Detalhes em `docs/dominios/comercial/personas.md` P-COM-01.

---

## P-OP-04 — Gerente operacional

**Quem é:** 30-45 anos. Braço-direito do dono. Acompanha fila de OS, atribui técnicos, lida com NC, intermedeia conflito agenda × cliente.

**Goals:**
- Visão consolidada da operação em UMA tela (JTBD-013)
- Saber onde cada técnico está hoje + amanhã
- Redistribuir OS quando técnico falta (JTBD-010)
- Aprovar adiantamento de técnico (JTBD-063) em < 5 min

**Frustrations:**
- "Cliente liga pedindo status de OS — eu não sei"
- Reagendar OS vira bagunça em planilha
- "Técnico X anda esquecido em 15 OS, técnico Y morrendo de trabalho"

**Permissões:** Gerente — tudo da Operação + ver financeiro não-sensível + admin RBAC de Operação.

---

## P-OP-05 — Cliente final (acompanhamento via portal)

Toca operação ao:
- Ver status da OS pelo portal/WhatsApp link
- Aprovar reagendamento proposto pelo gerente
- Receber notificação "técnico saiu pra você"

Detalhes em `docs/dominios/comercial/personas.md` P-COM-03.

---

## P-OP-06 — Signatário técnico (RBC NIT-DICLA-021)

Pessoa física com **competência declarada** + qualificação registrada (diploma + curso + CGCRE). Toca Operação ao **assinar certificado** ao final da OS de calibração.

Detalhes em `docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md`.

---

## Anti-personas

- **Técnico que não quer mobile** (recusa app) — fora do mercado-alvo
- **Cliente que pede personalização de fluxo de OS** — ANTI-11 (proibido)

---

## Referências

- `docs/discovery/personas-detalhadas.md` (Persona 5 técnico de campo; Persona 7 metrologista; Persona 9 motorista UMC)
- `docs/discovery/jobs-to-be-done.md` (BIG-01, BIG-02, BIG-05, BIG-08)
- ADR-0003 (mobile)
