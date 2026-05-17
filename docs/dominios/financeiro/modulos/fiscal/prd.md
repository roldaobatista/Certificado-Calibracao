---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# PRD — Fiscal (NFS-e + NFe)

## 1. O que é

Emissão, cancelamento, correção e contingência de documentos fiscais (NFS-e municipal + NFe estadual quando aplicável). Integração via BaaS (PlugNotas/Focus) pra abstrair heterogeneidade de 5500+ municípios.

## 2. Por que existe

Dor #10 (NFS-e multi-município) — Big Job 04 (BIG-04). **Deadline regulatório 01/09/2026** (Porto Alegre 01/07/2026): municípios saem do padrão local pro CONFAZ 95/22 nacional. Sem isso, Aferê = receita zero (tenant não consegue faturar serviço).

Wave A #1 absoluto. Top 3 lock obrigatório.

## 3. Personas

P-FIN-01 (emite NFS-e), P-FIN-02 (dono — vê emissões/cancelamentos), P-FIN-05 (contador externo — V2 SPED), P-FIN-06 (auditor fiscal — V2 acesso indireto).

## 4. Escopo MVP-1 (Wave A)

- Emitir NFS-e em ≥ 70% dos municípios via BaaS (cobertura ABRASF + grandes capitais)
- Cancelar NFS-e (< 24h)
- Emitir CC-e (correção)
- Contingência automática via BaaS (SVC-AN/SVC-RS pra NFe; mecanismos do município pra NFS-e)
- Inutilização de numeração
- Configuração tenant: regime fiscal + alíquotas + código LC 116 (tenant configura com contador)
- WORM 5 anos do XML
- UI estado "operando em contingência"
- Audit completo de cada emissão/cancelamento
- Plug & play do certificado digital (A1; A3 conforme ADR-0009)

## 5. Escopo cutover 01/09/2026

- Smoke test sandbox 30 dias antes
- Comunicado aos tenants 15 dias antes
- Modo "rascunho postergado" durante semana de cutover
- Suporte estendido
- Postmortem

## 6. Non-goals MVP-1 (explícitos)

- **Aferê NÃO calcula imposto** — só exibe campos pra preenchimento orientado pelo contador.
- Cálculo de ISS/ICMS automático.
- Apuração mensal contábil (responsabilidade contador externo).
- SPED Fiscal export — V2.
- NFe completa (V2 — calibração emite NFS-e majoritariamente; NFe entra quando tenant vende peça).
- DDA (Débito Direto Autorizado).
- Cobertura de FP2 exclusivos (Vitória) — verificar BaaS antes de aceitar tenant da região (`fiscal.md`).
- Integração com sistema contábil externo (Domínio/Alterdata) — V2.
- Lucro Real complexo / ZFM SUFRAMA particular (anti-persona).

## 7. User Stories

- **US-FIS-001:** OS concluída + cliente paga → tenant emite NFS-e em 1 toque (pré-preenchida) → cliente recebe XML+PDF por email.
- **US-FIS-002:** SEFAZ/município fora → sistema entra em contingência **automática** (SVC ou mecanismo do município); UI mostra "Operando em contingência"; tenant continua emitindo.
- **US-FIS-003:** tenant emite NFS-e com valor errado → cancela em < 24h.
- **US-FIS-004:** erro corrigível (descrição) → CC-e em 1 toque.
- **US-FIS-005:** numeração pulou → sistema alerta "Inutilize {N-M} até dia X"; tenant 1 toque inutiliza.
- **US-FIS-006:** contador externo (V2) acessa export read-only com audit reforçado.

## 8. NFR

- Emissão p95 < 5s (depende de SEFAZ/município)
- Disponibilidade: 99,5% emissão (BaaS define SLA upstream)
- Contingência automática: detecção < 60s, troca de modo sem intervenção
- WORM: imutabilidade verificável por hash

## 9. Invariantes

- **INV-007 — NF-e contingência desde dia 0** (inegociável; sem contingência = não vai pra produção)
- INV-008 — audit log obrigatório de cada emissão/cancelamento/correção
- XML original preservado em WORM 5 anos

## 10. Dependências

- Contas a Receber (origem do trigger de emissão pós-`Pago`)
- OP-FIN (módulo financeiro mínimo)
- ADR-0008 (FiscalProvider — fiscal pluggable)
- ADR-0009 (onde A3 assina)
- BaaS escolhido (PlugNotas ou Focus — abstraído)
