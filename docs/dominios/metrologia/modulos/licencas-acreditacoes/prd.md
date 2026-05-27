---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: licencas-acreditacoes
dominio: metrologia
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - docs/dominios/seguranca/modulos/certificados-digitais/prd.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0014-transicoes-regulatorias.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0046-ocsp-crl-revogacao-online.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0048-a3-ecpf-rt-cadastro.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
historico:
  - 2026-05-23 — versão draft com US-LIC-001..013 + ADR-0014 (transições regulatórias) + ADR-0048 (cadastro A3 segregado).
  - 2026-05-27 — Onda PRE-A.3 BATCH B1 saneamento perfil ADR-0067 (AC-LIC-001-3 perfil-aware fecha FAIL L6 + matriz perfil + AC binário GIVEN-WHEN-THEN + ADR-0025 v2 planejamento URS/IQ/OQ/PQ + status promovido para stable).
---

# PRD — Módulo Licenças, Acreditações e Autorizações da Empresa

> Gestão centralizada dos documentos regulatórios da empresa prestadora: licenças, acreditações (RBC/CGCRE), certificados digitais, alvarás, ART/RRT, certidões e autorizações legais. Crítico em ambiente regulado.

---

## 1. O que este módulo é

Cadastro vivo de TODOS os documentos legais e regulatórios que autorizam a empresa a operar: acreditação RBC/CGCRE (ISO 17025), licenças sanitárias/ambientais, alvarás, certidões negativas, ART/RRT do responsável técnico, certificados digitais A1/A3 da empresa, autorizações INMETRO/ANVISA, contratos de adesão regulamentares. Para cada documento, controla validade, alertas de vencimento, histórico de renovação e — quando a regra de negócio exige — bloqueia operações dependentes se o documento estiver vencido.

## 2. Por que este módulo existe (problema a resolver)

Empresa que opera sem documento válido sofre multa, suspensão da acreditação e perde contratos. Hoje (Balanças Solution) o controle é planilha + memória do responsável — risco real de descobrir o vencimento depois da auditoria. Em laboratório RBC, perder a acreditação inviabiliza o negócio (CGCRE 8.4 + NIT-DICLA exigem cadeia documental válida).

## 3. Personas

**Persona dominante:** P-MET-01 (responsável administrativo da empresa — gestor de documentação regulatória; também P-FIN-02 — dono, em laboratórios pequenos). Para acreditação RBC entra P-MET-02 (RT signatário). Detalhe em `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

## 3.1 Perfil regulatório (ADR-0067 — CRÍTICO)

> **Matriz feature × perfil canônica:** `docs/conformidade/comum/matriz-feature-perfil.md`.
>
> **Atenção L6:** versão anterior do AC-LIC-001-3 marcava cadastro CGCRE bloqueante sem checar `Tenant.perfil_regulatorio` — perfil D (comercial puro) podia cadastrar acreditação CGCRE e burlar matriz. Corrigido 2026-05-27 com predicate `tenant_perfil_e(['A','B','C'])` como pré-condição.

Predicates canônicos consumidos por este módulo (`src/infrastructure/authz/predicates.py`):

- **`tenant_perfil_e(perfis_aceitos)`** — fail-closed timeout 50ms. Lê `Tenant.perfil_regulatorio` via ContextVar `perfil_tenant_context`.
- **`acreditacao_cgcre_aplicavel_por_perfil(tenant_id) -> bool`** — retorna `True` somente para perfil A. Consumido por job `verificar_vigencia_acreditacao_perfil_a` (Sprint 3 SAN-PERFIL-TENANT — mensal).

| Feature do módulo | Perfil A — RBC acreditado | Perfil B — Rastreável | Perfil C — Em preparação | Perfil D — Comercial puro |
|---|---|---|---|---|
| **US-LIC-001** cadastrar acreditação CGCRE com flag bloqueante | ✅ OBRIGATÓRIO + escopo CGCRE preenchido | ⚪ OPCIONAL (rastreabilidade simples) | ✅ OBRIGATÓRIO em modo preparatório (gate trilha D→A) | ❌ DESABILITADO (predicate `tenant_perfil_e(['A','B','C'])` rejeita) |
| **US-LIC-002** alertas vencimento 90/60/30/15/7d | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL (licenças sanitárias/ambientais comuns; sem CGCRE) |
| **US-LIC-003** bloqueio operação por doc vencido | ✅ OBRIGATÓRIO (acreditação CGCRE bloqueia emissão RBC) | ⚪ OPCIONAL (sem CGCRE) | ✅ OBRIGATÓRIO (ART/RRT do RT) | ⚪ OPCIONAL |
| **US-LIC-010** ampliação de escopo CGCRE | ✅ OBRIGATÓRIO disponível | ❌ DESABILITADO | ⚪ Wave B (caminho trilha D→A) | ❌ DESABILITADO |
| **US-LIC-011** responder NC CGCRE | ✅ OBRIGATÓRIO (≤30d) | ❌ DESABILITADO | ⚪ OPCIONAL (supervisão pré-A) | ❌ DESABILITADO |
| **US-LIC-012** revisão CGCRE quinquenal | ✅ OBRIGATÓRIO | ❌ DESABILITADO | ❌ DESABILITADO | ❌ DESABILITADO |
| **US-LIC-013** dossiê pré-auditoria CGCRE | ✅ OBRIGATÓRIO | ❌ DESABILITADO | ⚪ OPCIONAL (preparação) | ❌ DESABILITADO |
| **Job mensal `verificar_vigencia_acreditacao_perfil_a`** (Sprint 3) | ✅ OBRIGATÓRIO (alerta 60d antes) | ⚪ N/A | ⚪ N/A | ⚪ N/A |
| **Retenção (matriz-feature-perfil §retenção)** | 25a (ISO 8.4 obrigação legal) | 25a recomendado | 25a | 5a (Receita) + anonimização agressiva |

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de licenças, acreditações, alvarás, autorizações, certidões, ART/RRT, certificados digitais da empresa.
- Tipos categorizados (regulatória / fiscal / sanitária / metrológica / segurança do trabalho / digital).
- Vínculo opcional com responsável técnico (cita módulo Responsável Técnico).
- Validade com data início + data fim + status calculado (vigente / vence em N dias / vencido / em renovação).
- Alertas configuráveis (90, 60, 30, 15, 7 dias antes do vencimento) por canal (e-mail, dashboard, app).
- Histórico de renovação (versionamento — cada renovação é uma nova revisão).
- Anexos PDF/imagem do documento original.
- Bloqueio operacional condicional: marcar documento como "bloqueante" → quando vencer, opera trava configurada (ex: bloquear emissão de certificado RBC se acreditação CGCRE vencida).
- Trilha de auditoria imutável de alterações (WORM).
- Relatório consolidado para auditoria externa (CGCRE, fisco, ANVISA).

## 5. Não-objetivos (Wave A — explícitos)

- NÃO emite os documentos regulatórios (isso é processo externo no órgão competente — CGCRE, ANVISA, CREA, CRQ).
- NÃO gerencia documentos de CLIENTES (isso é módulo CRM/clientes).
- NÃO gerencia licenças de SOFTWARE (chaves de produto, SaaS — isso é módulo TI/infra).
- NÃO substitui o processo legal de renovação — apenas alerta e bloqueia.
- NÃO armazena certificado digital A3 (token físico fica com o titular; aqui só registra metadados + validade — cadastro físico migrou para `seguranca/certificados-digitais` ADR-0048).
- NÃO promove perfil regulatório do tenant automaticamente — promoção exige A3 + admin Aferê + PDF CGCRE (ADR-0067 + função SECURITY DEFINER `aplicar_evento_cgcre`).
- **Integração API com CGCRE** — V2 (sem API pública estável hoje).
- **Auto-renovação via portal do órgão** — V2.

## 5.1 Validação software (ADR-0025 v2 — planejamento Wave A)

ADR-0025 v2 estende validação ISO 17025 cl. 7.11 para módulos não-laboratoriais que afetam decisão regulatória. Para `licencas-acreditacoes` em Wave A devem ser planejados:

- **URS (User Requirements Specification):** documento `docs/dominios/metrologia/modulos/licencas-acreditacoes/urs.md` (a criar) — vigência + bloqueio + notificação D-30/D-15/D-0 + matriz perfil.
- **IQ (Installation Qualification):** automatizado via teste de smoke + migration drill `validar_licencas_acreditacoes`.
- **OQ (Operational Qualification):** testes regressão `tests/test_licencas_us_*.py` cobrindo todos os AC binários (perfil A/B/C/D) + drill UNHAPPY (perfil D tenta cadastrar CGCRE → 403).
- **PQ (Performance Qualification):** smoke periódico em produção pós-cutover (Wave A — `GATE-LIC-PQ`).

Matriz §3.1 — perfil A obrigatório URS+IQ+OQ+PQ; B opcional; C obrigatório parcial (URS+OQ — gate trilha D→A); D desabilitado.

## 6. User Stories

### US-LIC-001: Cadastrar licença/documento regulatório

**Como** responsável administrativo, **quero** cadastrar uma licença da empresa com tipo, número, órgão emissor, data emissão, data validade e anexo PDF, **para** ter controle centralizado dos documentos regulatórios.

**Critérios de aceite:**
- **AC-LIC-001-1**: GIVEN usuário admin autenticado no tenant AND `Tenant.perfil_regulatorio` resolvido via ContextVar, WHEN cadastra licença via POST `/api/v1/licencas` com campos obrigatórios (tipo, número, órgão emissor, data emissão, data validade, anexo), THEN sistema valida tipo × perfil (matriz §3.1), persiste `Licenca{licenca_id, tipo, numero, orgao_emissor, vigencia_inicio, vigencia_fim, status_calculado, proximo_alerta_em, perfil_no_evento}` AND publica `Licencas.LicencaCadastrada{licenca_id, tipo, perfil_no_evento}`.
- **AC-LIC-001-2**: GIVEN documento sem anexo PDF/imagem, WHEN tenta salvar, THEN sistema bloqueia com 422 `{erro: "ANEXO_OBRIGATORIO", detalhe: "evidência probatória obrigatória para auditoria"}` (`INV-046`).
- **AC-LIC-001-3 (perfil-aware — corrige FAIL L6 SAN-PERFIL-TENANT — ADR-0067)**: GIVEN admin tenta cadastrar `tipo="acreditacao_cgcre"` AND `Tenant.perfil_regulatorio ∈ {A,B,C}` (B/C aceitos pois B pode evoluir para A e C está em preparação — gate trilha D→A), WHEN POST `/api/v1/licencas`, THEN predicate `tenant_perfil_e(['A','B','C'])` aceita; sistema exige campos adicionais `{escopo_acreditacao, numero_cgcre, ilac_mra_aderido_bool}`, marca `bloqueante_para_emissao_rbc=True` por padrão (apenas perfil A), persiste, publica `Licencas.AcreditacaoCGCRECadastrada{perfil_no_evento, escopo}`.
- **AC-LIC-001-3b (perfil D rejeitado)**: GIVEN admin tenant `perfil=D` tenta cadastrar `tipo="acreditacao_cgcre"`, WHEN POST, THEN predicate `tenant_perfil_e(['A','B','C'])` rejeita com 403 `{erro: "ACREDITACAO_CGCRE_EXIGE_PERFIL_ABC", perfil_atual: "D", alternativa: "promova_para_C_via_admin_afere"}` AND publica `Licencas.AcreditacaoCGCRECadastroBloqueado{tenant_id, perfil}` (defesa anti-fraude documental L6 — perfil D não pode burlar matriz cadastrando CGCRE).
- **AC-LIC-001-4 (perfil A — promoção obrigatória sincroniza Tenant)**: GIVEN admin Aferê cadastra acreditação CGCRE como bloqueante AND tenant `perfil_regulatorio=B|C`, WHEN POST com flag `promove_para_A=True` + A3 admin + PDF CGCRE, THEN sistema dispara `aplicar_evento_cgcre(tenant_id, "PROMOCAO_REGULATORIA", perfil_novo='A', ...)` (função SECURITY DEFINER Sprint 1 SAN-PERFIL-TENANT) AND atualiza `Tenant.perfil_regulatorio = 'A'` + `Tenant.acreditacao_cgcre_numero` + `Tenant.acreditacao_vigencia_inicio/fim` AND publica `Tenant.PerfilPromovido{tenant_id, anterior, novo, auditor_cgcre}`.

**Não-objetivos desta US:** integração com órgão emissor (API CGCRE).

**Invariantes:** `INV-046` (anexo de evidência obrigatório), `INV-001` (trilha imutável WORM), `INV-TENANT-001`, **`INV-LIC-PERFIL-001`** (novo Onda PRE-A.3: cadastro de acreditação CGCRE exige `tenant_perfil_e(['A','B','C'])`; perfil D rejeitado).

**Dependências:** Bloqueado por: ADR-0002 (multi-tenancy), ADR-0067 (perfil tenant). Predicate `tenant_perfil_e` (Sprint 2 SAN-PERFIL-TENANT).

---

### US-LIC-002: Alertar antes do vencimento

**Como** responsável administrativo, **quero** receber alertas em 90/60/30/15/7 dias antes do vencimento, **para** iniciar a renovação a tempo.

**Critérios de aceite:**
- **AC-LIC-002-1**: GIVEN documento com `vigencia_fim = D`, WHEN job diário `verificar_alertas_licencas` (07:00 BRT) detecta `today ∈ {D-90, D-60, D-30, D-15, D-7}`, THEN dispara notificação via `EmailTemplateProvider` (ADR-0060) + dashboard + push app para `responsavel_documento_id` + admin do tenant AND publica `Licencas.AlertaVencimentoDisparado{licenca_id, dia_relativo, canal}`.
- **AC-LIC-002-2**: GIVEN documento vencido sem renovação (`vigencia_fim < today`), WHEN job roda no D+1, THEN escala alerta (severidade alta) + atualiza `status_calculado='vencido'` + publica `Licencas.LicencaVencida{licenca_id, dias_vencido, eh_bloqueante}`.
- **AC-LIC-002-3**: GIVEN documento renovado dentro da janela (nova `vigencia_fim > today`), WHEN admin cadastra renovação, THEN sistema cancela alertas pendentes E reagenda baseado na nova `vigencia_fim` AND publica `Licencas.LicencaRenovada{licenca_id, nova_vigencia_fim}`.
- **AC-LIC-002-4 (perfil A — job dedicado mensal Sprint 3 SAN-PERFIL)**: GIVEN `tenant_perfil_e(['A'])` AND `Tenant.acreditacao_vigencia_fim` < `today + 60d`, WHEN job mensal `verificar_vigencia_acreditacao_perfil_a` roda dia 1 às 02:00 BRT, THEN dispara alerta P1 ao dono Aferê + admin tenant + RT (CGCRE risk catastrófico) AND publica `Tenant.AcreditacaoVigenciaProximaDoFim{tenant_id, dias_restantes}`.

**Invariantes:** `INV-001` (trilha WORM em alertas e renovações).

---

### US-LIC-003: Bloquear operação por documento vencido

**Como** sistema, **quero** impedir operação dependente quando documento "bloqueante" estiver vencido, **para** evitar emissão ilegal/inválida (ex: certificado RBC sem acreditação vigente).

**Critérios de aceite:**
- **AC-LIC-003-1 (perfil A — bloqueio efetivo emissão RBC)**: GIVEN `tenant_perfil_e(['A'])` AND acreditação CGCRE marcada `bloqueante=True` AND `vigencia_fim < today`, WHEN técnico tenta emitir certificado RBC (US-CER-001 AC-4 referencia este AC), THEN sistema bloqueia com 409 `{erro: "ACREDITACAO_CGCRE_VENCIDA", venceu_em: DD/MM/AAAA, licenca_id, link_renovacao}` AND publica `Licencas.OperacaoBloqueadaDocVencido{tenant_id, perfil, operacao, licenca_id}`.
- **AC-LIC-003-2 (modo emergencial — qualquer perfil — INV-033)**: GIVEN documento bloqueante vencido, WHEN admin Aferê (Roldão) marca "operação em modo emergencial" via POST `/api/v1/licencas/{id}/modo-emergencial` com `justificativa ≥100 chars + A3`, THEN sistema libera operação dependente MAS registra evento auditável `Licencas.ModoEmergencialAtivado{licenca_id, justificativa_hash, a3_id, expira_em}` + audit WORM AND expira em até 7 dias (sem renovação automática).
- **AC-LIC-003-3 (doc não-bloqueante)**: GIVEN documento bloqueante=False, WHEN vence, THEN sistema apenas alerta (AC-LIC-002) — NÃO bloqueia operação.
- **AC-LIC-003-4 (perfil != A tentando se aproveitar de US-LIC-003)**: GIVEN tenant `perfil != A` AND tenta cadastrar acreditação CGCRE bloqueante, WHEN POST, THEN AC-LIC-001-3b rejeita previamente (defesa em profundidade).

**Invariantes:** `INV-032` (doc bloqueante vencido impede operação dependente), `INV-033` (modo emergencial exige justificativa + A3 + WORM + expira em 7d), `INV-001`, `INV-LIC-PERFIL-001`.

**Dependências:** Bloqueia módulos: `metrologia/certificados` (US-CER-001 AC-4), `metrologia/calibracao` (US-CAL emissão).

---

### US-LIC-004: Histórico de renovação versionado

**Como** auditor RBC/CGCRE, **quero** ver o histórico completo de renovações de cada documento, **para** comprovar continuidade da conformidade.

**Critérios de aceite:**
- **AC-LIC-004-1**: GIVEN documento com 3 renovações, WHEN consulta histórico, THEN sistema lista todas as revisões com data emissão, data validade, anexo, quem renovou e quando.
- **AC-LIC-004-2**: GIVEN renovação anterior, WHEN tenta editar/excluir, THEN sistema bloqueia (revisão é imutável — só pode criar nova versão).

**Invariantes:** `INV-001` (WORM em trilha de auditoria — revisão é imutável).

---

### US-LIC-005: Cadastrar e controlar ART/RRT do responsável técnico

**Como** responsável técnico, **quero** cadastrar minha ART/RRT vinculada à empresa com validade, **para** atender exigência CREA/CRQ/conselho profissional.

**Critérios de aceite:**
- **AC-LIC-005-1**: GIVEN responsável técnico cadastrado no módulo RT, WHEN cria ART/RRT vinculada, THEN sistema exige número da ART, conselho emissor, data registro, data validade, anexo.
- **AC-LIC-005-2**: GIVEN ART/RRT vencida e marcada bloqueante, WHEN técnico tenta assinar certificado, THEN sistema bloqueia com mensagem clara.

**Invariantes:** `INV-019` (RT habilitado quando aplicável), `INV-032` (ART/RRT vencida bloqueia se marcada bloqueante), `INV-001`.

---

### US-LIC-006: Cadastrar certificado digital A1/A3 da empresa (Onda 8 — fonte de verdade migrou)

**Como** responsável administrativo, **quero** registrar metadados do certificado digital A1/A3 (CNPJ, validade, AC emissora), **para** controlar vencimento e renovação.

**Onda 8 (ADR-0048):** cadastro físico do e-CNPJ migrou pra módulo `seguranca/certificados-digitais` (US-CER-DIG-001). Este US permanece como **referência cruzada** pra controle operacional de vencimento + bloqueio de operações dependentes.

**Critérios de aceite (atualizados):**
- **AC-LIC-006-1**: GIVEN admin tenant, WHEN consulta painel de licenças, THEN sistema mostra entrada "e-CNPJ" vinculada via FK pra `certificados-digitais.cert_id`, com `valido_ate`, `ac_emissora`, status local (vigente/vencido/revogado).
- **AC-LIC-006-2**: GIVEN cert A3 expirando em 30 dias OU revogado pela AC (`A3.RevogacaoDetectada` ADR-0046), WHEN sistema verifica, THEN dispara alerta com instruções + bloqueia emissão de NF se marcado bloqueante (US-LIC-003 herdada).

**Invariantes:** `INV-A3-OCSP-001` (ADR-0046), `INV-017`, `INV-001`. Vincula ADR-0009, ADR-0046, ADR-0048.

---

### US-LIC-008 (REPOSICIONADA — ADR-0048): Cadastro físico do e-CPF do RT migrou pra `certificados-digitais`

**Status:** delegada ao módulo `seguranca/certificados-digitais` (US-CER-DIG-002). Este placeholder garante rastreabilidade da numeração + lembra que `licencas-acreditacoes` consulta o cert via FK pra controle operacional de bloqueio (US-LIC-003).

- **AC-LIC-008-1**: GIVEN RT desligado (`Colaborador.Desligado` is_rt_signatario=true — INV-INT-002), WHEN consumer reage, THEN marca cert A3 do RT como `bloqueado_para_assinatura` aqui + delega revogação efetiva ao módulo `certificados-digitais` (US-CER-DIG-006).
- **Vínculo onboarding (A-REG-06):** wizard onboarding RT em `certificados-digitais` (AC-CER-DIG-002-1) exige `cpf + A3 + OCSP good + subject_cn.cpf == usuario.cpf`. `licencas-acreditacoes` recebe evento `CertificadoDigital.Cadastrado{escopo: rt_signatario}` e cria entrada de controle ART/RRT vinculada.

---

### US-LIC-009 (REPOSICIONADA — ADR-0048): Cadastro físico do e-CPF de demais signatários migrou pra `certificados-digitais`

**Status:** delegada ao módulo `seguranca/certificados-digitais` (US-CER-DIG-003).

---

### US-LIC-010 (Onda 8 — ADR-0014 fluxo 7): Ampliação de escopo de acreditação CGCRE

**Como** RT, **quero** registrar pedido de ampliação de escopo (novas grandezas/faixas), **para** preparar dossiê pra submissão CGCRE e acompanhar status.

**Critérios de aceite:**
- **AC-LIC-010-1**: GIVEN RT acessa licença CGCRE vigente, WHEN clica "Solicitar ampliação", THEN sistema cria entidade `PedidoAmpliacaoEscopo` com `{grandezas_novas, faixas_novas, padroes_novos_id, procedimentos_validados_id, status: rascunho}`.
- **AC-LIC-010-2**: GIVEN pedido completo (dossiê + ART RT + padrões rastreáveis + validação 7.11), WHEN RT submete, THEN sistema valida pré-requisitos, gera PDF consolidado, publica `Licencas.AmpliacaoEscopoSubmetida`, status→`em_analise_cgcre`.
- **AC-LIC-010-3**: GIVEN CGCRE aprova ampliação, WHEN admin registra resultado + carta CGCRE, THEN cria nova revisão da licença com escopo expandido + publica `Licencas.AcreditacaoAmpliada` (consumidor: `certificados` libera emissão nas novas grandezas).

**Invariantes:** `INV-INT-003` (snapshot acreditação), `INV-001`.

---

### US-LIC-011 (Onda 8 — ADR-0014 fluxo 8): Responder NC CGCRE (SLA 30 dias)

**Como** RT, **quero** registrar e responder NC aberta pela CGCRE em supervisão, **para** evitar suspensão.

**Critérios de aceite:**
- **AC-LIC-011-1**: GIVEN admin recebe ofício CGCRE com NC, WHEN cadastra `NCCgcre {numero, severidade, prazo_resposta, evidencias_solicitadas}`, THEN sistema publica `Licencas.NCCgcreAberta`, agenda alertas D-15/7/3/1 antes do prazo de resposta (≤30 dias), bloqueia emissão se severidade=`maior` AND escopo afetado.
- **AC-LIC-011-2**: GIVEN RT prepara resposta + evidências + plano de ação, WHEN submete via UI, THEN sistema gera PDF consolidado assinado pelo RT (ADR-0047 LTV) + publica `Licencas.NCCgcreRespondida`.
- **AC-LIC-011-3 (prazo perdido)**: GIVEN >30 dias sem resposta, WHEN sistema verifica, THEN escalation P1 ao dono Aferê + bloqueia emissão hard até resposta + publica `Licencas.NCCgcrePrazoVencido`.

**Invariantes:** `INV-032` (doc bloqueante), `INV-001`, `INV-INT-002` (RT designado).

---

### US-LIC-012 (Onda 8 — ADR-0014 fluxo 9): Preparar revisão CGCRE a cada 5 anos

**Como** admin, **quero** sistema avisar 12 meses antes da revisão CGCRE quinquenal + checklist preparatório, **para** evitar lapsos.

**Critérios de aceite:**
- **AC-LIC-012-1**: GIVEN acreditação vigente com `proxima_revisao_5anos` calculada, WHEN data ≥ D-365/180/90/60/30, THEN sistema dispara alerta progressivo + checklist (atualização padrões, ART RT, validações 7.11, dossiê histórico).
- **AC-LIC-012-2**: GIVEN admin marca checklist 100% concluído, WHEN gera dossiê pré-revisão, THEN sistema produz PDF consolidado + publica `Licencas.DossieRevisao5AnosPronto`.

---

### US-LIC-013 (Onda 8 — M-REG-05): Preparar dossiê pré-auditoria CGCRE

**Como** admin, **quero** gerar checklist NIT-DICLA-021/030 com export consolidado, **para** apresentar à auditoria CGCRE/RBC.

**Critérios de aceite:**
- **AC-LIC-013-1**: GIVEN auditoria CGCRE agendada, WHEN admin clica "Gerar dossiê", THEN sistema produz PDF + ZIP com: licenças vigentes, ART RT, CertCalibração últimos 12m, NCs abertas/fechadas, validações 7.11, registros de treinamento, padrões com rastreabilidade.
- **AC-LIC-013-2**: GIVEN dossiê gerado, WHEN auditor consulta hash, THEN bate com registro WORM.

---

### US-LIC-007: Relatório consolidado para auditoria externa

**Como** auditor externo (CGCRE, fisco), **quero** receber PDF consolidado com todas as licenças vigentes + histórico, **para** comprovar conformidade em auditoria.

**Critérios de aceite:**
- **AC-LIC-007-1**: GIVEN auditoria agendada, WHEN admin gera relatório, THEN sistema produz PDF com lista de documentos vigentes (tipo, número, validade, anexo embed), documentos vencidos, histórico últimos 24 meses, e hash SHA-256 do relatório.
- **AC-LIC-007-2**: GIVEN relatório gerado, WHEN auditor verifica hash, THEN bate com hash registrado em trilha WORM.

**Invariantes:** `INV-001` (WORM no relatório consolidado).

---

## 7. Métricas de sucesso (inline + detalhe em `metricas.md`)

- **Zero operações executadas com documento bloqueante vencido** (target: 100%) — `INV-032`.
- **Renovações iniciadas em janela ≥30 dias antes do vencimento** (target: ≥90%).
- **% perfil A com acreditação CGCRE vigente** (target: 100%) — job mensal `verificar_vigencia_acreditacao_perfil_a` (Sprint 3 SAN-PERFIL-TENANT).
- **Tempo médio de alerta D-60 até renovação concluída** (mediana): ≤ 45 dias.
- **% NCs CGCRE respondidas dentro do SLA 30d** (perfil A): 100% (`INV-INT-002`).
- **% tentativas perfil D cadastrar CGCRE bloqueadas pelo predicate** = 100% (defesa anti-fraude L6).
- **Drift `Tenant.perfil_regulatorio` vs licenças cadastradas** = 0 incidentes (validação cruzada mensal — Wave A `GATE-LIC-DRIFT`).

## 8. NFR

- **Performance:** consulta dashboard < 500ms p95.
- **Disponibilidade:** SLO 99,9% (módulo crítico — bloqueia operações dependentes).
- **Segurança:** anexos PDF criptografados em repouso (B2 + KMS Multi-Region); trilha WORM imutável; SEC-001/SEC-002.
- **Acessibilidade:** WCAG 2.1 AA (ADR-0057).
- **Retenção (matriz-feature-perfil §retenção):** perfil A/B/C 25a; perfil D 5a.

## 9. Dependências (ADRs + módulos)

**Módulos:**

- `metrologia/responsabilidade-tecnica` (ADR-0022) — fornece RT designado para vínculo ART/RRT.
- `metrologia/certificados` — consumer downstream de `Licencas.AcreditacaoCGCREVencida` (US-CER-001 AC-4 bloqueia emissão RBC).
- `seguranca/certificados-digitais` (ADR-0048) — cadastro físico A3 (US-LIC-006/008/009 reposicionadas).
- `infrastructure/tenant` — fornece `Tenant.perfil_regulatorio` + recebe atualização via `aplicar_evento_cgcre` (ADR-0067 Sprint 1).
- `notificacoes/cliente` — consumer alertas (ADR-0060 `EmailTemplateProvider`).

**ADRs aceitas:**

- **ADR-0009** — A3 cliente-side (US-LIC-003 modo emergencial exige A3).
- **ADR-0014** — transições regulatórias (US-LIC-010/011/012 — fluxos 7/8/9).
- **ADR-0022** — RT do tenant (vínculo ART/RRT).
- **ADR-0025 v2** — validação software ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ — §5.1).
- **ADR-0046** — OCSP/CRL revogação online (US-LIC-006 A3 ICP-Brasil).
- **ADR-0047** — PAdES-LTV (PDF longa duração 25a — US-LIC-011 resposta NC).
- **ADR-0048** — cadastro segregado A3 (US-LIC-006/008/009 delegadas).
- **ADR-0060** — `EmailTemplateProvider` (US-LIC-002 alertas + Sprint 3 job).
- **ADR-0067** — perfil regulatório do tenant entidade temporal (canônico — fonte L6 fix).

## 10. Glossário

Ver `glossario.md` + `docs/comum/glossario.md`. Termos canônicos adicionados nesta sanação:

- **Perfil regulatório:** `Tenant.perfil_regulatorio` enum `{A_ACREDITADO_RBC, B_RASTREAVEL, C_EM_PREPARACAO, D_COMERCIAL_PURO}` — pré-condição de cadastro CGCRE (ADR-0067).
- **Predicate `tenant_perfil_e(perfis_aceitos)`:** função canônica `src/infrastructure/authz/predicates.py` — fail-closed timeout 50ms. Lê ContextVar `perfil_tenant_context`.
- **Predicate `acreditacao_cgcre_aplicavel_por_perfil(tenant_id) -> bool`:** retorna `True` somente perfil A. Consumido pelo job mensal Sprint 3.
- **`aplicar_evento_cgcre(tenant_id, direcao, ...)`:** função SECURITY DEFINER (Sprint 1 SAN-PERFIL-TENANT) — única forma de UPDATE em `tenants.perfil_regulatorio`. Hook `tenant-perfil-imutavel-check` bloqueia UPDATE direto.
- **Doc bloqueante:** flag em licença que, quando vencida, impede operação dependente (`INV-032`).
- **Modo emergencial:** mecanismo de exceção auditada do dono Aferê — libera operação por até 7d com A3 + justificativa ≥100 chars (`INV-033`).
- **Trilha D→A:** caminho de evolução de tenant `perfil D → C → B → A` ao longo de meses/anos (BIG-03 discovery — diferencial competitivo). Codificada via ADR-0067 + comando `provisionar_tenant`.

## 11. Como este PRD evolui

- US nova → próximo ID `US-LIC-NNN`.
- US deprecada → `@deprecated` + ADR.
- Novo tipo de documento regulatório → adicionar em catálogo + AC novo.
- Mudança em matriz perfil × tipo de licença → emenda ADR-0067 + atualização `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator`.
