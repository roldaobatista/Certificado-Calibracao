---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
---

# Personas do módulo OS

> Detalhe transversal em `../personas.md` (domínio Operação) e `docs/discovery/personas-detalhadas.md`. Aqui só o **papel específico em OS**.
>
> **Revisado em 2026-05-23 (auditoria pre-Marco 3):** adicionado P-OP-03 (atendente) — citado em PRD §3 + ADR-0023 mas ausente até então.

---

## P-OP-01 (Técnico de campo) — papel em OS

**Goals em OS:**
- Ver minhas atividades do dia em < 30s (de N OS diferentes ou da mesma)
- Iniciar atividade específica no app sem digitar nada (1 tap)
- Executar checklist da atividade offline (sem perder foto/assinatura)
- Concluir atividade no cliente — OS pode ficar aberta com outras atividades

**Frustrations:**
- App perde foto na sync
- Estado da atividade volta atrás sem explicação
- Checklist exige campo irrelevante pro tipo da atividade

**Jornada típica:**
1. Acordo → abro app → vejo agenda do dia (lista de atividades AGENDADA por OS)
2. 1 tap no endereço → Google Maps
3. Chego no cliente → "Iniciar atividade X" → atividade vira EM_EXECUCAO + GPS captura
4. Executo serviço → preencho checklist da atividade → tiro fotos → cliente assina (AceiteAtividade gravado)
5. "Concluir atividade" → atividade vira CONCLUIDA → próxima atividade ou próxima OS

**Devices:** mobile (app nativo ou PWA — ver ADR-0003).
**Frequência:** diária, múltiplas atividades por dia.

---

## P-OP-02 (Metrologista bancada) — papel em OS

**Goals em OS:**
- Recepcionar instrumento → escanear QR → criar OS com atividade tipo=calibração
- Iniciar atividade de calibração → escolher padrão usado da lista (com rastreabilidade RBC)
- Concluir atividade de calibração → dispara `AtividadeConcluida` → módulo Metrologia cria registro técnico
- Marcar NC na atividade quando medição sai fora do limite

**Frustrations:**
- "Tenho que digitar tudo no sistema e depois no Excel" (Dor #06)
- Padrão sem rastreabilidade aparece na lista

**Devices:** web desktop (laboratório).
**Possível duplicação:** este papel é igual a P-METR-01 do domínio metrologia. **Decisão:** quando promover ao domínio compartilhado, manter aqui só nota "ver `../../metrologia/personas.md#P-METR-01`".

---

## P-OP-03 (Atendente de balcão / recepcionista) — papel em OS

> Adicionada em 2026-05-23 — auditor-produto identificou ausência crítica. P-OP-03 era citado no PRD §3 e na ADR-0023 ("atendente cadastra 1 OS com 2 atividades") sem definição.

**Goals em OS:**
- Cadastrar OS no balcão em < 3 min — cliente esperando
- Saber quais atividades a OS precisa (manutenção corretiva + calibração? só calibração? + verif INMETRO?)
- Capturar foto + identificação do instrumento na recepção
- Imprimir etiqueta interna com QR (reusa modelo Marco 2 equipamentos)
- Apresentar termo de aceite + capturar assinatura cliente (AceiteAtividade por atividade)

**Frustrations:**
- Cliente não sabe descrever o defeito ("tá zoando", "não calibra")
- Sistema obriga preencher tipo único quando o caso é combinado (problema resolvido pela ADR-0023)
- Cliente recusa foto por privacidade industrial — não há "termo de dispensa" hoje (TEMA-D.9 pendente)

**Devices:** web desktop (balcão) + impressora térmica de etiqueta.
**Frequência:** alta — entrada de N OS por dia em laboratório de grande porte.

---

## P-OP-04 (Gerente operacional) — papel em OS

**Goals em OS:**
- Tela única: fila de atividades por estado + por técnico (JTBD-013)
- Redistribuir atividades quando técnico falta (JTBD-010) — drag & drop por atividade, não por OS
- Aprovar reabertura (cria OS-filha)
- Cancelar OS com razão obrigatória + notificar cliente (cascateia atividades pendentes)
- Visão das OS combinadas em andamento (manutenção+calibração) e o gate de sequência

**Frustrations:**
- "Cliente liga pedindo status da OS — não sei" (Dor #05)
- Reagendamento vira bagunça
- OS combinada parada porque atividade 1 (manutenção) ainda não fechou e atividade 2 (calibração) está bloqueada por sequência

**Devices:** web desktop + mobile (consulta).

---

## P-OP-05 (Cliente final) — papel em OS

**Goals em OS:**
- Ver status da OS pelo portal/WhatsApp link (`docs/dominios/comercial/`) — vê 1 OS, N etapas
- Aprovar reagendamento proposto
- Receber notificação "técnico saiu pra você" / "calibração concluída — certificado em revisão"

**Frustrations:**
- "Recebi 2 OS pra mesma balança" (problema antigo — resolvido pela ADR-0023)
- Termo de aceite aparece 1 vez no portal mas serviço tem 2 etapas (esclarecer no UX)

**Devices:** mobile (link WhatsApp) + web.
**Status LGPD:** P-OP-05 é **titular de dado pessoal** quando PF (cliente individual). Quando PJ, o titular é o contato PF da empresa cliente. Ver `docs/conformidade/comum/papeis-lgpd-multi-tenant.md` (TEMA-D.10 pendente).

---

## Convenções

Papel que aparece em ≥2 módulos com mesma responsabilidade → promover pra `../personas.md`. Hook valida não-duplicação.
