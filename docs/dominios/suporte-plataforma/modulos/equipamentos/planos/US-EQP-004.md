---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-004
---

# Plano US-EQP-004 — Transferir equipamento entre clientes do mesmo tenant (com aceite duplo)

> Story em `prd.md` §6 (US-EQP-004).
>
> **Pré-requisitos:** US-EQP-001 (equipamento + cliente_id_original_hash) + US-EQP-002 (versionamento) + Marco 1 clientes (bloqueio cliente).
>
> **Revisão (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 tech-lead + 6 advogado. Pareceres em `revisoes/US-EQP-004-{tech-lead,advogado}.md`. **Dívida regulatória explícita** em `equipamentos/transferencia-aceite-presencial-marco2.md` — portal-cliente OTP fica Wave B+.

## Resumo

Implementar endpoint `POST /v1/equipamentos/{id}/transferir` com (a) restrição intra-tenant (INV-050), (b) aceite duplo cedente+cessionário (advogado B2), (c) `motivo_categoria` enum, (d) sanitização anti-PII em `motivo_detalhe`, (e) bloqueio se cedente bloqueado/inadimplente, (f) segregação de histórico de certs pro cessionário (RBC B6 — cl. 4.2), (g) evento `equipamento.transferido` com payload sanitizado (hashes).

## Sequência de tasks

- **T-EQP-038**: model `TransferenciaEquipamentoAceite` (migration 0013) — campos: `equipamento_id`, `cliente_origem_id_hash`, `cliente_destino_id_hash`, `motivo_categoria`, `motivo_detalhe_hash`, `aceite_origem_em`, `aceite_origem_versao_texto_id`, `aceite_origem_ip_hash`, `aceite_origem_via` (enum), `aceite_destino_em`, `aceite_destino_versao_texto_id`, `aceite_destino_ip_hash`, `aceite_destino_via`, `usuario_id_tenant`. RLS policy. Trigger PG `bloquear_update_aceite_apos_concretizado`.
- **T-EQP-039**: constants `texto_versao_transferencia.py` em `src/infrastructure/equipamentos/` — `VERSAO_VIGENTE = "v1.0-2026-05-18"` + dict `TEXTOS_HISTORICOS` com texto do termo (advogado D2).
- **T-EQP-040**: enum `motivo_categoria_transferencia` em domain enums: `venda | comodato | doacao | correcao_cadastral | outro`.
- **T-EQP-041**: validação anti-PII em `motivo_detalhe` (mesma regex `localizacao_fisica`).
- **T-EQP-042**: porta `BloqueioClienteQueryService` consumida — já existe no módulo clientes Marco 1; adapter `DjangoBloqueioClienteQueryService` reusa lógica de `cliente.bloqueado` + `cliente.tem_fatura_aberta`. Para Wave A Marco 2 (sem módulo financeiro), `tem_fatura_aberta` retorna sempre False via stub `StubFinanceiroQueryService` (registrar porta + adapter empty mais um — `FinanceiroQueryService`).
- **T-EQP-043**: porta `FinanceiroQueryService` em `src/domain/.../ports/` + `EmptyFinanceiroQueryService` (sempre `tem_fatura_aberta=False`) + binding em settings.
- **T-EQP-044**: use case `TransferirEquipamento`:
  - Validar `novo_cliente_id` existe + `novo_cliente.tenant_id == equipamento.tenant_id` (INV-050) — senão 422 genérico "cliente não encontrado neste tenant".
  - Validar cedente não bloqueado + sem fatura aberta — senão 412.
  - Validar aceite_origem + aceite_destino presentes — senão 400.
  - Validar `motivo_detalhe` anti-PII — senão 400.
  - Gravar `TransferenciaEquipamentoAceite` + atualizar `Equipamento.cliente_atual_id`.
  - `cliente_id_original_hash` permanece imutável (INV-025).
  - Setar `Equipamento.consentimento_compartilhamento_historico_em_transferencia` conforme aceite do cedente (default false — RBC B6).
  - Gravar audit `equipamento.transferido` com payload sanitizado (hashes — payload exato no modelo-de-dominio v2).
- **T-EQP-045**: ajuste em `EquipamentoSerializer` (ficha 360°) — se cessionário visualiza e `consentimento_compartilhamento_historico_em_transferencia=false`, oculta certs anteriores à transferência + retorna banner "histórico anterior preservado mas confidencial" (RBC B6).
- **T-EQP-046**: action `equipamento.transferir` no seed authz (migration 0014). Atribuir aos perfis admin, metrologista, atendente.
- **T-EQP-047**: rate limit conservador no endpoint (10 req/min/usuário — mutação destrutiva).
- **T-EQP-048**: testes:
  - `test_transferir_happy_path_grava_audit_sanitizado`
  - `test_transferir_cross_tenant_retorna_422_sem_oracle` (INV-050)
  - `test_transferir_cliente_bloqueado_retorna_412`
  - `test_transferir_cliente_com_fatura_aberta_retorna_412` (stub Wave A retorna false; teste fixa stub pra retornar true)
  - `test_transferir_sem_aceite_origem_retorna_400`
  - `test_transferir_sem_aceite_destino_retorna_400`
  - `test_motivo_detalhe_com_cpf_retorna_400`
  - `test_motivo_categoria_invalido_retorna_400`
  - `test_cliente_id_original_hash_permanece_imutavel_apos_transferencia` (INV-025)
  - `test_cessionario_sem_consentimento_nao_ve_certs_anteriores` (RBC B6)
  - `test_cessionario_com_consentimento_ve_certs_anteriores` (RBC B6)
  - `test_evento_transferido_payload_so_hashes_e_categorias` (advogado B2)
  - `test_aceite_versao_texto_id_referencia_constante_vigente`
  - `test_authz_atendente_pode_transferir` / `test_authz_tecnico_nao_pode`
  - `test_idempotency_key_24h_recusa_reuso_destrutivo`

## Modelos/tabelas envolvidos

- **Novo:** `transferencia_equipamento_aceite`
- **Já existe:** `equipamento`, `audit_trail.eventos`, `cliente` (modulo Marco 1)
- **Trigger novo:** `bloquear_update_aceite_apos_concretizado`

## Endpoints envolvidos

- `POST /v1/equipamentos/{id}/transferir`

## Hooks ativados

- Todos US-EQP-001/002/003 + `port-binding-validator` valida `FinanceiroQueryService` não-Empty em prod (mas Marco 2 Wave A ainda pode ser Empty — abrir override `# port-binding-validator: skip-empty -- modulo financeiro ainda nao existe` apenas em `settings.development` e `settings.test`).

## Testes obrigatórios

Ver T-EQP-048 (15 testes). Cobertura ≥85%.

## Riscos / pontos sensíveis

1. **`tem_fatura_aberta` stub retorna False:** durante Marco 2, cedente nunca bloqueado por fatura. Risco real só quando módulo financeiro nasce. Mitigação: hook `port-binding-validator` ainda permite Empty se override explícito em settings dev/test.
2. **`consentimento_compartilhamento_historico_em_transferencia`:** UI ainda não existe (Marco 2 entrega só backend). Cessionário visualiza ficha 360° sem certs anteriores até portal-cliente Wave B+. Mitigação: serializer já oculta corretamente; UI HTMX da ficha mostra banner.
3. **Aceite por portal-cliente:** Marco 2 não tem portal-cliente. Aceite é capturado via UI HTMX no Aferê (atendente preenche "aceite presencial — cliente assinou no balcão"). V2 com portal-cliente real.
4. **Texto do termo legalmente vinculante:** versionado em constants. Mudança = nova versão. Aceites antigos preservam versão dada (advogado R2 US-CLI-001).

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar separação trans aceite x equip update (atômico via @transaction.atomic).
- `advogado-saas-regulado`: validar texto do termo + sanitização do payload audit + base legal art. 7º V/VI.
- `consultor-rbc-iso17025`: confirmar que segregação de histórico atende cl. 4.2.

## Non-goals deste plano

- NÃO implementar portal-cliente para aceite externo (Wave B+).
- NÃO implementar A3 obrigatória na transferência (V2 configurável por tenant).
- NÃO implementar webhook de aceite via e-mail externo (V2).
- NÃO implementar VIEW real `FinanceiroQueryService` (depende módulo financeiro).

---

## Endereçamento da revisão (12 ressalvas)

### Tech-lead

- **TL1 (CRÍTICA — atomicidade):** use case com `@transaction.atomic` + `select_for_update()` no `Equipamento` (lost-update em transferência concorrente). Outbox descartado — `audit_trail.eventos` WORM já serve como log-as-bus (padrão Marco 1 clientes).
- **TL2 (CRÍTICA — oracle cross-tenant):** **1 SELECT tenant-scoped único** `Cliente.objects.filter(id=novo_cliente_id).first()` (RLS é defesa primária). NUNCA dois SELECTs. Teste fuzzing 100 UUIDs respostas byte-idênticas.
- **TL3 (ALTA — Idempotency-Key):** tabela PostgreSQL `idempotency_key` com RLS (não Redis — embora Redis exista agora, idempotency precisa de durabilidade transacional). Decorator `@idempotent` em `src/infrastructure/shared/idempotency.py`. T-EQP-049/050 novas.
- **TL4 (ALTA — consentimento_compartilhamento):** **flag imutável no `TransferenciaEquipamentoAceite`** (decisão daquela transferência) + **flag derivada `mostrar_historico_anterior` no `Equipamento`** (último aceite governa). Modelo v3 atualizado.
- **TL5 (ALTA — ordem de validações):** Idempotency-Key → payload sintático → authz → existência (422 genérico) → bloqueio (412) → lock+update. Reason 422 SEMPRE idêntico.
- **TL6 (MÉDIA — ip_hash):** salt por tenant + canonização IPv6 (reusar `hash_pii_com_salt_tenant` do fix Marco 1).

### Advogado

- **R1 (BLOQUEANTE — texto termo v1.0):** `TEXTOS_HISTORICOS["v1.0-2026-05-18"]` em `src/infrastructure/equipamentos/texto_versao_transferencia.py` replica D2 do PRD-advogado + 3 gaps (canal LGPD art. 18, Lei 14.063/2020 art. 4º I, não-cessão NF-e/cert/responsabilidades). Texto completo no parecer.
- **R2 (BLOQUEANTE — aceite presencial = fraude):** mitigação tríplice **OBRIGATÓRIA** Marco 2:
  - Campos novos: `aceite_origem_atendente_user_id` + `aceite_origem_evidencia_storage_key` (idem destino).
  - Aviso UX CLT art. 482 "a" + CP art. 299 — checkbox ciência obrigatório (Tela 8 ui.md v3).
  - `via` no payload do evento (enum: portal_cliente_otp / email_confirmado / presencial_atendente / contrato_fisico_digitalizado — Marco 2 só presencial/contrato_fisico).
  - Dívida documentada em `transferencia-aceite-presencial-marco2.md`.
- **R3 (CONCERN — limite chars):** `motivo_detalhe` 500→300 chars. Regex anti-PII reusa US-EQP-001.
- **R4 (CONCERN — payload faltando):** `equipamento.transferido` payload acrescenta `texto_versao_id` + `aceite_origem_via` + `aceite_destino_via`. Padronizar `motivo_texto_hash` → `motivo_detalhe_hash`.
- **R5 (CONCERN — estrutura constants):** `texto_versao_transferencia.py` espelha `lgpd.py` Marco 1 (VERSAO_VIGENTE + TEXTOS_HISTORICOS). Trigger `bloquear_update_aceite_apos_concretizado` cobre `texto_renderizado_hash`. Testes: mudança não-retroativa + versão inexistente 400.
- **R6 (CONCERN — texto rejeição 409 idempotency):** mensagem PT inequívoca pra reuso de key fora da janela 24h.

## Sequência revisada de tasks (15 originais + 5 novas)

- **T-EQP-038**: model `TransferenciaEquipamentoAceite` com `consentimento_compartilhamento` (TL4 imutável) + `aceite_*_atendente_user_id` + `aceite_*_evidencia_storage_key` (R2) + `aceite_*_via` enum (R2) + RLS
- **T-EQP-039**: `texto_versao_transferencia.py` com texto v1.0 completo (R1 + R5)
- **T-EQP-040**: enum `motivo_categoria_transferencia`
- **T-EQP-041**: regex anti-PII `motivo_detalhe` 300 chars (R3)
- **T-EQP-042**: adapter `DjangoBloqueioClienteQueryService` reusa Marco 1
- **T-EQP-043**: porta `FinanceiroQueryService` + `EmptyFinanceiroQueryServiceAdapter` (allowed em dev/test via override)
- **T-EQP-044**: use case `TransferirEquipamento` com `@transaction.atomic` + `select_for_update` (TL1) + ordem dura TL5 + 1 SELECT TL2
- **T-EQP-045**: serializer `EquipamentoSerializer` oculta certs anteriores se `mostrar_historico_anterior=false` (TL4 derivada)
- **T-EQP-046**: action `equipamento.transferir` no seed authz + predicate `tenant_nao_suspenso` (ADR-0015)
- **T-EQP-047**: rate limit 10 req/min/usuário
- **T-EQP-047a (NOVA)**: aviso UX checkbox ciência CLT/CP (R2)
- **T-EQP-048**: testes (15 originais + 4 R6 advogado + 1 TL2 fuzzing 100 UUIDs)
- **T-EQP-049 (NOVA)**: migration tabela `idempotency_key` com RLS (TL3)
- **T-EQP-050 (NOVA)**: decorator `@idempotent` em `src/infrastructure/shared/idempotency.py` (TL3)
- **T-EQP-051a (NOVA)**: trigger `bloquear_update_aceite_apos_concretizado` estendido para `texto_renderizado_hash` (R5)
