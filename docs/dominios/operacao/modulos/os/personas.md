---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Personas do módulo OS

> Detalhe transversal em `../personas.md` (domínio Operação) e `docs/discovery/personas-detalhadas.md`. Aqui só o **papel específico em OS**.

---

## P-OP-01 (Técnico de campo) — papel em OS

**Goals em OS:**
- Ver minhas OS do dia em < 30s
- Iniciar OS no app sem digitar nada (1 tap)
- Executar checklist offline (sem perder foto/assinatura)
- Encerrar OS no cliente (não voltar pra empresa só pra isso)

**Frustrations:**
- App perde foto na sync
- Estado da OS volta atrás sem explicação
- Checklist exige campo irrelevante pro tipo da OS

**Jornada típica:**
1. Acordo → abro app → vejo agenda do dia (lista de OS AGENDADA)
2. 1 tap no endereço → Google Maps
3. Chego no cliente → "Iniciar OS" → estado vira EM_EXECUCAO + GPS captura
4. Executo serviço → preencho checklist → tiro fotos → cliente assina
5. "Concluir OS" → estado vira CONCLUIDA → próxima OS

**Devices:** mobile (app nativo ou PWA — ver ADR-0003).
**Frequência:** diária, múltiplas OS por dia.

---

## P-OP-02 (Metrologista bancada) — papel em OS

**Goals em OS:**
- Recepcionar instrumento → escanear QR → abrir OS de calibração
- Escolher padrão usado da lista (com rastreabilidade RBC)
- Concluir OS gerando certificado rascunho (evento `OSConcluida` dispara Metrologia)
- Marcar NC quando medição sai fora do limite

**Frustrations:**
- "Tenho que digitar tudo no sistema e depois no Excel" (Dor #06)
- Padrão sem rastreabilidade aparece na lista

**Devices:** web desktop (laboratório).

---

## P-OP-04 (Gerente operacional) — papel em OS

**Goals em OS:**
- Tela única: fila de OS por estado + por técnico (JTBD-013)
- Redistribuir OS quando técnico falta (JTBD-010) — drag & drop
- Aprovar reabertura (cria OS-filha)
- Cancelar OS com razão obrigatória + notificar cliente

**Frustrations:**
- "Cliente liga pedindo status da OS — não sei" (Dor #05)
- Reagendamento vira bagunça

**Devices:** web desktop + mobile (consulta).

---

## P-OP-05 (Cliente final) — papel em OS

**Goals em OS:**
- Ver status da OS pelo portal/WhatsApp link (`docs/dominios/comercial/`)
- Aprovar reagendamento proposto
- Receber notificação "técnico saiu pra você"

**Devices:** mobile (link WhatsApp) + web.

---

## Convenções

Papel que aparece em ≥2 módulos com mesma responsabilidade → promover pra `../personas.md`. Hook valida não-duplicação.
