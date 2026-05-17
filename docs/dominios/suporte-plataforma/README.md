---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Domínio: Suporte-Plataforma

## O que é este domínio

Suporte-Plataforma agrupa **os ativos físicos + catálogos que sustentam a operação**: equipamentos calibrados pelo tenant para seus clientes (instrumentos em campo), produtos/peças/serviços do catálogo do tenant, estoque (multi-local), fornecedores, padrões metrológicos (lab interno).

## Fronteiras com outros domínios

- **Entra:** cadastro de equipamento do cliente, catálogo de produto/peça/serviço, estoque multi-local, fornecedor, padrão metrológico (pesos, ferramentas de referência).
- **NÃO entra (vai pra Metrologia):** processo de calibração em si, cálculo de incerteza, certificado emitido — embora o equipamento ESTEJA no centro do certificado.
- **NÃO entra (vai pra Comercial):** cliente final do tenant.
- **NÃO entra (vai pra Operação):** OS que consome a peça — embora o consumo BAIXE o estoque.
- **NÃO entra (vai pra Financeiro):** custo da peça em valor monetário — embora o catálogo INFORME o custo.

## Módulos deste domínio

| Módulo | Status | Pasta | Cobertura discovery |
|---|---|---|---|
| Equipamentos do cliente | ⏳ a especificar | `modulos/equipamentos/` | OP16 (nova) — Wave A |
| Produtos/Peças/Serviços (catálogo) | ⏳ a especificar | `modulos/produtos-pecas-servicos/` | Gap — proposta MVP-2 |
| Estoque multi-local | ⏳ a especificar | `modulos/estoque/` | BIG-12 + 6 JTBDs Wave B |
| Fornecedores | ⏳ a especificar | `modulos/fornecedores/` | OP13 (nova) — Wave C |
| Padrões metrológicos (pesos/ferramentas) | ⏳ a especificar | `modulos/padroes-metrologicos/` | INV-021 (novo); INV-022 verificação intermediária |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Núcleo:
- **Almoxarife** (estoque)
- **Metrologista de bancada** (escolhe padrão pra cada calibração)
- **Comprador / responsável de compras** (relação com fornecedor)
- **Técnico de campo** (consome peça no campo; transferência 2-etapas com aceite)
- **Auditor CGCRE** (V2 — verifica rastreabilidade de padrão)

## Compliance específico

- **ISO 17025 cláusula 6.5 (rastreabilidade metrológica):** padrão usado tem certificado próprio rastreável; classe declarada
- **INV-021:** pesos padrão com classe ISO 16834 + certificado de calibração próprio
- **INV-022:** verificação intermediária de padrão em uso ≤ intervalo de re-calibração
- **Sucata/descarte:** peças vencidas/obsoletas seguem norma ambiental (descarte controlado)
- **Selo INMETRO rastreável (BIG-12):** transferência 2-etapas + foto obrigatória do lacre

## Integrações com outros domínios

- Suporte-Plataforma → Operação: peça reservada pra OS; consumo automático ao concluir
- Suporte-Plataforma → Metrologia: padrão selecionado pra calibração (rastreabilidade)
- Suporte-Plataforma → Financeiro: cotação de compra vira contas a pagar
- Suporte-Plataforma ← Comercial: equipamento vinculado a cliente (visão 360°)

## ADRs específicos do domínio

A criar conforme módulos amadurecem. Possíveis:
- ADR estoque (estratégia de reserva otimista vs pessimista)
- ADR fornecedores (relação direta vs via marketplace)

## Status do domínio

🟡 **Estoque (BIG-12) é diferencial real mas Wave B; Equipamentos (OP16 nova) suporta OP2/OP3 em Wave A; Fornecedores é Wave C. Catálogo (produtos/peças/serviços) é gap MVP-1.** Padrões metrológicos têm INVs novos (021/022) que destravam acreditação RBC.
