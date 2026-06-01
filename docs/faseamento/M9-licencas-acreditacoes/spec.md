---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: draft
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M9-licencas-acreditacoes
tipo: spec-faseamento
relacionados:
  - docs/faseamento/M9-licencas-acreditacoes/T-LIC-000-investigacao.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/faseamento/ordem-dependencia-bloco-metrologia.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-3-padroes.md
  - docs/adr/0072-path-infra-metrologia-aninhado.md
---

# Spec de faseamento — M9 `metrologia/licencas-acreditacoes` (núcleo regulatório)

> **Escopo:** núcleo lógico/regulatório da gestão de documentos da empresa — cadastro
> vivo de `Licenca`/`DocumentoRegulatorio` (acreditação RBC/CGCRE, licenças, ART/RRT,
> certidões) com vigência canônica, status calculado, alertas de vencimento, histórico
> versionado WORM, anexo probatório obrigatório, **bloqueio de operação por documento
> vencido**, e **sincronização da vigência da acreditação CGCRE → `Tenant.acreditacao_
> vigencia_fim`** (que o M8 já lê). PDF consolidado real, e-mail real, A3/PAdES e fluxos
> CGCRE complexos (ampliação/NC/revisão) ficam DIFERIDOS — espelha o recorte M5-M8.
> Path aninhado ADR-0072 `src/{domain,infrastructure}/metrologia/licencas_acreditacoes/`.
> Base: `T-LIC-000-investigacao.md` (dossiê 5 leitores, convergência forte).

## 1. Por que agora (ordem de dependência)

#5 e ÚLTIMO do bloco metrologia (`ordem-dependencia-bloco-metrologia.md`). É o
**pré-requisito de toda emissão** que faltava: o M8 `certificados` deixou
`acreditacao_vigente_para_rbc` em **fail-open lazy** enquanto `Tenant.acreditacao_
vigencia_fim` for `None` (GATE-CER-CGCRE-VIG-DATA-POPULAR). Este módulo é a **fonte rica**
que popula esse campo — fechando o gate sem retrabalho.

## 2. Seam pronto (NÃO reconstruir — T-LIC-000 §2)

| Peça | Onde | Uso no M9 |
|------|------|-----------|
| `aplicar_evento_cgcre(...)` SECURITY DEFINER | `tenant/migrations/0008` | cadastro/promoção CGCRE CHAMA esta função (única forma de mutar `Tenant.perfil`/acreditacao) |
| `Tenant.acreditacao_{cgcre_numero,vigencia_inicio,vigencia_fim,suspensa_em,suspensa_ate,ilac_mra}` | `tenant/models.py:80-135` | CACHE desnormalizado da acreditação; M9 sincroniza via `aplicar_evento_cgcre` |
| Job `verificar_vigencia_acreditacao_perfil_a` | `application/tenant/jobs/` | US-LIC-002-4 (refinar p/ consultar a entidade `Licenca`) |
| Predicates `tenant_perfil_e` / `acreditacao_cgcre_aplicavel_por_perfil` | `authz/perfil_tenant_helper.py:106` | AC-LIC-001-3/3b (defesa L6) — chamar direto no use case |
| `acreditacao_vigente_para_rbc` (consumidor M8) | `domain/metrologia/certificados/transicoes.py:109` | M9 popula o dado; sem retrofit no M8 nesta frente |
| VOs `JanelaVigencia`/`Grandeza`/`FaixaMedicao` + WORM/RLS/hash-chain/path aninhado | M5-M8 | reusar molde — zero padrão novo |

## 3. Escopo — US cobertas (núcleo)

| US do PRD | O que entra AGORA | O que difere |
|-----------|-------------------|--------------|
| **US-LIC-001** cadastrar documento regulatório | entidade `Licenca` + `RevisaoDocumento` (v1); perfil-aware (`tenant_perfil_e(['A','B','C'])` para CGCRE — defesa L6); anexo sha256 obrigatório (INV-046); status calculado (vigente/vence-em/vencido/em-renovação); promoção perfil A via `aplicar_evento_cgcre` (AC-LIC-001-4); eventos WORM | integração API CGCRE (V2) |
| **US-LIC-002** alertas de vencimento | job diário (D-90/60/30/15/7) cria `AlertaVencimento` + evento/dashboard; refina job perfil A existente; renovação reagenda | envio de e-mail real (ADR-0060 — Wave B); push app |
| **US-LIC-003** bloqueio por doc vencido | `BloqueioOperacional` (INV-032 fail-closed perfil A) + **query service `vigente_para_rbc(tenant, data)`** (porta que o M8 consome) + modo emergencial (INV-033 — registra justificativa ≥100ch + `a3_id`) | assinatura A3 real do modo emergencial (Wave B) |
| **US-LIC-004** histórico versionado | `RevisaoDocumento` append-only imutável (WORM) + listagem | — |
| **US-LIC-005** ART/RRT do RT | tipo especial + vínculo opcional `ResponsavelTecnico` + bloqueio assinatura se vencida | integração CREA/CRQ (V2) |
| **(sincronização)** vigência → Tenant | `Licenca`(CGCRE).vigencia_fim → `Tenant.acreditacao_vigencia_fim` via `aplicar_evento_cgcre` | — (fecha GATE-CER-CGCRE-VIG-DATA-POPULAR) |

## 4. Non-goals desta frente (diferidos — declarados; espelha M8)

US-LIC-006/008/009 (cadastro físico A3 — já delegado a `seguranca/certificados-digitais`
ADR-0048; M9 mantém só referência cruzada FK + alerta) · US-LIC-007/013 (PDF/ZIP
consolidado real — núcleo entrega export estruturado) · US-LIC-010 (ampliação escopo CGCRE)
· US-LIC-011 (responder NC CGCRE com PAdES-LTV) · US-LIC-012 (revisão quinquenal) — todos
ADR-0014 fluxos 7/8/9, **Wave B** · e-mail real (ADR-0060) · A3/carimbo real (ADR-0009/0047)
· integração API CGCRE / auto-renovação (V2) · dossiê de validação cl. 7.11 com parecer RBC
credenciado (pré-produção — `project_sem_contratacoes_externas_ate_producao`). Todos
rastreados como GATE-LIC-* Wave A/B.

## 5. Invariantes (a cravar em REGRAS — família INV-LIC-*)

Núcleo (numeração definitiva no `/plan`):
- **INV-LIC-PERFIL-001** — cadastro de `tipo=acreditacao_cgcre` exige `tenant_perfil_e(['A','B','C'])` server-side; perfil D → 403 (defesa anti-fraude L6 — já citado no PRD).
- **INV-LIC-ANEXO-001** — todo documento regulatório exige anexo probatório (sha256 server-side) no cadastro → senão 422 `ANEXO_OBRIGATORIO` (formaliza INV-046 para a entidade).
- **INV-LIC-VIG-SYNC-001** — vigência de acreditação CGCRE em `Tenant.acreditacao_vigencia_fim` é mantida **exclusivamente** via `aplicar_evento_cgcre` (nunca UPDATE direto — hook `tenant-perfil-imutavel-check`); `Licenca` é a fonte de verdade (ADR-0079 a propor).
- **INV-LIC-WORM-001** — `RevisaoDocumento` e `EventoEmergencial` são append-only (WORM Padrão B); correção só por nova revisão.
- **INV-LIC-BLOQUEIO-001** — documento `bloqueante=True` vencido impede operação dependente (INV-032); fail-closed perfil A; modo emergencial (INV-033) exige justificativa ≥100ch + `a3_id` + expira ≤7d.
- **Reusadas:** INV-032, INV-033, INV-046, INV-INT-001/003/004, INV-VIG-001..004, INV-SOFT-001/002, INV-TENANT-001..004, INV-TENANT-PERFIL-001/003/004, INV-ANON-001..004 (PII de RT/titular), INV-HMAC-001..005.

## 6. Fatias propostas (refinar no /plan — ordem por dependência)

- **Fatia 1a** — domínio puro: enums (`TipoDocumentoRegulatorio`, `MotivoRevisao`, estados) + entidades (`Licenca`/`DocumentoRegulatorio`, `RevisaoDocumento`, `AlertaVencimento`, `BloqueioOperacional`, `EventoEmergencial`) + transições WORM + validações (INV-046/032/033 + status calculado + tipo×perfil) + repository Protocols. Zero Django.
- **Fatia 1b** — schema: migrations RLS v2 + WORM Padrão B (triggers anti-mutação) + grants + seed authz + UNIQUE idempotência alertas + drill `validar_licencas_acreditacoes` + mappers/repositories aninhados.
- **Fatia 2** — use cases + REST: `cadastrar_documento_regulatorio` (perfil-aware + anexo) + `renovar_documento` + `promover_perfil_a` (invoca `aplicar_evento_cgcre`) + `acionar_modo_emergencial` + ViewSet (CRUD + ações) + idempotência (IDEMP-001) + eventos WORM.
- **Fatia 3** — **fecha o ciclo com o M8**: sincronização `Licenca`(CGCRE)→`Tenant.acreditacao_vigencia_fim` + query service `vigente_para_rbc(tenant, data)` fail-closed (porta M8) + job de alertas (D-90..D-7) + refino do job perfil A. **Fecha GATE-CER-CGCRE-VIG-DATA-POPULAR.**
- **Fatia 4** — histórico versionado (US-LIC-004) + ART/RRT (US-LIC-005) + **P7** (família INV-LIC-* em REGRAS + `TestINV_LIC_*` + hooks: `lic-anexo-obrigatorio-check`, `lic-perfil-cgcre-check`, `lic-emergencial-a3-check`).
- **P8/P9** — matriz-reconciliacao (molde M7) + emenda PRD + URS (ADR-0025 v2) + auditores roteados (INV-RITUAL-003).

## 7. Decisões / questões para os revisores (P2)

- **ADR-0079 (propor):** `Licenca` (acreditação CGCRE) é **fonte de verdade rica**;
  `Tenant.acreditacao_vigencia_fim` é **cache desnormalizado** mantido SÓ via
  `aplicar_evento_cgcre`. Direção de sincronização unidirecional. **Revisão `tech-lead`**
  (decisão de arquitetura, análoga a ADR-0078). Sem dupla fonte de verdade.
- **Reconciliar semântica de bloqueio com o M8 (`consultor-rbc`):** o M8 (INV-CER-CGCRE-VIG-001)
  **rebaixa** RBC→não-RBC no ponto de emissão (não hard-block). O US-LIC-003 fala em
  **bloqueio hard** (409) do documento bloqueante. Definir a fronteira: o documento bloqueante
  vencido bloqueia a operação de emissão? Ou o M8 já trata via rebaixamento e o US-LIC-003 é a
  trava "antes de chegar ao M8"? (provável: US-LIC-003 é a porta `vigente_para_rbc` que o M8
  consome; o "409 hard" é configurável por perfil — A bloqueia, B/C/D rebaixa).
- **Modo emergencial (`consultor-rbc` + `tech-lead`):** registrar `a3_id` + justificativa
  ≥100ch + expira ≤7d nesta frente; assinatura A3 REAL diferida (Wave B) — aceitar o registro
  sem validação criptográfica agora (fail-open lazy declarado, como o A3 dos demais módulos)?
- **Retenção perfil-aware** (matriz-feature-perfil): 25a A/B/C, 5a D — usar
  `ReferenciaPIIAnonimizavel` para PII de RT/titular de ART/RRT.

**Próximo:** revisões `consultor-rbc` + `tech-lead` (P2) → incorporar → `plan` (P3, crava
ADR-0079 + numera INV-LIC + tasks) → `/tasks` → implement Fatia 1a.
