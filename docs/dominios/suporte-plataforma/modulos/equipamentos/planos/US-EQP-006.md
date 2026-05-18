---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-006
---

# Plano US-EQP-006 — Receber equipamento no laboratório (ISO 17025 cl. 7.4)

> Story em `prd.md` §6 (US-EQP-006).
>
> **Pré-requisitos:** US-EQP-001 (equipamento), US-EQP-002 (versionamento se cadastro provisório vira definitivo), US-EQP-005 (porta `NotificacaoClienteService`).
>
> **Revisão (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 tech-lead + 6 advogado. Pareceres em `revisoes/US-EQP-006-{tech-lead,advogado}.md`. **Decisão Roldão Caminho A: entidade nova `RecebimentoProvisorio` separada** (cravada em modelo-de-dominio v3 + INV-EQP-PROV-001).

## Resumo

Implementar entidade `EquipamentoRecebimento` com máquina de estados ≥6 fases (RBC B3), foto + condição visual obrigatórias em perfil A (RBC B2), checklist de anomalias + decisão (RBC B1), workflow de devolução com termo assinado, eventos `equipamento.recebido_no_lab` / `equipamento.devolvido_ao_cliente` / `equipamento.anomalia_recebimento`.

## Sequência de tasks

- **T-EQP-057**: model `EquipamentoRecebimento` (migration 0018) — todos campos do modelo-de-dominio v2 §EquipamentoRecebimento + RLS policy.
- **T-EQP-058**: enum `condicao_visual` em domain enums: `integro | amassado | lacre_violado | contaminado | sem_acessorios | outros`.
- **T-EQP-059**: enum `decisao_apos_anomalia`: `prosseguir | contatar_cliente_aguardando | recusar_devolver | prosseguir_com_ressalva`.
- **T-EQP-060**: enum `status_fluxo_lab` com máquina de estados — `aguardando_recebimento → recebido_pendente_inspecao → em_inspecao_visual → aguardando_calibracao → em_calibracao → aguardando_aprovacao_tecnica → aguardando_devolucao → devolvido`. Alternativos terminais: `nao_conformidade_recebimento`, `nao_conformidade_calibracao`. Função `transicao_permitida(de, para) -> bool` em `src/domain/.../status_fluxo_lab.py` (espelho INV-027 da OS).
- **T-EQP-061**: trigger PG `validar_transicao_status_fluxo_lab` (migration 0019) — rejeita UPDATE com transição inválida.
- **T-EQP-062**: serviço de upload de foto em `src/infrastructure/equipamentos/foto_upload.py`:
  - Valida tamanho ≤5MB + formato (JPEG/PNG).
  - **Remove EXIF obrigatoriamente** (Pillow `image.copy()` sem `_getexif()`).
  - Storage: Backblaze B2 com chave KMS por tenant (RAT-EQP-FOTO + retenção). Para Wave A Marco 2 Sandbox, usar storage local com aviso "não usar em prod" — porta `FotoStorageService` + adapter `LocalFotoStorageService` (dev) + `B2FotoStorageService` stub (Wave A+).
  - Retorna URL + hash da foto (para audit).
- **T-EQP-063**: porta `FotoStorageService` em `src/domain/.../ports/` + adapters dev/stub-prod + binding em settings.
- **T-EQP-064**: use case `RegistrarRecebimento`:
  - Validar perfil_tenant_no_momento_cadastro do equipamento + se A → ≥1 foto obrigatória; senão opcional.
  - Validar condição visual != integro → `decisao_apos_anomalia` + `justificativa_decisao ≥30 chars` obrigatórios.
  - Criar `EquipamentoRecebimento` com `status_fluxo_lab=recebido_pendente_inspecao`.
  - Atualizar `Equipamento.status = em_calibracao_lab` (enquanto recebimento aberto).
  - Gravar audit `equipamento.recebido_no_lab` + se anomalia: `equipamento.anomalia_recebimento` + chamar `NotificacaoClienteService.notificar_anomalia_recebimento()` se decisão = `contatar_cliente_aguardando`.
- **T-EQP-065**: use case `AvancarFluxoLab` — `PATCH /v1/equipamentos/{id}/recebimentos/{rid}`:
  - Validar transição via `transicao_permitida(de, para)`.
  - Idempotente: mesma transição duas vezes não duplica audit.
  - Audit `equipamento.fluxo_lab_avancado` com `de + para + observacoes`.
- **T-EQP-066**: use case `RegistrarDevolucao` — `POST /v1/equipamentos/{id}/recebimentos/{rid}/devolucoes`:
  - Validar `status_fluxo_lab` in últimas fases (aguardando_devolucao).
  - Foto devolução obrigatória em A.
  - `termo_devolucao_assinado_url` opcional (portal cliente Wave B+; presencial via upload).
  - Atualiza `data_hora_devolucao` + `condicao_visual_devolucao` + `fotos_devolucao` + `status_fluxo_lab=devolvido`.
  - Atualiza `Equipamento.status = ativo`.
  - Audit `equipamento.devolvido_ao_cliente`.
- **T-EQP-067**: actions no seed authz (migration 0020): `equipamento.receber_no_lab`, `equipamento.avancar_fluxo_lab`, `equipamento.devolver`. Atribuir: almoxarife + metrologista + admin.
- **T-EQP-068**: estender ficha 360° (US-EQP-003) — aba "Recebimentos" mostra histórico de recebimentos do equipamento; visível só pra metrologista + almoxarife (RBC C8).
- **T-EQP-069**: testes:
  - `test_recebimento_perfil_A_sem_foto_retorna_422` (RBC B2)
  - `test_recebimento_perfil_A_com_foto_e_condicao_integro_201`
  - `test_recebimento_perfil_B_sem_foto_aceita_201` (foto opcional fora de A)
  - `test_condicao_anomala_sem_decisao_retorna_400` (RBC B1)
  - `test_decisao_contatar_cliente_dispara_notificacao_via_porta`
  - `test_foto_exif_removido_no_upload` (RAT-EQP-FOTO)
  - `test_foto_excede_5mb_retorna_400`
  - `test_transicao_recebido_para_em_inspecao_visual_ok`
  - `test_transicao_aguardando_recebimento_direto_para_devolvido_retorna_422` (RBC B3)
  - `test_transicao_para_nao_conformidade_recebimento_ok`
  - `test_devolucao_sem_status_aguardando_devolucao_retorna_412`
  - `test_devolucao_perfil_A_sem_foto_retorna_422`
  - `test_devolucao_atualiza_equipamento_status_para_ativo`
  - `test_recebimento_apos_devolucao_cria_novo_registro` (múltiplas calibrações no tempo)
  - `test_ficha_360_aba_recebimentos_visivel_metrologista_almoxarife_apenas` (RBC C8)
  - `test_evento_equipamento_recebido_no_lab_grava_audit`
  - `test_authz_atendente_nao_pode_receber`

## Modelos/tabelas envolvidos

- **Novo:** `equipamento_recebimento` (com RLS + trigger transição)
- **Já existe:** `equipamento` (atualiza `status` no recebimento e devolução)
- **Já existe:** `audit_trail.eventos`

## Endpoints envolvidos

- `POST /v1/equipamentos/{id}/recebimentos` (multipart com fotos)
- `PATCH /v1/equipamentos/{id}/recebimentos/{rid}` (avançar fluxo)
- `POST /v1/equipamentos/{id}/recebimentos/{rid}/devolucoes` (multipart com fotos + termo)

## Hooks ativados

- Todos anteriores + `policy-test-coverage` no trigger PG transição.

## Testes obrigatórios

Ver T-EQP-069 (17 testes). Cobertura ≥85%. Total estimado Marco 2: ~85 testes novos do módulo equipamentos.

## Riscos / pontos sensíveis

1. **EXIF strip:** Pillow não remove EXIF "in place" por default — precisa criar nova imagem sem EXIF + reescrever. Teste exige conferência byte-a-byte de ausência de EXIF.
2. **Storage local em dev:** path absoluto fora do repo (`/tmp/afere-fotos-dev/`) para não vazar pra produção. Override `FotoStorageService` Empty proibido em prod via `port-binding-validator`.
3. **Máquina de estados:** 8 estados principais + 2 alternativos = 10. Função `transicao_permitida` precisa cobrir explicitamente quais transições são válidas (não usar lógica implícita "i+1"). Tabela de transições em `status_fluxo_lab.py`.
4. **Equipamento sucateado durante recebimento:** se metrologista detecta dano irreparável durante calibração, fluxo vai pra `nao_conformidade_calibracao` + admin sucata equipamento (US-EQP-005). Documento o fluxo cruzado.
5. **Foto pode ter PII (rosto):** advogado B4 — RAT-EQP-FOTO. Marco 2 entrega EXIF strip + aviso UX antes da câmera (Tela 6). Blur facial fica V2.
6. **Termo devolução assinado:** Marco 2 não tem portal-cliente. URL aponta pra upload presencial pelo almoxarife (foto da assinatura física do cliente no momento da retirada).

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar arquitetura porta `FotoStorageService` + função `transicao_permitida` + trigger PG.
- `advogado-saas-regulado`: validar texto aviso UX antes da câmera + base legal RAT-EQP-FOTO em perfil B/C/D (opcional vs obrigatória em A).
- `consultor-rbc-iso17025`: confirmar que máquina de estados ≥6 fases + foto condição chegada atende cl. 7.4.4 + 7.4.5 + 7.10 completamente.

## Non-goals deste plano

- NÃO implementar blur facial server-side (V2).
- NÃO implementar portal-cliente para aceite digital da devolução (Wave B+).
- NÃO implementar AWS B2 storage real (porta + stub local; deploy real fica em runbook).
- NÃO implementar OCR anti-PII em foto (V2).
- NÃO implementar workflow async de aprovação de NC (Marco 2 deixa transição manual via Django admin; UI futura).

---

## Endereçamento da revisão (12 ressalvas)

### Tech-lead

- **TL1 (CRÍTICA — cadastro provisório):** **ACEITO POR ROLDÃO Caminho A.** Tabela `RecebimentoProvisorio` SEPARADA (cravada em modelo-de-dominio v3 + INV-EQP-PROV-001). `Equipamento.cliente_atual_id` NASCE NOT NULL (US-EQP-001). Promoção é evento único auditável.
- **TL2 (CRÍTICA — EXIF strip):** `image.copy()` NÃO basta. Código exato: `Image.new(mode, size) + putdata(image.getdata()) + ImageOps.exif_transpose` (cobre JPEG + PNG + rotação). Teste byte-search por `b"Exif\x00\x00"` + `b"GPS"`.
- **TL3 (ALTA — `FotoStorageService` storage_key):** **ACEITO.** `FotoArmazenada` retorna `storage_key` (NÃO URL — URL é regenerada via signed URL TTL curto). Modelo v3 atualizou `fotos_chegada`/`fotos_devolucao`/`foto_principal_storage_key`.
- **TL4 (CRÍTICA — paridade Python↔SQL):** enum + tabela `_TRANSICOES_PERMITIDAS` frozenset + função SQL com tabela seed `equipamentos_status_fluxo_lab_transicao` + teste de paridade `test_paridade_tabela_python_e_pg_transicoes` + idempotência (mesma transição = no-op). Hook `policy-test-coverage` cobra 3 testes.
- **TL5 (MÉDIA — payload audit):** hash de foto sim; `tag`/`numero_serie`/nome não.
- **TL6 (MÉDIA — `recebimento_aberto_id`):** **ACEITO.** Materializado via trigger no Equipamento (cravado em modelo v3). Resolve ambiguidade `status=em_calibracao_lab` com múltiplos recebimentos.

### Advogado

- **R1 (CONCERN — aviso UX cópia literal):** task de replicação do texto exato de `ui.md §Tela 6` + `aviso_camera_versao_id` versionado + `aviso_camera_aceito_em` (espelho `aceite_lgpd_versao_texto` US-CLI-001 R2). Novo AC-EQP-006-6.
- **R2 (CONCERN — termo devolução):** Lei 14.063/2020 art. 4º I **NÃO cobre** upload da foto da assinatura física pelo almoxarife — qualificação correta: documento particular CPC art. 411 III. Renomear na UI ("Comprovante de devolução assinado"). Modelo v3 já renomeou `termo_devolucao_assinado_storage_key`. Wave B+ migra pra Lei 14.063 art. 4º I quando portal-cliente entrar.
- **R3 (BLOQUEANTE — INV-EQP-ANOM-001/002):** `anomalias_observadas` + `justificativa_decisao` regex anti-PII (espelho INV-EQP-LOC-001). INVs cravadas. Aviso UX abaixo do textarea + testes novos.
- **R4 (CONCERN — exclusão isolada foto):** endpoint novo `DELETE /v1/equipamentos/{id}/recebimentos/{rid}/fotos/{foto_id}` com motivo enum + justificativa + guard ISO 17025 (409 se exclusão deixaria perfil A sem evidência cl. 7.4.4) + audit imutável (hash preservado, binary deletado). Authz: metrologista + admin (almoxarife NÃO). Blur diferido V2.
- **R5 (CONCERN — template `contatar_cliente_aguardando`):** texto cravado (≤120 palavras, base art. 7º V, cita tenant como remetente, oferece devolução, sem marketing). Versionado.
- **R6 (CONCERN — payload `anomalia_recebimento`):** renomear `anomalia` → `anomalia_hash` (HMAC salgado por tenant) + `anomalia_categoria` (enum). Defesa contra corner case regex.

## Sequência revisada de tasks

- **T-EQP-057**: model `EquipamentoRecebimento` (modelo v3 — storage_key) + RLS
- **T-EQP-057a (NOVA)**: model `RecebimentoProvisorio` (Caminho A — INV-EQP-PROV-001) + RLS + trigger anti-FK provisória em certificado
- **T-EQP-058**: enum `condicao_visual`
- **T-EQP-059**: enum `decisao_apos_anomalia`
- **T-EQP-060**: enum `status_fluxo_lab` + tabela `_TRANSICOES_PERMITIDAS` frozenset (TL4)
- **T-EQP-060a (NOVA)**: migration seed `equipamentos_status_fluxo_lab_transicao` (tabela SQL espelho TL4)
- **T-EQP-061**: trigger PG `validar_transicao_status_fluxo_lab` (TL4)
- **T-EQP-061a (NOVA)**: teste `test_paridade_tabela_python_e_pg_transicoes` (TL4)
- **T-EQP-062**: serviço upload de foto com EXIF strip CORRETO (TL2 — `Image.new + putdata + ImageOps.exif_transpose`) + teste byte-search (TL2)
- **T-EQP-063**: porta `FotoStorageService` retornando `FotoArmazenada` com `storage_key` (TL3) + `LocalFotoStorageServiceAdapter` (dev) + `B2FotoStorageServiceAdapter` stub
- **T-EQP-064**: use case `RegistrarRecebimento` + regex anti-PII `anomalias_observadas` (R3) + atualizar `recebimento_aberto_id` no Equipamento (TL6)
- **T-EQP-064a (NOVA)**: trigger PG `materializar_recebimento_aberto_id` (TL6)
- **T-EQP-065**: use case `AvancarFluxoLab` (idempotente TL4)
- **T-EQP-066**: use case `RegistrarDevolucao` com `termo_devolucao_assinado_storage_key` (R2 — qualificado CPC art. 411 III) + atualizar `recebimento_aberto_id=NULL` (TL6)
- **T-EQP-066a (NOVA)**: endpoint `DELETE /v1/equipamentos/{id}/recebimentos/{rid}/fotos/{foto_id}` com guard ISO 17025 (R4)
- **T-EQP-067**: actions seed authz + ação nova `equipamento.deletar_foto_recebimento` (admin+metrologista)
- **T-EQP-067a (NOVA)**: `aviso_camera_versao_id` em constants + `aviso_camera_aceito_em` no `EquipamentoRecebimento` (R1)
- **T-EQP-067b (NOVA)**: template e-mail `contatar_cliente_aguardando` v1.0-2026-05-18 (R5)
- **T-EQP-067c (NOVA)**: use case `PromoverRecebimentoProvisorio` em `src/application/.../promover_provisorio.py` (Caminho A TL1)
- **T-EQP-068**: ficha 360° aba "Recebimentos"
- **T-EQP-069**: testes (17 originais + R3 anti-PII fuzzing + R4 endpoint delete + R6 payload hash + TL4 paridade + TL6 trigger materializar + Caminho A: `test_recebimento_provisorio_nao_emite_cert` INV-EQP-PROV-001)
