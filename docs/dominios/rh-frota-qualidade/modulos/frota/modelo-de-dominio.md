---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Modelo de domínio — Frota

## Agregados

### Veiculo (agregado raiz)
- `id`, `tenant_id` (INV-TENANT-002), `placa` (UNIQUE com tenant_id), `chassi`, `renavam`, `modelo`, `marca`, `ano_fabricacao`, `ano_modelo`, `categoria` (enum: CARRO, MOTO, VAN, UMC, CAMINHAO), `cor`, `combustivel` (enum), `km_atual`, `data_aquisicao`, `valor_aquisicao?`, `ativo`, `crlv_url?`, `seguradora?`, `apolice?`.
- Invariantes:
  - Veículo categoria UMC requer pelo menos um motorista UMC vinculado ao tenant antes de ser agendado em OS de campo.
  - `km_atual` é monotônico crescente (atualizado por abastecimento ou OS); rejeitar UPDATE que diminua sem flag de correção.

### Atribuicao (entidade)
- `id`, `veiculo_id`, `colaborador_id`, `data_inicio`, `data_fim?`, `tipo` (FIXA, POR_OS, POOL).
- Invariante: Atribuir veículo a colaborador sem papel MOTORISTA (ou MOTORISTA_UMC se UMC) é bloqueado.

### Jornada (entidade — coração do INV-020)
- `id`, `veiculo_id`, `colaborador_id` (motorista), `os_id?` (link Operação), `inicio_direcao` (timestamp), `fim_direcao?`, `pausas` (lista de `{inicio, fim, tipo}` — tipo: DESCANSO_30MIN, REFEICAO, ESPERA), `tempo_total_direcao` (calculado), `tempo_espera` (calculado — sobreaviso 1/3 CLT 235-C §9), `validada_em?`, `assinatura_motorista?`.
- **INV-020 — invariantes ativas:**
  - Não pode iniciar nova jornada antes de 11h do `fim_direcao` da jornada anterior do mesmo motorista.
  - A cada 5h30 acumuladas de direção dentro da jornada, precisa de pausa DESCANSO_30MIN antes de retomar.
  - Hook valida no AGENDAMENTO da OS (preditivo) e no EXECUTIVO (motorista tentando iniciar).

### Manutencao (entidade)
- `id`, `veiculo_id`, `tipo` (PREVENTIVA, CORRETIVA), `data_servico`, `km_servico`, `descricao`, `oficina`, `valor`, `nota_fiscal_url?`, `proxima_revisao_km?`, `proxima_revisao_data?`.

### Abastecimento (entidade)
- `id`, `veiculo_id`, `colaborador_id`, `data`, `km`, `litros`, `valor_total`, `valor_por_litro` (calculado), `posto`, `combustivel`, `nota_fiscal_url?`, `caixa_tecnico_id?` (FK Financeiro).

### ChecklistPreViagem (entidade)
- `id`, `veiculo_id`, `colaborador_id`, `os_id?`, `data`, `itens` (lista `{descricao, marcado, critico}`), `bloqueante_nao_resolvido` (calculado), `assinatura?`.
- Invariante: Iniciar OS de campo (UMC) com item crítico não-marcado é bloqueado. Itens críticos default: "padrões com calibração vigente", "padrões com verificação intermediária OK" (INV-022), "pneus + freio + óleo OK", "certificados de padrão a bordo".

### CRLV / IPVA / Multa / Sinistro
- Entidades simples MVP-1 (registro + anexo + data). Workflow administrativo = V2.

## Relacionamentos

- Veiculo 1—N Atribuicao
- Veiculo 1—N Jornada
- Veiculo 1—N Manutencao
- Veiculo 1—N Abastecimento
- Veiculo 1—N ChecklistPreViagem
- Veiculo N—1 Tenant
- Jornada N—1 Colaborador (motorista — RH)
- Abastecimento N—0..1 CaixaTecnico (Financeiro — OP3.2)
- Veiculo 1—N OS (Operação) — atribuição por agendamento

## INV-020 detalhado (motor de jornada)

**Lei 13.103/2015 + CLT 235-C §9 — regras codificadas:**

1. **11h ininterruptas entre jornadas:** `inicio_direcao_nova ≥ fim_direcao_anterior + 11h`.
2. **30 min descanso a cada 5h30:** Dentro de uma jornada, soma de direção desde último DESCANSO_30MIN não excede 5h30 sem nova pausa.
3. **Tempo-espera = 1/3 do salário-hora (sobreaviso):** Marcado, calculado pelo Financeiro (regra aqui = registrar o evento).
4. **Direção em 24h ≤ 10h** ([INFERÊNCIA — confirmar Lei 13.103]; tratar como soft-alerta MVP-1, hard-block após confirmação jurídica).

**Hook:**
- `validate_inv020_on_schedule(os_id, motorista_id, veiculo_id, inicio_previsto, duracao_estimada)` → retorna `{ok, violacao?, recomendacao?}`.
- Disparado em: criação de OS, edição de horário, troca de motorista, início efetivo da jornada.

**Notificações:**
- T-5h25 de direção: push "Pare em 5 minutos pra descansar 30 min (Lei 13.103)".
- T-10h45 ininterruptas: push "Encerre a jornada em 15 min (Lei 13.103)".

## Eventos

`VeiculoCadastrado`, `JornadaIniciada`, `JornadaEncerrada`, `PausaRegistrada`, `Inv020Violado` (P0), `ChecklistCompletado`, `ManutencaoVencida`.

## Não-modelado MVP-1

GPS, telemetria, roteirização, processo administrativo de multa, gestão de pneu. → V2+.

## Dúvidas em aberto

- [INFERÊNCIA] Tempo-espera 1/3: confirmar fórmula exata com `subagent advogado-saas-regulado` antes de Financeiro implementar.
- [INFERÊNCIA] Categoria CNH exigida por categoria de veículo: tabela seed (B, C, D, E) — mapear no implementation.
