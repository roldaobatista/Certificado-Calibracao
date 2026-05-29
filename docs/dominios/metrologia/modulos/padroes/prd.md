---
owner: roldao
revisado-em: 2026-05-29
proximo-review: 2026-08-27
status: stable
diataxis: explanation
audiencia: agente
modulo: padroes
dominio: metrologia
versao: 2
historico:
  - 2026-05-27 — Onda PRE-A.3 saneamento pré-Wave A (BATCH B3): frontmatter canônico
    (revisado-em + proximo-review hífen); perfil ADR-0067 reforçado em US-PAD-001/005
    com predicate `tenant_perfil_e([...])` e matriz feature×perfil; ADR-0025 v2 estendida
    (URS/IQ/OQ/PQ específicos do módulo padrões + 2º caminho de cálculo do valor
    convencional + cartas controle Shewhart adiantadas Wave A em perfil A — L3#A9);
    nova US-PAD-007 (equipamentos auxiliares cl. 6.4.5 — L3#7 crítico); ADR-0068 sucessão
    RT; ADR-0064 HMAC; matriz feature×perfil; non-objetivos atualizados; status →
    stable.
  - 2026-05-23 — versão inicial Onda 5 saneamento pós-auditoria projeto-inteiro 10 lentes.
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/dominios/metrologia/modulos/procedimentos/prd.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-3-padroes.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - docs/adr/0066-predicates-cmc-procedimento-fail-open-lazy-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/conformidade/comum/matriz-feature-perfil.md
---

# PRD — Módulo Padrões Metrológicos do laboratório

> **v2 (stable 2026-05-27):** Onda PRE-A.3 fechou o ritual pré-Wave A. ADR-0040
> (padrão metrológico como entidade separada de `equipamentos`) referenciada;
> ADR-0067 (perfil regulatório) declarada em US; ADR-0025 v2 estendida ao módulo
> com URS/IQ/OQ/PQ próprios + 2º caminho de cálculo de valor convencional;
> equipamentos auxiliares cl. 6.4.5 incluídos como US nova; cartas controle
> Shewhart adiantadas Wave A em perfil A (L3#A9).

## 1. O que este módulo é

Cadastro dos **padrões metrológicos do laboratório do tenant** — pesos padrão
classe E1/E2/F1/F2 (OIML R111), termômetros padrão, manômetros padrão,
conjuntos de massas, blocos padrão, padrões elétricos — que são usados para
calibrar os equipamentos dos clientes finais. Cada padrão tem cert de
rastreabilidade externo vigente (rastreável a INMETRO/RBC/BIPM), classe
declarada, faixas e incertezas; participa de **recal externo periódico**,
**verificação intermediária** (cl. 6.4.10), **intercomparações (PT —
proficiency testing)** em perfil A (INV-023) e — quando aplicável —
**cartas controle Shewhart** (perfil A).

Inclui também (US-PAD-007 nova) **equipamentos auxiliares do laboratório** —
termo-higrômetro de sala, fonte de tensão estável, banho termostático —
exigidos por ISO 17025 cl. 6.4.5 e flagrados como gap CRÍTICO L3#7 na
auditoria projeto-inteiro.

Persona principal: gestor de qualidade (P-OP-04) + metrologista de bancada
(P-OP-02).

**Wave A · módulo paralelo ao Marco 4 (`calibracao`)** — destrava
INV-002 (cadeia de rastreabilidade na emissão de cert), INV-011 (cert
bloqueia se padrão tem cal vencida), INV-021..023 (controle de classe +
verificação intermediária + PT) e ADR-0040.

## 2. Por que existe (problema a resolver)

- BIG-04 (rastreabilidade ao SI) — sem padrão canônico, certificado emitido
  vira fraude regulatória.
- OP14 (recal externo do padrão é evento agendado, não improviso) —
  laboratórios perdem prazo de recal e operam com padrão vencido.
- Dor #04 (padrão derivou e ninguém percebeu — verificação intermediária
  ausente).
- L3#7 (CRÍTICO) — equipamentos auxiliares cl. 6.4.5 (termo-higrômetro,
  fonte tensão, banho) eram non-goal sem cadastro mínimo; supervisão CGCRE
  flagra em 1ª visita.
- L3#A9 — perfil A exige cartas controle Shewhart por padrão desde a 1ª
  supervisão CGCRE; estava postergado para MVP-2 → adiantado para Wave A.
- Conformidade ISO 17025 cl. 6.4.5 (equipamentos auxiliares) + cl. 6.5
  (rastreabilidade metrológica) + cl. 6.4.10 (verificação intermediária)
  + cl. 6.6 (PT em A) + NIT-DICLA-030 rev. 15 item 8.2.6 (incerteza +
  valor convencional obrigatórios no cert aceito).

## 3. Personas

- **P-OP-04 — Gestor de qualidade do tenant** (principal): cadastra padrão,
  gerencia recal, registra PT, aprova baixa, mantém cartas controle.
- **P-OP-02 — Metrologista de bancada**: seleciona padrão na calibração
  (Marco 4), registra verificação intermediária, plota carta controle.
- **P-OP-03 — RT do tenant** (ADR-0022 v2 + ADR-0068): aprova baixa
  definitiva, assina dossiê CGCRE com A3.
- **P-COM-02 — Consultor RBC / supervisor CGCRE** (perfil A): consulta
  padrões para preparar dossiê CGCRE; revisa cartas controle.

Detalhes em `personas.md` (do domínio metrologia).

## 4. Perfil regulatório (ADR-0067)

| Perfil | Status do módulo | Predicate de entrada |
|---|---|---|
| **A — Acreditado RBC** | ✅ OBRIGATÓRIO_FULL (recal + VI + PT + cartas Shewhart + dossiê CGCRE) | `tenant_perfil_e(["A"])` em US-PAD-005 (PT) + US-PAD-008 (Shewhart) + US-PAD-006 (dossiê) |
| **B — Rastreável** | ✅ OBRIGATÓRIO (recal + VI; PT opcional; sem selo RBC) | `tenant_perfil_e(["A", "B"])` em US-PAD-001 com `vinculacao` restrita |
| **C — Em preparação D→A** | ✅ OBRIGATÓRIO_PARCIAL (recal + VI; PT recomendado; cartas Shewhart opcionais) | mesmo que B + warning em UI |
| **D — Comercial puro** | 🟢 OPCIONAL_RECOMENDADO (cadastro de padrão mas sem fluxo PT/RBC) | sem bloqueio |

Linha "Padrão metrológico (recal externo + VI + PT)" da matriz
`docs/conformidade/comum/matriz-feature-perfil.md` é fonte da verdade.

## 5. Escopo (o que ESTÁ)

- CRUD de `PadraoMetrologico` (UNIQUE por tenant + número de série) com
  grandezas + faixas + incertezas tipadas (VOs em
  `src/domain/metrologia/value_objects.py`).
- Vinculação à cadeia (BIPM, INMETRO, RBC, INTERNACIONAL) + validade do
  cert externo.
- Fluxo **recal externo**: envio ao lab credenciado → recebimento do novo
  cert → atualização de `incertezas_certificado` +
  `validade_certificado_rastreabilidade` (transacional com evento
  `padrao.recal_externo_concluido`).
- **Verificação intermediária** (cl. 6.4.10) entre recals externos —
  INV-022 + INV-CAL-VI-001.
- **Intercomparação / PT** (perfil A — INV-023) com resultado registrado.
- **Cartas controle Shewhart** (perfil A — US-PAD-008) com pontos +
  limites estatísticos.
- **Equipamentos auxiliares cl. 6.4.5** (US-PAD-007) — cadastro mínimo +
  calibração + VI.
- **Baixa / sucatamento** (estado terminal) preservando histórico WORM.
- **Exportação dossiê CGCRE** (Wave B+ — gera PDF/A com cadeia completa
  para supervisão).
- Estado: `EM_USO` / `EM_RECAL_EXTERNO` / `INTERCOMPARACAO_PT_EM_CURSO`
  / `BAIXADO` / `SUCATEADO`.

## 6. Não-objetivos

- NÃO calibra outro padrão (lab interno calibrando padrão do próprio lab —
  caso "calibração interna" exige ADR adicional Wave B+).
- NÃO trata padrão emprestado/alugado (Wave B+).
- NÃO emite cert (cert é Marco 4 calibração + módulo `certificados`).
- NÃO modela equipamento do cliente (módulo `equipamentos`).
- NÃO entrega exportação PDF/A dossiê CGCRE no Wave A (gera dados
  estruturados; PDF/A é Wave B+).
- NÃO entrega scanner de padrão por QR (padrão fica fisicamente no lab —
  não circula).
- NÃO substitui sistema de gestão da qualidade ISO 9001.

## 7. User Stories

### US-PAD-001 — Cadastrar padrão metrológico

**Como** gestor de qualidade, **quero** cadastrar um padrão com cert
externo, **para** começar a usá-lo em calibrações.

- **AC-PAD-001-1**: GIVEN tenant ativo + gestor de qualidade autenticado,
  WHEN preencho NS + fabricante + modelo + ≥1 grandeza + ≥1 faixa + ≥1
  incerteza + vinculacao + cert externo PDF + validade, THEN
  `PadraoMetrologico` salvo com `estado=EM_USO`; evento `padrao.cadastrado`
  publicado em hash-chain HMAC ADR-0064.
- **AC-PAD-001-2**: GIVEN tento cadastrar sem incerteza OU sem valor
  convencional no cert externo, THEN sistema retorna 422 citando
  NIT-DICLA-030 item 8.2.6 (INV-014 reusado / INV-PAD-002).
- **AC-PAD-001-3**: GIVEN preencho `vinculacao=RBC`, WHEN
  `tenant_perfil_e(["A"])` retorna FALSE (perfil B/C/D), THEN sistema
  retorna 422 com mensagem "padrão RBC exige tenant perfil A acreditado
  CGCRE" (INV-015 + INV-PAD-005 + ADR-0067 §"Decisão" item 4).
- **AC-PAD-001-4**: GIVEN tento cadastrar NS já existente no mesmo tenant,
  THEN sistema retorna 409 `PadraoDuplicado`.

**Invariantes:** INV-021, INV-PAD-001, INV-PAD-002, INV-PAD-005,
INV-TENANT-001.

### US-PAD-002 — Registrar recal externo (envio + retorno)

**Como** gestor de qualidade, **quero** registrar envio do padrão ao lab
externo e a chegada do novo cert, **para** manter cadeia de
rastreabilidade.

- **AC-PAD-002-1**: GIVEN padrão `EM_USO`, WHEN registro envio ao lab
  externo com data + lab destinatário + responsável envio, THEN
  `estado=EM_RECAL_EXTERNO`; evento `padrao.recal_externo_iniciado`.
- **AC-PAD-002-2**: GIVEN padrão `EM_RECAL_EXTERNO`, WHEN registro retorno
  com novo cert externo PDF + nova incerteza + nova validade + data recal,
  THEN `incertezas_certificado` + `validade_certificado_rastreabilidade`
  atualizados em transação atômica; evento `padrao.recal_externo_concluido`;
  `estado=EM_USO`; hash-chain HMAC ADR-0064 emendado.
- **AC-PAD-002-3**: GIVEN padrão em recal há > 90 dias sem retorno, THEN
  alerta P2 no painel-do-dono ("padrão pendente de retorno").
- **AC-PAD-002-4**: GIVEN tento UPDATE direto em `incertezas_certificado`
  SEM passar pelo fluxo de `padrao.recal_externo_concluido`, THEN trigger
  PG bloqueia (INV-PAD-006).

**Invariantes:** INV-021, INV-PAD-006, INV-CAL-RAST-001, INV-HMAC-001..005.

### US-PAD-003 — Verificação intermediária periódica

**Como** metrologista, **quero** registrar verificação intermediária (entre
recals externos), **para** detectar drift antes do recal seguinte.

- **AC-PAD-003-1**: GIVEN padrão `EM_USO`, WHEN registro VI com resultado
  (aprovado/reprovado) + método + responsável + data, THEN
  `VerificacaoIntermediaria` criada; evento
  `padrao.verificacao_intermediaria_registrada`.
- **AC-PAD-003-2**: GIVEN VI reprovada, WHEN salva, THEN a porta
  `padrao_bloqueado_para_uso` passa a bloquear o padrão para uso em calibração
  (**bloqueio lógico**, análogo à carta de controle AC-PAD-008 — NÃO há transição
  automática de estado) até nova VI aprovada; o RT decide o encaminhamento
  (recal externo / baixa) explicitamente (INV-CAL-VI-001 / INV-PAD-003).
  *(Emendado 2026-05-29 — PROD-PAD-04: alinha o AC ao comportamento real do
  código, que faz bloqueio lógico via porta, não state-machine.)*
- **AC-PAD-003-3**: GIVEN classe E1/E2/F1/F2 + sem VI nos últimos N meses
  (configurável por classe), THEN alerta P2 + dashboard marca padrão como
  "VI pendente".

**Invariantes:** INV-022, INV-CAL-VI-001.

### US-PAD-004 — Baixar / sucatar padrão (terminal)

**Como** gestor de qualidade, **quero** baixar padrão (fim de vida útil ou
perda), **para** removê-lo do pool ativo.

- **AC-PAD-004-1**: GIVEN padrão `EM_USO` sem calibração em curso usando
  ele, WHEN baixo com motivo (≥30 chars) + tipo (`fim_vida_util` /
  `extraviado` / `danificado_irrecuperavel` / `vendido`) + assinatura A3
  do RT (ADR-0022 v2 + ADR-0068), THEN `estado=BAIXADO` (não terminal —
  pode reaparecer) ou `SUCATEADO` (terminal); `revogado_em` +
  `motivo_revogacao` preenchidos (ADR-0030 + INV-SOFT-002).
- **AC-PAD-004-2**: GIVEN há calibração em curso usando padrão, THEN
  bloqueia baixa com mensagem citando IDs de calibração.
- **AC-PAD-004-3**: GIVEN tento DELETE direto, THEN trigger PG bloqueia
  (INV-SOFT-002 padrão B WORM).

**Invariantes:** INV-PAD-003, INV-SOFT-002, INV-VIG-002, INV-017.

### US-PAD-005 — Intercomparação (PT) em perfil A

**Como** gestor de qualidade de tenant em perfil A, **quero** registrar
participação em comparação interlaboratorial, **para** atender INV-023
(cl. 6.6 + ISO/IEC 17043).

- **AC-PAD-005-1**: GIVEN `tenant_perfil_e(["A"])` retorna TRUE + padrão
  `EM_USO`, WHEN registro participação em PT com lab organizador +
  protocolo + data início, THEN `estado=INTERCOMPARACAO_PT_EM_CURSO`;
  evento `padrao.intercomparacao_iniciada`.
- **AC-PAD-005-2**: GIVEN PT em curso, WHEN registro resultado
  (aprovado/rejeitado/sob_revisao) + relatório PT + zeta-score, THEN
  evento `padrao.intercomparacao_concluida`; padrão volta a `EM_USO`.
- **AC-PAD-005-3**: GIVEN resultado rejeitado, THEN bloqueia uso do
  padrão até NC ser tratada (INV-012 + INV-CAL-WORM-001).
- **AC-PAD-005-4**: GIVEN `tenant_perfil_e(["A"])` retorna FALSE, WHEN
  gestor tenta abrir tela US-PAD-005, THEN UI esconde + endpoint retorna
  403 `RecursoExclusivoPerfilA`.

**Invariantes:** INV-023, INV-PERFIL-001 (ADR-0067).

### US-PAD-006 — Exportar dossiê CGCRE (Wave A — dados; PDF Wave B+)

**Como** gestor de qualidade preparando supervisão CGCRE, **quero**
exportar dossiê com cadeia metrológica completa, **para** entregar ao
supervisor.

- **AC-PAD-006-1 (Wave A)**: GIVEN `tenant_perfil_e(["A"])` retorna TRUE +
  padrão `EM_USO`, WHEN clico "exportar dossiê", THEN sistema gera JSON
  estruturado com toda cadeia (cert externo histórico + VIs + PTs + cartas
  Shewhart + uso em calibrações) + hash-chain HMAC ADR-0064 incluído.
- **AC-PAD-006-2 (Wave B+)**: PDF/A com selo CGCRE + assinatura A3 do RT
  + TSA-ITI PAdES-LTV (ADR-0047).

**Invariantes:** INV-CAL-WORM-001, INV-HMAC-001..005.

### US-PAD-007 — Equipamentos auxiliares cl. 6.4.5 (gap crítico L3#7)

**Como** gestor de qualidade, **quero** cadastrar e controlar
equipamentos auxiliares do laboratório (termo-higrômetro de sala, fonte
de tensão estável, banho termostático), **para** atender ISO 17025
cl. 6.4.5 (equipamentos auxiliares também precisam estar em controle
metrológico).

- **AC-PAD-007-1**: GIVEN gestor autenticado, WHEN cadastra equipamento
  auxiliar (categoria `AUXILIAR_AMBIENTAL` / `AUXILIAR_ELETRICO` /
  `AUXILIAR_TERMOMETRICO`) + NS + fabricante + modelo + faixa de uso +
  validade da calibração interna, THEN registro persistido como
  `PadraoMetrologico.subtipo=AUXILIAR`.
- **AC-PAD-007-2**: GIVEN equipamento auxiliar com calibração vencida,
  WHEN sistema valida pré-calibração de algum padrão principal que
  consome esse auxiliar (ex: VI de peso padrão na sala usa
  termo-higrômetro), THEN bloqueia execução até auxiliar dentro da
  validade (INV-PAD-007 nova).
- **AC-PAD-007-3**: GIVEN tenant `perfil_regulatorio = A`, WHEN supervisão
  CGCRE consulta dossiê, THEN equipamentos auxiliares aparecem listados
  com vínculo aos padrões principais que dependem deles (cadeia
  documental cl. 6.4.5).
- **AC-PAD-007-4**: GIVEN `subtipo=AUXILIAR`, WHEN sistema cria, THEN
  fluxo de recal externo opcional (auxiliar pode ter calibração interna);
  porém VI obrigatória nos **seus próprios intervalos** — `intervalo_recal_meses`
  e `intervalo_vi_meses` configuráveis por equipamento auxiliar com
  `criterio_intervalo` justificado (cl. 6.4.7 + ILAC-G24), NÃO herdados do
  padrão principal. O vínculo principal↔auxiliar é modelado como entidade
  temporal N:N `VinculoAuxiliar` (ADR-0030) com a grandeza de influência
  (temperatura/umidade/pressão); a leitura ambiental do auxiliar compõe o
  `PadraoUsadoSnapshot` na seleção pela calibração M4 (plan §14 C-8 + C-9).
- **AC-PAD-007-5**: GIVEN padrão principal com `VinculoAuxiliar` vigente cujo
  auxiliar está com calibração/rastreabilidade vencida (ou fora de `EM_USO` /
  VI REPROVADA), WHEN o M4 consulta a porta `padrao_bloqueado_para_uso` antes
  de gravar `PadraoUsado`, THEN o principal é bloqueado (fail-CLOSED) — auxiliar
  vencido contamina o balanço de incerteza (INV-PAD-007 cl. 6.4.5).

**Invariantes:** INV-PAD-007 (nova — auxiliar em controle antes de uso),
INV-021, INV-TENANT-001.

### US-PAD-008 — Cartas controle Shewhart por padrão (perfil A — L3#A9 adiantado Wave A)

**Como** gestor de qualidade de tenant em perfil A, **quero** plotar
cartas controle estatístico (Shewhart) por padrão a partir das VIs e
recals, **para** detectar drift / shift / runs / trends antes da
supervisão CGCRE (perfil A exige desde a 1ª supervisão — L3#A9).

- **AC-PAD-008-1**: GIVEN `tenant_perfil_e(["A"])` retorna TRUE + padrão
  com ≥ 10 pontos de VI/recal nos últimos 24 meses, WHEN gestor abre tela
  "Carta Controle", THEN sistema plota carta Shewhart com linha central
  (média móvel) + UCL/LCL (±3σ) + zona de alerta (±2σ) + pontos
  observados.
- **AC-PAD-008-2**: GIVEN regra Western Electric detectada pelo motor
  versionado (`versao_motor_shewhart`) — (R1) 1 ponto fora ±3σ; (R2) 2 de 3
  pontos consecutivos fora ±2σ **do mesmo lado** da média; (R3) 4 de 5 pontos
  consecutivos fora ±1σ **do mesmo lado** da média; (R4) 8 pontos sequenciais
  do mesmo lado da média; (R5 — tendência) 7 pontos consecutivos monotonicamente
  crescentes ou decrescentes (detecta deriva — Dor #04), WHEN próxima VI
  registrada, THEN sistema dispara alerta P1 + grava registro WORM
  `AnaliseCartaControle` congelando os limites vigentes no instante (LC/UCL/LCL/σ
  + `versao_motor_shewhart`) + bloqueia uso do padrão até o RT registrar
  `decisao_rt` (ACEITO_COM_JUSTIFICATIVA / RECALIBRAR / SUSPENDER_USO) com
  justificativa canonicalizada ADR-0029 (INV-PAD-010 + ADR-0070).
- **AC-PAD-008-2b**: GIVEN estado de alerta/tendência detectado (R2, R3 ou R5),
  mesmo sem violação dura de ±3σ, THEN também exige `AnaliseCartaControle` WORM
  registrada (decisao_rt = ACEITO_COM_JUSTIFICATIVA no mínimo) antes de liberar
  uso continuado do padrão (corretora FURO-3 / C-16 + ADR-0070 §Decisão item 3).
- **AC-PAD-008-3**: GIVEN carta controle, WHEN export pra dossiê CGCRE
  (US-PAD-006), THEN imagem PNG + dados CSV incluídos.
- **AC-PAD-008-4**: GIVEN tenant `perfil_regulatorio != A`, WHEN abre
  tela US-PAD-008, THEN UI mostra "Feature exclusiva perfil A
  acreditado" + link de promoção para perfil A.

**Invariantes:** INV-PAD-008 (nova — perfil A obrigatório), INV-PERFIL-001.

### US-PAD-009 — Verificação de software por 2 implementações independentes do mesmo mensurando (cl. 7.11 — ADR-0071)

**Como** RT do tenant em perfil A ou B, **quero** que o valor convencional do
padrão seja calculado por **duas implementações independentes do MESMO modelo
metrológico** (mesmo mensurando) que devem convergir, **para** provar ausência
de bug de software de cálculo (ISO 17025 cl. 7.11 — ADR-0071 que refina
ADR-0025 v2).

- **AC-PAD-009-1**: GIVEN padrão `EM_USO` com ≥ 2 recals externos no
  histórico, WHEN sistema calcula o valor convencional, THEN executa o mesmo
  modelo metrológico por 2 implementações independentes (Caminho A = média
  ponderada pela inversa da variância em forma fechada; Caminho B = mesma média
  via pesos normalizados) que estimam o **mesmo mensurando** e devem convergir
  dentro da tolerância relativa `1e-30` (Decimal prec=50).
- **AC-PAD-009-2**: GIVEN divergência entre as 2 implementações do mesmo
  mensurando acima da tolerância numérica, THEN trata-se de **bug de software**
  (não investigação metrológica): levanta `DivergenciaImplementacoesError` e
  bloqueia o cálculo/release (INV-PAD-009 — ADR-0071). NOTA: detecção de
  **deriva/tendência** NÃO entra aqui — é controle de estabilidade e fica em
  US-PAD-008 (carta Shewhart, regra de tendência R5).
- **AC-PAD-009-3**: GIVEN o cálculo da incerteza expandida do valor
  convencional, WHEN os graus de liberdade efetivos `ν_eff` < 30, THEN o fator
  de abrangência `k` é calculado via **Welch-Satterthwaite + t-Student**
  (JCGM 100 Anexo G), não `k=2` fixo (ADR-0071 item 3).
- **AC-PAD-009-4**: GIVEN tenant `perfil_regulatorio = A`, WHEN dossiê
  CGCRE exportado, THEN a verificação por 2 implementações (resultado de
  convergência + `versao_motor`) aparece documentada (cadeia ADR-0025 v2
  cl. 7.11.3).

**Invariantes:** INV-PAD-009 (redefinida ADR-0071 — divergência entre as 2
implementações do mesmo mensurando bloqueia release como bug de software,
distinta de controle de deriva), INV-VAL-001 (ADR-0025 v2).

## 8. Bases legais LGPD (art. 7º)

| Finalidade | Base legal | Justificativa |
|---|---|---|
| Cadastro de padrão | art. 7º II | Obrigação regulatória ISO 17025 cl. 6.5 |
| Recal externo (cert externo PDF) | art. 7º II | Obrigação regulatória |
| Verificação intermediária | art. 7º II | Obrigação regulatória cl. 6.4.10 |
| Intercomparação PT | art. 7º II | Obrigação regulatória cl. 6.6 |
| Cartas controle Shewhart | art. 7º II | Obrigação regulatória cl. 7.7 |
| Equipamentos auxiliares | art. 7º II | Obrigação regulatória cl. 6.4.5 |
| Dossiê CGCRE | art. 7º II | Supervisão regulatória |
| Executor/responsável de VI/PT/recal (dado funcional) | art. 7º II + art. 7º V | Compõe registro técnico ISO 17025 (II) + relação operacional (V) |

> **Emenda v2 (2026-05-28 — revisão `advogado-saas-regulado` C-13/C-14):**
>
> Os **campos estruturados** do padrão (NS, faixa, incerteza, classe) não contêm
> PII — é instrumento físico. MAS dois cuidados:
>
> 1. **Dado do funcionário (executor/responsável):** no EVENTO WORM vai só hash
>    (HMAC-tenant — ADR-0064). No registro operacional quente o `user_id` segue a
>    retenção do cadastro (5 anos). PORÉM o **nome desnormalizado que compõe a
>    evidência técnica de VI/PT/recal herda 25 anos** (cl. 8.4), com anonimização
>    de CPF e preservação do nome — replica o **Cenário A** da matriz de retenção
>    (igual ao signatário de certificado em M4 / DRILL-RET-07). Direito do titular
>    (art. 18): recusa parcial fundamentada (art. 16 I).
> 2. **PDF do cert externo (`cert_externo_storage_key`):** PODE conter **PII de
>    terceiro** (assinatura/nome/CPF do signatário do lab acreditado). Tratado
>    como documento **cifrado pela chave KMS do tenant** (crypto-shredding no
>    offboarding), base art. 7º II + art. 16 I; **sem tentar anonimizar o binário
>    probatório**. NÃO é "dado sem PII". O evento só guarda hash; o binário em B2
>    é cifrado (confirmar com tech-lead na implementação).
>
> Pendente /implement: linha na matriz de retenção `docs/conformidade/comum/retencao-matriz.md`
> ("Executor/responsável de evento de padrão") + drill análogo DRILL-RET-07.
> Redação DPA sobre PII de terceiro embarcada → lote revisão OAB pré-produção.

## 9. Métricas (ver `metricas.md`)

- % padrões em uso com cert externo dentro da validade ≥ 100% (em A)
- % padrões com VI dentro do prazo declarado ≥ 95% (em A)
- Tempo médio recal externo (envio → retorno) ≤ 60 dias
- % padrões em A com PT ativo no ciclo declarado ≥ 100%
- **% padrões em A com carta controle Shewhart ativa ≥ 100%** (nova — L3#A9)
- **% equipamentos auxiliares com calibração vigente = 100%** (nova — L3#7)
- Zero divergências não resolvidas entre as 2 implementações do mesmo mensurando (bug de software, cl. 7.11 — US-PAD-009/ADR-0071)

## 10. NFR

- Performance: listagem de padrões p95 ≤ 1.0s; plot carta Shewhart p95
  ≤ 2.0s para 24 meses de pontos.
- Segurança: padrão é "do tenant"; RLS por `tenant_id` obrigatório
  (ADR-0002); evento `padrao.*` em hash-chain HMAC ADR-0064.
- Auditoria: WORM em VI + PT + recal + cartas Shewhart (INV-CAL-WORM-001
  estendido).
- Acessibilidade: WCAG 2.1 AA (ADR-0057).

## 11. ADRs e INVs aplicáveis

- **ADRs:** 0002 (RLS), 0007 (codegen), 0022 v2 (RT competência por método),
  0025 v2 (validação software estendida ao módulo padrões — URS/IQ/OQ/PQ +
  2º caminho de cálculo), 0030 (vigência canônica), 0031 (soft-delete
  padrão B), 0040 (padrão como entidade separada), 0064 (HMAC 25a),
  0066 (fail-open lazy), 0067 (perfil), 0068 (sucessão RT),
  **0070 (carta Shewhart híbrida read-model + WORM `AnaliseCartaControle`),
  0071 (2º caminho = 2 implementações do mesmo mensurando cl. 7.11 +
  Welch-Satterthwaite), 0072 (path infra metrologia aninhado)**.
- **INVs:** INV-021..023, INV-PAD-001..010, INV-CAL-SNAP-001,
  INV-CAL-RAST-001, INV-CAL-VI-001, INV-CAL-WORM-001, INV-VIG-001..004,
  INV-SOFT-001/002, INV-HMAC-001..005, INV-PERFIL-001, INV-VAL-001.

## 12. Glossário e referências

- **CMC** — Capacidade de Medição e Calibração; o que o lab pode oferecer
  com selo RBC (ver `metrologia/escopos-cmc` Wave A).
- **Rastreabilidade ao SI** — cadeia documentada até INMETRO/BIPM
  (cl. 6.5).
- **U (Uncertainty)** — incerteza expandida (GUM) — coverage factor k=2.
- **Faixa** — intervalo `[min, max]` em uma grandeza para o qual o
  padrão é válido.
- **Método** — procedimento técnico aplicado (ex: comparação direta /
  substituição / curva de calibração).
- **Carta Shewhart** — controle estatístico **híbrido** (ADR-0070): gráfico
  read-model on-demand (linha central + UCL/LCL ±3σ + zona alerta ±2σ) + as 5
  regras Western Electric (R1 fora 3σ / R2 2-de-3 2σ mesmo lado / R3 4-de-5 1σ
  mesmo lado / R4 run-8 / R5 tendência-7). A **decisão do RT** sobre regra
  disparada é congelada num registro WORM `AnaliseCartaControle` (INV-PAD-010).
- **PT (Proficiency Testing)** — ISO/IEC 17043 — comparação
  interlaboratorial.
- **Equipamento auxiliar** — instrumento que apoia a calibração mas não
  é o padrão principal (cl. 6.4.5).
- `modelo-de-dominio.md` — entidades, agregados, portas, eventos.
- VOs metrológicos: `src/domain/metrologia/value_objects.py`.
- `docs/conformidade/comum/retencao-matriz.md` — padrão é registro
  ISO 17025 cl. 8.4 (25 anos).
- Glossário metrologia: `../glossario.md`.

## 13. Como este PRD evolui

- US nova → próximo `US-PAD-NNN`.
- Mudança em AC implementado → ADR + novo teste de regressão.
- Mudança no schema → ADR + migration.
