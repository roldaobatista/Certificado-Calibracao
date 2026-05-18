---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-004
---

# Plano US-CLI-004 — Bloquear cliente inadimplente (manual + automático)

> Story em `docs/dominios/comercial/modulos/clientes/prd.md` §6 US-CLI-004 (7 ACs).
>
> **Dependência crítica:** ADR-0015 fluxo 4 + módulo `financeiro/contas-receber` (NÃO existe ainda). Esta US implementa o **lado do cliente** completo (AC-1, AC-2 manual; contrato de evento e job stub pros automáticos AC-3..7).

## Escopo realista pra Marco 1 (sem outros módulos)

- **AC-CLI-004-1** (bloqueio manual) — COMPLETO. Endpoint POST `/clientes/{id}/bloquear/` exigindo justificativa ≥30 chars.
- **AC-CLI-004-2** (denied em OS/orçamento/agenda) — COMPLETO no lado do AuthorizationProvider. Quando OS/orcamentos/agenda existirem (Wave A), eles consultam `Cliente.bloqueado` ou passam `resource={"cliente_id":X}` no `can()` e o provider extende com este predicado. Por hora, contrato cravado em **uma função utilitária** `cliente_bloqueado_para_acao(cliente_id) -> bool` que esses módulos chamarão.
- **AC-CLI-004-3** (job D+90 automático) — CONTRATO + JOB STUB. Management command `cliente_inadimplencia_alertas` que consome um cursor de `ContasReceber` (interface mock por enquanto, hookada via setting). Wave A do `financeiro/contas-receber` substitui o mock.
- **AC-CLI-004-4** (consumidores) — não implementáveis sem os módulos; contrato de eventos `Cliente.Bloqueado` / `Cliente.Desbloqueado` documentado em `docs/comum/automacoes-catalogo.md` (existente).
- **AC-CLI-004-5** (régua D+30/60/89) — só documentação do contrato + 3 eventos esquematizados; implementação no `comunicacao-omnichannel`.
- **AC-CLI-004-6** (reativação automática) — endpoint POST `/clientes/{id}/desbloquear/` (manual) + handler stub do evento `ContasReceber.Pago` (a definir).
- **AC-CLI-004-7** (auditoria com causation_id) — preencher `payload.causation_id` no audit `cliente.bloqueado`/`cliente.desbloqueado`.

## Sequência de tasks

- **T-CLI-019**: campos no Cliente: `bloqueado: bool`, `bloqueio_motivo: str (40)`, `bloqueio_justificativa: text`, `bloqueio_em: datetime`, `bloqueio_por_usuario_id: UUID`.
  Enum `MOTIVO_BLOQUEIO_MANUAL`, `MOTIVO_BLOQUEIO_INADIMPLENCIA_90D`.
- **T-CLI-020**: migration adicionando campos.
- **T-CLI-021**: endpoints POST `/clientes/{id}/bloquear/` e POST `/clientes/{id}/desbloquear/`. Exigem perfil `admin_tenant` (gerente financeiro entra em Wave A).
  Authz actions: `clientes.bloquear`, `clientes.desbloquear`.
- **T-CLI-022**: utilitária `src/application/comercial/clientes/cliente_bloqueado.py` com `cliente_bloqueado_para_acao(cliente_id, action) -> Decisao` — contrato pra OS/orçamento consultarem (Wave A).
- **T-CLI-023**: migration seed `clientes.bloquear` e `clientes.desbloquear` para admin_tenant.
- **T-CLI-024**: audit `cliente.bloqueado` + `cliente.desbloqueado` com causation_id (UUID opcional ligando ao título vencido).
- **T-CLI-025**: 9 testes:
  - `test_bloqueio_manual_exige_justificativa_minima_30_chars`
  - `test_bloqueio_manual_publica_audit_com_motivo_e_usuario`
  - `test_bloqueio_persiste_estado_no_cliente`
  - `test_desbloqueio_manual_funciona`
  - `test_desbloqueio_audita_quem_desbloqueou`
  - `test_bloquear_exige_perfil_admin_tenant`
  - `test_utilitaria_cliente_bloqueado_para_acao_retorna_denied_quando_bloqueado`
  - `test_utilitaria_retorna_allowed_quando_nao_bloqueado`
  - `test_bloqueio_eh_idempotente` (bloquear cliente ja bloqueado nao quebra)

## Non-goals deste plano

- Job Celery real (depende de ContasReceber). Implementar como management command stub.
- Régua D+30/60/89 (Wave A — comunicacao-omnichannel).
- Reativação automática event-driven (Wave A — financeiro/contas-receber).
- UI de bloqueio (só API).

## Subagentes a consultar

- `tech-lead-saas-regulado`: APROVADO COM RESSALVAS (7 — 3 críticas, 4 médias).
- `advogado-saas-regulado`: APROVADO COM RESSALVAS BLOQUEANTES (6).

---

## Endereçamento da revisão (13 ressalvas)

### Tech-lead (7)
- **TL1 (CRÍTICA — modelagem)**: tabela 1:N `cliente_bloqueios` (id, cliente, motivo_categoria, motivo_observacao, justificativa_bruta, causation_type, causation_id, bloqueado_em, bloqueado_por_usuario_id, desbloqueado_em, desbloqueado_por_usuario_id, desbloqueado_motivo). UNIQUE INDEX parcial `(cliente_id) WHERE desbloqueado_em IS NULL` garante 1 ativo. Cliente.bloqueado vira property que consulta esta tabela.
- **TL2 (CRÍTICA — predicate ABAC)**: removida utilitária. Predicate `cliente_nao_bloqueado` em `src/infrastructure/authz/predicates.py` (registry pattern). `AuthorizationProvider.can(resource={"cliente_id":X})` consulta. Wave A do `os/orcamentos/agenda` passa `resource={"cliente_id": X}` automaticamente.
- **TL3 (CRÍTICA — idempotência)**: no-op quando já bloqueado. Endpoint retorna `200 OK` com `{"ja_estava_bloqueado": true, "bloqueio_atual_id": ...}` sem republicar evento nem sobrescrever motivo.
- **TL4 (ALTA — causation_type)**: enum `titulo_vencido` / `importacao_batch` / `politica_inadimplencia` / `manual_decisao_admin` com CHECK constraint na migration.
- **TL5 (ALTA — Procrastinate)**: criar Protocol `InadimplenciaSource` em `src/domain/comercial/clientes/inadimplencia_source.py`. Adapter mock `MockInadimplenciaSource` (lê de dict de settings) em `infrastructure`. Job real entra em Wave A. Worker Procrastinate **não roda nesta US** — management command on-demand cumpre AC-3 com o mock.
- **TL6 (MÉDIA — audit)**: action lowercase `cliente.bloqueado` / `cliente.desbloqueado`. Payload sem PII cru: `{cliente_id, motivo_categoria, justificativa_hash, causation_type, causation_id, usuario_id, event_id (uuid)}`.
- **TL7 (MÉDIA — só admin_tenant)**: matriz só `clientes.bloquear` e `clientes.desbloquear` para `admin_tenant`. Perfil `financeiro` entra em Wave A.

### Advogado (6)
- **R1 (BLOQUEANTE — justificativa no audit)**: `justificativa_bruta` fica APENAS na tabela `cliente_bloqueios` (banco operacional do tenant — sujeita a crypto-shredding Wave B). Audit grava `justificativa_hash` (SHA-256).
- **R2 (BLOQUEANTE — enum 5 motivos)**: cravados — `manual_inadimplencia`, `manual_quebra_confianca`, `manual_solicitacao_juridico`, `manual_outro`, `automatico_inadimplencia_90d`. Mesma regex anti-PII de US-CLI-005 aplica em `motivo_observacao` (opcional).
- **R3 (BLOQUEANTE — gate régua CDC + Lei 14.181)**:
  - Bloqueio automático D+90 **OFF por default** no Marco 1: flag `Tenant.bloqueio_automatico_inadimplencia_habilitado = False` (migration nova).
  - Bloqueio manual exige `confirmacao_comunicacao_previa: True` no payload (checkbox no futuro). Sem isso = 400.
  - INV-CLI-BLOQ-001 nova em `REGRAS-INEGOCIAVEIS.md`: bloqueio automático só dispara se flag tenant=true E há registro de régua D+30/60/89 (validado por hook em Wave A).
- **R4 (clareza)**: docstring do modelo cita INV-013 estendida — confidencialidade reforçada do motivo.
- **R5 (Wave A — pré-alerta 24h)**: documentar como contrato de evento futuro `Cliente.AlertaPreBloqueio24h` no `automacoes-catalogo.md` (referência); implementação Wave A.
- **R6 (Wave A — view sanitizada)**: documentar débito em `docs/governanca/debitos-ritual.md`; quando Wave A entregar `lgpd-portal`, criar view.

## Sequência revisada (atualiza T-CLI-019 a T-CLI-025)

- **T-CLI-019**: criar modelo `ClienteBloqueio` (1:N) em `models.py` + property `Cliente.bloqueado`.
- **T-CLI-020**: migration `0008_cliente_bloqueio` cria tabela com UNIQUE INDEX parcial + CHECK constraints.
- **T-CLI-021**: adicionar field `Tenant.bloqueio_automatico_inadimplencia_habilitado` (default False) — migration `tenant 0002`.
- **T-CLI-022**: enum constants em `src/infrastructure/clientes/bloqueio.py` (MOTIVOS, CAUSATION_TYPES).
- **T-CLI-023**: predicate registry em `src/infrastructure/authz/predicates.py` + predicate `cliente_nao_bloqueado` (chamado pelo provider via resource).
- **T-CLI-024**: estender `DjangoAuthorizationProvider._decidir()` pra consultar predicates registrados quando `resource` contém `cliente_id`.
- **T-CLI-025**: endpoints POST `/clientes/{id}/bloquear/`, POST `/clientes/{id}/desbloquear/`. Idempotência no-op (TL3). Bloqueio manual exige `confirmacao_comunicacao_previa: True` (R3). Justificativa ≥30 chars; observação com regex anti-PII (R2 espelha US-005).
- **T-CLI-026**: audit `cliente.bloqueado` / `cliente.desbloqueado` com `justificativa_hash` + `event_id`.
- **T-CLI-027**: Protocol `InadimplenciaSource` em `src/domain/comercial/clientes/` + adapter `MockInadimplenciaSource`. Management command `job_inadimplencia_alertas` que itera a source e bloqueia se tenant habilitar.
- **T-CLI-028**: migration seed `clientes.bloquear` + `clientes.desbloquear` para admin_tenant.
- **T-CLI-029**: criar INV-CLI-BLOQ-001 em `REGRAS-INEGOCIAVEIS.md` + atualizar `debitos-ritual.md` com débitos Wave A (R5 + R6).
- **T-CLI-030**: 14 testes (9 originais + 5 novos das ressalvas):
  - bloqueio manual exige justificativa ≥30 chars
  - bloqueio manual exige `confirmacao_comunicacao_previa=True` (R3)
  - persistência: cliente.bloqueado property reflete ClienteBloqueio ativo
  - audit `cliente.bloqueado` sem PII cru (R1 + TL6)
  - desbloqueio funciona + audita quem
  - perfil tecnico tenta bloquear = 403
  - predicate ABAC: can("os.criar", resource={"cliente_id": bloqueado}) = denied
  - predicate ABAC: cliente não bloqueado = allowed
  - idempotência no-op (TL3): bloquear cliente já bloqueado = 200 com flag `ja_estava_bloqueado`
  - histórico preservado: bloqueia / desbloqueia / bloqueia de novo → 2 linhas em cliente_bloqueios
  - motivo invalido (fora do enum) = 400 (R2)
  - observação com CPF rejeita = 400 (R2)
  - bloqueio automático com flag tenant OFF: management command itera e NÃO bloqueia (R3)
  - bloqueio automático com flag tenant ON + source mock retorna inadimplente → cria bloqueio com causation_type=titulo_vencido
