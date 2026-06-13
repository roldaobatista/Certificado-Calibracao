---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: colaboradores
tipo: reviews-p2
relacionados:
  - docs/faseamento/colaboradores/spec.md
  - docs/faseamento/colaboradores/T-COL-000-investigacao.md
---

# P2 — Revisões consolidadas + decisões Roldão — frente `colaboradores`

> tech-lead-saas-regulado + advogado-saas-regulado, 2026-06-13. Ambos
> **APROVA COM CORREÇÕES**. Rodada batch Roldão (frente nova) resolveu 2 decisões
> de produto. Todas as correções incorporadas na `spec.md` v2.

## Decisões Roldão (rodada batch P2, 2026-06-13)

- **R-COL-1 — MOTORISTA_UMC sem CNH = SALVAR COM PENDÊNCIA.** Cadastra agora,
  marca `pendencia_cnh=true`; o bloqueio acontece na **alocação** (frota/agenda),
  não no cadastro. Resolve o conflito Família 0 (modelo-de-domínio × api/ui).
  → corrigir `api.md`/`ui.md` no P8 (remover o 422 `MOTORISTA_SEM_CNH` do cadastro).
- **R-COL-2 — ASO fora do MVP de colaboradores.** ASO (dado de saúde, art. 11) é
  do módulo `seguranca-trabalho` (dono oficial). Enum `Documento.tipo` no MVP =
  `{CTPS, CNH, CERTIFICADO_CURSO, OUTRO}` — **sem ASO**. Resolve ADV-COL-03/07 por
  remoção (não há PII de saúde órfã). PRD não pedia ASO; foi adição do modelo.

## Tech-lead — TL-COL-01..15 (APROVA COM CORREÇÕES)

**Bloqueantes (resolvidos na spec v2):**
- **TL-COL-01** Cadeia de identidade Colaborador↔Usuario↔RT: `ResponsavelTecnicoTenant`
  correlaciona por `usuario_id` (FK obrigatória), não `colaborador_id`. ⇒ atribuir
  SIGNATARIO exige `colaborador.usuario_id IS NOT NULL` **E** `RTCompetencia` vigente
  com **o mesmo `usuario_id`** (não só "FK RT vigente"). Nome/CPF probatório do
  signatário = snapshot WORM do RT; colaboradores **não** é fonte. → `INV-COL-SIGNATARIO-IDENTIDADE` (D-COL-11 v2).
- **TL-COL-02** `Colaborador.Desligado` (e eventos com consumer cross-módulo) por
  **outbox transacional** (`outbox=True`, ADR-0033 + `bus_outbox` no mesmo atomic),
  **não** cadeia-hash-only nem "fail-open lazy". INV-INT-011 exige entrega garantida
  ≤2s. "fail-open lazy" (ADR-0066) é para **predicate** síncrono, não para publicação. (D-COL-10 v2)
- **TL-COL-05** Mascaramento PII precisa ser **multi-papel** (`MATRIZ_VISAO_PII[campo][papel]`
  + caso `proprio_colaborador`), não binário como `filtrar_visao_margem`. `/elegiveis`
  precisa DTO mínimo. CPF: **últimos 2 dígitos** (conflito spec×exports → 2). (D-COL-7 v2)
- **TL-COL-06** **Blur de rosto NÃO existe no molde** (é dev novo) e na foto de
  colaborador o rosto É a finalidade. ⇒ sem blur; EXIF strip mantém. Foto via
  `AnexoStoragePort` (consistência), não BYTEA. (D-COL-6 v2)
- **TL-COL-08** ASO não pode dividir storage/RBAC com CTPS/CNH ⇒ resolvido por R-COL-2 (ASO fora).

**Altos (resolvidos na spec v2):**
- **TL-COL-03** Path domain **ANINHA**: `src/domain/rh_frota_qualidade/colaboradores/`
  + `src/application/rh_frota_qualidade/colaboradores/` + `src/infrastructure/colaboradores/`
  (infra sempre flat). Critério real do codebase: domínio multi-módulo aninha
  (comercial/metrologia/operacao); precificacao/pps são módulos soltos. (D-COL-1 v2)
- **TL-COL-04** Precisa dos **dois** campos: `data_desligamento` (estado de negócio,
  manager `ativos`) **+** `deletado_em`/`deletado_por_usuario_id`/`deletado_motivo`
  (soft-delete Padrão C, corrige cadastro errado, manager default). (D-COL-3 v2)
- **TL-COL-07** "trigger BEFORE DELETE molde clientes" **não existe** (clientes usa FK
  PROTECT). Consumers a jusante referenciam por **UUID opaco** (sem FK) ⇒ PROTECT não
  dispara. INV-COL-INATIVO = **fail-open lazy genuíno** (ADR-0066): check no use case
  consultando módulos a jusante via porta (stub bloqueia conservador enquanto não existem)
  + trigger PG defensivo. (D-COL-3 v2 / §5)
- **TL-COL-09** Não citar `JanelaVigencia` como reuso em model mutável; verdade
  probatória do signatário mora no RT (WORM). Papel mutável OK p/ demais. (D-COL-4 v2)
- **TL-COL-10** `CatalogoHabilidade`: molde seed **GLOBAL** (authz `0003_seed_perfis`,
  não per-tenant `precificacao 0008`); lista de grandezas **literal** no seed (sem import
  de `metrologia` — não há enum canônico de grandeza, é texto livre em `RTCompetencia.grandeza`);
  model **próprio em `colaboradores`** com seed na migration da frente (não poluir
  `configuracoes_sistema` com tabela de RH). Atinge o objetivo do gap #4 (aresta runtime
  com `calibracao` quebrada) por lista literal. → ajusta A10. (D-COL-5 v2)

**Médios (anotados no plan/P7):** TL-COL-11 advisory lock por tenant na troca de DONO
(ADR-0065) + drill cronometrado · TL-COL-12 `prefetch_related` em list/`/elegiveis`
(`assertNumQueries` P7) · TL-COL-13 evento de desligamento carrega chave idempotente
estável (`colaborador_id+data_desligamento`) · TL-COL-14 CHECK `0 ≤ comissao_default_pct ≤ 100`
· TL-COL-15 audit via `publicar_evento` (cadeia central) + INV-AUDIT-IMMUT-002 (tabela
`*_eventos` nasce com trigger anti-mutation).

## Advogado/DPO — ADV-COL-01..08 (APROVA COM CORREÇÕES; congelamento RAT/DPIA respeitado)

**Código que NÃO espera o GATE (na spec v2):**
- **ADV-COL-01 (MÉDIO)** Base legal **difere por vínculo** (CLT=obrigação legal art.7º II
  × PJ/terceirizado=execução de contrato art.7º V; estagiário=Lei 11.788). ⇒ mapa
  `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` (constante de domínio — fonte que o RAT do GATE
  vai fotografar) + `INV-COL-DOC-VINCULO` (alerta: TERCEIRIZADO/PJ não anexam CTPS —
  minimização art.6º III). Determina se o titular **consegue** exercer eliminação.
- **ADV-COL-03/07 (MÉDIO)** ASO segregado ⇒ resolvido por R-COL-2 (ASO fora do MVP).
- **ADV-COL-04 (MÉDIO)** `/elegiveis` cross-módulo ⇒ `INV-COL-ELEGIVEIS-MINIMO`: DTO
  **allowlist** (`colaborador_id`, `nome_exibicao`, `papel`, `habilidades`, `ativo`);
  **NUNCA** CPF/e-mail/telefone/documentos/comissão/foto/vínculo/observação.
- **ADV-COL-02 (BAIXO)** Foto de colaborador é dado **comum** (identificação, art.7º V),
  **não** biométrico sensível (art.11 §4 só com extração/matching). Sem blur; EXIF strip
  sim. Matching biométrico futuro = non-goal + hook `block-biometric-feature` + RIPD/ADR.
- **ADV-COL-06 (BAIXO)** Vocabulário: hash HMAC = **pseudonimização** (não "anonimização")
  — CPF é enumerável; a chave HMAC é PII-crítica. `tipos_servico_assinava` no payload:
  manter (contrato v9 INV-INT-011) mas documentar minimização. `comissoes_pendentes_count` OK.
- **ADV-COL-08 (BAIXO)** Busca `q` por CPF = oráculo de presença ⇒ guard: busca-por-CPF
  só para quem tem `ver_pii` (Dono).

**GATEs rastreados (CONGELADOS até GATE-LGPD-RAT-CONSOLIDACAO — NÃO escrever agora):**
A3 RAT CTPS/CNH/foto/certificados · A4 retenção CTPS/CNH/foto · A6 zona ADR-0021 por
campo · A7 DPIA cadastro (não-ASO). `[OAB-PRE-PROD]`: texto de bloqueio fundamentado ao
titular · ratificação matriz de zonas aplicada a colaborador · DPA Aferê↔tenant sobre PII
de colaborador · designação formal de DPO. **Nada bloqueia dogfooding; bloqueia go-live com dado real.**

**ADV-COL-05 (OK):** Cenário D suficiente p/ MVP — hard-delete bloqueado (INV-COL-INATIVO)
é o controle crítico já no código; anonimização diferida; signatário preservado 25a.

## Novas invariantes (vs spec v1)

`INV-COL-SIGNATARIO-IDENTIDADE` (usuario_id casa com RT) · `INV-COL-ELEGIVEIS-MINIMO`
(DTO allowlist) · `INV-COL-DOC-VINCULO` (alerta coerência documento×vínculo).
Removidas/N/A: `INV-COL-DOC-ASO-RBAC` (ASO fora do MVP — R-COL-2).
