---
owner: roldao
revisado_em: 2026-05-30
status: stable
diataxis: explanation
audiencia: agente
proposito: índice da documentação completa do Aferê Prumo (camada de IA), importada e versionada DENTRO do repo do Aferê
---

# Aferê Prumo — documentação completa (LEIA PRIMEIRO)

> **O que é esta pasta:** a documentação **completa** do **Aferê Prumo** (a camada de IA do Aferê),
> **copiada e versionada DENTRO do repositório do Aferê** em 2026-05-30. Antes ela vivia só no projeto
> irmão `C:/projetos/balancas-solution-ia/` (pasta solta, não-versionada) — agora está aqui, junto do
> código, à prova de mover/clonar/apagar. **Esta é a fonte de verdade da doc do Aferê Prumo daqui pra frente.**

## Ordem de leitura (ao construir o Aferê Prumo, em Wave B/C)

1. **`ENCAIXE-NO-AFERE.md`** ⭐ — mapa de encaixe: o que reusar do Aferê, o que construir, em que ordem, o que falta.
2. **`descoberta/sintese-final.md`** — o resumo de tudo (problema, personas, 23 decisões de produto, riscos, métricas).
3. **`descoberta/agentes.md`** — as **10 fichas-contrato dos agentes** (= o PRD dos agentes: o que cada um faz, ações permitidas, o que nunca faz, escalonamento).
4. **`descoberta/regras-negocio.md`** — regras reais + tom de voz (extraído de conversas reais) + exemplos.
5. **`descoberta/exemplos-saida-ia.md`** — 25 exemplos de resposta da IA validados pelo dono.
6. **`adr/ADR-0000/0001/0002`** — uso de IA (multi-LLM + Maritaca), stack/integração (IA = domínio no Aferê), multi-empresa/armazenamento (pgvector + Hostinger). Todos aceitos.
7. **`adr/AUDITORIA-CEGA-ARQUITETURA-2026-05-29.md`** — validação por 10 arquitetos independentes (Opus).
8. **`adr/ADR-0000-benchmark-llms.md`** — comparação custo×qualidade de LLMs (texto/áudio/busca).

## O que NÃO está aqui (matéria-prima pesada — 24 GB)

A documentação (texto, ~1 MB) está toda aqui. A **matéria-prima coletada** (24 GB) **não** foi copiada
(grande demais pra repositório git) — continua em `C:/projetos/balancas-solution-ia/docs/descoberta/dados-reais/`:
- **Cérebro técnico** (1.099 fontes, ~84 MB): manuais Toledo, normas OIML/Inmetro → insumo do `DocumentSearchProvider` (carga inicial, Onda 0).
- **Drive bruto** (13.986 documentos baixados) — origem do cérebro.
- **Áudios do WhatsApp** (1.120 `.opus`) + transcrições — origem do tom de voz.
- **Banco Auvo** (sqlite: 341 clientes, 389 produtos, 429 orçamentos) → insumo da migração Auvo→Aferê.

> ⚠️ **Pendência (a decidir com o dono):** essa matéria-prima de 24 GB precisa de um lar mais seguro que
> uma pasta solta (backup externo, armazenamento em nuvem, ou recoleta na hora da construção). Não bloqueia
> agora (só é usada na construção em Wave B/C), mas não deixar só na pasta solta indefinidamente.

## Estado

Aferê Prumo = **descoberto + arquitetado + encaixado**, **PAUSADO** até Wave B/C (decisão do dono 2026-05-30:
ritmo normal, não antecipar). Ver `../evolucao/afere-prumo-trilha-ia.md` (resumo no roadmap) e `AGENTS.md §1`.
