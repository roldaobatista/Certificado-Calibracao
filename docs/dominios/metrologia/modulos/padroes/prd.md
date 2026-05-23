---
owner: Roldão
revisado-em: 2026-05-23
status: draft
modulo: padroes
dominio: metrologia
versao: 1
---

# PRD — Módulo Padrões Metrológicos do laboratório

> **v1 (draft 2026-05-23):** criado na Onda 5 saneamento pós-auditoria
> projeto-inteiro 10 lentes (G2 CRÍTICO). Módulo era apenas non-goal
> em `equipamentos` (NG-EQP-6); ADR-0040 cravou separação. Pendente
> revisão dos 4 subagentes (`tech-lead-saas-regulado`,
> `advogado-saas-regulado`, `corretora-seguros-saas`,
> `consultor-rbc-iso17025`) antes de virar `stable`.

## 1. O que este módulo é

Cadastro dos **padrões metrológicos do laboratório do tenant** —
pesos padrão classe E1/E2/F1/F2 (OIML R111), termômetros padrão,
manômetros padrão, conjuntos de massas, blocos padrão, padrões
elétricos — que são usados para calibrar os equipamentos dos
clientes finais. Cada padrão tem cert de rastreabilidade externo
vigente (rastreável a INMETRO/RBC/BIPM), classe declarada, faixas e
incertezas; participa de **recal externo periódico** e de
**intercomparações (PT — proficiency testing)** em perfil A
(INV-023). Persona principal: gestor de qualidade (P-OP-04 novo) +
metrologista de bancada (P-OP-02).

**Wave A · módulo paralelo ao Marco 4 (`calibracao`)** — destrava
INV-002 (cadeia de rastreabilidade na emissão de cert),
INV-011 (cert bloqueia se padrão tem cal vencida), INV-021..023
(controle de classe + verificação intermediária + PT) e ADR-0040.

## 2. Por que existe (problema a resolver)

- BIG-04 (rastreabilidade ao SI) — sem padrão canônico, certificado
  emitido vira fraude regulatória.
- OP14 (recal externo do padrão é evento agendado, não improviso) —
  laboratórios perdem prazo de recal e operam com padrão vencido.
- Dor #04 (padrão derivou e ninguém percebeu — verificação
  intermediária ausente).
- Conformidade ISO 17025 cl. 6.5 (rastreabilidade metrológica) +
  cl. 6.4.10 (verificação intermediária) + cl. 6.6 (PT em A) +
  NIT-DICLA-030 rev. 15 item 8.2.6 (incerteza + valor convencional
  obrigatórios no cert aceito).

## 3. Personas

- **P-OP-04 — Gestor de qualidade do tenant** (principal —
  promovido): cadastra padrão, gerencia recal, registra PT,
  aprova baixa.
- **P-OP-02 — Metrologista de bancada**: seleciona padrão na
  calibração (Marco 4), registra verificação intermediária.
- **P-COM-02 — Consultor RBC** (V2): consulta padrões para
  preparar dossiê CGCRE.

Detalhes em `personas.md` (do domínio metrologia).

## 4. Escopo (o que ESTÁ)

- CRUD de `PadraoMetrologico` (UNIQUE por tenant + número de
  série) com grandezas + faixas + incertezas tipadas (VOs em
  `src/domain/metrologia/value_objects.py`).
- Vinculação à cadeia (BIPM, INMETRO, RBC, INTERNACIONAL) +
  validade do cert externo.
- Fluxo **recal externo**: envio ao lab credenciado → recebimento
  do novo cert → atualização de `incertezas_certificado` +
  `validade_certificado_rastreabilidade` (transacional com evento
  `padrao.recal_externo_concluido`).
- **Verificação intermediária** (cl. 6.4.10) entre recals
  externos — INV-022 + INV-CAL-VI-001.
- **Intercomparação / PT** (perfil A — INV-023) com resultado
  registrado.
- **Baixa / sucatamento** (estado terminal) preservando
  histórico WORM.
- **Exportação dossiê CGCRE** (Wave B+ — gera PDF/A com cadeia
  completa para supervisão).
- Estado: `EM_USO` / `EM_RECAL_EXTERNO` / `INTERCOMPARACAO_PT_EM_CURSO`
  / `BAIXADO` / `SUCATEADO`.

## 5. Non-goals

- NÃO calibra outro padrão (lab interno calibrando padrão do
  próprio lab — caso "calibração interna" exige ADR adicional
  Wave B+).
- NÃO trata padrão emprestado/alugado (Wave B+).
- NÃO emite cert (cert é Marco 4 calibração + módulo
  `certificados`).
- NÃO modela equipamento do cliente (módulo `equipamentos`).
- NÃO entrega exportação dossiê CGCRE no Wave A (gera dados
  estruturados; PDF/A dossiê é Wave B+).
- NÃO entrega scanner de padrão por QR (padrão fica fisicamente
  no lab — não circula).

## 6. User Stories

### US-PAD-001 — Cadastrar padrão metrológico

**Como** gestor de qualidade, **quero** cadastrar um padrão com
cert externo, **para** começar a usá-lo em calibrações.

- **AC-PAD-001-1**: GIVEN tenho tenant ativo, WHEN preencho NS +
  fabricante + modelo + ≥1 grandeza + ≥1 faixa + ≥1 incerteza +
  vinculacao + cert externo PDF + validade, THEN `PadraoMetrologico`
  salvo com `estado=EM_USO`; evento `padrao.cadastrado` publicado.
- **AC-PAD-001-2**: GIVEN tento cadastrar sem incerteza ou sem
  valor convencional no cert externo, THEN sistema retorna 422
  citando NIT-DICLA-030 item 8.2.6 (INV-014 reusado / INV-PAD-002).
- **AC-PAD-001-3**: GIVEN preencho `vinculacao=RBC`, WHEN tenant
  não está em perfil A, THEN sistema retorna 422 com mensagem
  "padrão RBC exige tenant perfil A" (INV-015 + INV-PAD-005).
- **AC-PAD-001-4**: GIVEN tento cadastrar NS já existente no
  mesmo tenant, THEN sistema retorna 409.

**Invariantes:** INV-021, INV-PAD-001, INV-PAD-002, INV-PAD-005,
INV-TENANT-001.

### US-PAD-002 — Registrar recal externo (envio + retorno)

**Como** gestor de qualidade, **quero** registrar envio do padrão
ao lab externo e a chegada do novo cert, **para** manter cadeia de
rastreabilidade.

- **AC-PAD-002-1**: GIVEN padrão `EM_USO`, WHEN registro envio ao
  lab externo com data + lab destinatário + responsável envio,
  THEN `estado=EM_RECAL_EXTERNO`; evento
  `padrao.recal_externo_iniciado`.
- **AC-PAD-002-2**: GIVEN padrão `EM_RECAL_EXTERNO`, WHEN
  registro retorno com novo cert externo PDF + nova incerteza +
  nova validade + data recal, THEN
  `incertezas_certificado` + `validade_certificado_rastreabilidade`
  atualizados em transação atômica; evento
  `padrao.recal_externo_concluido`; `estado=EM_USO`.
- **AC-PAD-002-3**: GIVEN padrão em recal há > 90 dias sem
  retorno, THEN alerta P2 no painel-do-dono ("padrão pendente de
  retorno").
- **AC-PAD-002-4**: GIVEN tento UPDATE direto em
  `incertezas_certificado` SEM passar pelo fluxo de
  `padrao.recal_externo_concluido`, THEN trigger PG bloqueia
  (INV-PAD-006).

**Invariantes:** INV-021, INV-PAD-006, INV-CAL-RAST-001.

### US-PAD-003 — Verificação intermediária periódica

**Como** metrologista, **quero** registrar verificação
intermediária (entre recals externos), **para** detectar drift
antes do recal seguinte.

- **AC-PAD-003-1**: GIVEN padrão `EM_USO`, WHEN registro VI com
  resultado (aprovado/reprovado) + método + responsável + data,
  THEN `VerificacaoIntermediaria` criada; evento
  `padrao.verificacao_intermediaria_registrada`.
- **AC-PAD-003-2**: GIVEN VI reprovada, WHEN salvo, THEN padrão
  passa pra `estado=EM_RECAL_EXTERNO` automaticamente + bloqueia
  uso até nova VI aprovada (INV-CAL-VI-001).
- **AC-PAD-003-3**: GIVEN classe E1/E2/F1/F2 + sem VI nos últimos
  N meses (configurável por classe), THEN alerta P2 + dashboard
  marca padrão como "VI pendente".

**Invariantes:** INV-022, INV-CAL-VI-001.

### US-PAD-004 — Baixar / sucatar padrão (terminal)

**Como** gestor de qualidade, **quero** baixar padrão (fim de
vida útil ou perda), **para** removê-lo do pool ativo.

- **AC-PAD-004-1**: GIVEN padrão `EM_USO` sem calibração em
  curso usando ele, WHEN baixo com motivo (≥30 chars) + tipo
  (`fim_vida_util`/`extraviado`/`danificado_irrecuperavel`/`vendido`),
  THEN `estado=BAIXADO` (não terminal — pode reaparecer) ou
  `SUCATEADO` (terminal); `revogado_em` + `motivo_revogacao`
  preenchidos (ADR-0030 + INV-SOFT-002).
- **AC-PAD-004-2**: GIVEN há calibração em curso usando padrão,
  THEN bloqueia baixa com mensagem citando IDs de calibração.
- **AC-PAD-004-3**: GIVEN tento DELETE direto, THEN trigger PG
  bloqueia (INV-SOFT-002 padrão B WORM).

**Invariantes:** INV-PAD-003, INV-SOFT-002, INV-VIG-002.

### US-PAD-005 — Intercomparação (PT) em perfil A

**Como** gestor de qualidade de tenant em perfil A, **quero**
registrar participação em comparação interlaboratorial, **para**
atender INV-023 (cl. 6.6 + ISO/IEC 17043).

- **AC-PAD-005-1**: GIVEN tenant perfil A + padrão `EM_USO`, WHEN
  registro participação em PT com lab organizador + protocolo +
  data início, THEN `estado=INTERCOMPARACAO_PT_EM_CURSO`; evento
  `padrao.intercomparacao_iniciada`.
- **AC-PAD-005-2**: GIVEN PT em curso, WHEN registro resultado
  (aprovado/rejeitado/sob_revisão) + relatório PT + zeta-score,
  THEN evento `padrao.intercomparacao_concluida`; padrão volta a
  `EM_USO`.
- **AC-PAD-005-3**: GIVEN resultado rejeitado, THEN bloqueia uso
  do padrão até NC ser tratada (INV-012 + INV-CAL-WORM-001).

**Invariantes:** INV-023.

### US-PAD-006 — Exportar dossiê CGCRE (Wave B+ — stub no Wave A)

**Como** gestor de qualidade preparando supervisão CGCRE,
**quero** exportar dossiê com cadeia metrológica completa,
**para** entregar ao supervisor.

- **AC-PAD-006-1** (Wave A): GIVEN padrão `EM_USO`, WHEN clico
  "exportar dossiê", THEN sistema gera JSON estruturado com toda
  cadeia (cert externo histórico + VIs + PTs + uso em
  calibrações) — PDF/A é Wave B+.
- **AC-PAD-006-2** (Wave B+): PDF/A com selo CGCRE + assinatura
  A3 do RT.

**Invariantes:** INV-CAL-WORM-001.

## 7. Bases legais LGPD (art. 7º)

| Finalidade | Base legal | Justificativa |
|---|---|---|
| Cadastro de padrão | art. 7º II | Obrigação regulatória ISO 17025 cl. 6.5 |
| Recal externo (cert externo PDF) | art. 7º II | Obrigação regulatória |
| Verificação intermediária | art. 7º II | Obrigação regulatória cl. 6.4.10 |
| Intercomparação PT | art. 7º II | Obrigação regulatória cl. 6.6 |
| Dossiê CGCRE | art. 7º II | Supervisão regulatória |

> Padrão metrológico **não contém PII direta** (é instrumento físico
> do laboratório). Responsável envio recal externo é dado funcional
> (não cliente final).

## 8. Métricas (ver `metricas.md`)

- % padrões em uso com cert externo dentro da validade ≥ 100% (em A)
- % padrões com VI dentro do prazo declarado ≥ 95% (em A)
- Tempo médio recal externo (envio → retorno) ≤ 60 dias
- % padrões em A com PT ativo no ciclo declarado ≥ 100%

## 9. NFR

- Performance: listagem de padrões p95 ≤ 1.0s
- Segurança: padrão é "do tenant"; RLS por `tenant_id` obrigatório
- Auditoria: WORM em VI + PT + recal (INV-CAL-WORM-001 estendido)

## 10. ADRs e INVs aplicáveis

- ADR-0040 (esta separação), ADR-0007 (codegen), ADR-0002 (RLS),
  ADR-0022 (RT — gestor de qualidade pode acumular ou ser RT),
  ADR-0030 (vigência canônica), ADR-0031 (soft-delete padrão B)
- INVs: INV-021..023, INV-PAD-001..006, INV-CAL-SNAP-001,
  INV-CAL-RAST-001, INV-CAL-VI-001, INV-CAL-WORM-001,
  INV-VIG-001..004, INV-SOFT-001/002

## 11. Glossário e referências

- `modelo-de-dominio.md` — entidades, agregados, portas, eventos
- VOs metrológicos: `src/domain/metrologia/value_objects.py`
- `docs/conformidade/comum/retencao-matriz.md` — padrão é registro
  ISO 17025 cl. 8.4 (25 anos)
