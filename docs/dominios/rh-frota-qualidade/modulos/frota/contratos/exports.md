---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Contrato Exports — Frota

## E-FRT-01 — Comprovante de jornada (PDF — CRÍTICO INV-020)
- **Quem dispara:** Motorista (próprio) + Gerente + Dono.
- **Conteúdo:** Identificação motorista + veículo, data, segmentos de direção, pausas, totais, citação à Lei 13.103/2015 + CLT 235-C, assinatura digital opcional.
- **Formato:** PDF/UA conforme (INV-016).
- **Uso:** Fiscalização rodoviária + auditoria trabalhista + audit interno.
- **Período:** Dia, semana, mês ou range.
- **Audit:** Geração registrada (INV-001).

## E-FRT-02 — Histórico de manutenção do veículo (PDF/Excel)
- Por veículo, com todos registros + valores + oficinas.
- Uso: Venda do veículo, garantia, auditoria fiscal.

## E-FRT-03 — Consumo / abastecimento (Excel)
- Colunas: Data, Veículo, Motorista, Km, Litros, R$/L, R$ total, Posto, NF anexa (link).
- Filtros: Veículo, Motorista, Período, Combustível.
- Cálculo derivado: Km/L do trecho entre abastecimentos.

## E-FRT-04 — Checklist pré-viagem (PDF assinável)
- Por OS, comprovação de que checklist foi feito antes da saída.
- Uso: Auditoria de qualidade interna + ISO 17025 cl. 6.4 (equipamento).

## E-FRT-05 — Lista de veículos (Excel/CSV)
- Para visão administrativa + cruzamento contábil.

## E-FRT-06 — Caixa do técnico reconciliado (PDF — link com Financeiro)
- Detalhado em módulo Financeiro.

## E-FRT-07 — Relatório de jornadas no mês (Excel — input pra cálculo trabalhista)
- Por motorista: horas dirigidas, horas-espera (sobreaviso), pausas, eventos INV-020 evitados.
- **AVISO obrigatório no topo:** "Este relatório é insumo. A folha de pagamento e o cálculo de horas extras não estão incluídos no MVP-1. Use com seu contador."

## Não-existem MVP-1

- Relatório de TCO (Wave C).
- Mapa de rotas (V2+ com GPS).
- Indicadores de telemetria (V2+).
- Eficiência de roteirização (V2+).

## Mascaramento LGPD

- Placa visível pra dono/gerente; mascarada pra cliente final em relatório de OS.
- Localização GPS (V2): tratamento de dado pessoal sensível — RIPD obrigatório.

## Auditoria

Todo export grava: usuário, timestamp, escopo, contagem de linhas (INV-001).

## Formatos

XLSX, CSV UTF-8 BOM, PDF/UA. ZIP pra exports massivos.
