---
owner: advogado-saas-regulado (subagente consultivo — NÃO substitui OAB)
revisado-em: 2026-05-20
status: stable
---

# Review advogado — T-CLI-107 + T-CLI-110

Veredito: **AJUSTAR** (todos absorvidos — ver `design.md`).

## Decisões A1..A4

- **A1** (PII em `acao`) → **SIM**, CHECK constraint
  `acao_formato_enum_semantico` + `acoes_canonicas.py`. LGPD art. 46
  (segurança) + art. 6º III (minimização).
- **A2** (retenção 7d) → **compatível**, mas precisa linha explícita
  na `retencao-matriz.md` §2 + DRILL-RET-11 mensal. LGPD art. 37 +
  art. 6º X. 7 dias = ponto de equilíbrio entre observabilidade e
  minimização (24h = insuficiente; 30d = excessivo).
- **A3** (cascata LGPD esquecimento) → **cascata SOMENTE em
  offboarding tenant** (cenário C da matriz). Pedido de titular
  individual (cenário B) NÃO toca `bus_outbox` — minimização cumprida
  pelo cleanup natural 7d. Anonimização art. 18 opera sobre cadeia
  F-A (fonte da verdade).
- **A4** (`ultimo_erro` PII) → **OBRIGATÓRIO** sanitizar +
  truncar 500 chars. Helper `sanitizar_erro_para_outbox` reusa
  `sanitizar_payload_audit`. Bloqueia incidente reportável ANPD Res.
  15/2024.

## Bloqueantes adicionais

- **BLOQ-A5** (`causation_id` correlação cruzada) → restringir SELECT
  a perfis `dpo` + `sre_aferê` + nota no ADR-0019 ("`causation_id` é
  dado pessoal indireto sob LGPD art. 12").
- **BLOQ-A6** (direito de acesso / portabilidade — art. 18 II e V) →
  **`bus_outbox` fora do escopo**. Fila intermediária ≤ 7d não é
  "tratamento durável" pra fins de art. 18; F-A é a fonte da verdade.
  Documentar em `lgpd_policy.py` (`INV-CLI-002`).
- **BLOQ-A7** (DPO inspecionar fila envenenada sem PII) → view
  `bus_outbox_diagnostico` (sem `envelope_jsonb`) + endpoint
  `/dpo/outbox-quarentena` (perfil dedicado AuthorizationProvider).
  Pode ser job separado dentro do mesmo T-CLI ou virar P-CLI futuro.
  Mínimo agora: management command `listar_outbox_envenenado` (cobre
  BLOQ-B do tech-lead também).

## Sugestões (SUG)

- SUG-1: métrica de PII slip-through (OBS-003 Wave A).
- SUG-2: minuta de cláusula DPA Aferê↔tenant pra fila intermediária
  (texto consultivo — advogado OAB valida quando 1º tenant externo
  chegar).
- SUG-3: política `lgpd_policy.py` `POLITICA_BUS_OUTBOX` declara
  natureza, base legal herdada, prazo, cascata, exclusão de art. 18.

## Limites honestos

- **Não substituo OAB.** Toda redação contratual (DPA, ToS,
  privacidade) precisa advogado licenciado.
- DPO formal (LGPD art. 41) pendente — backlog Wave A pré-1º tenant
  externo.
- Cláusula DPA da SUG-2 é minuta consultiva — não assinar sem revisão
  humana.

## Tabela de riscos consolidada

| ID | Risco | Prob | Impacto | Sev | Mitigação |
|---|---|---|---|---|---|
| BLOQ-A1 | PII em `acao` por engano | M | A | BLOQ | CHECK + enum canônico |
| BLOQ-A2 | Retenção contestada | B | M | BLOQ | Linha matriz + drill mensal |
| BLOQ-A3 | Cascata indevida (titular) | M | A | BLOQ | Diferenciar B vs C |
| BLOQ-A4 | PII em `ultimo_erro` | A | A | BLOQ | Helper sanitiza + 500c |
| BLOQ-A5 | Correlação `causation_id` | B | M | BLOQ | Acesso restrito + ADR |
| BLOQ-A6 | Resposta ambígua art. 18 | B | M | BLOQ | Documento explícito |
| BLOQ-A7 | Fila envenenada com PII | M | A | BLOQ | View diagnóstico sem envelope |
| SUG-1 | PII slip-through sanitizador | B | A | SUG | Métrica Wave A |
| SUG-2 | DPA sem cláusula fila | M | M | SUG | Cláusula com OAB |
| SUG-3 | Política LGPD não documenta | M | B | SUG | `POLITICA_BUS_OUTBOX` em `lgpd_policy.py` |
