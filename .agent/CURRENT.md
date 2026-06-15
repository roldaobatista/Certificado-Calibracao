# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-15)

- Fatias 1a (domínio) + 1b (schema PG) DONE. Dep `os-multi-equipamento` FECHADA (envelope por item).
  Decisões Fatia 2 em `tasks.md`: D-FATIA2-A numeração BURACOS_ACEITOS · B série LAZY · C deps na view.
- **Ondas 2a/2b/2c-1 DONE:** criar+itens+`OrcamentoViewSet` · enviar/recusar/cancelar/expirar · item de
  calibração DECLARA mensurando (migration 0008).
- **Onda 2c-2 DONE (`243ce69`):** motor análise crítica cl. 7.1 + `aprovar_orcamento` (matriz A/B/C/D
  fail-closed; portas server-side; snapshot_hash ADR-0029). 7 auditores + `consultor-rbc` PASS (ACH-3 corrigido).
- **Onda 2d DONE (`b6aeadd`):** consumers `handle_os_aberta` (fecha saga→convertido) +
  `handle_cliente_anonimizado` (LGPD: rascunho cancela / enviado EXPIRA[Roldão] / aprovado+ preserva; dormente
  =GATE-ANON-EVENTO-RECONCILIAR). 7 auditores PASS.
- **Onda 2e DONE (2026-06-15):** REST PÚBLICO `OrcamentoPublicoView` (T-ORC-038) — GET allowlist anti-vazamento +
  POST aprovar 1-clique; token resolve tenant SEM RLS (SECURITY DEFINER migration 0009); rate-limit 30/min/IP;
  Aprovacao WORM aceite rico HMAC; `ressalvas_confirmadas` se `com_ressalva`; reprova A→422 sem Aprovacao; link
  one-shot. 7 auditores PASS zero MÉDIO+. **135 testes verdes** (1 flake transitório de ambiente descartado).
- **PRÓXIMO = Onda 2f** (T-ORC-050..054: cravar INV-ORC-* em REGRAS + hooks + contrato E2E envelope + UNHAPPY
  por perfil + anti-vazamento) → P8/P9. Pendentes: T-ORC-039 TemplateViewSet · GATEs 2e RATELIMIT-PUBLICO /
  LGPD-RETENCAO-APROVACAO / PUB-PERF / PUB-FORENSE.

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14, ADR-0082)

- Retrofit OS 1→N equipamentos + `ItemComercialOS`. P0→P9 (7 auditores, 2ª passada 4/4 PASS). 96 verdes.
  Débitos: **GATE-OSME-RECEBIMENTO-7.5** · **GATE-OS-AUTHZ-ACTION-MAP** (pré-existente). Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
