---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-16
status: draft
diataxis: explanation
audiencia: [agente, auditor]
frente: agenda
tipo: investigacao-p0
relacionados:
  - docs/dominios/operacao/modulos/agenda/prd.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0051-propagacao-adr0023-modulos.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/adr/0033-bus-idempotencia-consumer.md
---

# T-AGE-000 — Investigação P0 da frente `agenda` (re-rastreio pós-módulos fechados)

> Regra #0 (investigar o estado real antes de especificar). Frente nível 5 (operação). PRD
> `stable` (US-AG-001..014, todas Wave A). Módulo NOVO — zero código. Esta investigação
> cristaliza o ESCOPO declarado + os SEAMS reais que módulos fechados (OS, colaboradores, RT,
> bus) expõem, para a spec não inventar contratos. Base: varredura do código real 2026-06-16.

## 1. Escopo — 14 US, TODAS Wave A

Calendário gerencial multi-técnico que distribui OS/bloqueios/eventos pelos slots dos técnicos
com **validação automática da jornada UMC (INV-020 — Lei 13.103)** quando aplicável.

| US | Entrega | Núcleo |
|---|---|---|
| US-AG-001 | Calendário semanal multi-técnico (1 coluna/técnico, slots 30min, p95≤1s/20téc) | A |
| US-AG-002 | Drag&drop valida INV-020 + conflito ANTES de salvar (422 se viola) | A |
| US-AG-003 | Bloqueio claro em violação 13.103 (422 `JornadaUMCViolada` + motivo + próximo slot) | A |
| US-AG-004 | `BloqueioAgenda` (férias/treino/atestado/outro) — barra atribuição | A |
| US-AG-005 | Feriados destacados + confirmação obrigatória ao agendar em feriado | A |
| US-AG-006 | Sugerir slot ao converter chamado→OS (RT subst→RTCompetencia→livre 7d) | A |
| US-AG-007 | Técnico vê própria agenda (mobile, read-only, offline) | A |
| US-AG-008 | Reagendamento notifica cliente (OmniChannel; recusa reverte) | A |
| US-AG-009 | Recorrência RRULE materializa em batch idempotente (ADR-0033) | A |
| US-AG-010 | Capacidade do dia (amarelo≥75% / vermelho≥90% de `horas_alocadas/úteis`) | A |
| US-AG-011 | Resolver conflito (manter_novo/antigo/reagendar_ambos + razão≥30) | A |
| US-AG-012 | No-show com custo de deslocamento + decisão de cobrar (→`AReceber.criar`) | A |
| US-AG-013 | Agendar **ATIVIDADE da OS**, não a OS inteira (ADR-0023/0051) | A |
| US-AG-014 | Agenda considera RT substituto (ADR-0068; A=412 fail-closed, B/C warning, D off) | A |

## 2. Modelo de domínio (agregados)

- **`EventoAgenda`** (raiz): `tecnico_id`, `inicia_at`/`termina_at`, `tipo` (os|bloqueio|descanso_legal|
  deslocamento|almoco|manutencao_interna|feriado), `estado` (agendado|em_execucao|concluido|cancelado|NO_SHOW).
  `atividade_id` **obrigatório quando tipo=os** (INV-AG-ADR0023-001); `os_id` derivado denormalizado.
  Append-only para auditoria (move = update timestamps + `EventoAuditoria`).
- **`Recorrencia`** (raiz): RRULE RFC 5545 → materializa N `EventoAgenda` via job.
- Subordinadas: **`EventoAuditoria`** (append-only, RAT-08), **`RegistroNoShow`** (custo+cobrar_cliente).
- Independentes: **`CapacidadeTecnico`** (dia_semana, horas_úteis, jornada), **`Feriado`** (nac/est/mun/custom).

## 3. INV-020 (Lei 13.103) — a criar do ZERO (zero código hoje)

Hook `validar_jornada_umc(tecnico_id, inicia_at, termina_at) → {ok, violacao?, sugestao_proximo_slot?}`:
1. **Descanso entre jornadas ≥ 11h** ininterruptas (Lei 13.103/2015 + CLT 235-C).
2. **Intervalo 30min a cada 5h30** de direção contínua (evento `descanso_legal`).
3. **Tempo de espera/sobreaviso** conta 1/3 da jornada.

Aplica SE: `tenant_perfil_e(['A','B','C']) AND colaborador.is_tecnico_campo AND evento.aloca_em_UMC`.
Perfil **D = opcional** (dispensa sem técnico de campo em UMC). Bloqueio → **422** + audit (compliance
trabalhista, retenção ≥5a; tentativas bloqueadas integram o relatório regulado Export 1).

## 4. Seams REAIS (contratos a respeitar — NÃO inventar)

**Ordens de Serviço** (`src/{domain,infrastructure}/operacao/os/` / `ordens_servico/`):
- Scheduling vive em `AtividadeSnapshot.tecnico_executor_id` + `agendada_para` (entities.py:56). Transição
  atividade `PENDENTE→AGENDADA` ao setar ambos; OS `RASCUNHO→AGENDADA` quando todas atividades ≥AGENDADA.
- **`OS_ATRIBUIDA` e `ATIVIDADE_REAGENDADA` NÃO cruzam o bus** (`value_objects.py:159`: mapeados `None`,
  comentário "interno; agenda consome via DB"). **Decisão de spec:** agenda lê `AtividadeDaOS` via query OU
  promove `os.atribuida`/`agenda.*` a Integration Event. → ver D-AGE (§5-B).
- `atribuir_tecnico` (`application/operacao/os/atribuir_tecnico.py`) é use case puro: **AC-OS-002b-2 (Lei
  13.103) é responsabilidade DO CALLER** — seam vazio que a agenda preenche (validar jornada ANTES de chamar).
- Consome do bus: `os.aberta`/`os.cancelada`/`os.reaberta`/`os.atividade_concluida`/`os.atividade_cancelada`.

**Colaboradores** (`src/{domain,infrastructure}/rh_frota_qualidade/colaboradores/`):
- Papéis `TECNICO`/`MOTORISTA_UMC`; `PapelColaboradorAtribuido.pendencia_cnh` (R-COL-1: "bloqueio real na
  alocação = frota/agenda" — `regras.py:127`). Agenda verifica `pendencia_cnh` + validade CNH antes de alocar UMC.
- `Habilidade`(nivel APRENDIZ/CAPACITADO/MESTRE)+`CatalogoHabilidade.grandeza` para matching.
- Porta `/colaboradores/elegiveis/?papel=tecnico` (DTO mínimo sem PII; **`pendencia_cnh` NÃO está no DTO** —
  agenda precisa extensão OU leitura direta do papel). `ColaboradorReferenciadoPort.esta_referenciado` — agenda
  deve fornecer impl concreta (colaborador com agenda futura não é hard-deletado).
- Consome: `colaborador.desligado` (cancelar agenda futura), `colaborador.papel_atribuido/revogado`.

**Responsável Técnico** (`src/infrastructure/responsavel_tecnico/`):
- `RTCompetencia`(grandeza+`declarado_em`/`vigente_ate`, EXCLUDE GIST 1-vigente-por-grandeza). Predicate
  REUSÁVEL `rt_competencia_cobre` (`predicates_os.py:67`) — agenda NÃO reimplementa. Sucessão via `trocar_rt`
  publica `tenant.rt.trocado`. US-AG-014 consulta `RTSubstituto`/competência por grandeza.

**Bus** (`src/infrastructure/{bus,audit}/`): `@consumer_idempotente` (event_id UUID + ON CONFLICT) + fan-out
`_REGISTRY: dict[str,list]`. Ações novas da agenda → PR em `acoes_canonicas.py`, slug `agenda.entidade.op`
(CHECK SQL `bus_outbox_acao_enum_semantico`). **Perfil:** `obter_perfil_tenant_corrente()`/`tenant_perfil_e`
server-side (ContextVar `perfil_tenant_context`), NUNCA do payload (INV-TENANT-PERFIL-002).

## 5. Decisões de cravação P0 (resolver os pontos abertos do PRD; ✅=cravado, 🔶=produto/Roldão, 🔷=revisão subagente)

- **A ✅** API exige `atividade_id` (verdade — ADR-0023/0051), não `os_id` (derivado). Corrigir contrato.
- **B ✅** Eventos com slug canônico **lowercase** `agenda.evento.alocado`/`agenda.evento.reagendado`/etc.; SEM
  aliases deprecated (módulo novo nasce limpo). `os_atribuida`/`atividade_reagendada` continuam locais na OS;
  a agenda publica os seus próprios `agenda.*` (consumidores: OS/CRM/capacity/contas-receber).
- **C ✅** Recorrência materializa por **JANELA temporal (90 dias)** idempotente por `recorrencia_id`+ocorrência
  (re-materializa no job diário); "12 ocorrências" do PRD = mínimo visível, não o critério (reconcilia AC-AG-009-1).
- **D ✅** US-AG-006: horizonte 7d; vazio → lista vazia + flag `ampliar_horizonte` (não expande sozinho).
- **E ✅** US-AG-011: razão ≥30 chars validada **SERVER-SIDE** (anti-bypass via API), não só UX.
- **F 🔶** US-AG-012: política de cobrar no-show = config tenant `cobranca_noshow_habilitada` (default **False**,
  conservador). Veto/ajuste do Roldão pendente (decisão de cobrança ao cliente).
- **G ✅** US-AG-008: Wave A só **aceita/recusa** (recusa reverte ao slot original + alerta gerente).
  **Contraproposta de horário pelo cliente = Wave B** (depende do portal — GATE-AGE-PORTAL).
- **H ✅** Contrato distingue **412 `SemRTNoSlot`** (precondição RT — US-AG-014) de **422 `JornadaUMCViolada`**
  (validação — US-AG-003). Incluir 412 no `api.md`.
- **I ✅** `tempo_deslocamento_estimado_s` = campo manual (minutos) preenchido pelo gerente; default null;
  `MapsProvider` real = **Wave B** (GATE-AGE-MAPS).
- **J ✅** `CapacidadeTecnico`: default **8h úteis seg–sex (08:00–17:00, 1h almoço)** se não cadastrada;
  CRUD simples Wave A para editar por técnico.
- **K ✅** Feriados: catálogo **nacional seed interno** + CRUD custom do tenant (estadual/municipal/empresa);
  **sem API externa** Wave A (GATE-AGE-FERIADO-API diferido).

## 6. GATEs + dependências externas (Wave A roda com fallback/stub)

- **GATE-AGE-MAPS** — `MapsProvider` (deslocamento real) Wave B; fallback manual.
- **GATE-AGE-OMNICHANNEL** — notificação ao cliente (US-AG-008) depende de `comunicacao-omnichannel` (DIFERIDO
  por bloqueio externo). Wave A: reagendamento salva; notificação enfileira/no-op até o módulo existir.
- **GATE-AGE-AR** — no-show cobrável (US-AG-012) publica para `contas-receber` (JÁ existe — `AReceber.criar`/
  lançamento manual). Wave A consome o título manual de CR.
- **GATE-AGE-PORTAL** — aprovação/contraproposta do cliente (portal não existe) Wave B.
- **GATE-AGE-CAPACITY** — sugestões de `capacity-planning-operacional` (não existe) Wave B; US-AG-006 usa só
  lógica interna (RT subst→competência→livre 7d).
- Pré-condições de cadastro (gates de dados): `colaborador.is_tecnico_campo`, `evento.aloca_em_UMC`,
  `Tenant.perfil_regulatorio` populados. `is_tecnico_campo` pode exigir **extensão de `colaboradores` (FECHADO)** —
  tratar como toque em módulo fechado (R14) OU derivar de papel TECNICO/MOTORISTA_UMC. → ver revisão tech-lead.

## 7. Próximo passo

**P1 — `spec.md`** (molde `contas-receber`/`orcamentos`): cravar D-AGE-* (decisões acima) + US→AC binários +
INV-AG-* candidatas (jornada UMC, overlap único, atividade_id obrigatório, perfil server-side, idempotência de
recorrência, RT substituto perfil-aware) + recorte núcleo vs GATE. **Revisão P2 obrigatória:** `tech-lead-saas-regulado`
(seams OS/colaboradores/RT + `is_tecnico_campo` em módulo fechado + promover evento vs ler DB) + `consultor-rbc-iso17025`
(INV-020 Lei 13.103 correto + RT substituto cl. 6.2.5/ADR-0068 + perfis). `advogado` se tocar PII/jornada trabalhista.
Depois P3 plan/tasks → fatias.
