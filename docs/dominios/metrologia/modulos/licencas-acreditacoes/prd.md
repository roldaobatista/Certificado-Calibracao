---
owner: roldao
revisado-em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
  - docs/dominios/seguranca/modulos/certificados-digitais/prd.md
  - docs/adr/0014-transicoes-regulatorias.md
  - docs/adr/0048-a3-ecpf-rt-cadastro.md
---

# PRD — Módulo Licenças, Acreditações e Autorizações da Empresa

> Gestão centralizada dos documentos regulatórios da empresa prestadora: licenças, acreditações (RBC/CGCRE), certificados digitais, alvarás, ART/RRT, certidões e autorizações legais. Crítico em ambiente regulado.

---

## 1. O que este módulo é

Cadastro vivo de TODOS os documentos legais e regulatórios que autorizam a empresa a operar: acreditação RBC/CGCRE (ISO 17025), licenças sanitárias/ambientais, alvarás, certidões negativas, ART/RRT do responsável técnico, certificados digitais A1/A3 da empresa, autorizações INMETRO/ANVISA, contratos de adesão regulamentares. Para cada documento, controla validade, alertas de vencimento, histórico de renovação e — quando a regra de negócio exige — bloqueia operações dependentes se o documento estiver vencido.

## 2. Por que este módulo existe (problema a resolver)

Empresa que opera sem documento válido sofre multa, suspensão da acreditação e perde contratos. Hoje (Balanças Solution) o controle é planilha + memória do responsável — risco real de descobrir o vencimento depois da auditoria. Em laboratório RBC, perder a acreditação inviabiliza o negócio (CGCRE 8.4 + NIT-DICLA exigem cadeia documental válida).

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` (domínio) + `docs/comum/personas.md`.

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

## 5. Non-goals (o que NÃO está neste módulo)

- NÃO emite os documentos regulatórios (isso é processo externo no órgão competente).
- NÃO gerencia documentos de CLIENTES (isso é módulo CRM/clientes).
- NÃO gerencia licenças de SOFTWARE (chaves de produto, SaaS — isso é módulo TI/infra).
- NÃO substitui o processo legal de renovação — apenas alerta e bloqueia.
- NÃO armazena certificado digital A3 (token físico fica com o titular; aqui só registra metadados + validade).

## 6. User Stories

### US-LIC-001: Cadastrar licença/documento regulatório

**Como** responsável administrativo, **quero** cadastrar uma licença da empresa com tipo, número, órgão emissor, data emissão, data validade e anexo PDF, **para** ter controle centralizado dos documentos regulatórios.

**Critérios de aceite:**
- **AC-LIC-001-1**: GIVEN usuário admin autenticado no tenant, WHEN cadastra licença com campos obrigatórios (tipo, número, órgão emissor, data emissão, data validade, anexo), THEN sistema persiste com status calculado e data próximo alerta.
- **AC-LIC-001-2**: GIVEN documento sem anexo PDF/imagem, WHEN tenta salvar, THEN sistema bloqueia com mensagem "anexo obrigatório para evidência de auditoria".
- **AC-LIC-001-3**: GIVEN tipo "acreditação CGCRE", WHEN cadastra, THEN sistema exige campo "escopo da acreditação" e marca documento como "bloqueante para emissão RBC" por padrão.

**Non-goals desta story:** integração com órgão emissor.

**Invariantes:** `INV-046` (anexo de evidência obrigatório), `INV-001` (trilha imutável WORM), `INV-TENANT-001`.

**Dependências:** Bloqueado por: ADR-0002 (multi-tenancy).

---

### US-LIC-002: Alertar antes do vencimento

**Como** responsável administrativo, **quero** receber alertas em 90/60/30/15/7 dias antes do vencimento, **para** iniciar a renovação a tempo.

**Critérios de aceite:**
- **AC-LIC-002-1**: GIVEN documento com data validade D, WHEN data atual = D-90, D-60, D-30, D-15 ou D-7, THEN sistema dispara notificação por e-mail + dashboard + app pra responsável do documento + admin do tenant.
- **AC-LIC-002-2**: GIVEN documento vencido sem renovação, WHEN passa 1 dia da validade, THEN sistema escalona alerta (severidade alta) e marca documento como "vencido".
- **AC-LIC-002-3**: GIVEN documento renovado dentro da janela, WHEN nova data validade > atual, THEN sistema cancela alertas pendentes e reagenda baseado na nova data.

**Invariantes:** `INV-001` (trilha WORM em alertas e renovações).

---

### US-LIC-003: Bloquear operação por documento vencido

**Como** sistema, **quero** impedir operação dependente quando documento "bloqueante" estiver vencido, **para** evitar emissão ilegal/inválida (ex: certificado RBC sem acreditação vigente).

**Critérios de aceite:**
- **AC-LIC-003-1**: GIVEN acreditação CGCRE marcada como bloqueante e vencida, WHEN técnico tenta emitir certificado RBC, THEN sistema bloqueia com mensagem clara "acreditação vencida em DD/MM — renovar antes de emitir" e cita o documento bloqueante.
- **AC-LIC-003-2**: GIVEN documento bloqueante vencido, WHEN admin marca "operação em modo emergencial" (com justificativa), THEN sistema libera operação MAS registra evento auditável "operação com documento vencido" e exige assinatura A3 do admin.
- **AC-LIC-003-3**: GIVEN documento bloqueante NÃO marcado como tal, WHEN vence, THEN sistema só alerta — não bloqueia.

**Invariantes:** `INV-032` (doc bloqueante vencido impede operação dependente), `INV-033` (modo emergencial exige justificativa + A3 + WORM), `INV-001`.

**Dependências:** Bloqueia módulos: Certificados (US-CER-001), Calibração (US-CAL-emissão).

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

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Zero operações executadas com documento bloqueante vencido (target: 100%).
- Renovações iniciadas em janela ≥30 dias antes do vencimento (target: ≥90%).

## 8. NFR

- **Performance:** consulta dashboard < 500ms p95.
- **Disponibilidade:** SLO 99.9% (módulo crítico — bloqueia operações).
- **Segurança:** anexos PDF criptografados em repouso (B2 + KMS); trilha WORM imutável; SEC-001/SEC-002.
- **Acessibilidade:** WCAG AA.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID `US-LIC-NNN`.
- US deprecada → `@deprecated` + ADR.
- Novo tipo de documento regulatório → adicionar em catálogo + AC novo.
