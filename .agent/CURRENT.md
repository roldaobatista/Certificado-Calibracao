# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `contas-receber` (Nível 5 — fecha a receita ponta a ponta)

- **RITUAL P0–P3 + Fatias 1a/1b/2a/2b DONE** — spec v2/plan/tasks (T-CR-010..061); núcleo REST completo (domínio puro +
  schema PG RLS v2/WORM + use cases manual + gateway Mock + webhook HMAC idempotente + override). Gatilho canônico =
  `os.concluida` ENRIQUECIDO no OUTBOX. Detalhe no diário + `docs/faseamento/contas-receber/`.
- **Fatia 3a DONE** (auto-faturamento de OS): T-CR-040/041/042. Bus virou **FAN-OUT** (`_REGISTRY: dict[str,list]`,
  tudo-ou-nada por linha) — [[fan-out-bus-consumers-os-concluida]]. `os.concluida`→título, baixa→`os.paga`.
- **Fatia 3b DONE** (inadimplência, commits `227c522`/`853f12c`/`671194f`): adapter PULL `TituloVencidoInadimplenciaSource`
  grace 45/20/30/7 por perfil + notificação D+30/D+45 perfil A **Caminho C** (remetente=tenant; e-mail nunca no evento) +
  `NotificacaoInadimplencia` INSERT-only (migration 0007) = prova; **fail-closed CDC** (perfil A só na régua com prova). 22 testes.
- **Fatia 3c DONE** (2026-06-16, commit pendente): desbloqueio (GATE-CLI-6). `contas_receber/queries_desbloqueio.py`
  (`cliente_atual_id_do_titulo` + `tem_outra_vencida_em_aberto` read-only) + `clientes/consumers/contas_receber_eventos.py`
  (`handle_contas_receber_pago` registrado em `clientes/apps.py:ready()`). Encerra **só** bloqueio automático (manual não
  cede); parcial/`parcialmente_pago` mantém (AC-CR-006-2); publica `cliente.desbloqueado`; idempotente. 9 testes; ruff+mypy
  limpos. Toca `clientes` FECHADO (só `apps.py:ready()` + NOVOS — R14).
- **PRÓXIMO = Fatia 3d** (INV-FIN-* ao mestre + hooks): cravar família `INV-FIN-*` em `REGRAS-INEGOCIAVEIS.md` (T-CR-046) +
  hooks `policy-tenant-vs-cliente.sh`/`cr-provider-import-fronteira-check.sh`/`cr-perfil-server-side-check.sh` no manifest
  (T-CR-047). Depois P8 (ADR reconcilia, molde 0083 — T-CR-060) / P9 (mutirão auditores — T-CR-061).
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
