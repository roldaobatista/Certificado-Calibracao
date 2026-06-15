# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-15)

- Fatias 1a (domínio) + 1b (schema PG) DONE. Dep `os-multi-equipamento` FECHADA (envelope por item).
  Decisões Fatia 2 em `tasks.md`: D-FATIA2-A numeração BURACOS_ACEITOS · B série LAZY · C deps na view.
- **Ondas 2a–2d DONE:** criar+itens+`OrcamentoViewSet` · enviar/recusar/cancelar/expirar · mensurando
  declarado (mig 0008) · motor análise crítica cl. 7.1 + `aprovar_orcamento` (matriz A/B/C/D fail-closed;
  snapshot_hash ADR-0029) · consumers `os.aberta`(saga→convertido)+`cliente_anonimizado` (LGPD). Detalhe: diário.
- **Onda 2e DONE (`dc15f10`):** REST PÚBLICO `OrcamentoPublicoView` — GET allowlist + POST aprovar 1-clique;
  token resolve tenant SEM RLS (SECURITY DEFINER mig 0009); rate-limit; Aprovacao WORM HMAC; reprova A→422; one-shot.
- **Onda 2f DONE (2026-06-15):** família INV-ORC-* cravada em REGRAS (+EXP-001 movida de invariantes-futuras) ·
  3 hooks pré-commit (margem-off/envelope-contrato/analise-perfil) no manifest · 3 testes regressão (contrato
  envelope produtor→consumidor / UNHAPPY por perfil 422+WORM / anti-vazamento allowlist) verdes. Runner de hooks
  0 falhas; camada A (seguranca/qualidade/llm-correctness) PASS zero MÉDIO+.
- **PRÓXIMO = P8** (T-ORC-060: ADR reconciliação `PrecoResolvido`×`Preco` + matriz-reconciliacao + STATUS-GERADO +
  GATEs rastreados) → **P9** (T-ORC-061: mutirão auditores roteados + 2ª passada escopada → FECHA orcamentos).
  Pendentes: T-ORC-039 TemplateViewSet · GATEs 2e (RATELIMIT/LGPD-RETENCAO/PUB-PERF/PUB-FORENSE) + EXPIRY-JOB.

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14, ADR-0082)

- Retrofit OS 1→N equipamentos + `ItemComercialOS`. P0→P9 (7 auditores, 2ª passada 4/4 PASS). 96 verdes.
  Débitos: **GATE-OSME-RECEBIMENTO-7.5** · **GATE-OS-AUTHZ-ACTION-MAP** (pré-existente). Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
