---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Contratos de Export — Módulo Agenda

> Relatórios e arquivos do módulo. Exports trabalhistas (INV-020) têm valor legal de auditoria — preservar.

---

## Export 1: Relatório de jornada UMC (PDF/XLSX) — REGULADO

**Propósito:** comprovar cumprimento Lei 13.103 + CLT 235-C em auditoria trabalhista ou fiscalização MTE.
**Formato:** PDF/UA (oficial) + XLSX (operacional).
**Regulado?:** sim — Lei 13.103/2015, CLT art. 235-C.
**Campos obrigatórios:** técnico (nome + CPF mascarado), período, jornadas (início/fim/duração), intervalos de 30min, descansos de 11h, tempo-espera registrado, violações tentadas e bloqueadas (com timestamp e ator).
**Assinatura digital:** opcional (ICP-Brasil A1) — recomendada pra valor probatório.
**Imutabilidade:** sim — gerado a partir de EventoAgenda + EventoAuditoria (append-only).
**Retenção:** 5 anos (compatível com prescrição trabalhista) — ver `../../../conformidade/comum/retencao-matriz.md`.

---

## Export 2: Agenda semanal (PDF/ICS)

**Propósito:** entregar pra técnico (impressão) ou importar em calendário externo (Google/Outlook — read-only).
**Formato:** PDF (impressão) + ICS RFC 5545 (import).
**Regulado?:** não.
**Campos:** eventos do técnico no período, cliente (mascarado se exportador não é o próprio técnico ou gerente), endereço, deslocamento estimado.
**Retenção:** geração on-demand.

---

## Export 3: Relatório de ocupação por técnico (XLSX)

**Propósito:** gerente avalia carga vs capacidade.
**Campos:** técnico, período, horas alocadas (por tipo), capacidade, % ocupação, reagendamentos, violações INV-020 bloqueadas.
**Filtros:** período, técnico, tipo de evento.

---

## Export 4: Histórico de reagendamentos por OS (CSV)

**Propósito:** auditoria operacional — quantas vezes OS X foi remarcada.
**Campos:** os_id, número, transições de slot (de, para, ator, at, motivo).
**Fonte:** EventoAuditoria.

---

## Export 5: Audit log de agenda (JSONL)

**Propósito:** auditoria LGPD/trabalhista.
**Acesso:** DPO/auditor/RH. Audit do próprio acesso (INV-013).
**Retenção:** 5 anos.

---

## Exports inter-módulos

- Eventos `AgendaSlotAlocado` / `AgendaReagendada` → consumidos por **OS** (sincroniza estado AGENDADA) e por **Comercial** (notifica cliente, alimenta timeline 360°).
- `JornadaUMCViolada` (mesmo bloqueado) → alimenta dashboard de compliance trabalhista.

---

## Versionamento

Templates de relatório regulado versionados; mudança exige ADR (impacto auditoria).

## Como evolui

Export novo → adicionar. Mudança em relatório de jornada UMC → ADR + revisão jurídica.
