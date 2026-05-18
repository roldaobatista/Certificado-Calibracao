---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 4-produto
auditor: auditor-produto
veredito: ADERENTE COM RESSALVAS
---

# AUDIT-04 — Aderência ao produto / AC / Non-goals / Scope creep

> Lente 4 de 10.

## VEREDITO

**ADERENTE COM RESSALVAS** — entrega substancialmente os AC das 5 US no escopo realista declarado. Sem funcionalidade fantasma nem violação grave de non-goal. Mas 1 AC documentado como cumprido sem teste que prove (performance), divergência de vocabulário glossário↔código, e descompasso PRD (PARCIAL) ↔ AGENTS (FECHADO).

## O que está bom (manter)

- US-CLI-001/003/004/005: cada AC com implementação real + teste nomeado. Dedup cross-tenant safe testado.
- Non-goals respeitados: sem ReceitaWS, sem UI, sem parsers nativos, sem async, sem rating. Código "magrelo" deliberado e anti-scope-creep explícito.
- Modelo de domínio ↔ models.py coerente nas entidades implementadas; Endereço/Contato/Segmento/Timeline corretamente NÃO implementados (nenhuma US do Marco 1 os exige).
- AC majoritariamente binários e verificáveis.

## Débitos

| ID | Descrição | Gravidade | AC/Non-goal | Arquivo | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| D1 | Plano US-CLI-002 lista `test_visao_360_performance_500_eventos_p95_abaixo_1500ms`, mas teste não existe. AC-CLI-002-2 cumprido só no papel. | ALTA | AC-CLI-002-2 | tests/test_clientes_us_cli_002_visao360.py | NÃO | Criar teste de performance OU rebaixar AC-002-2 no PRD com decisão registrada. |
| D2 | Glossário define "cliente master"/"perdedor"; código usa vencedor/perdedor, nunca "master". Mesmo conceito, nomes divergentes doc↔API. | MÉDIA | Glossário (princípio 1) | views.py, mesclar_clientes.py, glossario.md | risco replicar | Alinhar vocabulário; decidir 1 termo antes de equipamentos definir o seu. |
| D3 | AC-CLI-002-1 / AC-CLI-005-1 atendidos por contrato de evento (módulos não existem) — legítimo, mas PRD ainda diz "PARCIAL" enquanto AGENTS diz FECHADO. | MÉDIA | AC-CLI-002-1, AC-CLI-005-1 | prd.md:15,53-62,93 | replicar o padrão OK; o descompasso NÃO | Atualizar PRD: status + anotar "Marco 1: contrato; consumo Wave A". Sincronizar com AGENTS. |
| D4 | `importar_executar` aceita content_type application/octet-stream fora da whitelist do plano (4 tipos). Scope creep silencioso. | BAIXA | AC-CLI-003-1 | views.py:658-664,784-790 | decidir | Formalizar octet-stream no §2.1 ou remover. |
| D5 | `Cliente.bloqueado` é property que faz query; N+1 latente em listagens; contradiz NFR de performance. | BAIXA | NFR §8 / AC-CLI-002-2 | models.py:206-211 | NÃO o padrão property-com-query | select_related/anotação ao listar. |

## Recomendação final

Liberar Marco 2 com 2 condições: (1) resolver D1 e D3 (criar teste de performance ou rebaixar AC formalmente + sincronizar PRD↔AGENTS↔planos); (2) decidir vocabulário (D2) antes de equipamentos definir glossário. Sem desvio de escopo nem feature inventada — o risco é AC verde sem teste e drift PRD↔código mascarando dívida sob "FECHADO". NÃO propagar o hábito de listar testes no plano que não chegam ao arquivo.
