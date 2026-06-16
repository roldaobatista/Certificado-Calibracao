# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — DECISÃO de próxima frente (nível 5/6 do `plano-dependencia-sistema.md`)

- **`contas-receber` FECHOU** (módulo 100% Wave A). Próxima frente NÃO cravada — candidatas nível 5: `agenda`,
  `caixa-tecnico`, `chamados`, `contas-pagar`; nível 6 gatilhado por recebimento: `comissoes`. Seguir ordem por
  dependência (criar a ordem se faltar); decisão de priorização = uma rodada batch antes de iniciar a frente nova.
- **Para o Roldão (quando ativar e-mail real do CR):** criar `.env` com `EMAIL_HOST`/`EMAIL_HOST_USER`/
  `EMAIL_HOST_PASSWORD`/`DEFAULT_FROM_EMAIL` (SMTP). Hoje modo teste (não envia). Disparo a PF real só após GATE-LGPD-RAT.

## Última frente FECHADA — `contas-receber` MÓDULO 100% Wave A (2026-06-16)

- Fatias 1a..3d + P8 (ADR-0084) + P9 (auditores: 7 PASS + 1 MÉDIO idempotência consertado — `UniqueConstraint`
  `gateway_event_id`/migration 0008; 2ª passada RESOLVIDO). Commits `79bf494`/`227c522`/`853f12c`/`671194f`/`aae7f08`/
  `d0eac7d`/`4f0f05f` (+conserto P9). Detalhe: `docs/faseamento/contas-receber/` + matriz §8 + diário. Gatilho =
  `os.concluida`; bus FAN-OUT [[fan-out-bus-consumers-os-concluida]]; INV-FIN-* no mestre; 3 hooks novos.
- **Débitos rastreados (Wave B / re-review):** desbloqueio SEM grace (assimetria c/ adapter 3b); snapshot webhook =
  valor_original (sem juros); desconto-pontualidade pré-venc sem fórmula; isolamento por-consumer do bus; GATE-CR-REPROVA-PAGA
  + GATE-CR-OBS-OS-SEM-CERT (ADR-0084); A3 real override (GATE-CR-A3); Asaas real (GATE-CR-ASAAS).
- **`orcamentos`** fechou antes (2026-06-15, ADR-0083). Detalhe no diário + [[estado-do-projeto-wave-a-em-curso]].

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
