# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-14)

- Fatias 1a (domínio, 45 testes) + 1b (schema PG, drill 20/20) DONE. Dep `os-multi-equipamento` FECHADA
  (envelope por item). P3 aprovado (`tech-lead`+`consultor-rbc`). Decisões Fatia 2 em `tasks.md`:
  D-FATIA2-A numeração BURACOS_ACEITOS (Roldão pode pedir gap-less) · B série LAZY · C deps `calcular_precos` na view.
- **Ondas 2a+2b DONE (2026-06-14):** criar+itens+`OrcamentoViewSet` (2a; conserto REGRA #0 `semaforo` 10→15,
  migration 0007) + enviar/recusar/cancelar/expirar (2b; eventos outbox, LinkPublico token 256b, motivo hasheado).
  Camada A 6 auditores PASS em cada. GATEs: EXPIRY-JOB · TRILHA-CANCELAMENTO (BAIXO). Totais: imposto por dentro.
- **Onda 2c-1 DONE (2026-06-14):** parecer `consultor-rbc` CONFIRMA D-ORC-5 (+6 ajustes). GAP REGRA #0:
  `Equipamento` não tem grandeza/faixa → o **item de calibração DECLARA o mensurando** (migration 0008:
  `grandeza_solicitada`/`faixa_solicitada_min/max`/`unidade_solicitada` + CHECK + validação fail-fast `Grandeza`/
  `FaixaMedicao`). **95 testes verdes** no módulo. Matriz validada A/B/C/D em `analise-critica-matriz.md`.
- **PRÓXIMO = Onda 2c-2** (motor análise crítica + `aprovar_orcamento`): implementar a matriz de
  `docs/faseamento/orcamentos/analise-critica-matriz.md` (AJUSTE-3 perfil A suspenso = fail-closed; itens_avaliados
  ricos; snapshot_hash ADR-0029; envelope `orcamento.aprovado`) → 2d consumers → 2e REST público → 2f + P8/P9.
  **Camada A de auditores + 2ª revisão consultor-rbc PENDENTE (rodar no fechamento da 2c).**

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14)

- Retrofit OS 1→N equipamentos (equip. por atividade) + `ItemComercialOS`. Aditivo/reversível. ADR-0082.
  Ritual P0→P9 (P9: 7 auditores → 2ª passada 4/4 PASS). Regressão OS **96 verdes**.
- Débitos: **GATE-OSME-RECEBIMENTO-7.5** (enforcement recebimento por atividade) · **GATE-OS-AUTHZ-ACTION-MAP**
  (`os.atualizar` não seedado em reagendar/transferir/cancelar/dispensa/reabrir — bug pré-existente).
  Detalhe: `matriz-reconciliacao.md` (ata P9) + `docs/faseamento/diario/`.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
