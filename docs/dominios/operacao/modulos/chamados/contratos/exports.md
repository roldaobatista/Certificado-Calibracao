---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Contratos de Export — Módulo Chamados

> Relatórios e arquivos do módulo. Não há exports regulados aqui (chamado é interno até virar OS).

---

## Export 1: Relatório de SLA (XLSX)

**Propósito:** gerente avalia cumprimento de SLA por período/tipo/atendente.
**Formato:** XLSX.
**Campos:** período, total chamados, % triados no prazo, % resolvidos no prazo, escalados, mediana tempo triagem, mediana tempo resolução, por atendente, por tipo, por urgência.
**Filtros:** período, tipo, atendente, canal.
**Retenção:** indefinida (gerencial).

---

## Export 2: Histórico de chamado do cliente (PDF)

**Propósito:** cliente solicita LGPD art. 18 (acesso aos seus dados) — exporta todos os chamados dele.
**Formato:** PDF/UA (INV-016).
**Regulado?:** sim (LGPD acesso aos dados).
**Campos:** todos os chamados do cliente + mensagens + eventos, telefone mascarado salvo no PDF do próprio titular.
**Acesso:** o próprio cliente (via portal) ou DPO sob requisição.
**Retenção:** geração on-demand; não armazena cópia permanente.

---

## Export 3: Fila de chamados (CSV)

**Propósito:** snapshot pra análise externa.
**Formato:** CSV UTF-8 com BOM.
**Campos:** id, número, estado, canal, cliente (mascarado se exportador não tem permissão), tipo, urgência, sla_alvo_at, sla_consumido_pct, atribuido_a, criado_at.

---

## Export 4: Audit log de chamado (JSONL)

**Propósito:** auditoria LGPD/operação — todo EventoDoChamado.
**Acesso:** DPO/auditor. Audit do próprio acesso (INV-013).
**Retenção:** matriz `../../../conformidade/comum/retencao-matriz.md` (mínimo 2 anos).

---

## Exports inter-módulos

- `ChamadoConvertidoEmOS` → módulo OS recebe `os_origem_chamado_id` e copia texto/anexos relevantes.
- Mensagens do chamado alimentam timeline 360° em **Comercial** (CRM).

---

## Versionamento

Templates de relatório/PDF versionados; PDF/UA conformance obrigatória (INV-016).

## Como evolui

Export novo → adicionar + validar PDF/UA se PDF.
