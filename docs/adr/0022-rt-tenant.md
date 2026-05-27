---
adr: 0022
titulo: Gestão do Responsável Técnico do tenant (RT — NIT-DICLA-021)
status: aceito
versao: v2 (2026-05-27 — RT competência por método específico, não só grandeza)
data: 2026-05-22
aceito-em: 2026-05-22 (Marco 2 entregue T-EQP-061..065 + tests/regressao/test_inv_eqp_rt_001.py)
v2-aceito-em: 2026-05-27 (auditoria 10 lentes pré-Wave A — L3#4 NIT-DICLA-021 exige método, não grandeza)
proposto-por: agente
revisado-por: consultor-rbc-iso17025, tech-lead-saas-regulado, advogado-saas-regulado
bloqueia-fase: Wave A (1ª supervisão CGCRE — laboratório acreditado precisa de RT credenciado por método)
depende-de: ADR-0002 (multi-tenancy + RLS), ADR-0009 (A3 cliente-side Lacuna), ADR-0012 (authz), ADR-0068 (sucessão RT)
---

# ADR-0022 — Gestão do Responsável Técnico do tenant

## Emenda v2 (2026-05-27) — Competência por método específico

> Auditoria 10 lentes pré-Wave A L3#4 detectou que `RTCompetencia` modelava só `grandeza` (massa/comprimento/temperatura/pressão) — NIT-DICLA-021 exige declaração **por método específico** (ex: "Massa **classe E2 OIML R111 método de subdivisão**"). RT "massa balança comum" hoje pode assinar cert RBC de massa padrão E1 sem barreira.
>
> **Decisão v2:** `RTCompetencia` ganha 3 campos novos:
>
> ```
> RTCompetencia(
>   ...
>   grandeza ENUM,               -- preservado v1
>   metodo_id UUID NOT NULL,     -- v2 NOVO — FK → ProcedimentoCalibracao
>   faixa_min DECIMAL NULL,      -- v2 NOVO — faixa inferior (ex: 1 mg)
>   faixa_max DECIMAL NULL,      -- v2 NOVO — faixa superior (ex: 50 kg)
>   ...
> )
> UNIQUE(tenant_id, rt_id, grandeza, metodo_id, faixa_min, faixa_max)
> ```
>
> **Predicate `rt_competencia_cobre` v2:** consulta `(grandeza, metodo_id, faixa)` na ordem — match exato OR match por faixa sobreposta OR fail-closed. Predicate continua paralelo a ADR-0066 (lazy fail-open) até Wave A criar `metrologia/procedimentos-calibracao` e plugar `Atividade.metodo_id` + `Atividade.faixa_medida`.
>
> **Retrofit RTCompetencia existente (Marco 2):** migration adicional. Para registros existentes (vindos de M2), `metodo_id` recebe valor seed `METODO_GENERICO_HISTORICO` com flag `precisa_revisao=true`. Hook bloqueia novo `RTCompetencia` sem `metodo_id`.
>
> **Tarefas Wave A bloqueantes (T-RT-V2-001..006):**
> 1. Migration adicionando 3 colunas + seed METODO_GENERICO_HISTORICO.
> 2. Use case `declarar_competencia_rt(rt_id, grandeza, metodo_id, faixa_min, faixa_max)`.
> 3. Predicate `rt_competencia_cobre` v2.
> 4. Hook `rt-competencia-metodo-obrigatorio-check`.
> 5. Admin Django + endpoint REST.
> 6. 10 testes regressão (match exato/faixa/fail-closed/registros históricos).

## Contexto

## Contexto

A NIT-DICLA-021 (Regulamento da Acreditação RBC) exige que cada
laboratório acreditado tenha um **Responsável Técnico (RT)**
credenciado com:

1. Identificação pessoal e profissional (registro CREA/CRQ/equivalente).
2. **Competência declarada** por grandeza metrológica (massa,
   comprimento, temperatura, pressão, etc.) — carta de competência
   anexada ao dossiê do tenant.
3. **Vigência contínua sem sobreposição temporal** — no momento X só
   pode existir UM RT ativo por grandeza por tenant.
4. **Histórico imutável** — encerramento de vigência (troca de RT,
   afastamento) preservado por 25 anos (ISO 17025 cl. 8.4 + RBC NIT-
   DICLA-021 cl. 4.2).
5. **Notificação ANPD + CGCRE em 30 dias** quando há troca de RT
   (cl. 5.6.1 — laboratório deve manter CGCRE informado).

Marco 2 entrega o **modelo de dados** + **fluxo CRUD** + **predicate
de competência** consumido pelos services US-EQP-002b (aprovação
gestor_qualidade exige RT com competência declarada para a grandeza
do equipamento). Marco 2 NÃO entrega: integração A3 cliente-side via
Lacuna (GATE-EQP-1 Wave A) nem notificação automatizada ANPD/CGCRE
(GATE-EQP-RT-NOTIF Wave A).

## Decisão

Cravar US-EQP-007 (entregue como código em Marco 2 — `src/infrastructure/
responsavel_tecnico/`) com 2 modelos:

### Modelo `ResponsavelTecnicoTenant`

12 campos: identidade pessoal (nome_completo, cpf_hash) + identidade
profissional (formacao_academica, registro_profissional_tipo +
registro_profissional_numero) + vigência (data_inicio_vigencia +
vigente_ate) + encerramento (encerrado_em + encerrado_por +
motivo_encerramento + motivo_detalhe).

Trigger PG `rt_imutavel_pos_insert` bloqueia UPDATE em todos os campos
**exceto** 4 campos de encerramento (transição única ativo→encerrado).
Após `encerrado_em NOT NULL` a linha vira totalmente imutável.

### Modelo `RTCompetencia`

5 campos: `rt_id` (FK), `grandeza` (enum), `carta_competencia_anexo_id`
(referência ao blob da carta), `declarado_em`, `vigente_ate` (NULL =
ativo indefinidamente).

`EXCLUDE USING GIST` (extensão `btree_gist`) cravando
**INV-EQP-RT-001**: sem sobreposição temporal por
`(tenant_id, grandeza, daterange(declarado_em, COALESCE(vigente_ate,
'infinity'), '[)'))`.

### Predicate `decisor_tem_competencia_para_atividade`

Em `predicates.py`: dado (decisor_id, atividade, grandeza, tenant_id),
retorna `True` se o decisor é RT ativo com competência declarada para
a grandeza naquele momento. Consumido pelo service `services_aprovacao`
(US-EQP-002b) quando decisor é `rt_signatario`. Marco 2 entrega
versão simples (existência de competência); Wave A introduz matriz
de competência fina por categoria de atividade.

### Eventos canônicos

4 ações em `acoes_canonicas.ACOES_RT`: `tenant.rt.cadastrado` /
`tenant.rt.encerrado` / `tenant.rt.trocado` (combinação atomic
encerrado+cadastrado) / `tenant.rt.competencia_declarada`. 25a WORM.

Payload sanitizado: `nome_completo_hash`, `cpf_hash`,
`registro_profissional_hash` (HMAC tenant) — texto cru NUNCA vaza.

### Endpoints (DRF)

`POST /api/v1/responsaveis-tecnicos/` (cadastrar),
`POST /{id}/encerrar/`, `POST /{id}/trocar/` (1 transação atômica),
`POST /{id}/competencias/` (declarar). Authz seedada (`tenant.rt.*`):
admin_tenant gerencia; rt_signatario+tecnico leem; gestor_qualidade
fica GATE-EQP-RT-AUTHZ Wave A.

## Consequências

### Positivas
- **Defesa metrológica em supervisão CGCRE**: trilha auditável 25a
  responde "quem era o RT da grandeza X em <data>?" em uma query.
- **INV-EQP-RT-001 cravada como constraint PG**: impossível ter 2
  RTs ativos pra mesma grandeza no mesmo instante (defesa contra
  erro operacional — admin_tenant não pode "esquecer" de encerrar
  o RT anterior).
- **Predicate de competência consumido em authz**: gestor_qualidade
  só pode aprovar mudança que envolva grandeza coberta pelo RT
  ativo. Defesa contra "RT genérico assina tudo".

### Negativas / aceitas
- Marco 2 entrega **stub de matriz por atividade** — predicate só
  checa existência de competência pra grandeza, não tipo de
  atividade (calibração vs ensaio vs verificação). Wave A expande.
- A3 client-side via Lacuna fica em GATE-EQP-1 (Wave A) — Marco 2
  dogfooding não emite cert assinado A3 (uso interno só).
- Notificação ANPD+CGCRE 30d via consumer real fica em
  GATE-EQP-RT-NOTIF (Wave A). Marco 2 publica evento canônico
  `tenant.rt.trocado` em bus_outbox; consumer real Wave A enviará
  comunicação formal.

### Cap de risco
- **Tenant que opera sem RT ativo (não cadastrou ainda)** continua
  podendo cadastrar equipamentos (US-EQP-001) mas NÃO pode aprovar
  versões via gestor_qualidade (US-EQP-002b) porque o predicate
  bloqueia. Documenta o gap operacionalmente em Wave A
  `onboarding-tenant` (ADR-0015).

## Implementação Marco 2 (✅ entregue)

- Módulo `src/infrastructure/responsavel_tecnico/` registrado em
  INSTALLED_APPS (commit `T-EQP-061..065`).
- Migrations `0001_initial` (RLS v2 + `EXCLUDE USING GIST` +
  trigger imutabilidade) + `0002_seed_authz_acoes` (4 ações
  `tenant.rt.*`).
- Services: `cadastrar_rt`, `encerrar_rt`, `trocar_rt`,
  `declarar_competencia` (transação atômica — 3 eventos em
  `trocar_rt`).
- Predicate `decisor_tem_competencia_para_atividade` em
  `predicates.py` (Marco 2: existência de competência por grandeza).
- Endpoints DRF: 4 actions no `ResponsavelTecnicoViewSet`.
- Tests anti-regressão: `tests/regressao/test_inv_eqp_rt_001.py`
  (T-EQP-094 — happy + sobreposição bloqueada + cross-tenant).

## Pendências Wave A rastreadas

| GATE | Item |
|------|------|
| GATE-EQP-1 | A3 cliente-side via Lacuna (assinatura RT em cert) |
| GATE-EQP-RT | Carta de competência declarada do RT humano credenciado (NIT-DICLA-021) — primeiro tenant pago |
| GATE-EQP-RT-AUTHZ | Authz `gestor_qualidade` em ações `tenant.rt.*` |
| GATE-EQP-RT-NOTIF | Consumer real notifica ANPD + CGCRE em 30d (`tenant.rt.trocado`) |

## Alternativas consideradas

1. **RT global por tenant (1 só, todas as grandezas)**: REJEITADA —
   labs reais frequentemente terceirizam grandezas (massa interno +
   pressão externo). Modelo simplificado viraria débito quando o 1º
   tenant pago tiver acreditação multi-grandeza.

2. **RT como `Usuario` com flag `is_rt=True`**: REJEITADA — RT é
   pessoa que pode não usar o sistema (consultor externo). Acoplar
   ao `Usuario` (que tem `email` + login) cria vínculo errado.
   Modelo separado permite cadastrar RT sem login (Wave A: convidar
   RT a criar conta opcionalmente).

3. **Sem `EXCLUDE USING GIST` — validar sobreposição no service**:
   REJEITADA — defesa em profundidade. Validação app-only não
   sobrevive a manutenção direta via app_migrator (bypass do service).

## Referências

- ABNT NBR ISO/IEC 17025:2017 cl. 5.6 (gestão de pessoal técnico)
- RBC NIT-DICLA-021 (Regulamento de Acreditação — cl. 4.2 +
  cl. 5.6.1)
- Spec `docs/faseamento/M2-equipamentos/spec.md` US-EQP-007
- Plan `docs/faseamento/M2-equipamentos/plan.md` P-EQP-R10
- Implementação `src/infrastructure/responsavel_tecnico/`
