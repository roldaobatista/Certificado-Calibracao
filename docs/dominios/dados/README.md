---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/novas funcionalidades.txt
---

# Domínio: Dados (BI, Indicadores e Inteligência Gerencial)

## O que é este domínio

Domínio **Dados** agrupa tudo o que tange a leitura agregada do negócio: dashboards, indicadores (KPIs), relatórios customizados, fluxo de caixa projetado, DRE, e qualquer visão que combina dados de **vários módulos transacionais** para responder perguntas do tipo "como vai a empresa?".

Não é um módulo operacional — é a camada de leitura/análise sobre tudo o que os outros domínios produzem.

## Por que este domínio existe (limite com outros)

**Entra neste domínio:**
- Consolidação de indicadores trans-módulos (financeiro + operacional + comercial juntos).
- Dashboards configuráveis por papel.
- Relatórios customizados, agendamento de envio, links públicos de dashboard.
- Materialização de dados (data marts internos) e camada de leitura otimizada.

**NÃO entra (e fica em outros domínios):**
- Relatórios operacionais do dia-a-dia do módulo (ex: "fila de OS hoje") — vivem no próprio módulo.
- Emissão de NF-e, certificados, contratos — Financeiro/Metrologia/Comercial.
- Auditoria/WORM/trilha imutável — Suporte-Plataforma (Família 3 Segurança).

## Módulos deste domínio

| Módulo | Status | Pasta |
|---|---|---|
| BI, Indicadores e Inteligência Gerencial | Wave B / V2 — draft | `modulos/bi/` |

> Outros candidatos futuros (não criados ainda): `relatorios-regulatorios/`, `data-export-publico/`.

## Personas que tocam este domínio

Ver `personas.md` deste domínio + `docs/comum/personas.md`. Personas principais:
- **P1 Dono/sócio** — consome KPIs financeiros e operacionais consolidados.
- **P2 Gerente operacional** — consome dashboards de produtividade, SLA, fila.
- **Analista (nova persona específica deste domínio)** — configura relatórios, exporta dados.

## Compliance específico

- **LGPD:** dashboards públicos ou compartilhados **não podem expor dado pessoal** sem agregação. Ver `../../conformidade/comum/lgpd-rat.md`.
- **Isolamento multi-tenant:** todo agregado respeita `INV-TENANT-001..004`. Hook `tenant-id-validator` valida queries.
- **Retenção:** dados agregados seguem a matriz de `../../conformidade/comum/retencao-matriz.md` (pendente).

## Integrações com outros domínios

- **Todos os domínios operacionais → Dados:** publicam eventos de domínio que materializam-se em data marts.
- **Dados → Suporte-Plataforma:** consome trilha de auditoria para indicadores de governança.
- Ver `../../comum/integracoes-inter-modulos.md`.

## ADRs específicos do domínio

- A criar: ADR sobre estratégia de materialização (views vs jobs procrastinate vs CDC).
- A criar: ADR sobre permissão de link público de dashboard (riscos LGPD).

## Status no roadmap

**Wave B / V2.** MVP-1 entrega apenas relatórios fixos por módulo (não este domínio inteiro). BI completo entra após Foundation F-A + Wave A consolidadas.
