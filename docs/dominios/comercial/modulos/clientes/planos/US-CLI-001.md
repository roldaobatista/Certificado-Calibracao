---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-001
---

# Plano US-CLI-001 — Cadastrar cliente PF em <1min

> Story em `docs/dominios/comercial/modulos/clientes/prd.md` §6.
>
> **Estado atual:** PARCIAL — base do modelo + API CRUD + validação CPF/CNPJ via VO já entregues. Falta completar AC-1 (409 estruturada) + AC-2 (aceite LGPD + evento).
>
> **Revisão técnica:** APROVADO COM RESSALVAS pelo tech-lead — 5 ressalvas endereçadas abaixo (§ Endereçamento revisão).
>
> **Revisão jurídica:** APROVADO COM RESSALVAS pelo advogado — 6 ressalvas endereçadas + texto do aceite cravado abaixo.

## Resumo

Completar AC-CLI-001-1 (link "cliente já existe" na 409) e AC-CLI-001-2 (aceite LGPD/RAT-03 obrigatório no cadastro + publicar evento `Cliente.Criado`).

## Sequência de tasks

- **T-CLI-001**: Campo `aceite_lgpd_em` (datetime) obrigatório no POST + migration.
- **T-CLI-002**: Catálogo de finalidades LGPD (RAT-03 + outras) em `docs/conformidade/comum/finalidades-lgpd.md` (curto, criar).
- **T-CLI-003**: Response 409 estruturada quando dedup dispara: `{"detail": "cliente_ja_existe", "cliente_id": "<uuid>", "link": "/api/v1/clientes/<uuid>"}` em vez de IntegrityError 400.
- **T-CLI-004**: Publicar `Cliente.Criado` na `auditoria` no `perform_create` (event-as-audit-trail enquanto eventbus formal não existe — Wave A).
- **T-CLI-005**: Testes cobrindo AC-1 (409 com link) e AC-2 (aceite LGPD obrigatório + evento gravado).

## Modelos/tabelas envolvidos

- `Cliente`: adicionar `aceite_lgpd_em` (DateTimeField).
- `Auditoria` (já existente, F-A): receberá entrada `Cliente.Criado`.

## Endpoints envolvidos

- `POST /api/v1/clientes/`: passa a validar aceite_lgpd_em obrigatório se POST; 409 estruturada em dedup.

## Hooks ativados

- `tenant-id-validator` (tem `tenant_id` no INSERT)
- `authz-check` (view já tem authz_action)
- `migration-rls-check` (alter na tabela já com RLS — não cria policy nova, deve passar)

## Testes obrigatórios

- AC-CLI-001-1: `test_dedup_retorna_409_com_link.py::test_cnpj_repetido_devolve_409_com_uuid_existente`
- AC-CLI-001-2 — LGPD: `test_aceite_lgpd_obrigatorio.py::test_post_sem_aceite_lgpd_em_retorna_400`
- AC-CLI-001-2 — evento: `test_evento_cliente_criado_gravado_em_auditoria.py::test_post_cliente_grava_audit_cliente_criado`

## Riscos / pontos sensíveis

1. **Backfill**: tabela `clientes` em dev tem 0 linhas — sem dados a migrar. Em prod (não existe ainda) precisaria backfill com `aceite_lgpd_em = criado_em` ou NULL.
2. **Catálogo de finalidades** pode crescer — começar com 4 (`execucao_contrato`, `obrigacao_legal`, `interesse_legitimo`, `consentimento`).
3. Evento `Cliente.Criado` ainda não tem eventbus — F-B não entregou Procrastinate ativo. Solução interim: gravar em `auditoria` como `action="Cliente.Criado"` com `payload_jsonb` contendo `cliente_id`. Wave B troca pra publish no bus quando este existir.

## Subagentes a consultar

- `advogado-saas-regulado`: validar texto do aceite LGPD + finalidade RAT-03.
- `tech-lead-saas-regulado`: validar interim event-as-audit-trail.

## Non-goals deste plano

- NÃO implementar US-002, 003, 004, 005 aqui — entram em planos separados.
- NÃO implementar consulta ReceitaWS (V2 conforme PRD §4).
- NÃO criar UI — só backend + testes.

---

## Endereçamento da revisão (11 ressalvas)

### Tech-lead (5)
- **TL1 (CRÍTICA — 409 cross-tenant safe):** dedup detectado via queryset filtrado por `active_tenant` (NUNCA `IntegrityError.__cause__`). Teste cross-tenant non-leak obrigatório.
- **TL2 (ALTA — campos LGPD):** `aceite_lgpd_em` (datetime null), `aceite_lgpd_versao` (str40 da constante vigente), `aceite_lgpd_ip_hash` (str64), `aceite_lgpd_origem` (enum balcao/portal/importacao), `aceite_lgpd_dispensa_motivo` (str60 vazio default).
- **TL3 (ALTA — evento):** `action = "cliente.criado"` (lowercase). Payload `{"cliente_id": uuid, "tipo_pessoa": str, "tenant_id": uuid, "documento_hash": sha256}` — sem CPF/CNPJ cru. Sem migração futura pro bus — bus publica adicional, audit fica.
- **TL4 (MÉDIA — hooks):** `_test-runner.sh` antes de commit (rodaremos).
- **TL5 (MÉDIA — testes faltantes):** acrescentar cross-tenant non-leak (mesmo CPF tenant A e B = 201 + 201), payload inválido (sem aceite_lgpd_em em PF = 400), audit não-órfão em rollback (ATOMIC_REQUESTS=True).

### Advogado (6)
- **R1 (texto cita tenant como controlador):** template com placeholder `[Razão Social do Tenant]` injetado em runtime.
- **R2 (snapshot legal completo):** os 4 campos de TL2 atendem (versão + ip_hash + finalidade + origem).
- **R3 (PJ sem PF dispensa):** se `tipo_pessoa=PJ` E `aceite_lgpd_em` não informado E `aceite_lgpd_dispensa_motivo` não informado → API rejeita 400 com mensagem "PJ sem aceite LGPD exige justificar dispensa (ex: 'pj_sem_pf_associada')". Se preenchido → aceite_lgpd_em NULL aceito.
- **R4 (link direitos LGPD):** UI fora de escopo deste plano (só backend). Backend retorna no response do POST campo `lgpd_direitos_link: "/{tenant_slug}/lgpd"` pra UI futura usar.
- **R5 (comentário retenção):** docstring do `Cliente.aceite_lgpd_*` cita "art. 16 II — acessórios à execução, retenção alinhada com cliente principal, crypto-shredding Wave B".
- **R6 (VO rejeita estrangeiro com mensagem clara):** mensagem de erro do CPF/CNPJ inclui "cadastro de estrangeiro será suportado em V2 — não use CPF de terceiro".

## Catálogo de finalidades LGPD

Criar `docs/conformidade/comum/finalidades-lgpd.md` com 4 entradas iniciais (validadas pelo advogado):
- `execucao_contrato` (Art. 7º V LGPD)
- `obrigacao_legal` (Art. 7º II — NF-e, certificado ISO 17025)
- `interesse_legitimo` (Art. 7º IX)
- `consentimento` (Art. 7º I)

## Texto do aceite LGPD (cravado pelo advogado, v1.0-2026-05-18)

> "Declaro estar ciente de que **[Razão Social do Tenant]** tratará meus dados pessoais (nome, CPF, contato e endereço) para a **execução dos serviços contratados** e para o cumprimento de **obrigações legais e regulatórias** aplicáveis (fiscais, metrológicas e contratuais), conforme art. 7º, incisos II e V, da Lei 13.709/2018 (LGPD). Posso exercer meus direitos de titular (art. 18) pelo canal indicado em **[link: /{tenant_slug}/lgpd]**."

**Versão da constante:** `v1.0-2026-05-18`. Mudança futura = nova versão, aceites antigos preservam versão dada.

## Sequência revisada de tasks

- **T-CLI-001**: criar `src/infrastructure/clientes/lgpd.py` com constants (`VERSAO_VIGENTE`, dict `TEXTOS_HISTORICOS`).
- **T-CLI-002**: criar `docs/conformidade/comum/finalidades-lgpd.md`.
- **T-CLI-003**: migration `0004_aceite_lgpd_e_origem.py` adicionando 5 campos LGPD ao `Cliente`.
- **T-CLI-004**: atualizar `Cliente.clean()` aplicando regras PF/PJ + dispensa.
- **T-CLI-005**: atualizar `ClienteSerializer` aceitando os 5 campos LGPD; preencher `aceite_lgpd_versao` automaticamente com `VERSAO_VIGENTE` se POST com `aceite_lgpd_em`.
- **T-CLI-006**: atualizar `ClienteViewSet.perform_create()` — coletar IP do request, hashear, passar pro serializer; capturar dedup via queryset filtrado (não IntegrityError); gravar audit `cliente.criado`.
- **T-CLI-007**: corrigir mensagem de erro CPF/CNPJ rejeitando estrangeiro (VO em `src/domain/shared/value_objects.py`).
- **T-CLI-008**: testes — 6 novos:
  - `test_aceite_lgpd_pf_obrigatorio`
  - `test_aceite_lgpd_pj_dispensa_com_motivo`
  - `test_aceite_lgpd_pj_sem_motivo_e_400`
  - `test_dedup_retorna_409_estruturada_com_link`
  - `test_dedup_cross_tenant_nao_vaza` (CPF=X em tenant A → 201; CPF=X em tenant B → 201, sem 409)
  - `test_post_cliente_grava_audit_cliente_criado_sem_pii`
