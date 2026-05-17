---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Métricas — Colaboradores

## North Star

**% de OS cuja alocação de técnico bate com matriz de habilidades cadastrada** ≥ 95% (M+3).

## Métricas de adoção (MVP-1)

| ID | Métrica | Meta M+3 | Como medir | Fonte |
|---|---|---|---|---|
| M-COL-01 | % tenants com ≥1 colaborador cadastrado além do dono | ≥ 80% | COUNT colaboradores por tenant | DB |
| M-COL-02 | % colaboradores com ≥1 habilidade na matriz | ≥ 70% | COUNT habilidades / COUNT colaboradores | DB |
| M-COL-03 | Tempo médio de cadastro de colaborador (form submit) | ≤ 3 min | Telemetria UI | Front |
| M-COL-04 | % OS faturadas com técnico identificado (input pra comissão BIG-09) | ≥ 95% | COUNT OS com técnico / total | DB |

## Métricas de qualidade

| ID | Métrica | Meta | Fonte |
|---|---|---|---|
| M-COL-05 | % colaboradores com papel "signatário" que têm escopo declarado (INV-003) | 100% (bloqueio duro) | DB |
| M-COL-06 | Cadastros bloqueados por CPF duplicado | Reportar | DB |
| M-COL-07 | % colaboradores ativos com CPF/CNPJ válido (validador) | ≥ 99% | DB |

## Métricas de comissão (suporte ao BIG-09)

| ID | Métrica | Meta | Fonte |
|---|---|---|---|
| M-COL-08 | Erro absoluto de comissão calculada vs declarada pelo dono no mês 1 | ≤ R$ 0,01 por OS | Comparação Financeiro |
| M-COL-09 | % técnicos que validam % de comissão no perfil próprio (MVP-1.5) | ≥ 50% | Telemetria |

## Não medir no MVP-1

- Engajamento / NPS interno do colaborador (V2)
- Turnover (V2 — depende de desligamento bem registrado)
- Custo de mão-de-obra (depende de folha — V2)

## Telemetria mínima

Eventos: `colab_cadastrado`, `colab_papel_adicionado`, `colab_habilidade_adicionada`, `colab_desligado`, `colab_comissao_alterada`. Todos com `tenant_id` + `colab_id` (hash) + `papel_set`.

## Alarmes

- M-COL-05 < 100% → alerta P0 (INV-003).
- M-COL-08 > R$ 1,00 → investigar bug de cálculo (Financeiro).
