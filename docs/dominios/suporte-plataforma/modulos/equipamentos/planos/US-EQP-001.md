---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-001
---

# Plano US-EQP-001 — Cadastrar equipamento com QR Code

> Story em `docs/dominios/suporte-plataforma/modulos/equipamentos/prd.md` §6 (US-EQP-001).
>
> **Estado inicial:** ZERO — módulo `equipamentos` ainda não tem código. Esta US é a fundação do Marco 2.
>
> **Revisão dos 2 subagentes (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 ressalvas tech-lead (2 BLOC, 3 CON, 1 NIT) + 5 ressalvas advogado (1 BLOC). Pareceres em `revisoes/US-EQP-001-tech-lead.md` + `revisoes/US-EQP-001-advogado.md`. Endereçamento abaixo.

## Resumo

Implementar CRUD inicial de equipamento com (a) TAG única por tenant (INV-049), (b) QR Code com hash HMAC-SHA256 + KMS_qr_secret (INV-051), (c) snapshot imutável de `perfil_tenant_no_momento_cadastro` (RBC B4), (d) validação anti-PII em `localizacao_fisica` (INV-EQP-LOC-001), (e) evento `equipamento.cadastrado` em `audit_trail.eventos` com payload sanitizado.

## Sequência de tasks

- **T-EQP-001**: criar app Django `src/infrastructure/equipamentos/` (apps.py, models.py inicial, urls.py).
- **T-EQP-002**: criar `src/domain/suporte_plataforma/equipamentos/__init__.py` + entidade `Equipamento` (dataclass + invariantes domain-level).
- **T-EQP-003**: migration 0001_initial — tabela `equipamento` com UNIQUE `(tenant_id, tag)` (INV-049) + RLS policy `equipamento_tenant_isolation`. Hook `migration-rls-check` + `policy-test-coverage` exigem testes happy+unhappy.
- **T-EQP-004**: migration 0002_perfil_tenant_snapshot — coluna `perfil_tenant_no_momento_cadastro` enum {A,B,C,D} NOT NULL + trigger PG `bloquear_update_perfil_tenant_snapshot` (anti-downgrade — RBC B4).
- **T-EQP-005**: VO `Tag` em `src/domain/suporte_plataforma/equipamentos/value_objects.py` — validação básica (≤30 chars, alfanumérico + hífen).
- **T-EQP-006**: validação anti-PII em `localizacao_fisica` (regex análoga US-CLI-004 R2 — CPF/CNPJ/e-mail/telefone/nomes próprios consecutivos). Reusar `src/domain/shared/pii_guard.py` se já existe; criar se não.
- **T-EQP-007**: criar `src/infrastructure/equipamentos/qr_token.py` — função `gerar_hash_qr(equipamento_id, tenant_id, emitido_em) -> str` usando HMAC-SHA256 com `KMS_qr_secret` lido de `settings.KMS_QR_SECRET` (mock seguro para dev — chave real só em prod via AWS KMS).
- **T-EQP-008**: model `QrCode` + migration 0003_qrcode — UNIQUE `hash` + RLS + trigger `bloquear_update_revogado_em_para_null`.
- **T-EQP-009**: porta domain `CertificadoQueryService` (Protocol) em `src/domain/suporte_plataforma/equipamentos/ports/certificado_query_service.py` + adapter `EmptyCertificadoQueryService` em `src/infrastructure/equipamentos/adapters/empty_certificado_query_service.py` + registro em `settings.PORT_BINDINGS`.
- **T-EQP-010**: porta `OSQueryService` + adapter `EmptyOSQueryService` (mesma estrutura T-EQP-009).
- **T-EQP-011**: use case `CadastrarEquipamento` em `src/application/suporte_plataforma/equipamentos/cadastrar_equipamento.py` — validação anti-PII + unicidade TAG + perfil snapshot + gerar QR + gravar audit `equipamento.cadastrado` com payload `{equipamento_id, tag, cliente_id_original_hash, perfil_tenant_no_momento_cadastro}`.
- **T-EQP-012**: `EquipamentoSerializer` + `EquipamentoViewSet` (POST/GET-list/GET-detail) com authz `equipamento.criar`/`equipamento.ler`/`equipamento.listar`.
- **T-EQP-013**: migration 0004_seed_authz_equipamento — registrar actions `equipamento.criar`, `equipamento.ler`, `equipamento.listar`, `equipamento.imprimir_etiqueta` + atribuir aos perfis (metrologista, almoxarife, atendente, admin).
- **T-EQP-014**: endpoint `GET /v1/equipamentos/{id}/qr` — gera PDF da etiqueta (Reportlab ou WeasyPrint — escolher Wave A) com QR + TAG + NS + logo tenant.
- **T-EQP-015**: testes:
  - `test_cadastrar_equipamento_happy_path`
  - `test_tag_duplicada_mesmo_tenant_409` (INV-049)
  - `test_tag_duplicada_cross_tenant_nao_vaza` (INV-049 + INV-TENANT-001)
  - `test_qr_hash_hmac_deterministico_e_opaco` (INV-051)
  - `test_qr_hash_min_22_chars_e_base64url` (INV-051 — ≥128 bits entropia)
  - `test_localizacao_fisica_com_cpf_rejeita_400` (INV-EQP-LOC-001)
  - `test_localizacao_fisica_com_nome_proprio_rejeita_400` (INV-EQP-LOC-001)
  - `test_perfil_tenant_no_cadastro_e_imutavel` (RBC B4 — trigger PG rejeita UPDATE)
  - `test_cliente_de_outro_tenant_retorna_422_sem_oracle` (INV-TENANT-001)
  - `test_evento_equipamento_cadastrado_grava_audit_sem_pii` (payload sanitizado)
  - `test_authz_atendente_pode_criar` / `test_authz_tecnico_campo_nao_pode_criar`
  - `test_pdf_etiqueta_contem_qr_tag_ns_logo`

## Modelos/tabelas envolvidos

- **Novo:** `equipamento` (campos do modelo-de-dominio v2 §Equipamento + RLS + UNIQUE)
- **Novo:** `qrcode` (HMAC hash + revogado_em)
- **Já existe (F-A):** `auditoria.eventos` — recebe `equipamento.cadastrado`
- **Já existe (F-B):** `authz.acao` + `authz.papel_acao` — recebe seeds das actions novas

## Endpoints envolvidos

- `POST /v1/equipamentos`
- `GET /v1/equipamentos/{id}` (subset — ficha 360° completa fica em US-EQP-003)
- `GET /v1/equipamentos?busca=&status=&cliente_id=` (subset — escopo por papel fica em US-EQP-003)
- `GET /v1/equipamentos/{id}/qr` (PDF etiqueta)

## Hooks ativados

- `tenant-id-validator` (INSERT com tenant_id obrigatório)
- `authz-check` (view com `authz_action`)
- `migration-rls-check` (cria policy em 0001)
- `policy-test-coverage` (exige `# tests-coverage: tests/equipamentos/test_rls_isolation.py::test_happy,test_unhappy`)
- `anti-mascaramento` (todos testes sem skip injustificado)
- `INV-checker` (TST-004 — testes que citam INV-049/051/EQP-LOC-001)
- `audit-pii-salt-check` (audit hash de cliente sempre salgado por tenant)
- Novo: `equipamento-imutabilidade-check.sh` (a criar em T-EQP-016 — bloqueia migration que altere campos imutáveis sem trigger PG correspondente)

## Testes obrigatórios

Ver T-EQP-015. Cobertura mínima 85% no módulo equipamentos após esta US. Total esperado: ~25 testes.

## Riscos / pontos sensíveis

1. **KMS_qr_secret em dev:** AWS KMS real não está disponível em dev. Solução: `settings.KMS_QR_SECRET = "dev-only-not-secret-rotate-in-prod"` lido de env var + warning em log se rodando com valor default em ambiente != dev. Hook `qr-hmac-check.sh` (a criar) bloqueia commit se string default for vista em `settings.production`.
2. **Trigger PG anti-mutation:** a migration 0001 já cria trigger ou criamos em 0002? Decisão: trigger só na 0002 — `perfil_tenant_no_momento_cadastro` é a coluna que ele protege. Imutabilidade de TAG/NS/fabricante depende da existência de Certificado (módulo certificados não existe ainda) — fica em US-EQP-002 (que toca isso explicitamente via porta stub).
3. **PDF generator:** Reportlab é mais leve; WeasyPrint produz HTML→PDF (mais fácil de evoluir). Decisão deferida pra revisão do tech-lead.
4. **Limite de tamanho TAG:** 30 chars suficiente? Em perfil A com prefixo CGCRE, pode ser apertado (`BLS-2026-000123` = 16 chars OK). Manter 30 hoje.
5. **Cadastro provisório (US-EQP-006):** US-EQP-001 entrega cadastro completo. Cadastro provisório (cliente trouxe equip novo sem cadastro) é uma variação do mesmo endpoint com `cliente_id` nullable + flag `cadastro_provisorio=true` que outras US (002/006) completam. Decisão deferida.

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar PDF generator + trigger PG + estrutura de portas stub.
- `advogado-saas-regulado`: validar texto de erro PT na rejeição anti-PII de localizacao_fisica + payload do audit (sanitização).
- `corretora-seguros-saas`: validar que KMS_qr_secret em dev não vaza em produção; suite de testes anti-violação INV-051 atende ADR-0019 Pilar 2.
- `consultor-rbc-iso17025`: confirmar que `perfil_tenant_no_momento_cadastro` snapshot é suficiente (ou exige eventos adicionais para audit CGCRE).

## Non-goals deste plano

- NÃO implementar versionamento pós-cert (US-EQP-002).
- NÃO implementar ficha 360° + scan QR dual-mode (US-EQP-003).
- NÃO implementar transferência (US-EQP-004).
- NÃO implementar sucatar com notificação (US-EQP-005).
- NÃO implementar `EquipamentoRecebimento` + máquina de estados (US-EQP-006).
- NÃO criar UI HTMX (Wave A entrega backend + serializers + testes; UI HTMX entra em iteração posterior do mesmo Marco).
- NÃO integrar com AWS KMS real (mock em dev; configuração real fica em runbook de deploy).
- **NÃO implementar cadastro provisório** (decisão Roldão Caminho A): `Equipamento.cliente_atual_id` NASCE NOT NULL. Recebimento provisório vira tabela separada `RecebimentoProvisorio` em US-EQP-006 (tech-lead US-006 R1).
- NÃO entregar aceite LGPD adicional no cadastro de equipamento — equipamento é bem móvel (CC art. 82), não titular (LGPD art. 1º). Aceite foi colhido em US-CLI-001 (advogado US-EQP-001 R4).

---

## Endereçamento da revisão (11 ressalvas — tech-lead 6 + advogado 5)

### Tech-lead

- **TL1 (BLOQUEADOR — `KMS_qr_secret`):** ler de `env("KMS_QR_SECRET")` em `config/settings/base.py`; default só em `dev.py`/`test.py`; `prod.py` SEM default (falha duro). Hook novo `qr-hmac-check.sh` com 4 regras: (a) HMAC literal proibido fora de `qr_token.py`, (b) string `dev-only-not-secret-rotate-in-prod` em `prod.py` BLOQUEIA, (c) `hashlib.sha256` puro em path de QR BLOQUEIA (forçar HMAC com secret), (d) ausência de `tenant_id` no payload do hash BLOQUEIA. +4 casos em `_test-runner.sh`.
- **TL2 (BLOQUEADOR — cadastro provisório non-goal):** `cliente_atual_id` NOT NULL nascendo na migration 0001. Provisório vai pra `RecebimentoProvisorio` em US-EQP-006 (decisão Roldão Caminho A).
- **TL3 (CONCERN ALTA — naming portas):** `PORT_BINDINGS` em `config/settings/base.py` + função `resolve_port(protocol)` em `src/infrastructure/shared/port_registry.py`. Naming `Empty<NomePort>Adapter`. Hook `port-binding-validator.sh` barra `Empty*` em prod (T-EQP-027 — US-EQP-003).
- **TL4 (CONCERN ALTA — trigger PG):** sintaxe completa `equipamento_anti_update_perfil_snapshot` usando `IS DISTINCT FROM` + `ERRCODE = 'check_violation'`. Comentário `# trigger-coverage:` no commit. Estender `audit-immutability-check.sh` pra barrar `DROP TRIGGER equipamento_anti_*`.
- **TL5 (CONCERN MÉDIA — PDF):** adotar **WeasyPrint** (reúso pro certificado ISO 17025 da Wave A+). Dockerfile precisa `libpango`. Teste de regressão por hash SHA-256 do PDF.
- **TL6 (NIT):** action `equipamento.imprimir_etiqueta` órfã — vincular ao endpoint `GET /qr` no seed authz ou remover (decisão: manter — endpoint existe em api.md).

### Advogado

- **R1 (CONCERN — texto PT-BR anti-PII):** texto em fixture com 4 regras invioláveis (não ecoar input, não listar categoria que disparou, não culpar atendente, exemplos neutros). Espelho exato US-CLI-004 R2.
- **R2 (BLOQUEADOR — payload audit sanitizado):** `equipamento.cadastrado` payload definitivo: `tag_hash`, `numero_serie_hash`, `localizacao_fisica_hash` (todos salgados por tenant); `cliente_id_original_hash` apenas (sem UUID); `fabricante`/`modelo` em claro (catálogo público); `perfil_tenant_no_momento_cadastro`/`ip_hash`/`user_agent_hash` em claro. Estender hook `audit-pii-salt-check`. Nova T-EQP-011a regressão anti-vazamento.
- **R3 (CONCERN — base legal):** seção "Base legal" do plano cita art. 7º II + art. 16 I (ISO 17025 cl. 8.4 prevalece sobre art. 18 VI) para `cliente_id_original_hash`.
- **R4 (NIT):** Non-goal jurídico explícito: SEM aceite LGPD no cadastro de equipamento (bem móvel, não titular).
- **R5 (CONCERN — 409 anti-oracle):** 409 não ecoa TAG submetida; não sugere próxima livre; não revela cliente; audit grava `motivo_categoria=tag_duplicada` + `tag_hash`. **Cross-tenant retorna 201** (não 409 — anti-oracle).

## Sequência revisada de tasks (15 originais + 5 novas)

- **T-EQP-001**: app Django `src/infrastructure/equipamentos/`
- **T-EQP-002**: entidade domain
- **T-EQP-003**: migration 0001 — UNIQUE `(tenant_id, tag)` + RLS
- **T-EQP-004**: migration 0002 — `perfil_tenant_no_momento_cadastro` + trigger TL4
- **T-EQP-005**: VO `Tag`
- **T-EQP-006**: regex anti-PII em `localizacao_fisica` (reusar `src/domain/shared/pii_guard.py` Marco 1)
- **T-EQP-007**: `qr_token.py` (HMAC TL1)
- **T-EQP-007a (NOVA)**: hook `qr-hmac-check.sh` + 4 casos `_test-runner.sh` (TL1)
- **T-EQP-008**: model `QrCode` + migration 0003
- **T-EQP-009**: porta `CertificadoQueryService` + `EmptyCertificadoQueryServiceAdapter` (TL3 naming)
- **T-EQP-010**: porta `OSQueryService` + `EmptyOSQueryServiceAdapter`
- **T-EQP-010a (NOVA)**: `PORT_BINDINGS` em `base.py` + `resolve_port()` em `src/infrastructure/shared/port_registry.py` (TL3)
- **T-EQP-011**: use case `CadastrarEquipamento` (R2 payload sanitizado + R5 anti-oracle)
- **T-EQP-011a (NOVA)**: teste regressão `test_audit_cadastrado_payload_sanitizado` (R2 + estender `audit-pii-salt-check`)
- **T-EQP-012**: serializer + viewset
- **T-EQP-013**: migration seed_authz
- **T-EQP-014**: endpoint PDF QR (WeasyPrint TL5 + libpango Dockerfile)
- **T-EQP-014a (NOVA)**: teste hash SHA-256 PDF (TL5)
- **T-EQP-015**: testes (acrescentar `test_cross_tenant_mesma_tag_retorna_201_ambas` R5 + `test_kms_qr_secret_dev_default_warning` TL1 + `test_payload_audit_so_hashes_e_publicos` R2)
