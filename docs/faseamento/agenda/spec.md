---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-16
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: agenda
tipo: spec
proximo-passo: P2 — revisão tech-lead + consultor-rbc (Lei 13.103 / ADR-0068)
relacionados:
  - docs/faseamento/agenda/T-AGE-000-investigacao.md
  - docs/dominios/operacao/modulos/agenda/prd.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0051-propagacao-adr0023-modulos.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/adr/0033-bus-idempotencia-consumer.md
---

# Spec — frente `agenda` (P1, derivada do PRD + T-AGE-000)

> Frente nível 5 (operação). Calendário gerencial multi-técnico que aloca **atividades de OS**,
> bloqueios e eventos nos slots dos técnicos, validando a **jornada UMC (Lei 13.103)** por perfil.
> Molde técnico = `ordens_servico` (vizinho de domínio) + ritual `contas-receber`.

## 1. O que é — e o que NÃO é (fronteiras)

**É:** o calendário que distribui o trabalho de campo: cada **`AtividadeDaOS`** (não a OS inteira —
ADR-0023/0051) ganha um técnico + uma janela de tempo; valida jornada/conflito/feriado ANTES de
gravar; materializa recorrências; registra no-show.

**Não é (fronteiras — D-AGE):**
- **Não é a dona do estado da atividade** (TL — seam OS). A agenda **chama** `atribuir_tecnico`
  (`application/operacao/os/`) para escrever `tecnico_executor_id`+`agendada_para`; a OS transita
  `PENDENTE→AGENDADA`. A agenda é o **caller** que valida a jornada UMC (AC-OS-002b-2, seam vazio hoje)
  ANTES de chamar. Não duplica a máquina de estados da OS.
- **Não calcula rota/deslocamento real** — `MapsProvider` = Wave B (GATE-AGE-MAPS); Wave A o gerente
  preenche o tempo manualmente.
- **Não notifica o cliente diretamente** — depende de `comunicacao-omnichannel` (DIFERIDO por bloqueio
  externo); Wave A o reagendamento grava e **enfileira** o aviso (GATE-AGE-OMNICHANNEL).
- **Não é o portal do cliente** — aprovação/contraproposta de janela = Wave B (GATE-AGE-PORTAL).
- **Não é capacity-planning** — sugestão de distribuição em lote = Wave B (GATE-AGE-CAPACITY); US-AG-006
  usa só lógica interna (RT substituto → competência → livre 7d).
- **Não reimplementa competência de RT** — reusa o predicate `rt_competencia_cobre` + `RTCompetencia`
  (ADR-0022) e escuta `tenant.rt.trocado` (ADR-0068).
- **Não cobra** — no-show cobrável **publica** para `contas-receber` (lançamento manual já existe).

## 2. Recorte núcleo Wave A vs diferido (por US)

| US | Núcleo Wave A | Diferido (GATE/Wave B) |
|----|---------------|------------------------|
| US-AG-001 calendário multi-técnico | grade semanal por técnico (slots 30min), leitura p95≤1s/20téc | render rico / drag-drop fluido (frente de telas) |
| US-AG-002 drag valida jornada+conflito | `POST /agenda/validar` (pré-save) + criar evento valida overlap+UMC (422) | — |
| US-AG-003 bloqueio claro 13.103 | 422 `JornadaUMCViolada{motivo, faltante_min, proximo_slot}` + audit | sugestão rica de re-slot |
| US-AG-004 bloqueio com motivo | `EventoAgenda(tipo=bloqueio)` férias/treino/atestado/outro | — |
| US-AG-005 feriados + confirmação | catálogo nacional seed + CRUD custom; flag `confirmar_feriado` | feriado por API externa (GATE-AGE-FERIADO-API) |
| US-AG-006 sugerir slot (chamado→OS) | RT subst→`RTCompetencia`→livre 7d; horizonte fixo 7d | sugestão de `capacity-planning` (GATE-AGE-CAPACITY) |
| US-AG-007 técnico vê própria agenda | endpoint read-only por `tecnico_id` (RLS upt self) | offline-sync app (frente app-tecnico) |
| US-AG-008 reagendar notifica cliente | reagenda + grava + **enfileira** aviso; recusa reverte+alerta | envio real (GATE-AGE-OMNICHANNEL); contraproposta (GATE-AGE-PORTAL) |
| US-AG-009 recorrência | RRULE materializa por **janela 90d** idempotente (ADR-0033) | edição-propaga-todos rica |
| US-AG-010 capacidade do dia | indicador `horas_alocadas/horas_úteis` (75%/90%) | — |
| US-AG-011 resolver conflito | `{manter_novo,manter_antigo,reagendar_ambos}` + razão≥30 **server-side** | — |
| US-AG-012 no-show + custo | `RegistroNoShow`(custo, cobrar_cliente); cobrável→`contas_receber` (GATE-AGE-AR) | régua de cobrança rica |
| US-AG-013 agendar ATIVIDADE | `atividade_id` obrigatório quando tipo=os; 2 atividades da mesma OS em técnicos ≠ ok | — |
| US-AG-014 RT substituto | RT projetado ao instante do slot: A determinístico=412 `SemRTNoSlot`/A incerto=warning; B/C warning+confirma; D off | gate duro de NC na emissão (`certificados`, já existe) |

## 3. Decisões cravadas (D-AGE-1..14)

- **D-AGE-1 — Path aninhado em `operacao` [🔷 confirmar tech-lead].** `src/domain/operacao/agenda/` +
  `src/application/operacao/agenda/` + `src/infrastructure/agenda/` (`app_label="agenda"`) — espelha OS
  (`domain/operacao/os/`, infra label `ordens_servico`). Domínio aninhado por área; infra flat com label.
- **D-AGE-2 — Agendar ATIVIDADE, não OS (ADR-0023/0051).** `EventoAgenda.atividade_id` NOT NULL quando
  `tipo=os`; `os_id` é derivado denormalizado (não fonte de verdade). INV-AG-ATIVIDADE-001.
- **D-AGE-3 — `EventoAgenda` é a raiz; máquina de estados Padrão A.** `agendado→em_execucao→concluido`;
  `agendado→cancelado`; `agendado→NO_SHOW`. Eventos passados imutáveis (move = update timestamps +
  `EventoAuditoriaAgenda` append-only).
- **D-AGE-4 — INV-020 (Lei 13.103) é predicate puro, perfil-AGNÓSTICO** [RBC-AGE-01 + ADV-AGE-01: jornada CLT é
  ordem pública trabalhista, **NÃO depende do perfil metrológico A/B/C/D**; **PRD §4/AC-AG-002-2 está ERRADO** ao
  gatear por perfil — corrigir o PRD (ação P3)]. `validar_jornada_umc(tecnico, regime, janela, eventos, capacidade)`.
  **Regras (citações corrigidas pelo advogado):** **R1** descanso inter-jornada ≥11h **ininterruptas** (CLT 235-C
  §3º + ADI 5322 / art. 66 geral); **R2** pausa ≥30min a cada 5h30 de direção contínua (CLT 235-C **§5º** + CTB
  67-C); **R3** 8h + até 2h extras (=10h); até 4h só c/ acordo coletivo (=12h) — 12x36 é figura distinta art. 235-F
  (CLT 235-C caput / art. 58 geral); **R4** descanso semanal ≥35h a cada 6 dias (§3º + ADI 5322); **R5** refeição
  ≥1h intrajornada (CLT **art. 71 §5º**). **Tempo de espera = jornada INTEGRAL 1/1** (ADI 5322 derrubou §8º/§9º;
  modulação **ex nunc desde 12/07/2023**), NÃO 1/3. **R6 (non-goal):** agenda é planejamento, **não substitui ponto**
  — controle/registro de jornada é obrigação patronal separada (dono = `frota`/folha). **R7 (advisory):** marcar
  evento que cruza **22h–5h** como jornada noturna (folha calcula adicional). Aplica SE `is_tecnico_campo AND
  aloca_em_umc`. Tentativa bloqueada → audit WORM (≥5a). **GATE-AGE-JORNADA-TRABALHISTA:** advogado humano OAB
  pré-produção (enquadramento individual + tabela final + convenção coletiva sindicato MT).
- **D-AGE-15 — Discriminador de REGIME de jornada** [ADV-AGE-02 — `is_tecnico_campo` mistura 2 regimes jurídicos].
  `regime_jornada ∈ {motorista_profissional (235-C: R1–R5 + espera 1/1), clt_geral (art. 58/71: R1/R3/R4/R5 sem R2 e
  sem espera-específica), nao_aplica}`. Enquadramento depende da CTPS real (análise trabalhista individual — RH/
  advogado humano, NÃO a IA). `colaboradores` está FECHADO → adicionar `regime_jornada` é nova flag/ADR [🔷 rotear
  ao tech-lead no P3]. Wave A: agenda lê o regime via porta; default conservador `nao_aplica` (não valida sem
  enquadramento explícito — evita falso-bloqueio E falso-negativo).
- **D-AGE-5 — A agenda ESCREVE na OS via `atribuir_tecnico`; LÊ via query; publica `agenda.*` própria.**
  Não promove `os_atribuida`/`atividade_reagendada` (continuam locais na OS). Eventos novos lowercase
  `agenda.evento.alocado`/`agenda.evento.reagendado`/`agenda.evento.cancelado`/`agenda.no_show.registrado`/
  `agenda.jornada_umc.violada` — PR em `acoes_canonicas.py` (slug `dominio.entidade.op`).
- **D-AGE-6 — US-AG-014 RT substituto perfil-aware, validado para o INSTANTE DO SLOT** [RBC-AGE-02: agendar é
  planejar, executar/emitir é que exige RT — não barrar cedo demais]. Reusa `rt_competencia_cobre` +
  `RTCompetencia` consultados **projetados para `slot.inicia_at`** (não "agora"). Perfil A: ausência
  **determinística** de titular/substituto competente no instante do slot → **412 `SemRTNoSlot`** (fail-closed);
  incerteza (titular sem bloqueio formal no período) → **warning `RTPendenteConfirmacaoNoSlot`** (planejar é
  permitido). B/C: warning + confirma; D: desabilitado. **O gate DURO de NC (cl. 6.2.5/7.8 — não emitir RBC sem
  signatário competente) vive na EMISSÃO (`certificados`/papel SIGNATARIO), já existente — a agenda alerta, não é
  o guardião primário.** INV-AG-PERFIL-001. **Pendência P3:** confirmar que a porta RT aceita consulta projetada
  a data futura (`rt_competencia_cobre(grandeza, instante=slot.inicia_at)`).
- **D-AGE-7 — Motorista sem CNH não aloca em UMC (R-COL-1).** Antes de alocar `MOTORISTA_UMC` em evento
  `aloca_em_umc`, agenda checa `pendencia_cnh` + validade da CNH → bloqueia (422). [TL-AGE-03: `pendencia_cnh`
  JÁ é legível via `PapelColaboradorOutputSerializer` (não está só no `/elegiveis`) — **zero extensão de
  `colaboradores`**; agenda lê pela porta `ColaboradorAgendaPort`.] INV-AG-CNH-001.
- **D-AGE-8 — Recorrência materializa por JANELA 90d, idempotente por `(recorrencia_id, ocorrencia_dt)`**
  (ADR-0033; re-materializa no job diário; "12 ocorrências" do PRD = mínimo visível). INV-AG-RECORRENCIA-001.
- **D-AGE-9 — No-show cobrável: agenda CHAMA `criar_titulo_manual` (use case público de CR) via porta
  `AReceberPort`** [TL-AGE-02: NÃO criar consumer dentro de CR (fechado) — simetria com D-AGE-5; o adapter da
  porta vive no infra da agenda; perfil server-side no título, não do payload]. Publica também
  `agenda.no_show.registrado` (auditoria/futuros consumidores). `RegistroNoShow` INSERT-only. GATE-AGE-AR.
- **D-AGE-10 — Feriados: seed nacional interno + CRUD custom por tenant** (estadual/municipal/empresa); sem
  API externa Wave A. Agendar em feriado exige `confirmar_feriado=true`.
- **D-AGE-11 — `CapacidadeTecnico` default 8h úteis seg–sex (08:00–17:00, 1h almoço)** se não cadastrada;
  CRUD simples por técnico. Base de US-AG-010 (capacidade) e da jornada.
- **D-AGE-12 — `is_tecnico_campo` é DERIVADO do papel** [TL-AGE-03 confirmou opção (a)]: `papel in {TECNICO,
  MOTORISTA_UMC}`, lido via `ColaboradorAgendaPort` (papel já legível). **NÃO existe nem se cria campo
  `is_tecnico_campo` em `colaboradores`** (FECHADO intacto). A única coisa que a agenda IMPLEMENTA para
  colaboradores é `ColaboradorReferenciadoPort.esta_referenciado` (técnico com agenda futura não é hard-deletado).
- **D-AGE-13 — Overlap único por técnico** via EXCLUDE GIST **com `tenant_id WITH =` como 1ª coluna** [TL-AGE-01
  travante — molde `excl_imposto_vigencia_sobreposta`; RLS não escopa a constraint]: `EXCLUDE USING gist
  (tenant_id WITH =, tecnico_id WITH =, tstzrange(inicia_at, termina_at, '[)') WITH &&) WHERE (estado !=
  'cancelado')`. Range **half-open `[)`** (slot 09:00–10:00 e 10:00–11:00 não colidem); `btree_gist` dos init
  scripts. INV-AG-OVERLAP-001.
- **D-AGE-14 — Multi-tenancy RLS v2** (ENABLE+FORCE+4 policies) em todas as tabelas; `EventoAuditoriaAgenda`
  + `RegistroNoShow` WORM INSERT-only; perfil server-side. Molde `ordens_servico`/`contas_receber`.

## 4. Modelo (domínio puro)

- **enums:** `TipoEvento`(os|bloqueio|descanso_legal|deslocamento|almoco|manutencao_interna|feriado),
  `EstadoEvento`(agendado|em_execucao|concluido|cancelado|no_show), `MotivoBloqueio`(ferias|treinamento|
  atestado|outro), `AcaoAuditoria`(criado|movido|cancelado|aprovado|no_show).
- **entities (`frozen+slots`):** `EventoAgenda` (raiz), `Recorrencia`, `RegistroNoShow`, `CapacidadeTecnico`,
  `Feriado`, `EventoAuditoriaAgenda`.
- **value_objects:** `Janela(inicia_at, termina_at)` (imutável, valida `inicia<termina`), `RegraRecorrencia`
  (RRULE RFC 5545), `ResultadoJornada(ok, violacao, faltante_min, proximo_slot)`.
- **transicoes.py:** `_TRANSICOES: Mapping[EstadoEvento, frozenset]` + `validar_transicao`.
- **jornada.py:** `validar_jornada_umc(...)` (puro — 3 regras Lei 13.103) + `proximo_slot_valido`.
- **recorrencia.py:** `materializar_janela(regra, inicio, dias=90) -> list[datetime]` (puro, determinístico).
- **portas.py (Protocols):** `OSSchedulingPort` (atribuir/ler atividade), `ColaboradorAgendaPort`
  (elegíveis + `pendencia_cnh`), `RTSubstitutoPort` (competência/substituto por grandeza), `MapsProvider`
  (stub Wave A), `NotificacaoClientePort` (stub/omnichannel), `AReceberPort` (no-show cobrável).
- **erros.py:** `JornadaUMCViolada`(422), `SemRTNoSlot`(412), `ConflitoAgenda`(409), `MotoristaSemCNH`(422),
  `FeriadoNaoConfirmado`(422), `PerfilIndeterminado`(fail-closed).

## 5. Invariantes candidatas (P7 crava em REGRAS + hook)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-AG-JORNADA-UMC-001 | jornada Lei 13.103 **perfil-AGNÓSTICA** (`is_tecnico_campo AND aloca_em_umc`); **5 regras** + espera=1/1 (ADI 5322); tentativa bloqueada → audit WORM; teste das 5 regras |
| INV-AG-OVERLAP-001 | EXCLUDE GIST **`(tenant_id, tecnico_id, tstzrange '[)')`** (exceto cancelado); 2 sobrepostos → 409; **drill PG de concorrência** (TL honestidade) |
| INV-AG-ATIVIDADE-001 | `atividade_id` NOT NULL quando `tipo=os` (CHECK + domínio `__post_init__`); ADR-0023/0051 |
| INV-AG-PERFIL-001 | perfil server-side (nunca payload); RT substituto **projetado ao instante do slot** — A determinístico=412/A incerto=warning/B-C warning/D off; gate duro de NC na emissão (não na agenda); UNHAPPY por perfil |
| INV-AG-RECORRENCIA-001 | materialização idempotente por `(recorrencia_id, ocorrencia_dt)` UNIQUE; job re-roda sem duplicar |
| INV-AG-CNH-001 | `MOTORISTA_UMC` com `pendencia_cnh`/CNH vencida não aloca em `aloca_em_umc`; teste 422 |
| INV-AG-AUDIT-WORM-001 | `EventoAuditoriaAgenda` + `RegistroNoShow` INSERT-only (trigger); teste anti-mutação |
| INV-AG-NOSHOW-AR-001 | no-show cobrável publica `agenda.no_show.registrado` consumido por CR; teste latência |
| INV-TENANT-* / INV-BUS-001 (herdadas) | RLS v2 FORCE; consumers `os.*`/`colaborador.*`/`tenant.rt.trocado` idempotentes (fan-out) |

## 6. Portas, eventos e seams

**Consome (bus):** `os.aberta`/`os.cancelada`/`os.reaberta`/`os.atividade_concluida`/`os.atividade_cancelada`
(libera/cria slot); `colaborador.desligado` (cancela agenda futura) /`papel_atribuido`/`papel_revogado`;
`tenant.rt.trocado` (revisa atribuições do RT anterior). Todos `@consumer_idempotente` (fan-out).
**Publica:** `agenda.evento.alocado`/`.reagendado`/`.cancelado`, `agenda.no_show.registrado`,
`agenda.jornada_umc.violada`, `agenda.conflito.resolvido`, `agenda.bloqueio.criado`.
**Lê via DB (seam OS):** `AtividadeDaOS.tecnico_executor_id`+`agendada_para` (escreve via `atribuir_tecnico`).
**Implementa para `colaboradores`:** `ColaboradorReferenciadoPort.esta_referenciado` (técnico com agenda
futura não é hard-deletado).

## 7. Non-goals

Não construir: MapsProvider real, roteirização TSP, sugestão por skill/proximidade automática, integração
Google/Outlook, reserva de veículo UMC, push mobile, contraproposta de cliente, capacity-planning, bot de
WhatsApp. GATEs: AGE-MAPS/OMNICHANNEL/PORTAL/CAPACITY/AR/FERIADO-API.

## 8. Estado da revisão P2 (CONCLUÍDA — detalhe em `reviews-consolidado.md`)

- ✅ **`tech-lead` — APROVA COM CORREÇÕES** (incorporadas): TL-AGE-01 EXCLUDE com `tenant_id` (D-AGE-13),
  TL-AGE-02 no-show via `criar_titulo_manual`/porta (D-AGE-9), TL-AGE-03 `pendencia_cnh`/`is_tecnico_campo`
  legíveis sem estender colaboradores (D-AGE-7/12). Médios P3: porta OSScheduling no infra, consumers fan-out.
- ✅ **`consultor-rbc` — RESSALVA** (incorporada): jornada 5 regras + espera 1/1 + perfil-agnóstica (D-AGE-4);
  RT validado ao instante do slot, gate duro de NC na emissão (D-AGE-6); jornada fora da matriz-feature-perfil.
- ✅ **`advogado` — minuta APROVA COM CORREÇÕES** (incorporada): citações R2=§5º/R5=art.71§5º; +R6 (ñ é ponto)
  +R7 (noturno); +D-AGE-15 discriminador `regime_jornada`; nota modulação ADI 5322 ex nunc 12/07/2023.

**Ações P3 derivadas (antes de plan/tasks):** (1) corrigir PRD §4/AC-AG-002-2 (remover gating por perfil do
INV-020 — perfil-agnóstico); (2) reescrever **INV-020 em `REGRAS-INEGOCIAVEIS.md`** (hoje desatualizado:
"espera 1/3 §9" → "1/1 ADI 5322" + R4/R5/R6/R7); (3) rotear `regime_jornada` ao tech-lead (flag/ADR em
`colaboradores` fechado — D-AGE-15). **GATE-AGE-JORNADA-TRABALHISTA** = advogado humano OAB pré-produção.
Depois: P3 plan/tasks → fatias (núcleo autossuficiente 1a/1b/2 com portas-stub; 3 cross-módulo por contrato público).
