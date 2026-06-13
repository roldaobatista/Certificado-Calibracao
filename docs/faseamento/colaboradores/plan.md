---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
proximo-passo: ready-for-implement
diataxis: reference
audiencia: [agente, tech-lead, auditor]
frente: colaboradores
tipo: plan
relacionados:
  - docs/faseamento/colaboradores/spec.md
  - docs/faseamento/colaboradores/reviews-consolidado.md
  - docs/faseamento/colaboradores/T-COL-000-investigacao.md
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/adr/0016-operacao-consistente.md
  - docs/faseamento/precificacao/plan.md
---

# Plan — frente `colaboradores` (RH mínimo, base nível 2)

> Deriva da `spec.md` v2 (P2 incorporado — tech-lead TL-COL-01..15 + advogado
> ADV-COL-01..08, AMBOS APROVA COM CORREÇÕES; decisões Roldão R-COL-1/2). Decisões
> D-COL-1..14 cravadas na spec §3; este plan materializa arquitetura por camada,
> fatias, riscos e GATEs. Molde de execução = frentes #1/#2/#3 (mesma anatomia).
> Módulo com **PII pesado** → P9 roda lente LGPD completa (auditor 10 obrigatório).

## Arquitetura (resumo operacional)

- **Path ANINHADO por domínio (D-COL-1 / TL-COL-03):**
  `src/domain/rh_frota_qualidade/colaboradores/` + `src/application/rh_frota_qualidade/colaboradores/`
  + `src/infrastructure/colaboradores/` (infra SEMPRE flat; `app_label = colaboradores`).
  Critério do codebase: domínio multi-módulo aninha (comercial/metrologia/operacao);
  precificacao/pps são módulos soltos. **Verificar no P5** se o conftest precisa de
  `_APP_MODULE_SUBPATH` (provável NÃO — models/migrations vivem em infra flat; o aninhamento
  é só de pacote Python no domain/application — molde `clientes` que aninha em `comercial/`).
- **Tabelas (5):** `colaborador` (raiz), `colaborador_papel`, `colaborador_habilidade`,
  `colaborador_documento` — todas RLS v2 FORCE + 4 policies; `catalogo_habilidade` —
  **GLOBAL read-only** (sem `tenant_id`, sem RLS por tenant; grant SELECT a `app_user`,
  INSERT só via migration de seed — TL-COL-10). **Verificar molde de tabela global no P5**
  (como a casa trata read-only global; checar se `authz` tem precedente).
- **Identidade Colaborador↔Usuario↔RT (D-COL-2/11 / TL-COL-01):** `Colaborador.usuario_id`
  é FK opcional. **SIGNATARIO exige** `usuario_id NOT NULL` **E** `RTCompetencia` vigente com
  **o mesmo `usuario_id`** (casa pessoa, não só "FK RT existe"). Nome/CPF probatório do
  signatário = snapshot WORM do `ResponsavelTecnicoTenant` — colaboradores só referencia.
  O predicate de RT (`responsavel_tecnico/predicates.py`) busca por `usuario_id`; reusar.
- **Desligamento (negócio) + soft-delete (correção) — DOIS mecanismos (D-COL-3 / TL-COL-04):**
  `data_desligamento`/`motivo_desligamento`/`ativo` (manager `ativos` filtra `data_desligamento
  IS NULL` → alimenta `/elegiveis`; registro permanece — INV-025) **+** `deletado_em`/
  `deletado_por_usuario_id`/`deletado_motivo` (soft-delete Padrão C, molde `clientes/models.py`;
  manager default filtra; `all_objects` expõe). Desligar → revoga papéis (revogado_em) +
  publica `Colaborador.Desligado` na MESMA transação.
- **Hard-delete bloqueado fail-safe (D-COL-3 / TL-COL-07 / INV-COL-INATIVO):** **nenhum
  endpoint de hard-delete no MVP** (só desligamento + soft-delete recuperável). Mecanismos:
  (a) trigger PG defensivo BEFORE DELETE no `colaborador` (bloqueia delete físico se houver
  papel/evento/filha — proteção mínima; consumers a jusante usam UUID opaco, então FK PROTECT
  do Django NÃO dispara); (b) porta `colaborador_referenciado_a_jusante` (Protocol + stub
  **conservador** que assume "pode estar referenciado" → bloqueia) como contrato fail-safe
  para a anonimização futura (GATE LGPD) — fail-open lazy ADR-0066 AQUI cabe (consulta a
  módulo inexistente). Hook `col-hard-delete-check` garante que nenhum endpoint de delete
  físico nasça sem a checagem.
- **Papel mutável com revogação auditada (D-COL-4 / TL-COL-09):** `data_inicio`/`data_fim?`/
  `revogado_em?` são COLUNAS do model (NÃO reusar VO `JanelaVigencia` em row mutável).
  DONO único por tenant = partial unique `WHERE papel='DONO' AND data_fim IS NULL AND
  revogado_em IS NULL`; **troca de DONO sob advisory lock por tenant** (ADR-0065, TL-COL-11).
  Revogação seta `revogado_em` — nunca deleta linha. Verdade probatória do signatário no RT (WORM).
- **CatalogoHabilidade seed global literal (D-COL-5 / TL-COL-10):** model próprio em
  `infrastructure/colaboradores/`; seed via `RunPython` na migration da frente, molde **global**
  (`authz/migrations/0003_seed_perfis.py` — NÃO per-tenant `precificacao/0008`). Lista de
  grandezas **literal no arquivo** (massa, volume, temperatura, dimensional, pressão, …) — sem
  import de `metrologia` (quebra a aresta runtime com `calibracao`, objetivo do gap #4).
  `Habilidade.catalogo_id` XOR `descricao_livre` (CHECK).
- **Documento + foto via `AnexoStoragePort` (D-COL-6 / TL-COL-06):** reusar a porta
  `AnexoStoragePort` (`application/metrologia/procedimentos_calibracao/anexo_storage.py`) +
  adapter `AnexoStorageLocal` content-addressed (SHA-256 server-side). **Foto pela MESMA porta**
  (não BYTEA inline): EXIF strip + MIME/5MB; **sem blur** (foto de colaborador é dado COMUM de
  identificação — ADV-COL-02). Enum `Documento.tipo = {CTPS, CNH, CERTIFICADO_CURSO, OUTRO}` —
  **ASO removido** (R-COL-2). `INV-COL-DOC-VINCULO` (alerta) bloqueia/avisa documento
  incompatível com vínculo (TERCEIRIZADO/PJ × CTPS). **B2 WORM real diferido** (GATE-COL-ANEXO-B2).
- **Mascaramento PII multi-papel server-side (D-COL-7 / TL-COL-05 / ADV-COL-04):** choke-point
  ÚNICO `filtrar_visao_pii(papeis_solicitante, sujeito, dados)` com `MATRIZ_VISAO_PII[campo][papel]`
  + caso `proprio_colaborador`; em TODO serializer; fail-closed. CPF só DONO (demais `***.***.***-NN`
  **últimos 2**); e-mail/telefone Dono/Gerente/próprio; CTPS/CNH só Dono+próprio. Busca `q` por
  CPF só p/ quem tem `ver_pii` (ADV-COL-08). Hook `col-pii-mascara-check`.
- **`/elegiveis` DTO mínimo (INV-COL-ELEGIVEIS-MINIMO / ADV-COL-04):** serializer **allowlist**
  separado do agregado: `colaborador_id`, `nome_exibicao`, `papel`, `habilidades`, `ativo` —
  NUNCA CPF/e-mail/telefone/documentos/comissão/foto/vínculo/observação. Teste UNHAPPY "campo
  fora da allowlist".
- **Eventos por OUTBOX TRANSACIONAL (D-COL-10 / TL-COL-02):** os eventos da frente têm consumers
  cross-módulo (≠ precificacao cadeia-só) → `publicar_evento(..., outbox=True)` (INSERT em
  `bus_outbox` no mesmo atomic, molde `audit/event_helpers.py`). `Colaborador.Desligado` carrega
  payload v9 + **chave idempotente estável** (`colaborador_id+data_desligamento`, TL-COL-13).
  6 consumers (INV-INT-011) plugam handlers depois, sem retrofit do publisher. **NÃO usar
  "fail-open lazy" para publicação** (só para predicate síncrono).
- **PII pseudonimizada em evento/log (D-COL-8 / ADV-COL-06):** CPF/nome/documento **hash
  HMAC-tenant** (ADR-0029/0064 — pseudonimização, não anonimização) em payload/log/4xx; só
  refs/UUID em claro. Reusar helper de hash canônico (M5/M9/PPS/precificacao). Hook
  `col-evento-pii-hash-check`. Chave HMAC-tenant é PII-crítica.
- **Base legal por vínculo no domínio (D-COL-6 / ADV-COL-01):** constante
  `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` (CLT=obrigação legal art.7º II; PJ/terceirizado=contrato
  art.7º V; estagiário=Lei 11.788) — fonte que o RAT do GATE fotografa. Determina resposta a
  pedido de eliminação. NÃO escrever RAT agora (congelado).
- **Audit INV-001 via cadeia central (D-COL-14 / TL-COL-15):** alteração de comissão/papel/
  desligamento via `publicar_evento` (cadeia hash). Tabela `*_eventos`, se criada, nasce com
  trigger anti-mutation (INV-AUDIT-IMMUT-002 + hook `audit-immutability-check`).
- **Anti-N+1 (TL-COL-12):** `prefetch_related` das filhas (papéis/habilidades/documentos) em
  `list` e `retrieve`; `/elegiveis` filtra no banco; `assertNumQueries` na Fatia 2.

## Cross-doc (P8 — emendas REAIS desta frente)

- `faseamento-modulos.md` linha ~105: mover `colaboradores` Wave B → **Wave A nível 2**
  (molde inline do `precificacao` linha 88) + nota "seed CatalogoHabilidade literal" (A9).
- `api.md`/`ui.md` de colaboradores: remover 422 `MOTORISTA_SEM_CNH` do cadastro (vira
  pendência — R-COL-1); remover ASO dos contratos (R-COL-2).
- `exports.md`: CPF mascarado = **últimos 2 dígitos** (corrige "últimos 3"); ASO fora do
  E-COL-04 (R-COL-2).
- `matriz-feature-perfil.md`: linha SIGNATARIO por perfil A/B/C/D (A8) + hook validator.
- `STATUS-GERADO.md` (via `scripts/status-projeto.sh`) + AGENTS §12: registrar GATE-COL-*.
- **CONGELADO (NÃO emendar agora — GATE-LGPD-RAT-CONSOLIDACAO):** RAT (A3), retenção (A4),
  zona ADR-0021 por campo (A6), DPIA cadastro (A7). Só rastrear como GATE.
- Catálogo de eventos: adicionar `Colaborador.Anonimizado` (A5) — contrato/schema (P7).

## Fatias

| Fatia | Entrega | Verificação (não declarar pronto sem rodar) |
|---|---|---|
| **1a domínio puro** | enums (`Vinculo` CLT/PJ/ESTAGIARIO/SOCIO/TERCEIRIZADO, `Papel` 7, `NivelHabilidade` APRENDIZ/CAPACITADO/MESTRE, `TipoDocumento` CTPS/CNH/CERTIFICADO_CURSO/OUTRO) + VO `CPF` (reusa shared) + entidades frozen (Colaborador, Papel, Habilidade, Documento, CatalogoHabilidade) + constante `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` + regras puras (`pode_atribuir_signatario(usuario_id, rt_match, perfil)`, `validar_dono_unico`, `pendencia_cnh_motorista`, `coerencia_documento_vinculo`, `derivar_ativo`, `cascade_revoga_papeis`, `payload_desligamento` v9) + porta `ColaboradorReferenciadoPort` (Protocol) + stub conservador + erros + repository Protocols | testes puros (signatario sem usuario_id → erro; RT não casa → erro; 2º DONO → erro; motorista sem CNH → pendencia=true sem erro — R-COL-1; terceirizado+CTPS → alerta vínculo; cascade revoga; payload v9 completo); ruff/mypy limpos |
| **1b schema PG** | models (5 tabelas) + migrations 0001..0006 (CreateModel + UNIQUE parcial CPF + partial unique DONO + CHECK comissão 0..100 + CHECK catalogo XOR livre / RLS v2 ×4 tabelas-tenant / `catalogo_habilidade` GLOBAL grant SELECT + INSERT-só-seed / trigger defensivo BEFORE DELETE no colaborador / grants / seed authz `colaboradores.*` / seed CatalogoHabilidade literal global) + mappers + repositories Django (advisory lock troca DONO) + drill `validar_colaboradores` + conftest seed | migrate OK; makemigrations --check; testes PG-real (RLS UNHAPPY ×4; UNIQUE CPF parcial; partial unique DONO; CHECK comissão; delete físico bloqueado por trigger; catalogo global legível por 2 tenants; seed authz + catalogo presentes); drill PASS |
| **2 use cases + REST** | cadastrar/editar (CPF imutável) / desligar (cascade + evento outbox) / atribuir_papel (signatario identidade+escopo; dono lock; motorista pendência) / revogar_papel / registrar_habilidade / anexar_documento (AnexoStoragePort + coerência vínculo) / consultar_elegiveis (DTO allowlist) / comissao_vigente + ViewSets ACTION_MAP `colaboradores.*` + `filtrar_visao_pii` em TODOS serializers + DTO mínimo `/elegiveis` + Idempotency-Key (escrita; leitura sem) + eventos `Colaborador.*` outbox hashificados + guard busca-CPF | testes puros (Fakes) + E2E PG-real (dedup CPF → 409; signatario UNHAPPY identidade ×3; mascaramento por papel ×N — Gerente não vê CPF, próprio vê próprio; `/elegiveis` nunca vaza PII; desligar publica 1 evento outbox payload v9; idempotência desligar 2x; `assertNumQueries` list/elegiveis — sem N+1) |
| **3 (P7) INVs + hooks + testes** | família `INV-COL-*` em REGRAS (nova seção) + `TestINV_COL_*` nomeadas (TST-004; PG-real onde é banco) + hooks no `pre-commit-manifest.tsv`: `col-pii-mascara-check`, `col-evento-pii-hash-check`, `col-hard-delete-check` + casos `_test-runner` + evento `Colaborador.Anonimizado` no catálogo (A5) + contagens via `status-projeto.sh --check` | hooks verdes (`bash .claude/hooks/_test-runner.sh`); anti-drift; `status-projeto.sh --check` verde |
| **P8** | emendas cross-doc REAIS (faseamento-modulos A9 · api/ui/exports R-COL-1/2 · matriz-feature-perfil A8) + matriz-reconciliacao ENXUTA (R20) + registro GATE-COL-* (STATUS-GERADO + AGENTS §12) + GATEs LGPD congelados rastreados (A3/A4/A6/A7) + frontmatters Família 0 draft→stable (lote R22) | gate anti-drift; `status-projeto.sh --check` |
| **P9** | auditores roteados (INV-RITUAL-003): 6 essenciais SEMPRE (qualidade·segurança·llm·idempotência·**conformidade-lgpd OBRIGATÓRIO [PII pesado]**·produto) + performance (list/elegiveis N+1) + observabilidade (PII em log + tenant_id/correlation_id) ; supplychain SÓ se dep nova (núcleo não traz); drift-docs FORA (R7). Verificação adversarial de TODO MÉDIO+ (R6); 2ª passada escopada (R5) | zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md; BAIXOs em lote pós-fechamento (R10) |

## Riscos mapeados

1. **Cadeia de identidade signatário (TL-COL-01) — risco ALTO.** Atribuir SIGNATARIO sem
   casar `colaborador.usuario_id == rt.usuario_id` liga colaborador a RT de outra pessoa →
   certificado com signatário errado. Teste UNHAPPY ×3 (usuario nulo / RT inexistente / RT de
   outro). A verdade probatória vem do RT (WORM), nunca do Colaborador.
2. **Evento por transporte errado (TL-COL-02).** Publicar `Colaborador.Desligado` por cadeia-só
   ou "fail-open lazy" fura o ≤2s de INV-INT-011 e força retrofit quando o 1º consumer ligar.
   Tem que ser `outbox=True` no mesmo atomic + chave idempotente. Teste do publisher (linha em
   `bus_outbox` + payload v9), independente dos consumers.
3. **Vazamento de PII no `/elegiveis` (ADV-COL-04) — risco ALTO.** Endpoint cross-módulo; se
   devolver o agregado mascarado vaza nome/telefone/e-mail p/ Operação. DTO allowlist é
   obrigatório (allowlist > blocklist). Teste UNHAPPY "campo fora da allowlist".
4. **Mascaramento multi-papel é padrão NOVO (TL-COL-05).** `filtrar_visao_pii` precisa estar em
   TODO serializer ANTES de qualquer endpoint sair. Hook `col-pii-mascara-check` + teste UNHAPPY
   por papel × campo. Risco = vazar CPF por um serializer esquecido.
5. **PII em log/evento (D-COL-8).** Risco = `logger.info(f"... cpf={cpf}")` ou CPF cru em corpo
   4xx. Hook `col-evento-pii-hash-check` (denylist adaptada do PEPH/PPS). Hash é pseudonimização.
6. **Tabela global `catalogo_habilidade` (TL-COL-10).** Sem `tenant_id` → não pode receber RLS
   por tenant nem cair no migration-linter de tenant_id (INV-TENANT-002). Tratamento especial:
   grant SELECT global, INSERT só seed. Verificar precedente na casa no P5 (evita falso-positivo
   do hook de tenant).
7. **Concorrência DONO (TL-COL-11).** Partial unique cobre INSERT duplo (→ 409); troca A→B sob
   advisory lock por tenant. Drill cronometrado (2 sessões) antes de "pronto pra produção".
8. **Base legal por vínculo (ADV-COL-01).** Sem o mapa no domínio, resposta a pedido de
   eliminação fica errada (CLT recusável × PJ frágil). Constante de domínio + validação
   documento×vínculo (alerta).

## GATEs nascidos / rastreados (não bloqueiam fechamento do núcleo)

- **GATE-COL-ANEXO-B2** — B2 WORM real dos documentos+foto (hoje `AnexoStorageLocal`).
- **GATE-COL-COMISSAO-COUNT** — `comissoes_pendentes_count` real no `Colaborador.Desligado`
  quando `comissoes` (a jusante) existir; hoje `=0` stub.
- **GATE-COL-CONSUMERS** — 6 reatores de `Colaborador.Desligado` (acesso-seguranca, os,
  comissoes, caixa-tecnico, certificados, suporte-saas) — módulos futuros plugam no outbox.
- **GATE-COL-PERFIL-MATRIZ** — linha matriz-feature-perfil SIGNATARIO por perfil A/B/C/D (A8).
- **GATE-LGPD-RAT-CONSOLIDACAO** (CONGELADO) — A3 RAT CTPS/CNH/foto/cert · A4 retenção · A6
  zona ADR-0021 por campo · A7 DPIA cadastro · `[OAB-PRE-PROD]`: texto bloqueio titular,
  ratificação matriz de zonas aplicada a colaborador, DPA Aferê↔tenant sobre PII de
  colaborador, designação DPO. Bloqueiam go-live com dado real, **não** dogfooding.

## Decisões do orquestrador (P3 — nenhuma de PRODUTO em aberto; R-COL-1/2 já no batch)

1. **Advisory lock troca de DONO = namespace `880_405`** (sequência da casa: 880_402 M8/CFG,
   880_403 PPS, 880_404 precificacao → 880_405). Confirmar livre no P5.
2. **6 migrations (0001..0006)** — CreateModel / RLS / trigger defensivo+partial-unique DONO /
   grants / seed authz / seed CatalogoHabilidade. `btree_gist` não é necessário (sem exclusion
   de vigência — papel é mutável, não WORM). Ajustar se o P5 revelar necessidade.
3. **Eventos por `outbox=True`** (cross-módulo) — diferente de precificacao (cadeia-só). Reusar
   `publicar_evento`/`event_helpers`; verificar assinatura real no P6.
4. **`CatalogoHabilidade` em `colaboradores`** (não em configuracoes-sistema) — desvio JUSTIFICADO
   do gap #4 (que listava configuracoes-sistema como UMA opção); o objetivo (quebrar aresta
   runtime com calibracao via lista literal) é atingido. Registrar nota no `plano-dependencia` no P8.
5. **ASO removido do enum (R-COL-2)** e **MOTORISTA pendência (R-COL-1)** — decisões Roldão; não reabrir.
