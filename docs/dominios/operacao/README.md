---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Domínio: Operação

## O que é este domínio

Operação agrupa **tudo da execução de serviços** depois que o orçamento foi aprovado: chamados técnicos, ordens de serviço, agenda de técnicos, deslocamento, execução de campo/laboratório, encerramento. É o coração do produto pra empresas de assistência técnica + calibração.

## Fronteiras com outros domínios

- **Entra:** chamado, OS, agenda de técnico, deslocamento + GPS, checklist, fotos, assinatura cliente, encerramento de OS.
- **NÃO entra (vai pra Comercial):** orçamento, contrato, prospecção.
- **NÃO entra (vai pra Metrologia):** emissão de certificado, cálculo de incerteza, signatário técnico — embora a OS DE CALIBRAÇÃO dispare o fluxo metrológico.
- **NÃO entra (vai pra Financeiro):** comissão liquidada, NFS-e emitida, contas a receber — embora a OS concluída ALIMENTE esses fluxos.
- **NÃO entra (vai pra Suporte-Plataforma):** consumo de estoque (a OS consome, mas o sistema de estoque é outro domínio).

## Módulos deste domínio

| Módulo | Status | Pasta | Cobertura discovery |
|---|---|---|---|
| Ordens de Serviço (OS) | ⏳ a especificar | `modulos/os/` | OP3 (Wave A) — ~75% mapeado |
| Chamados / Helpdesk | ⏳ a especificar | `modulos/chamados/` | OP15 (nova) — extrair de OP3 |
| Agenda / Programação | ⏳ a especificar | `modulos/agenda/` | OP10 — anunciada mas **não desenvolvida** ⚠️ |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Núcleo:
- **Técnico de campo** (UMC + veículo + app mobile)
- **Metrologista de bancada** (lab interno — também toca Metrologia)
- **Atendente** (abre chamado + agenda)
- **Gerente operacional** (vê fila + atribui + redistribui)
- **Cliente final** (acompanha via portal)

## Compliance específico

- **INV-020 Lei 13.103/2015** — motorista profissional (UMC): jornada 11h ininterruptas + descanso 30min/5h30. Hook valida agenda da UMC. **Crítico.**
- **ISO 17025 cláusula 7.10** — não-conformidade bloqueia emissão de certificado (`conformidade-iso-17025.md`). OS marca a NC; calibração trata.
- **LGPD RAT-07** — geolocalização técnico de campo + RIPD obrigatória.
- **RAT-08** — audit log de toda ação CRUD em OS.

## Integrações com outros domínios

Eventos catalogados em `../../comum/integracoes-inter-modulos.md`:
- Operação ← Comercial: `OrcamentoAprovado` cria OS rascunho
- Operação → Metrologia: `OSConcluida` (tipo calibração) dispara certificado rascunho
- Operação → Financeiro: `OSConcluida` (qualquer tipo) dispara cobrança / NFS-e
- Operação → Suporte-Plataforma: consumo de peça baixa estoque (com aceite 2-etapas)
- Operação → Comercial: `OSConcluida` alimenta timeline 360° + NPS

## ADRs específicos do domínio

- ADR-0003 — Mobile do técnico de campo (stub criado; especificar quando F-D começar)
- ADR-0004 — **Sync strategy mobile** (offline-first; conflitos por entidade) — **bloqueia F-D**

## Status do domínio

🟡 **OP3 (OS) é a maior cobertura do MVP-1; OP10 Agenda é lacuna estrutural; OP15 Chamados precisa ser destacada de OP3.** Eventos entre módulos do domínio bem mapeados. **Bloqueio:** sem agenda formalizada, OS roda sem programação consistente.
