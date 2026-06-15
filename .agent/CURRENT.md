# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-14)

- Fatias 1a (domínio, 45 testes) + 1b (schema PG, drill 20/20) DONE. Dep `os-multi-equipamento` FECHADA
  (envelope por item). P3 aprovado (`tech-lead`+`consultor-rbc`). Decisões Fatia 2 em `tasks.md`:
  D-FATIA2-A numeração BURACOS_ACEITOS (Roldão pode pedir gap-less) · B série LAZY · C deps `calcular_precos` na view.
- **Onda 2a DONE (2026-06-14):** `criar_orcamento` + `adicionar_item`/`editar_item` + `OrcamentoViewSet`
  (criar/itens/editar/retrieve/list). Conserto REGRA #0: campo `semaforo` 10→15 (migration 0007 — `indisponivel`
  estourava o INSERT). 6 auditores camada A PASS (2 MÉDIO de cobertura consertados + 2ª passada). **20 testes
  verdes** (7 puros `calculo` + 13 E2E). Totais: imposto por dentro, `liquido == total_bruto - descontos`.
- **Onda 2b DONE (2026-06-14):** `enviar` (congela V1 + LinkPublico token 256b + evento `orcamento.enviado`) +
  `recusar`/`cancelar`/`expirar-vencidos` (eventos outbox; motivo hasheado; sweep idempotente). 6 auditores
  camada A PASS. **+7 testes E2E** (72 verdes no módulo). GATEs novos: EXPIRY-JOB · TRILHA-CANCELAMENTO (BAIXO).
- **PRÓXIMO = Onda 2c** (`aprovar_orcamento` interno: análise crítica cl.7.1 perfil-aware A/B/C/D +
  `AnaliseCriticaOrcamento` WORM + envelope `orcamento.aprovado` por item) → 2d consumers → 2e REST público →
  2f testes + P8/P9. Detalhe: `docs/faseamento/orcamentos/{spec,plan,tasks}.md`.

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
