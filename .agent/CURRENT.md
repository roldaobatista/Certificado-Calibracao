# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `contas-receber` (Nível 5 — fecha a receita ponta a ponta)

- **RITUAL P0–P3 + Fatias 1a/1b/2a/2b DONE** — spec v2/plan/tasks (T-CR-010..061); núcleo REST completo (domínio puro +
  schema PG RLS v2/WORM + use cases manual + gateway Mock + webhook HMAC idempotente + override). Gatilho canônico =
  `os.concluida` ENRIQUECIDO no OUTBOX. Detalhe no diário + `docs/faseamento/contas-receber/`.
- **Fatia 3a/3b/3c DONE** (commits `79bf494`/`227c522`/`853f12c`/`671194f`/`aae7f08`): auto-faturamento de OS (bus FAN-OUT
  [[fan-out-bus-consumers-os-concluida]]) + inadimplência (adapter PULL grace 45/20/30/7 + notificação D+30/D+45 perfil A
  Caminho C + prova `NotificacaoInadimplencia` fail-closed CDC) + desbloqueio GATE-CLI-6 (`queries_desbloqueio` + consumer
  `handle_contas_receber_pago`, só bloqueio automático, parcial mantém AC-CR-006-2). Detalhe no diário.
- **Fatia 3d DONE** (2026-06-16, commit pendente): seção `## INV-FIN-*` CRAVADA em `REGRAS-INEGOCIAVEIS.md` (T-CR-046 —
  GW/PERFIL/GRACE/SNAPSHOT/REATIV/INAD + INV-CR-* + INV-FIS-CR-001; `invariantes-futuras.md`→ponteiro) + 3 hooks (T-CR-047:
  `cr-perfil-server-side`/`cr-provider-import-fronteira`/`policy-tenant-vs-cliente`) no manifest, 23 casos verdes. **Todo o
  CÓDIGO da frente CR está DONE — falta só fechamento P8/P9.**
- **PRÓXIMO = P8** (T-CR-060): ADR de reconciliação (molde ADR-0083 — `Titulo`×"ContasReceber" do PRD + gatilho
  `os.concluida`≠`Certificado.Emitido`, emenda ADR-0043/INV-CAL-FIN-001) + `matriz-reconciliacao.md` (AC↔código↔teste) +
  `STATUS-GERADO` (`status-projeto.sh --check`) + frontmatters `stable` + `plano-dependencia-sistema.md` (nível 5 fecha
  receita). Depois **P9** (T-CR-061): mutirão auditores roteados; MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada.
- **Débitos p/ P9:** desbloqueio SEM grace (assimetria c/ adapter 3b); snapshot webhook=valor_original (sem juros);
  desconto-pontualidade pré-vencimento sem fórmula; isolamento por-consumer do bus (re-review quando saga sair do stub).
- **Migration test_afere:** `migrate --database=default` com `-e PYTEST_CURRENT_TEST=1 -e DATABASE_URL=...@db/test_afere`
  (router faz DDL só em `migrator` fora de pytest; NÃO dropar — perde extensões).
- **Para o Roldão (quando ativar e-mail real):** criar `.env` com `EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`/
  `DEFAULT_FROM_EMAIL` (provedor SMTP). Hoje em modo teste (não envia). Disparo a PF real só após GATE-LGPD-RAT.

## Última frente FECHADA — `orcamentos` MÓDULO 100% Wave A (2026-06-15)

- Detalhe no diário + [[estado-do-projeto-wave-a-em-curso]]. ADR-0083 (`PrecoResolvido`). Commits
  `b002dae`/`cf12bc8`/`24404ca`/`4f8b326`. US Wave B: 003/006/010. Matriz: `orcamentos/matriz-reconciliacao.md` §8.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
