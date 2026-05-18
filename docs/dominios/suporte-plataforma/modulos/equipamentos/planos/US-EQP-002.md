---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-002
---

# Plano US-EQP-002 — Editar equipamento com versionamento pós-emissão

> Story em `prd.md` §6 (US-EQP-002).
>
> **Pré-requisito:** US-EQP-001 entregue (módulo + tabela `equipamento` + porta `CertificadoQueryService` stub).
>
> **Revisão (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 tech-lead + 6 advogado. Pareceres em `revisoes/US-EQP-002-{tech-lead,advogado}.md`. **Decisão Roldão: fatiar workflow gestor_qualidade em US-EQP-002b separada.**

## Resumo

Implementar PATCH em equipamento com (a) bloqueio de campos imutáveis pós-cert (INV-025), (b) versionamento via `EquipamentoVersao` quando há cert emitido, (c) motivo de mudança enum controlado (RBC B7), (d) assinatura A3 do RT obrigatória em perfil A para mudanças em classe/faixa, (e) workflow de aprovação `gestor_qualidade` quando `motivo=outros`.

## Sequência de tasks

- **T-EQP-016**: hook novo `equipamento-imutabilidade-check.sh` em `.claude/hooks/` — bloqueia migration que altere `tag`, `numero_serie`, `fabricante`, `cliente_id_original_hash`, `perfil_tenant_no_momento_cadastro` sem trigger PG correspondente. Atualizar `_test-runner.sh` com 6 casos. INV-checker integrado.
- **T-EQP-017**: model `EquipamentoVersao` + migration 0005_equipamento_versao — UNIQUE `(equipamento_id, versao_n)` + RLS + esquema Pydantic do `snapshot_atributos_versionaveis` em `src/domain/suporte_plataforma/equipamentos/snapshot.py`.
- **T-EQP-018**: enum `motivo_mudanca` em `src/domain/suporte_plataforma/equipamentos/enums.py` (6 valores RBC B7: correcao_cadastro_inicial / reparo_reclassificou / recalibracao_revelou_drift_permanente / troca_componente_principal / reidentificacao_fabricante / outros).
- **T-EQP-019**: migration 0006_trigger_imutaveis_pos_cert — trigger PG `bloquear_update_imutaveis_pos_cert` consulta porta `CertificadoQueryService.equipamento_tem_certificado_emitido` (via função SQL stub que sempre retorna false enquanto módulo certificados não existe; quando módulo nascer, vira VIEW). Exige `# tests-coverage` apontando happy+unhappy.
- **T-EQP-020**: campos novos em `EquipamentoVersao` — `exige_assinatura_a3_rt` (bool) + `assinatura_a3_hash` (text NULL) + `motivo_detalhe` (text); migration 0007.
- **T-EQP-021**: use case `EditarEquipamento` em `src/application/.../editar_equipamento.py`:
  - Se tenta tocar imutável → 422 com mensagem PT.
  - Se altera versionável + porta `CertificadoQueryService.equipamento_tem_certificado_emitido()` retorna false → UPDATE direto.
  - Se altera versionável + cert emitido → cria `EquipamentoVersao` com snapshot completo (incluindo `cliente_atual_id_no_momento` — tech-lead C2).
  - Se altera `classe_exatidao`/`faixa_medicao` + perfil A → exige `assinatura_a3_token` no payload; valida via porta `AssinaturaA3Service` (a criar — stub `MockAssinaturaA3Service` para Wave A Marco 2 que sempre retorna ok).
  - Se `motivo_mudanca=outros` → exige `motivo_detalhe ≥100 chars` + retorna 202 "aguardando aprovação gestor qualidade" (workflow async: cria registro `AprovacaoPendenteEquipamentoVersao` que o gestor aprova/rejeita; Marco 2 entrega a fila pendente, aprovação manual via Django admin).
- **T-EQP-022**: porta `AssinaturaA3Service` (Protocol) + adapter `MockAssinaturaA3Service` (sempre ok + log warning) + `LacunaWebPkiAssinaturaA3Service` stub (a implementar quando ADR-0009 fechar).
- **T-EQP-023**: actions novas `equipamento.editar` + `equipamento.aprovar_versionamento` no seed authz (migration 0008).
- **T-EQP-024**: tabela `AprovacaoPendenteEquipamentoVersao` (migration 0009) + Django admin com botão "aprovar / rejeitar" e justificativa.
- **T-EQP-025**: emit eventos `equipamento.editado` (pré-cert UPDATE direto) e `equipamento.versao_criada` (pós-cert, payload `{equipamento_id, versao_n, campos_alterados[], motivo_mudanca, assinou_a3}`).
- **T-EQP-026**: testes:
  - `test_editar_pre_cert_update_direto`
  - `test_editar_pos_cert_cria_versao_novo_snapshot` (INV-025)
  - `test_imutavel_pos_cert_retorna_422_tag` (INV-025)
  - `test_imutavel_pos_cert_retorna_422_numero_serie` (INV-025)
  - `test_imutavel_pos_cert_retorna_422_fabricante` (INV-025)
  - `test_imutavel_pos_cert_retorna_422_perfil_tenant` (RBC B4)
  - `test_motivo_outros_exige_justificativa_100_chars`
  - `test_motivo_outros_dispara_aprovacao_pendente_202`
  - `test_perfil_A_altera_classe_sem_a3_retorna_422`
  - `test_perfil_A_altera_classe_com_a3_aceita_e_grava_hash`
  - `test_perfil_B_altera_classe_sem_a3_aceita` (não exige A3 fora de A)
  - `test_cliente_atual_id_preservado_no_snapshot_versao` (tech-lead C2)
  - `test_localizacao_fisica_com_pii_em_versao_rejeita` (INV-EQP-LOC-001 aplica em versionamento também)
  - `test_evento_versao_criada_grava_audit_com_motivo_enum`
  - `test_authz_metrologista_pode_editar` / `test_authz_atendente_nao_pode_editar`

## Modelos/tabelas envolvidos

- **Novo:** `equipamento_versao`
- **Novo:** `aprovacao_pendente_equipamento_versao`
- **Já existe:** `equipamento` (US-EQP-001) — recebe trigger PG
- **Já existe (F-A):** `auditoria.eventos`

## Endpoints envolvidos

- `PATCH /v1/equipamentos/{id}`
- `POST /v1/equipamentos/{id}/aprovacoes-versao/{aprovacao_id}/decidir` (gestor qualidade — Marco 2 deixa via Django admin; endpoint vira US futura)

## Hooks ativados

- Todos os do US-EQP-001 + `equipamento-imutabilidade-check.sh` (T-EQP-016) + `policy-test-coverage` no trigger PG (T-EQP-019).

## Testes obrigatórios

Ver T-EQP-026 (15 testes). Cobertura ≥85%.

## Riscos / pontos sensíveis

1. **Porta `AssinaturaA3Service` stub:** `MockAssinaturaA3Service` sempre ok pode mascarar bugs no fluxo. Mitigação: 2 testes (`perfil_A_sem_a3` e `perfil_A_com_a3`) garantem que o **fluxo de exigência** funciona, não a validação real da assinatura.
2. **Trigger PG depende de porta:** consulta `CertificadoQueryService` via função SQL stub. Quando módulo certificados nascer, função vira VIEW real. Hook `port-binding-validator` (a criar US-EQP-003) bloqueia release prod se binding ainda for stub.
3. **Workflow async `gestor_qualidade`:** Marco 2 entrega tabela + Django admin. Endpoint próprio + UI HTMX entram em US futura. Risco: aprovação manual pendente fica eternamente se gestor não decide — adicionar job de SLA D+7 que escala alerta P2.
4. **Snapshot vs cliente_atual_id (tech-lead C2):** decisão é incluir `cliente_atual_id_no_momento` no snapshot. Toda transferência (US-EQP-004) também precisa criar versão? Não — transferência altera `cliente_atual_id` (operacional, não versionável). Snapshot guarda valor no momento de mudança de versionável.

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar trigger PG com função stub + workflow async + adapter `MockAssinaturaA3Service`.
- `advogado-saas-regulado`: validar texto PT da exigência A3 + audit hash de aprovação do gestor.
- `consultor-rbc-iso17025`: confirmar que enum motivo_mudanca + assinatura A3 RT atendem cl. 7.5 + 8.4.

## Non-goals deste plano

- NÃO implementar integração real Lacuna Web PKI (ADR-0009 quando fechar).
- NÃO implementar UI HTMX do gestor aprovar.
- NÃO implementar VIEW real `tem_certificado_emitido` (depende módulo certificados).
- NÃO implementar versionamento de outros atributos além dos listados (versionavel é fechado).
- **NÃO implementar workflow `gestor_qualidade` aprovando `motivo=outros` (fatiado pra US-EQP-002b).** US-EQP-002 entrega versionamento + motivo enum + A3 RT em perfil A. `motivo=outros` retorna 202 "aguardando aprovação — não implementado neste Marco; use motivo específico" (até US-EQP-002b chegar).

---

## Endereçamento da revisão (12 ressalvas)

### Tech-lead

- **TL1 (CRÍTICA — função SQL stub escapa hook):** função SQL `equipamento_tem_certificado_emitido_v0_stub()` (sufixo `_v0_stub` mandatório). Estender `port-binding-validator.sh` para varrer `pg_proc` por funções `_v0_stub` em `settings.production`. COMMENT PG explícito. Teste anti-promoção.
- **TL2 (ALTA — `MockAssinaturaA3Service` bomba):** gravar canário em `auditoria` action `assinatura_a3.mock_usado` com hash formato `MOCK-A3-{uuid}`. Stub Lacuna (`LacunaWebPkiAssinaturaA3Service`) `raise NotImplementedError`. Hook `mock-in-production` cobre.
- **TL3 (ALTA — fatiar US):** **ACEITO POR ROLDÃO.** Workflow gestor_qualidade vai pra US-EQP-002b. Esta US entrega só versionamento + A3 RT + erro 422 para `motivo=outros`.
- **TL4 (MÉDIA — JSONB):** Pydantic com `extra="forbid"` na camada application. GIN index só se medir hot path (não criar agora).
- **TL5 (MÉDIA — enum fechado):** mini-ADR `ALTER TYPE motivo_mudanca` (procedimento + revisão RBC obrigatória) — link em `docs/adr/` (a criar quando demanda nascer). Teste anti-regressão dos 6 valores.
- **TL6 (MÉDIA — race trigger PG):** use case com `select_for_update()` no Equipamento; trigger é defesa em profundidade; 409 esperada em corrida.

### Advogado

- **R1 (BLOQUEADOR — textos PT-BR rejeição 422):** 5 textos prontos por campo imutável (TAG, NS, fabricante, perfil_tenant, cliente_id_original) citando ISO 17025 cl. 8.4 + 7.8.2 + NIT-DICLA-005/030 + caminho alternativo (motivo `correcao_cadastro_inicial` ou sucateamento). Versionar em `src/infrastructure/equipamentos/mensagens_imutaveis.py`.
- **R2 (BLOQUEADOR — audit aprovação imutável):** 16 campos da `AprovacaoPendenteEquipamentoVersao` (vai pra US-EQP-002b mas modelagem cravada aqui): `gestor_user_id_hash` (sobrevive crypto-shredding), `decisao_assinatura_hash` (HMAC tenant-salt), `parecer_gestor_texto` (regex anti-PII INV-EQP-VERSAO-001), trigger `bloquear_update_decisao_aprovacao` (estende `audit-immutability-check`). Segregação ISO 17025 cl. 6.2 (solicitante ≠ aprovador). SLA D+3 (sem cert) / D+7 (com cert).
- **R3 (CONCERN — A3 versionada):** campo novo `assinatura_a3_versao_texto_id` em `EquipamentoVersao`. Texto v1.0 com 6 cláusulas + Lei 14.063/2020 art. 4º III + MP 2.200-2 art. 10 §1º + Lei 9.933/1999.
- **R4 (CONCERN — INV-EQP-VERSAO-001):** regex anti-PII em `motivo_detalhe` (INV cravada). Mensagem rejeição 400 PT.
- **R5 (CONCERN — INV-EQP-VERSAO-002):** envelope eventos sanitizado — 5 proibições (motivo_detalhe bruto, valores antigo/novo, cliente_atual_id UUID, A3 hash completo, NS em claro). INV cravada.
- **R6 (CONCERN — testes):** 4 novos — `test_motivo_detalhe_com_pii_rejeita`, `test_parecer_gestor_com_pii_rejeita` (US-002b), `test_solicitante_nao_pode_aprovar_propria_versao` (US-002b), `test_evento_versao_criada_nao_vaza_motivo_detalhe`.

## Sequência revisada de tasks (US-EQP-002 reduzida — gestor_qualidade migrou pra 002b)

- **T-EQP-016**: hook `equipamento-imutabilidade-check.sh` (TL1 estende a função SQL `_v0_stub`)
- **T-EQP-017**: model `EquipamentoVersao` + migration + esquema Pydantic `extra=forbid` (TL4)
- **T-EQP-018**: enum `motivo_mudanca` + teste anti-regressão 6 valores (TL5)
- **T-EQP-019**: função SQL stub `_v0_stub` + migration 0006 trigger consumindo função
- **T-EQP-020**: `EquipamentoVersao.assinatura_a3_versao_texto_id` (R3) + textos v1.0 em `src/infrastructure/equipamentos/parecer_tecnico_rt.py`
- **T-EQP-020a (NOVA)**: `src/infrastructure/equipamentos/mensagens_imutaveis.py` com 5 textos PT-BR (R1)
- **T-EQP-021**: use case `EditarEquipamento` com `select_for_update()` (TL6) + 422 estruturada PT (R1) + regex anti-PII em `motivo_detalhe` (R4)
- **T-EQP-022**: porta `AssinaturaA3Service` + `MockAssinaturaA3Service` com canário (TL2)
- **T-EQP-023**: action `equipamento.editar` no seed authz
- **T-EQP-024**: stub de tabela `AprovacaoPendenteEquipamentoVersao` ainda neste Marco (campos R2) — implementação completa em US-EQP-002b
- **T-EQP-025**: eventos `equipamento.editado`/`versao_criada` sanitizados (R5 — INV-EQP-VERSAO-002)
- **T-EQP-026**: testes (14 — removidos os 3 de aprovação `motivo=outros` que vão pra US-002b; acrescentados R6 + TL5)
