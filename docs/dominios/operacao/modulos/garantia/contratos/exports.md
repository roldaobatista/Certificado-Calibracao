---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: garantia
dominio: operacao
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Garantia

> Formatos de saída. Nenhum export regulado fiscal nasce neste módulo (fiscal vive em Financeiro/Fiscal).

---

## Exports

### Export 1: Laudo de Garantia (PDF)

**Propósito:** entregar ao cliente / arquivar laudo da decisão.
**Formato:** PDF (PDF/UA — `INV-016`).
**Regulado?:** não (boa prática CDC).
**Validador:** validador interno PDF/UA.
**Template:** `templates/garantia/laudo.html` (a criar quando Foundation F-A começar).
**Campos obrigatórios:** garantia_id, OS-mãe, OS-filha, cliente, tipo, decisão, parcela_cobravel_pct, causa_raiz, texto, anexos referenciados, assinatura+timestamp, hash do laudo.
**Assinatura digital:** assinatura do responsável (A1 mínimo nos perfis B/C/D — `INV-017` análogo quando aplicável a documento legal).
**Imutável pós-emissão:** sim (`INV-001`).
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md` — defesa contra ação CDC (5 anos mínimos).

**Exemplo (snippet):**
```
LAUDO DE GARANTIA Nº GAR-2026-000123
OS-mãe: OS-2026-005678  |  OS-filha: OS-2026-005899
Decisão: PROCEDENTE   |   Causa raiz: DEFEITO_PECA
Parcela cobrável: 0%
Assinado por: Fulano da Silva (CPF ***.***.***-)
Hash: sha256:abc...
```

---

### Export 2: Relatório de Custo de Garantia (XLSX)

**Propósito:** gerente analisa custo do retrabalho.
**Formato:** XLSX.
**Regulado?:** não.
**Campos:** período, OS-filha, OS-mãe, cliente, técnico, custo_mao_obra, custo_peca, custo_deslocamento, custo_total, decisão, causa_raiz.
**Assinatura:** não.
**Imutável:** não — relatório operacional.
**Retenção:** uso operacional; replicável on-demand.

---

### Export 3: Relatório de Reincidência (XLSX + CSV)

**Propósito:** análise externa, planilha do dono.
**Formato:** XLSX e CSV.
**Campos:** escopo (cliente/técnico/peça/equipamento), id, nome, qtd_procedentes_6m, primeira_data, ultima_data, OSs_referencia[].
**Assinatura:** não.
**Imutável:** não.

---

### Export 4: Dossiê de Garantia-Fornecedor (PDF + anexos)

**Propósito:** evidência ao fornecedor pra ressarcimento.
**Formato:** PDF com anexos compilados.
**Campos:** garantia, peça, nota de remessa, laudo técnico, fotos do defeito, valor pleiteado.
**Assinatura:** carimbo do tempo (recomendado) — não é fiscal.
**Imutável:** sim após enviar (`INV-001`).
**Retenção:** mínimo 5 anos (defesa em caso de não-ressarcimento).

---

## Exports inter-módulos

- Laudo de Garantia (Export 1) → consumido pelo módulo OS (anexa na OS-filha).
- Relatório de Custo (Export 2) → consumido pelo Financeiro pra fechamento mensal.
- Reincidência (Export 3) → consumido pelo CRM (alertar atendimento sobre cliente reincidente) e Engenharia (peça-modelo problemática).

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento

Templates versionados; mudança em layout do laudo → ADR (impacta documento legal).

## Como evolui

Export novo → adicionar + validar acessibilidade PDF/UA quando regulado/legal.
