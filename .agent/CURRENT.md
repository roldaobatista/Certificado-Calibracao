# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `contas-receber` (Nível 5 — fecha a receita ponta a ponta)

- **RITUAL P0–P3 FECHADO** (2026-06-15): T-CR-000 + `spec.md` v2 + reviews P2 + `plan.md`/`tasks.md` (T-CR-010..061).
  Gatilho canônico = `os.concluida` ENRIQUECIDO no OUTBOX. Gateway = Mock (Asaas=GATE). Em `docs/faseamento/contas-receber/`.
- **Fatias 1a/1b/2a/2b DONE** — núcleo REST completo: domínio puro + schema PG (RLS v2/WORM) + use cases manual +
  gateway Mock + webhook HMAC idempotente + override. Detalhe no diário.
- **Fatia 3a DONE** (2026-06-15): auto-faturamento de OS. T-CR-040 enriquece outbox `os.concluida`
  (cliente + `valor_total_centavos` int = `valor_total_atualizado`/INV-OS-FAT-001; WORM intacto). T-CR-041
  `criar_titulo_a_partir_de_os` + consumers `handle_os_concluida`/`handle_os_reaberta`. T-CR-042 baixa → `os.paga`.
  **Achado: bus virou FAN-OUT** (`os.concluida` já tinha saga de anonimização; `_REGISTRY: dict[str,list]`,
  tudo-ou-nada por linha; tech-lead Opus aprovou c/ correções) — [[fan-out-bus-consumers-os-concluida]].
  Verde: 13 (3a) + 4 (fan-out) + 28 (regressão CR Fatia 2) + 13 (fb_reconciliacao).
- **Fatia 3b-1 DONE** (commit `227c522`): adapter `TituloVencidoInadimplenciaSource` (PULL) lê `Titulo` vencido +
  grace 45/20/30/7 por perfil; `InadimplenciaItem`+perfil/grace_perfil Optional (toca `clientes` FECHADO); `get_source()`
  parametrizado `INADIMPLENCIA_SOURCE_IMPL` (default "interim" = INATIVO). 10+15 testes.
- **Fatia 3b-2 DONE** (commit `853f12c`): notificação D+30/D+45 perfil A — parecer advogado **Caminho C** (e-mail ao
  cliente, **remetente = tenant**; e-mail nunca no evento; evento `inadimplencia_dura_atingida` = aviso ao admin).
  Config `EMAIL_*` SMTP via env (test=locmem) + `CANAL_REGULARIZACAO_URL`. Template minuta CONGELADA (GATE-LGPD-RAT). 7 testes.
- **Fatia 3b-3 DONE** (2026-06-16): model `NotificacaoInadimplencia` (INSERT-only, migration 0007 RLS+WORM) = prova de
  envio; job grava prova só se e-mail enviado (fail-closed CDC); idempotência por `UNIQUE(tenant,titulo,marco)`; marco por
  janela. Fail-closed no adapter: perfil A não entra na régua sem prova. 22 testes Fatia 3b verdes. **Módulo CR: Fatia 3b
  (inadimplência) COMPLETA.**
- **PRÓXIMO = Fatia 3c** (desbloqueio — GATE-CLI-6): query `tem_outra_vencida_em_aberto` exposta por CR + consumer NOVO em
  `clientes` de `contas_receber.pago` → encerra `ClienteBloqueio` + publica `cliente.desbloqueado` (idempotente; parcial
  mantém). Atenção RLS `upt_self_select` / toca `clientes` FECHADO (R14). Depois 3d (INV-FIN-* ao mestre + hooks) → P8
  (ADR reconcilia, molde 0083) / P9 (mutirão auditores).
- **Migration test_afere:** router faz DDL só em `migrator` fora de pytest; aplicar nova migration ao test_afere =
  `migrate --database=default` com `-e PYTEST_CURRENT_TEST=1 -e DATABASE_URL=...@db/test_afere` (NÃO dropar — perde extensões).
- **Débitos p/ P9:** snapshot webhook=valor_original (sem juros); desconto-pontualidade pré-vencimento sem fórmula;
  isolamento por-consumer do bus (re-review quando a saga sair do stub).
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
