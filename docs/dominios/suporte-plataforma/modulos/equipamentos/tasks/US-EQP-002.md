---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-002
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-002.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Workflow gestor_qualidade fatiado pra US-EQP-002b (decisão Roldão / TL3).
---

# Tasks T-EQP-016..T-EQP-026 — US-EQP-002 (editar equipamento + versionamento pós-cert + A3 RT)

> Forward-looking. Pré-requisito: US-EQP-001 entregue. Workflow `motivo=outros` aprovação `gestor_qualidade` **FORA** desta US — vai pra US-EQP-002b. Esta US apenas modela stub da tabela `AprovacaoPendenteEquipamentoVersao` (campos R2 advogado já cravados).

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-016 | Hook `equipamento-imutabilidade-check.sh` + 6 casos `_test-runner.sh` (bloqueia ALTER em TAG/NS/fabricante/cliente_id_original_hash/perfil_tenant sem trigger PG) | `.claude/hooks/equipamento-imutabilidade-check.sh` | AC-1 | INV-025 | TL1 (CRÍTICA — estende com `_v0_stub`) |
| T-EQP-017 | Model `EquipamentoVersao` + migration 0005 + schema Pydantic `snapshot_atributos_versionaveis` (`extra="forbid"`) + UNIQUE `(equipamento_id, versao_n)` + RLS | `0005_equipamento_versao.py` + `snapshot.py` | AC-2 | INV-025 | TL4 (Pydantic forbid) |
| T-EQP-018 | Enum `motivo_mudanca` (6 valores RBC B7) + teste anti-regressão | `src/domain/.../enums.py` + teste | AC-3 | — | TL5 (mini-ADR `ALTER TYPE`) |
| T-EQP-019 | Função SQL `equipamento_tem_certificado_emitido_v0_stub()` + migration 0006 trigger `bloquear_update_imutaveis_pos_cert` consumindo a função (COMMENT explícito; sufixo `_v0_stub` mandatório) | `0006_trigger_imutaveis_pos_cert.py` | AC-1 | INV-025 | TL1 (CRÍTICA — função SQL stub escapa hook) |
| T-EQP-020 | Campos `exige_assinatura_a3_rt` (bool) + `assinatura_a3_hash` (text NULL) + `motivo_detalhe` (text) + `assinatura_a3_versao_texto_id` em `EquipamentoVersao`; migration 0007 | `0007_a3_e_motivo_detalhe.py` + `src/infrastructure/equipamentos/parecer_tecnico_rt.py` | AC-4 | — | R3 advogado (A3 versionada) |
| T-EQP-020a (NOVA) | `src/infrastructure/equipamentos/mensagens_imutaveis.py` — 5 textos PT-BR de rejeição 422 (TAG, NS, fabricante, perfil_tenant, cliente_id_original) citando ISO 17025 cl. 8.4 + 7.8.2 + NIT-DICLA-005/030 + caminho alternativo | `mensagens_imutaveis.py` | AC-1 | INV-025 | R1 advogado (BLOQUEADOR textos PT) |
| T-EQP-021 | Use case `EditarEquipamento` com `select_for_update()` no Equipamento; 422 estruturada PT; regex anti-PII em `motivo_detalhe`; ramo pré-cert UPDATE direto / pós-cert cria `EquipamentoVersao`; A3 RT obrigatório em perfil A pra classe/faixa; `motivo=outros` retorna 422 "não implementado neste Marco" (até 002b) | `src/application/.../editar_equipamento.py` | AC-1, AC-2, AC-4 | INV-025, INV-EQP-VERSAO-001 | TL6 (race trigger PG), R1 (textos), R4 (anti-PII INV-EQP-VERSAO-001) |
| T-EQP-022 | Porta `AssinaturaA3Service` + `MockAssinaturaA3ServiceAdapter` (sempre ok + canário audit `assinatura_a3.mock_usado` + hash `MOCK-A3-{uuid}`) + `LacunaWebPkiAssinaturaA3ServiceAdapter` (`raise NotImplementedError`) | `src/domain/.../ports/assinatura_a3_service.py` + adapters | AC-4 | INV-AUTHZ-001 | TL2 (ALTA — mock bomba; hook `mock-in-production` cobre) |
| T-EQP-023 | Action `equipamento.editar` no seed authz (migration 0008) | `0008_seed_authz_editar.py` | AC-1 | SEC-LEAST-PRIV | — |
| T-EQP-024 | Stub tabela `AprovacaoPendenteEquipamentoVersao` (campos R2 advogado já cravados aqui; implementação completa em 002b) | `0009_aprovacao_pendente_stub.py` | AC-3 | — | R2 advogado (modelagem antecipada) |
| T-EQP-025 | Eventos `equipamento.editado` (pré-cert) e `equipamento.versao_criada` (pós-cert) com envelope sanitizado — 5 proibições R5 advogado (sem motivo_detalhe bruto, sem valores antigo/novo, sem cliente_atual_id UUID, sem A3 hash completo, sem NS em claro) | `src/application/.../editar_equipamento.py` (emissor) | AC-3 | INV-EQP-VERSAO-002 | R5 advogado (CRAVADA INV) |
| T-EQP-026 | Suite ~14 testes: pré-cert UPDATE direto, pós-cert cria versão, imutável retorna 422 (TAG/NS/fabricante/perfil_tenant), motivo=outros retorna 422 neste Marco, perfil A altera classe sem A3 retorna 422, perfil A altera com A3 grava hash, perfil B altera sem A3 aceita, cliente_atual_id_no_momento preservado no snapshot, localizacao_fisica com PII em versão rejeita, evento versao_criada audit motivo enum, authz, **+ teste anti-regressão 6 valores enum (TL5)** **+ test_motivo_detalhe_com_pii_rejeita (R4)** **+ test_evento_versao_criada_nao_vaza_motivo_detalhe (R5)** | `tests/equipamentos/test_us_eqp_002_versionamento.py` | AC-1, AC-2, AC-3, AC-4 | INV-025, INV-EQP-VERSAO-001/002, RBC B4 | todas |

## Pareceres aplicados

- `revisoes/US-EQP-002-tech-lead.md` — APROVADO COM RESSALVAS (TL1 função SQL stub, TL2 mock A3, **TL3 fatiar 002b — ACEITO**, TL4 Pydantic forbid, TL5 mini-ADR enum, TL6 race trigger)
- `revisoes/US-EQP-002-advogado.md` — APROVADO COM RESSALVAS (R1 BLOC textos imutáveis, R2 BLOC audit aprovação 16 campos, R3 A3 versionada, R4 INV-EQP-VERSAO-001, R5 INV-EQP-VERSAO-002, R6 testes)

## Total

12 tasks (11 originais + 1 nova) · ~14 testes · 5 migrations · 1 hook novo (`equipamento-imutabilidade-check.sh`). Workflow gestor_qualidade migrou pra US-EQP-002b (13 testes adicionais lá).
