---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Modelo de domínio — Capacity Planning Operacional

## Entidades

### Recurso
- **Atributos:** id, tenant_id, tipo (tecnico|equipe|laboratorio), referencia_id (colaborador_id ou equipe_id ou lab_id), nome, ativo (bool)
- **Invariantes:** INV-TENANT-001; referencia_id válida no módulo origem (Colaboradores/Equipes/Laboratórios)

### CapacidadeBase
- **Atributos:** id, recurso_id, horas_semanais, dias_uteis[], vigencia_inicio, vigencia_fim (null = vigente)
- **Invariantes:** apenas uma vigente por recurso; mudança gera novo registro (versionado)

### Ausencia
- **Atributos:** id, recurso_id, tipo (ferias|atestado|treinamento|manutencao_lab), data_inicio, data_fim, horas_dia_afetadas
- **Invariantes:** períodos não sobrepõem por tipo "ferias"

### TipoServicoCapacidade
- **Atributos:** id, tipo_servico_id, recursos_elegiveis[], tempo_medio_minutos, tempo_override_minutos (nullable), atualizado_em
- **Invariantes:** tempo_medio recalculado dos últimos 90 dias de OS

### Alocacao
- **Atributos:** id, recurso_id, os_id (nullable), evento_agenda_id (nullable), data_inicio, data_fim, horas, status (planejada|confirmada|realizada|cancelada)
- **Invariantes:** ou os_id ou evento_agenda_id presente; soma de horas por dia ≤ capacidade efetiva diária

### PrevisaoDemanda
- **Atributos:** id, tipo_servico_id, semana_inicio, horas_previstas, fonte (historico|fila|sazonalidade|misto), calculado_em
- **Invariantes:** uma previsão por (tipo_servico, semana, fonte)

### Simulacao
- **Atributos:** id, criada_por_id, nome, descricao, criada_em, estado (rascunho|aplicada|descartada), payload_json
- **Invariantes:** simulação não afeta dados reais até "aplicar"

### Gargalo
- **Atributos:** id, recurso_id, periodo_inicio, periodo_fim, taxa_ocupacao, severidade (atencao|gargalo|sobrecarga), detectado_em, resolvido_em (null)
- **Invariantes:** um gargalo aberto por (recurso, janela)

### IndicacaoContratacao
- **Atributos:** id, tipo_servico_id, fte_sugerido, horizonte_semanas, justificativa, criada_em, status (aberta|encaminhada|rejeitada|atendida)

---

## Agregados

| Raiz | Inclui | Invariantes |
|---|---|---|
| Recurso | CapacidadeBase, Ausencia, Alocacao | soma alocações ≤ capacidade efetiva |
| Simulacao | (próprio) | isolada |
| Gargalo | (próprio) | dispara alerta ao abrir |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| JanelaTempo | (data_inicio, data_fim) | Sim |
| Ocupacao | (horas_disponiveis, horas_ocupadas, taxa) | Sim |
| Skill | (tipo_servico_id, nivel) | Sim |

---

## Eventos publicados

| Evento | Quando dispara | Payload | Consumidores |
|---|---|---|---|
| `CapacityPlanning.GargaloDetectado` | nova entrada em Gargalo | {recurso_id, janela, severidade} | Notificações, Métricas |
| `CapacityPlanning.SobrecargaDetectada` | ocupação > 100% | {recurso_id, janela} | Notificações |
| `CapacityPlanning.DistribuicaoSugerida` | motor sugere alocação | {os_id, recurso_id, score} | Agenda, OS |
| `CapacityPlanning.SimulacaoAplicada` | simulação vira realidade | {simulacao_id, mudancas[]} | Agenda |
| `CapacityPlanning.IndicacaoContratacao` | abre indicação | {tipo_servico, fte, horizonte} | RH/Colaboradores |

## Eventos consumidos

| Evento | Origem | Uso |
|---|---|---|
| `Agenda.EventoCriado/Alterado/Cancelado` | Agenda | atualizar Alocacao |
| `OS.OSCriada/Concluida/Cancelada` | OS | recalcular ocupação + tempo médio |
| `Colaboradores.AusenciaRegistrada` | Colaboradores | criar Ausencia |
| `Colaboradores.EscalaAtualizada` | Colaboradores | atualizar CapacidadeBase |

---

## Comandos

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| cadastrarRecurso | UI | tipo válido | Recurso criado |
| definirCapacidadeBase | UI | recurso ativo | CapacidadeBase vigente |
| registrarAusencia | UI / evento Colaboradores | datas válidas | Ausencia criada |
| simularCenario | UI gerente | — | Simulacao em rascunho |
| aplicarSimulacao | UI gerente | simulação válida | mudanças aplicadas + evento |
| sugerirDistribuicao | API / motor | OS sem recurso | DistribuicaoSugerida + evento |
| confirmarDistribuicao | UI | sugestão pendente | Alocacao criada |
| abrirIndicacaoContratacao | motor | delta sustentado > N semanas | IndicacaoContratacao + evento |

---

## Schema físico

Tabelas `cpo_recurso`, `cpo_capacidade_base`, `cpo_ausencia`, `cpo_alocacao`, `cpo_tipo_servico`, `cpo_previsao_demanda`, `cpo_simulacao`, `cpo_gargalo`, `cpo_indicacao_contratacao`. Schema detalhado em `../schema-banco.md` quando criado.

## Como evolui

Solver matemático → ADR. Heurísticas de sugestão → configuração tenant.
