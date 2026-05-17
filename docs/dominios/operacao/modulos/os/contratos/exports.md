---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Contratos de Export — Módulo OS

> Relatórios e arquivos gerados pelo módulo. Certificados são export da **Metrologia** (gerado a partir do evento `OSConcluida`), não desta pasta.

---

## Export 1: Comprovante de execução de OS (PDF)

**Propósito:** entregar ao cliente um PDF assinado eletronicamente com o que foi feito (foto, checklist, assinatura).
**Formato:** PDF/UA (acessível — INV-016).
**Regulado?:** não (entrega comercial). Para calibração, certificado oficial é exportado em Metrologia.
**Template:** `templates/os-comprovante.html` [a definir].
**Campos obrigatórios:** número da OS, cliente, equipamento, tipo, datas (início/fim), técnico, itens executados, fotos, assinatura do cliente, geo se OS de campo.
**Assinatura digital:** opcional (ICP-Brasil A1) — obriga apenas se tenant exigir.
**Imutabilidade:** sim a partir de OS CONCLUIDA.
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md`.

---

## Export 2: Relatório de produtividade do técnico (XLSX/CSV)

**Propósito:** gerente avalia carga e desempenho por técnico/período.
**Formato:** XLSX preferido; CSV alternativo.
**Regulado?:** não.
**Campos:** técnico, período, OSs CONCLUIDA, tempo médio, % no prazo, taxa de retrabalho, taxa de NC.
**Fonte:** view materializada agregando `os` + `os_evento`.
**Retenção:** indefinida (relatório gerencial).

---

## Export 3: Fila de OS por estado (CSV)

**Propósito:** snapshot da fila pra análise externa.
**Formato:** CSV (UTF-8 com BOM pro Excel BR).
**Campos:** id, número, estado, tipo, cliente, técnico, prazo, criada_at, dias_em_aberto.
**Filtros:** mesmos da `GET /v1/os` (estado, técnico, período).

---

## Export 4: Audit log de OS (JSON Lines)

**Propósito:** auditoria LGPD/ISO — todo `EventoDeOS` em formato exportável (RAT-08).
**Formato:** JSONL (1 linha por evento).
**Campos:** os_id, evento_tipo, payload, at, ator_id, geo (mascarada se RAT-07 exigir).
**Acesso:** apenas papel "auditor" / DPO. Audit do próprio acesso (INV-013).
**Retenção:** ver matriz (mínimo 5 anos pra OS de calibração — ISO 17025).

---

## Exports inter-módulos

- `OSConcluida` (tipo=calibracao) → consumido por **Metrologia** que gera o **certificado PDF assinado** (ISO 17025 cl. 7.8). Ver `../../../metrologia/modulos/calibracao/contratos/exports.md`.
- `OSConcluida` (qualquer tipo) → consumido por **Financeiro** que gera **NFS-e** + **boleto/cobrança**. Ver `../../../financeiro/`.

---

## Versionamento

Templates de PDF versionados; mudança visual em comprovante exige bump no CHANGELOG. PDF/UA conformance obrigatória (INV-016).

## Como evolui

Export novo → adicionar + validar PDF/UA se PDF. Mudança em template regulado → ADR.
