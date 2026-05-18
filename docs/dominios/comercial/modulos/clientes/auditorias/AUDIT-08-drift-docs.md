---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 8-drift-docs
auditor: auditor-drift-docs
veredito: DRIFT GRAVE
---

# AUDIT-08 — Drift Documentação vs Código real

> Lente 8 de 10.

## VEREDITO

**DRIFT GRAVE** — doc canônica de produto coerente, mas o `modelo-de-dominio.md` do clientes (exatamente o doc que o agente do Marco 2 vai ler como template de modelagem) descreve schema especulativo e divergente do models.py real. Replicar propaga modelagem fantasma.

## O que está coerente (confiar)

- Mapa tasks→commit→AC (tasks/US-CLI-001.md): commit b130577 existe, toca os arquivos certos, 8 testes confirmados. Rastreabilidade real.
- INV-024/036 implementadas no models.py:7-9 via UNIQUE parcial.
- ADR-0017 (CNPJ alfanumérico) coerente.
- Soft-delete US-CLI-005 bate doc↔código.

## Drift detectado

| ID | Doc afirma | Realidade | Grav. | Doc | Código | Correção |
|---|---|---|---|---|---|---|
| D1 | Entidades Endereço, Contato, Segmento, EventoTimeline no modelo | models.py só tem Cliente, ClienteBloqueio, ClienteImportacaoDeclaracao | GRAVE | modelo-de-dominio.md:22-36,40-44 | models.py | Marcar como "(planejado V2 — não no Marco 1)". |
| D2 | Atributos rating, ie, im, limite_credito, segmento_ids, criado_por; VOs LimiteCredito, BloqueioComercial | Nenhum existe; bloqueio é entidade 1:N | GRAVE | modelo-de-dominio.md:18,51-52 | models.py:41-201,261 | Reescrever conforme schema real. |
| D3 | lgpd_aceite_em, lgpd_aceite_versao | Reais: aceite_lgpd_em, aceite_lgpd_versao + 8 campos LGPD a mais | MODERADO | modelo-de-dominio.md:17 | models.py:86-165 | Corrigir nomes; listar os 10 campos reais. |
| D4 | status: draft no modelo/prd/glossario | Marco 1 FECHADO | MODERADO | modelo-de-dominio.md:4 etc. | (entregue) | Promover stable após reconciliar. |
| D5 | CLAUDE.md "8 hooks... Faltam 3"; _test-runner "23 casos" | 16 hooks reais; ~114 casos | MODERADO | CLAUDE.md:67,110 | .claude/hooks/ | Atualizar para 16 hooks; corrigir contagem. |
| D6 | AGENTS contraditório (103 vs 113 vs 71 vs 15 hooks/casos) | 16 hooks, ~114 casos | MODERADO | AGENTS.md:62,113,205,209 | .claude/hooks/ | Unificar num número verificado por _test-runner. |
| D7 | task: migration 0004_aceite_lgpd_e_origem.py | Real: 0004_aceite_lgpd.py | LEVE | tasks/US-CLI-001.md | migrations/ | Corrigir nome. |
| D8 | Sem âncora de total de INV | 82 IDs INV únicos; sem doc afirma total | LEVE | REGRAS-INEGOCIAVEIS.md | — | Total no frontmatter de REGRAS. |

## Recomendação final

A doc do clientes NÃO é confiável como referência de modelagem pro equipamentos. Confiável (template): tasks/US-CLI-*.md, docstrings do models.py, revisões dos subagentes. NÃO confiável: modelo-de-dominio.md (escrito no discovery, nunca reconciliado; descreve 4 entidades + ~6 atributos/VOs inexistentes). Ação antes do M2 /implement: reconciliar modelo-de-dominio com models.py (D1-D3), promover draft→stable só após reconciliar (D4), unificar contagem hooks/testes em CLAUDE+AGENTS a partir de execução real (D5-D6). D7-D8 higiene.
