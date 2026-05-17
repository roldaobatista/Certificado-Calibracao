---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
---

# Contratos API — Módulo Contratos (recorrentes)

## Convenções

- Prefixo `/v1/contratos`.
- Endpoints públicos (cliente externo): `/v1/public/contratos/{token}`.
- `X-Tenant-ID` + Bearer nos internos.

## Endpoints internos

### `POST /v1/contratos`
Criar rascunho (US-CTR-001).
**Body:** `{cliente_id, escopo: [{equipamento_id, servico_id, quantidade, valor_unitario}], vigencia_inicio, vigencia_fim, periodicidade, reajuste?, template_id?}`
**Resposta 201:** `{id, numero, estado: "rascunho"}`
**Invariantes:** INV-TENANT-001, cliente ativo, vigência válida.

### `POST /v1/contratos/{id}/ativar`
Mudar rascunho → vigente após aprovação cliente.
**Pré:** LGPD aceite registrado + escopo válido.
**Pós:** agenda primeiro ciclo + evento `Contrato.Criado`.

### `GET /v1/contratos`
Lista filtrada.
**Query:** `estado[]`, `cliente_id`, `responsavel_id`, `vigencia_fim_em_ate`, `valor_min`.

### `GET /v1/contratos/{id}`
Detalhes + versão ativa + ciclos.

### `PATCH /v1/contratos/{id}`
Atualizar campos não-críticos (observação, responsável). **NÃO** muda escopo nem valor (use aditivo).

### `POST /v1/contratos/{id}/suspender` (Wave B)
**Body:** `{motivo, inicio, retomada_prevista}`
**Pré:** estado=vigente.
**Evento:** `Contrato.Suspenso`.

### `POST /v1/contratos/{id}/retomar` (Wave B)
**Pré:** estado=suspenso.

### `POST /v1/contratos/{id}/encerrar` (US-CTR-005)
**Body:** `{motivo, prejuizo_concreto?, justificativa}`
**Pré:** estado in [vigente, suspenso].
**Evento:** `Contrato.Encerrado`.
**Anti-fidelidade:** nunca cobrar mais que `prejuizo_concreto` justificado.

### `POST /v1/contratos/{id}/renovar` (US-CTR-004, Wave B)
**Body:** `{nova_vigencia, escopo_revisado?, valor_revisado?, observacoes?}`
**Pré:** estado=vigente, próximo ao fim (configurável).
**Pós:** cria contrato_novo + marca atual como `renovado` + aponta `substituido_por`.
**Evento:** `Contrato.Renovado`.

### `POST /v1/contratos/{id}/aditivar` (US-CTR-006, Wave B)
**Body:** `{motivo, snapshot_novo: {...}, aplica_a_partir_de}`
**Efeito:** nova versão.
**Evento:** `Contrato.Aditivado`.

### `GET /v1/contratos/{id}/ciclos`
Lista ciclos previstos + executados.

### `GET /v1/contratos/pre-os`
Bandeja de pré-OS pendentes de confirmação (US-CTR-002).
**Query:** `responsavel_id?`, `dias_pendentes_min`.

### `POST /v1/contratos/ciclos/{ciclo_id}/confirmar`
Atendente confirma pré-OS → OS formal.
**Body:** `{data_real?, tecnico_id?, observacoes?}`
**Evento:** `Contrato.OSConfirmada`.

### `POST /v1/contratos/ciclos/{ciclo_id}/skip`
Pular este ciclo (com motivo).
**Body:** `{motivo}`

### `GET /v1/contratos/{id}/pdf`
Download PDF do contrato (versão ativa).
Ver `exports.md`.

### `GET /v1/contratos/{id}/versoes`
Histórico de versões/aditivos.

## Endpoints públicos (cliente — sem auth)

### `GET /v1/public/contratos/{token}`
Carregar contrato pra aprovação ou consulta.
**Rate limit:** 30 req/min/IP.

### `POST /v1/public/contratos/{token}/aprovar`
Cliente aprova novo contrato/aditivo/renovação.
**Body:** `{nome_aprovador, email_aprovador, lgpd_aceite: true}`

### `POST /v1/public/contratos/{token}/encerrar` (US-CTR-005)
Cliente encerra (anti-fidelidade).
**Body:** `{motivo, confirmacao_2step: true}`
**Janela arrependimento:** 7 dias (cliente pode reverter via mesmo link).

### `POST /v1/public/contratos/{token}/pedir-ajuste`
**Body:** `{texto}` — notifica vendedor.

## Jobs (background)

### `POST /internal/jobs/gerar-pre-os` (cron diário)
Roda 1x/dia (configurável). Itera contratos vigentes com próxima_execucao ≤ hoje+7d.
**Métrica:** taxa de sucesso > 99.5%.

### `POST /internal/jobs/aplicar-reajuste` (cron mensal aniversário)
Aplica reajuste configurado na renovação automática.

### `POST /internal/jobs/disparar-alertas-vigencia` (cron diário)
Dispara alertas 90/60/30 dias antes do fim.

## Eventos consumidos

- `Cliente.Bloqueado/Desbloqueado` → atualiza flag de bloqueio nos contratos.
- `OS.Concluida` (operação) → marca ciclo como executado + agenda próximo.
- `Catalogo.PrecoAlterado` → **NÃO retroage** (INV-026); só afeta renovações futuras.

## Rate limits

- Endpoint público: 30 req/min/IP.
- POST encerrar público: 3 req/hora/IP (anti-bot).
- POST renovar/aditivar internos: 30 req/min/usuário.

## Versionamento

v1 → v2 janela 6 meses.

## Como evolui

Endpoint novo → US-CTR-NNN.
