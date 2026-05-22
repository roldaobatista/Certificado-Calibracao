---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
modulo: calibracao
dominio: metrologia
---

# Métricas do módulo Calibração

> KPIs de negócio + SLI/SLO técnico + métricas regulatórias CGCRE. Detalhe operacional em `../../../operacao/observabilidade.md` (a criar — GATE-OBS-CAL-1 Wave A pós F-C).
>
> **Reescrito em 2026-05-23 (Onda 7C — NOVO-ALTO-15 R2):** retrofit pós-auditoria rodada 2. Todas as métricas carregam `tenant_id` como label/dimensão obrigatória (OBS-002). Cadeia `correlation_id` carregada em todos os logs. Adicionados: ciclo CAPA, alertas padrão-vencido-mid-uso, NC por padrão/cliente/executor, SLO regulatório CGCRE marcado.

---

## KPIs de negócio

Toda métrica carrega `tenant_id` como label/dimensão obrigatória (OBS-002 — INV-OBS-002) + `correlation_id` em log.

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Calibrações concluídas no prazo | `Calibracao.APROVADA` antes do prazo prometido na OS | ≥ 85% | timestamp transições + `os.prazo_prometido` | semanal |
| Tempo médio RECEPCIONADA→APROVADA | Horas úteis BR via workalendar (feriados móveis) | ≤ 5 dias úteis | timestamp transições da máquina de estados Calibracao | semanal |
| Taxa de NC em calibração | `Calibracao` com status NAO_CONFORME ÷ total Calibracao no período | ≤ 8% | máquina de estados | mensal |
| **Taxa de NC por padrão** | NC ÷ total calibrações por padrão usado (rolling 90d) | ≤ 5% por padrão | join Calibracao × PadraoUsado | mensal |
| **Taxa de NC por cliente** | NC ÷ total calibrações por cliente (rolling 90d) | tendência ↓ | join Calibracao × Cliente | mensal |
| **Taxa de NC por executor** | NC ÷ total calibrações por `executor_id` (rolling 90d) | identificar outlier | join Calibracao × Usuario | mensal |
| **Taxa de NC por método** | NC ÷ total por `metodo` da `ConfiguracaoCalibracao` (rolling 90d) | tendência ↓ | join Calibracao × ConfiguracaoCalibracao | trimestral |
| **Tempo médio CONTIDA→FECHADA (ciclo CAPA)** | NaoConformidade.created_at → status=FECHADA | ≤ 14 dias úteis | máquina de estados NaoConformidade | mensal |
| **% NCs reabertas** | NaoConformidade com status=REABERTA (eficácia INEFICAZ) ÷ total | ≤ 10% | snapshot status NaoConformidade | trimestral |
| **% calibrações sob exceção 6.2.5** | Calibrações onde `executor==revisor` ÷ total (ADR-0026 + INV-CAL-CONF-001) | ≤ 5%/mês | flag exceção registrada | mensal — gestor de qualidade revisa trimestralmente |
| Taxa de correção de leitura | `LeituraCorrecao` ÷ total Leitura na calibração (cl. 7.5) | < 10% (indicador competência executor) | count `leitura_correcao` ÷ count `leitura` | mensal |
| Tempo médio de revisão (REVISAO_1) | Horas úteis entre `LeiturasFinalizadas` e `RevisadaPrimeira` | ≤ 1 dia útil | timestamp eventos | semanal |
| Tempo médio de 2ª conferência | Horas úteis entre `RevisadaPrimeira` e `SegundaConferenciaAprovada` | ≤ 1 dia útil | timestamp eventos | semanal |
| Cobertura de ensaios complementares | Calibrações com `EnsaioComplementar` ÷ total que método exige | ≥ 95% | join Calibracao × EnsaioComplementar × metodo | trimestral |

---

## SLI/SLO técnico

Todas SLI carregam `tenant_id` como dimensão.

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade API Calibração | 99.9% | 43min/mês |
| Latência p95 GET /calibracao/{id} | < 500ms | — |
| Latência p95 POST /calibracao/{id}/calcular-incerteza | < 3s | — |
| Latência p95 POST /calibracao/{id}/revisoes | < 1s | — |
| Taxa de erro 5xx | < 0.1% | — |
| **Lag export PG → B2 WORM** (`EventoDeCalibracao`) | < 1h | absoluto — perda implica recall regulatório |

---

## SLOs regulatórios CGCRE (Pós-F-C — promovidos de KPI a SLO duro)

Métricas com **erro orçamento ZERO ABSOLUTO** — qualquer violação dispara alerta P0 + bloqueio operacional automático.

| SLO regulatório | Target absoluto | Justificativa |
|---|---|---|
| **Calibrações RBC fora do escopo CMC** | = 0 | INV-002 + INV-015 — fraude regulatória |
| **Padrões usados fora de vigência** | = 0 | INV-011 + INV-CAL-RAST-001 — cadeia metrológica quebrada |
| **Certificados emitidos sem 2ª conferência** | = 0 | INV-CAL-CONF-001 — NC crítica CGCRE |
| **Certificados sem RT habilitado na grandeza na data execução** | = 0 | INV-CER-COMP-001 + INV-CAL-RT-001 |
| **Replay determinístico do motor de incerteza falha** | = 0 | ADR-0025 + INV-CAL-VAL-003 |

---

## Dashboards canônicos (por persona)

| Persona | Painel | Métricas-chave |
|---|---|---|
| P-METR-01 metrologista bancada | "Fila de calibração" | Calibrações em RECEPCIONADA/CONFIGURADA/EM_EXECUCAO + tempo desde último evento + NC abertas |
| P-METR-02 RT signatário | "Revisão + 2ª conferência" | Calibrações aguardando REVISAO_1/CONFERENCIA_2 + tempo desde 1ª revisão + competência alertas |
| P-METR-03 gestor de qualidade | "CAPA + tendência" | NaoConformidade abertas + ciclo CAPA por estado + % reabertura + reincidência padrão/cliente/executor |
| P-METR-04 recepcionista | "Recepção hoje" | RecepcaoItemCalibracao pendente + aptidão + aceites cliente pendentes |

- **Grafana:** [link a definir pós ADR-0001]
- **Axiom (logs):** [link]

---

## Alertas (todos carregam tenant_id + correlation_id)

| Alerta | Quando dispara | Notificado | Severidade | Ação acionável |
|---|---|---|---|---|
| Cert padrão a 30 dias do vencimento | `Padroes.CertificadoVencendo` | RT + Qualidade | P3 | agendar calibração externa |
| **Cert padrão venceu mid-calibração** (NOVO-MÉD-3 R2) | `PadraoUsado.snapshot_padrao.data_validade < now()` e Calibração com este padrão em status NÃO terminal | RT + Qualidade | **P1** | reiniciar calibração com padrão vigente |
| VI reprovada | `Padroes.VerificacaoIntermediariaReprovada` | RT + Qualidade | P2 | abrir CAPA + bloqueio uso padrão |
| Medição de controle FAIL (3σ) | `Padroes.MedicaoControleAlertaFAIL` | RT + Qualidade | P1 | abrir CAPA automática + bloqueio padrão |
| EP escore z ≥ 3 | `Proficiencia.EscoreInsatisfatorio` | RT + Qualidade | P1 | abrir CAPA + investigar grandeza/método |
| Calibração travada em revisão > 7 dias úteis | snapshot status `EM_REVISAO_1`/`AGUARDANDO_2A_CONFERENCIA` há > 7d úteis | RT + gerente operacional | P2 | redistribuir RT |
| Taxa de exceção 6.2.5 > 5%/mês | rolling count exceções/mês | gestor de qualidade | P2 | ADR-0026 revisão trimestral |
| % NCs reabertas > 10%/trimestre | rolling count REABERTA/FECHADA | gestor de qualidade | P2 | análise sistêmica causa-raiz |
| Lag export PG → B2 > 1h | `evento_wal_export_lag_seconds` | oncall + RT | **P1** | risco de perda definitiva de audit WORM |
| Reincidência NC mesmo padrão > 5/30d | rolling NC por padrão | RT + gestor qualidade | P1 | retirar padrão de uso |

---

## Métricas de saúde dos agentes neste módulo

- Tokens consumidos / US-CAL-NNN entregue
- Taxa de retrabalho IA (US reaberta após "concluída")
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + configurar coleta + bump CHANGELOG. SLO regulatório CGCRE muda → ADR + parecer consultor-rbc-iso17025 humano antes do aceite.
