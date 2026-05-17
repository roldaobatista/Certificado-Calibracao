---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Contrato API — Frota

> Stack pendente (ADR-0001). Convenções REST + JSON abaixo.

## Veículos

### `GET /api/v1/veiculos`
- Query: `categoria?`, `status?`, `responsavel_id?`, `q?` (placa/modelo).

### `POST /api/v1/veiculos`
- Validação placa formato + dedup `(tenant_id, placa)`.

### `GET|PATCH|DELETE /api/v1/veiculos/{id}`
- DELETE = soft (inativar). Hard delete bloqueado se há OS/jornada referenciando.

### `POST /api/v1/veiculos/{id}/atribuicoes`
- Body: `{ colaborador_id, data_inicio, data_fim?, tipo }`.
- Erro 422 `MOTORISTA_SEM_PAPEL` se colaborador não tem papel MOTORISTA (ou MOTORISTA_UMC quando categoria=UMC).

## Jornada (INV-020 — CRÍTICO)

### `POST /api/v1/jornadas:check`
- **Idempotente, sem efeito colateral.** Usado pelo agendador da OS.
- Body: `{ motorista_id, veiculo_id, inicio_previsto, duracao_estimada_h }`.
- Resposta:
  ```json
  { "ok": false, "violacao": "INV-020-11H", "detalhe": "Última jornada encerrou às 22h. Próxima jornada só pode iniciar a partir das 09h.", "recomendacoes": [ ... ] }
  ```
- Códigos de violação: `INV-020-11H` (11h ininterruptas), `INV-020-5H30` (5h30 sem pausa), `INV-020-10H-24H` (limite 10h/24h — [INFERÊNCIA]).

### `POST /api/v1/jornadas`
- Inicia jornada. Body: `{ veiculo_id, motorista_id, os_id?, inicio_direcao }`.
- Erro 409 `INV-020-VIOLACAO` se viola 11h.

### `POST /api/v1/jornadas/{id}/pausas`
- Body: `{ inicio, fim?, tipo: DESCANSO_30MIN|REFEICAO|ESPERA }`.

### `POST /api/v1/jornadas/{id}:encerrar`
- Body: `{ fim_direcao, observacao? }`.

### `GET /api/v1/jornadas/{id}/comprovante`
- Retorna PDF/UA assinável (INV-016).

### `GET /api/v1/motoristas/{id}/jornada-atual`
- Resposta: `{ status, tempo_direcao_acumulado, tempo_ate_proxima_pausa, jornada_id }`.

## Manutenção

### `GET|POST /api/v1/veiculos/{id}/manutencoes`

## Abastecimento

### `GET|POST /api/v1/veiculos/{id}/abastecimentos`
- POST exige `km` ≥ `km_atual` do veículo (rejeita 422 se menor sem flag).

## Checklist pré-viagem

### `POST /api/v1/checklists-pre-viagem`
- Body: `{ veiculo_id, colaborador_id, os_id?, itens: [{descricao, marcado, critico}] }`.
- Resposta inclui `pode_iniciar_os` (bool).

## Caixa do técnico (OP3.2)

### `POST /api/v1/caixas-tecnico` (proxy pro Financeiro)
- Endpoints completos em `dominios/financeiro/.../caixa-tecnico/contratos/api.md`.

## Webhooks (saída)

- `inv020.violacao` — payload com tenant, motorista, jornada, tipo violação. P0.
- `manutencao.vencida` — diário.
- `crlv.vencendo` — 60/30/15 dias antes.

## Rate limit

[INFERÊNCIA] 200 req/min motorista app (alta frequência por GPS futuro). 60 req/min gerente.

## Erros padronizados

`MOTORISTA_SEM_PAPEL`, `MOTORISTA_SEM_CNH`, `INV-020-11H`, `INV-020-5H30`, `INV-020-10H-24H`, `PLACA_INVALIDA`, `KM_RETROATIVO`, `CHECKLIST_CRITICO_PENDENTE`, `VEICULO_INATIVO`.

## Não-existem MVP-1

Endpoints de GPS, telemetria, roteirização, OBD-II. → V2+.
