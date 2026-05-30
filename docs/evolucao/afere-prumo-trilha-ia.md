---
owner: roldao
revisado_em: 2026-05-30
proximo_review: 2026-08-30
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/arquitetura/anti-corrosion-layer.md
  - docs/adr/0000-uso-de-ia.md
  - docs/adr/0005-engine-automacoes.md
  - docs/adr/0059-llmprovider.md
---

# Aferê Prumo — trilha da camada de IA (entra em Wave B/C)

> **Ponteiro/marcador.** A camada de IA do Aferê — produto **"Aferê Prumo"** — foi **descoberta e arquitetada
> por completo** num projeto irmão. Este documento marca **ONDE ela entra no roadmap do Aferê** e aponta pra
> documentação completa, pra não se perder quando o Aferê chegar em Wave B/C.
>
> ✅ **ATUALIZAÇÃO 2026-05-30:** a documentação completa foi **copiada e versionada NESTE repo** em
> **`docs/afere-prumo/`** (antes só no projeto irmão, pasta não-versionada). Comece por
> **`docs/afere-prumo/LEIA-PRIMEIRO.md`**. Os caminhos `C:/projetos/balancas-solution-ia/...` citados abaixo
> são a ORIGEM; a **fonte de verdade agora é `docs/afere-prumo/`**.
>
> **Importante:** é o **mesmo desenvolvedor (Claude Code) + dono (Roldão)** nos dois projetos. "Encaixar o Aferê
> Prumo" = numa sessão futura no contexto deste repo (Aferê), retomar a documentação abaixo e construir, seguindo
> o ritual normal do Aferê (PRD do módulo → spec → plan → tasks → implementação + drill PASS ZERO).

## 1. O que é o Aferê Prumo

Camada de IA (cérebro + agentes por setor) vendida como **add-on do Aferê**. Atende o cliente no **WhatsApp
(majoritariamente áudio)**, monta orçamento, abre OS, confere certificado, avisa prazos de recalibração — sempre
com **aprovação humana** (human-in-the-loop). **Decisão de arquitetura fechada:** é um **DOMÍNIO DENTRO do Aferê**
(não um sistema separado), **reusando as portas** do anti-corrosion layer — não reconstrói nada.

## 2. Quando entra: Wave B/C (ritmo normal)

Decisão do dono (2026-05-30): **ritmo normal, sem antecipar.** O Aferê Prumo entra quando o Aferê amadurecer até
**Wave B/C** — precisa do **MVP-1 rodando com dados reais** (clientes, OS, certificados na Balanças Solution) pra
a IA ter sobre o que agir. Não divide o time/esforço durante o MVP-1.

## 3. O que construir (resumo — detalhe no mapa de encaixe)

**Portas novas em `src/infrastructure/`** (várias já previstas no roadmap, hoje só documentadas):
- `llm/` — `LLMGateway` (LiteLLM + Anthropic + **Maritaca**; `model_class fast|deep|br-sovereign`) — ADR-0059 (Onda 3 plano-v2)
- `omnichannel/` — WhatsApp Cloud API (Meta direto) — módulo `comunicacao-omnichannel` (Wave B.1)
- `docsearch/` — busca **vetorial** (pgvector + híbrida BM25) — evolui `gestao-documental` (Wave B.3)
- `bpm/` — motor de automações (`ProcrastinateBpmEngine`) + **editor visual** por cima — `automacoes-bpm` (Wave B.3, ADR-0005)
- `stt/` — transcrição de áudio local (whisper.cpp) — **porta NOVA** (nem está no anti-corrosion layer hoje)

**Domínio novo:** `src/domain/copiloto` (+ `src/application/copiloto`) — agentes por setor, roteador, Inbox de
aprovação, regras de comportamento configuráveis por empresa.

**Reusa direto (não recria):** `multitenant` (RLS), `authz`, `audit`, `webhook_out`, `tenant`, `usuario`, e os
módulos núcleo (`clientes`, `ordens_servico`, `equipamentos`, `calibracao`, `certificados`, `orcamentos`).

## 4. Documentação completa (projeto irmão `balancas-solution-ia`)

Tudo em `C:/projetos/balancas-solution-ia/`:
- **`docs/ENCAIXE-NO-AFERE.md`** ⭐ — mapa de encaixe (LER PRIMEIRO ao retomar): dependências, ordem, decisão de roadmap.
- `docs/descoberta/` — `sintese-final.md` (stable), **`agentes.md`** (10 fichas-contrato = PRD dos agentes), `regras-negocio.md` (tom de voz + regras reais), `exemplos-saida-ia.md` (25 exemplos validados pelo dono).
- `docs/adr/ADR-0000/0001/0002` — uso de IA (multi-LLM + Maritaca), stack/integração (IA = domínio no Aferê), multi-empresa/armazenamento (pgvector + Hostinger). **Todos aceitos.**
- `docs/adr/AUDITORIA-CEGA-ARQUITETURA-2026-05-29.md` — validação por 10 arquitetos independentes (Opus).
- `dados-reais/_banco/cerebro/` — **1.099 fontes** já coletadas (manuais Toledo, normas OIML/Inmetro) = insumo do `docsearch`.

## 5. Decisões-chave já fechadas (não reabrir sem motivo)

- IA = **domínio dentro do Aferê** (reusa as 19 portas; escreve só pelas portas/serviços, nunca SQL direto).
- **Multi-LLM sem lock-in** via `LLMGateway`; default provisório **Sabiá (Maritaca) na frente + Claude reserva** (testar no piloto).
- **Tudo na Hostinger** (mesmo VPS do Aferê; whisper roda em CPU no volume inicial).
- **Transcrição local** (whisper) — áudio não sai do Brasil (LGPD).
- **Editor visual** = casca sobre o `BpmEngineProvider`, não produto do zero.
