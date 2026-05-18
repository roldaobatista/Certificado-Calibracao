---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-006
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-006.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Caminho A (RecebimentoProvisorio separada) cravado por decisão Roldão.
---

# Tasks T-EQP-057..T-EQP-069 — US-EQP-006 (receber no lab ISO 17025 cl. 7.4 + RecebimentoProvisorio)

> Forward-looking. Pré-requisitos: US-EQP-001 + US-EQP-002 + porta `NotificacaoClienteService` (US-EQP-005). Caminho A: `Equipamento.cliente_atual_id` nasce NOT NULL; provisório vai pra tabela separada `RecebimentoProvisorio`.

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-057 | Model `EquipamentoRecebimento` (migration 0018) — campos modelo v3 (`storage_key` no lugar de URL — TL3), `recebimento_aberto_id` materializado por trigger no Equipamento, RLS | `0018_equipamento_recebimento.py` | AC-1 | — | TL3 (storage_key) + TL6 (recebimento_aberto_id) |
| T-EQP-057a (NOVA) | Model `RecebimentoProvisorio` separado (Caminho A) + RLS + trigger anti-FK provisória em `certificado` (cravado em modelo v3) | `0018_equipamento_recebimento.py` (mesma) | AC-1 | INV-EQP-PROV-001 | TL1 (CRÍTICA — Caminho A Roldão) |
| T-EQP-058 | Enum `condicao_visual`: `integro / amassado / lacre_violado / contaminado / sem_acessorios / outros` | `src/domain/.../enums.py` | AC-2 | — | — |
| T-EQP-059 | Enum `decisao_apos_anomalia`: `prosseguir / contatar_cliente_aguardando / recusar_devolver / prosseguir_com_ressalva` | `src/domain/.../enums.py` | AC-2 | — | — |
| T-EQP-060 | Enum `status_fluxo_lab` + tabela `_TRANSICOES_PERMITIDAS` frozenset em `status_fluxo_lab.py` (espelho INV-027 OS); 8 estados + 2 alternativos terminais | `src/domain/.../status_fluxo_lab.py` | AC-3 | — | TL4 (CRÍTICA — paridade Python↔SQL) |
| T-EQP-060a (NOVA) | Migration seed `equipamentos_status_fluxo_lab_transicao` (tabela SQL espelho do frozenset) | `0019_seed_transicoes_status_fluxo_lab.py` | AC-3 | — | TL4 |
| T-EQP-061 | Trigger PG `validar_transicao_status_fluxo_lab` rejeita UPDATE com transição inválida (migration 0019) + `# tests-coverage` happy/unhappy | `0019_trigger_transicao_fluxo_lab.py` | AC-3 | — | TL4 |
| T-EQP-061a (NOVA) | Teste `test_paridade_tabela_python_e_pg_transicoes` (3 testes — frozenset == tabela SQL; transição inválida ambos rejeitam; idempotência mesma transição = no-op) | `tests/equipamentos/test_paridade_transicoes.py` | AC-3 | — | TL4 |
| T-EQP-062 | Serviço upload foto em `foto_upload.py` — valida ≤5MB + JPEG/PNG; **EXIF strip CORRETO**: `Image.new(mode, size) + putdata(image.getdata()) + ImageOps.exif_transpose` (cobre JPEG+PNG+rotação); teste byte-search por `b"Exif\x00\x00"` + `b"GPS"`; retorna `FotoArmazenada(storage_key, hash)` | `src/infrastructure/equipamentos/foto_upload.py` | AC-4 | — | TL2 (CRÍTICA — EXIF strip correto) |
| T-EQP-063 | Porta `FotoStorageService` retornando `FotoArmazenada` com `storage_key` (NÃO URL — URL via signed URL TTL curto) + `LocalFotoStorageServiceAdapter` (dev — path `/tmp/afere-fotos-dev/`) + `B2FotoStorageServiceAdapter` stub (Wave A+); binding em settings; **Empty proibido em prod** via `port-binding-validator` | `src/domain/.../ports/foto_storage_service.py` + adapters | AC-4 | — | TL3 (ALTA — storage_key) |
| T-EQP-064 | Use case `RegistrarRecebimento`:<br/>(a) perfil A → ≥1 foto obrigatória; outros opcional;<br/>(b) condição != `integro` → `decisao_apos_anomalia` + `justificativa_decisao ≥30 chars` obrigatórios;<br/>(c) regex anti-PII `anomalias_observadas` + `justificativa_decisao` (espelho INV-EQP-LOC-001);<br/>(d) cria recebimento com `status_fluxo_lab=recebido_pendente_inspecao`;<br/>(e) atualiza `Equipamento.status=em_calibracao_lab` + `recebimento_aberto_id`;<br/>(f) audit `equipamento.recebido_no_lab` + anomalia: `equipamento.anomalia_recebimento` (campo `anomalia_hash` HMAC + `anomalia_categoria` enum — R6);<br/>(g) decisão `contatar_cliente_aguardando` → `NotificacaoClienteService.notificar_anomalia_recebimento()` | `src/application/.../registrar_recebimento.py` | AC-1, AC-2, AC-3, AC-4 | INV-EQP-ANOM-001/002, INV-EQP-LOC-001 análoga | R3 advogado (BLOQ INVs cravadas), R6 (payload hash) |
| T-EQP-064a (NOVA) | Trigger PG `materializar_recebimento_aberto_id` no Equipamento (atualiza on insert/update do recebimento) | `0018_equipamento_recebimento.py` (mesma) | AC-3 | — | TL6 (recebimento_aberto_id) |
| T-EQP-065 | Use case `AvancarFluxoLab` — `PATCH /v1/equipamentos/{id}/recebimentos/{rid}`; valida transição via `transicao_permitida(de, para)`; idempotente (mesma transição duas vezes = no-op); audit `equipamento.fluxo_lab_avancado` (`de + para + observacoes`) | `src/application/.../avancar_fluxo_lab.py` | AC-3 | — | TL4 (idempotência) |
| T-EQP-066 | Use case `RegistrarDevolucao` — `POST /.../devolucoes`; valida status in `aguardando_devolucao`; foto devolução obrigatória em A; `termo_devolucao_assinado_storage_key` opcional (qualificado **documento particular CPC art. 411 III** — NÃO Lei 14.063 — R2); atualiza `data_hora_devolucao` + `condicao_visual_devolucao` + `fotos_devolucao` + `status_fluxo_lab=devolvido`; atualiza `Equipamento.status=ativo` + `recebimento_aberto_id=NULL` (TL6); audit `equipamento.devolvido_ao_cliente` | `src/application/.../registrar_devolucao.py` | AC-1, AC-2, AC-4 | — | R2 advogado (CPC art. 411 III + UI renomear "Comprovante de devolução assinado") |
| T-EQP-066a (NOVA) | Endpoint `DELETE /v1/equipamentos/{id}/recebimentos/{rid}/fotos/{foto_id}` — motivo enum + justificativa + guard ISO 17025 (409 se exclusão deixaria perfil A sem evidência cl. 7.4.4) + audit imutável (hash preservado, binary deletado); authz: metrologista + admin (almoxarife NÃO) | `src/infrastructure/equipamentos/views.py` + use case | AC-4 | — | R4 advogado (CONCERN exclusão isolada) |
| T-EQP-067 | Actions seed authz (migration 0020): `equipamento.receber_no_lab`, `equipamento.avancar_fluxo_lab`, `equipamento.devolver`, `equipamento.deletar_foto_recebimento` (admin+metrologista); perfis: almoxarife + metrologista + admin (receber/avançar/devolver) | `0020_seed_authz_recebimento.py` | AC-1 | SEC-LEAST-PRIV | R4 |
| T-EQP-067a (NOVA) | `aviso_camera_versao_id` em constants (versionado) + `aviso_camera_aceito_em` no `EquipamentoRecebimento` (espelho `aceite_lgpd_versao_texto` US-CLI-001 R2); texto idêntico ao `ui.md §Tela 6` | `src/infrastructure/equipamentos/aviso_camera.py` | AC-2 | — | R1 advogado (cópia literal + AC novo EQP-006-6) |
| T-EQP-067b (NOVA) | Template e-mail `contatar_cliente_aguardando` v1.0-2026-05-18 — ≤120 palavras, base art. 7º V, cita tenant como remetente, oferece devolução, sem marketing | `templates/email/contatar_cliente_aguardando.html` | AC-3 | — | R5 advogado |
| T-EQP-067c (NOVA) | Use case `PromoverRecebimentoProvisorio` — promove `RecebimentoProvisorio` → `Equipamento` definitivo via evento único auditável (Caminho A) | `src/application/.../promover_provisorio.py` | AC-1 | INV-EQP-PROV-001 | TL1 (Caminho A Roldão) |
| T-EQP-068 | Estender ficha 360° (US-EQP-003) — aba "Recebimentos" visível só pra metrologista + almoxarife (RBC C8) | `src/infrastructure/equipamentos/serializers.py` (estendido) | AC-2 | — | RBC C8 |
| T-EQP-069 | Suite 22 testes: perfil A sem foto 422 / com foto 201; perfil B sem foto 201; condição anômala sem decisão 400; `contatar_cliente_aguardando` dispara notificação; EXIF removido (byte-search TL2); foto > 5MB 400; transições válidas/inválidas; devolução sem aguardando_devolucao 412; devolução perfil A sem foto 422; devolução atualiza status equipamento; múltiplos recebimentos no tempo; ficha aba visível só metrologista+almoxarife; audit recebido_no_lab; authz atendente não pode; **+ `test_recebimento_provisorio_nao_emite_cert` (INV-EQP-PROV-001 — Caminho A)** **+ paridade transições TL4 (3 testes T-EQP-061a)** **+ trigger recebimento_aberto_id (TL6)** **+ regex anti-PII anomalias/justificativa fuzzing (R3)** **+ DELETE foto guard ISO 17025 (R4)** **+ payload anomalia_hash (R6)** | `tests/equipamentos/test_us_eqp_006_recebimento.py` | AC-1, AC-2, AC-3, AC-4 | INV-EQP-ANOM-001/002, INV-EQP-PROV-001 | todas |

## Pareceres aplicados

- `revisoes/US-EQP-006-tech-lead.md` — APROVADO COM RESSALVAS (**TL1 CRÍTICA Caminho A ACEITO**, TL2 CRÍTICA EXIF strip correto, **TL3 ALTA storage_key ACEITO**, TL4 CRÍTICA paridade Python↔SQL, TL5 payload audit, **TL6 recebimento_aberto_id ACEITO**)
- `revisoes/US-EQP-006-advogado.md` — APROVADO COM RESSALVAS (R1 aviso UX cópia literal, R2 CPC art. 411 III, **R3 BLOQ INV-EQP-ANOM-001/002**, R4 endpoint DELETE foto, R5 template contatar_cliente, R6 payload `anomalia_hash` + `anomalia_categoria`)

## Total

20 tasks (13 originais + 7 novas) · 22 testes · 3 migrations · 2 tabelas novas (`equipamento_recebimento` + `recebimento_provisorio`) · 2 templates e-mail v1.0 versionados · 2 triggers PG.
