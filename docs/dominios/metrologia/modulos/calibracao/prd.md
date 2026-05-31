---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md
  - docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md
  - docs/dominios/metrologia/modulos/calibracao/politica-verificacao-intermediaria.md
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - docs/dominios/metrologia/modulos/procedimentos/prd.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0044-exportacao-regulatoria-anvisa-saude.md
  - docs/adr/0045-certificado-recall-suspensao-errata.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
  - docs/adr/0065-concorrencia-calibracao-metrologica.md
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/plan.md
fase-ritual: P3-aprovada (2026-05-25 — §11 absorve ACs novos do P3 M4)
---

# PRD — Módulo Laboratório de Calibração e Metrologia

> Núcleo do diferencial competitivo do "Aferê": execução técnica de calibração metrológica conforme ISO 17025, com rastreabilidade, controle de padrões, cálculo de incerteza e revisão técnica. Disputa direta com Calibre.Software.

---

## 1. O que este módulo é

Plataforma de execução de calibração metrológica em laboratório acreditado: entrada do instrumento, identificação por QR Code, configuração da calibração, seleção dos padrões utilizados, registro das leituras, cálculo automático de erro e incerteza (orçamento por componente), avaliação de conformidade, revisão técnica + segunda conferência, decisão final (aprovado/reprovado/condicional) e disparo para o módulo Certificados emitir o documento final.

Cobre também a infraestrutura metrológica: controle de pesos padrão, classes, calibração externa dos padrões, verificação intermediária, ensaios (linearidade, repetibilidade, excentricidade), comparação interlaboratorial, ensaio de proficiência, escopo de acreditação e controle de capacidade de medição e calibração (CMC).

## 2. Por que este módulo existe (problema a resolver)

Mystery shopping da Calibre.Software (concorrente) mostra cálculo de incerteza opaco, planilhas externas Excel acopladas e revisão técnica como afterthought. Nosso diferencial: execução nativa no sistema, incerteza calculada com auditoria do orçamento por componente, segunda conferência obrigatória, rastreabilidade metrológica até padrão nacional, e bloqueio operacional se escopo/CMC não cobrir a calibração solicitada.

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Entrada do instrumento no laboratório (recepção, registro, etiqueta interna).
- Identificação por QR Code (etiqueta interna do lab).
- Configuração da calibração (grandeza, faixa, pontos a calibrar, método).
- Seleção dos padrões utilizados (com validação de vigência do certificado do padrão).
- Registro das leituras (manual ou via integração com instrumento padrão).
- Cálculo automático de erro.
- Cálculo de incerteza (GUM + Suplemento 1 quando aplicável).
- Orçamento de incerteza por componente (tabela rastreável).
- Avaliação de conformidade (regra de decisão configurável — ILAC G8).
- Revisão técnica (1ª conferência).
- Segunda conferência (independente, por RT diferente quando possível).
- Decisão: aprovado, reprovado, condicional.
- Disparo de emissão para módulo Certificados.
- Reemissão controlada (cita módulo Certificados).
- Controle de validade interna do registro de calibração (≠ validade do certificado).
- Histórico de calibrações por instrumento.
- Controle de pesos padrão (cadastro, classe, validade, localização).
- Calibração externa dos padrões (registro do ciclo de envio + recebimento).
- Verificação intermediária (entre calibrações externas).
- Rastreabilidade metrológica documentada (cadeia até padrão nacional/INMETRO).
- Ensaios de linearidade, repetibilidade, excentricidade.
- Comparação interlaboratorial (registro de participação + resultados).
- Ensaio de proficiência (registro de participação + escore).
- Escopo de acreditação (catálogo do que o lab pode calibrar com selo RBC).
- Controle de faixas de medição.
- Controle de Capacidade de Medição e Calibração (CMC) por grandeza/faixa.

## 5. Non-goals (o que NÃO está neste módulo)

- NÃO emite o certificado PDF — isso é módulo **Certificados** (US-CER-001).
- NÃO emite NF-e — módulo **Fiscal**.
- NÃO gerencia acreditação CGCRE da empresa — módulo **Licenças e Acreditações** (US-LIC-001/003).
- NÃO substitui sistema de gestão da qualidade ISO 9001 — apenas atende 17025.
- NÃO faz manutenção do instrumento — módulo **Ordens de Serviço** (mas pode disparar OS de manutenção quando reprovado).
- NÃO substitui planilha Excel pra cálculos exploratórios em P&D — é produção.

## 6. User Stories

### US-CAL-001: Recepcionar instrumento no laboratório

**Como** recepcionista do lab, **quero** registrar entrada do instrumento com cliente, descrição, série, fabricante e gerar etiqueta interna com QR Code, **para** iniciar o fluxo de calibração rastreável.

**Critérios de aceite:**
- **AC-CAL-001-1**: GIVEN **atividade de OS tipo=calibracao** (ADR-0023) OU recepção avulsa, WHEN registra entrada (cliente, instrumento, condições recebidas), THEN sistema gera etiqueta interna PDF com QR Code apontando ao registro de calibração. Quando origem = atividade de OS, o registro de calibração é vinculado via `link_modulo_tecnico` da atividade — permite OS combinada (manutenção + calibração) com a calibração só iniciando após manutenção concluída.
<!-- prd-ux-states: skip -- emenda pontual M6 (ADR-0073/0074) em AC do PRD M4; secao UX estados nao-felizes e debito proprio do M4 calibracao, rastreado a parte -->
- **AC-CAL-001-2**: GIVEN escopo de acreditação NÃO cobre o instrumento, WHEN tenta cadastrar como calibração RBC, THEN sistema avisa e permite seguir como NÃO-RBC. **ADR-0073/0074 (M6 escopos-cmc — 2026-05-30, substitui o fail-open lazy da ADR-0066)**: validação REAL na **configuração** via porta `escopos_cmc.query_service.cobre()` (o predicate STUB `cmc_cobre` da ADR-0066 está deprecado/no-op). Grandeza+faixa server-side (não payload — SEG-CAL-10), via `Calibracao.faixa_calibrada_declarada` (frente SAN-FAIXA-CALIBRADA). Recepção = aviso degradante NÃO-RBC; configuração = bloqueio (ver AC-CAL-002-2). Terminologia ADR-0075: só perfil A é "escopo RBC acreditado"; B/C/D é "capacidade interna declarada".

**Invariantes:** `INV-TENANT-001`, `INV-CAL-WORM-001`.

---

### US-CAL-002: Configurar calibração

**Como** metrologista, **quero** configurar a calibração (grandeza, faixa, pontos, método, condições ambientais alvo), **para** padronizar a execução.

**Critérios de aceite:**
- **AC-CAL-002-1**: GIVEN configuração nova, WHEN seleciona grandeza+faixa, THEN sistema oferece métodos disponíveis (NIT-DICLA / norma técnica) e padrões compatíveis.
<!-- prd-ux-states: skip -- emenda pontual M6 (ADR-0073/0074) em AC do PRD M4; secao UX estados nao-felizes e debito proprio do M4 calibracao, rastreado a parte -->
- **AC-CAL-002-2**: GIVEN faixa fora do escopo CMC, WHEN tenta salvar como RBC, THEN sistema bloqueia citando CMC oficial. **ADR-0073/0074 (M6 escopos-cmc — 2026-05-30)**: bloqueio 412 `EscopoNaoCobreFaixa` REAL na configuração via `escopos_cmc.query_service.cobre()` — contenção total da faixa (INV-ECMC-005), só perfil A. `GATE-CAL-CMC-PREDICATE` (portão de configuração) **FECHADO** pela frente SAN-FAIXA-CALIBRADA + Fatia 3. A 2ª condição U≥CMC na emissão (INV-ECMC-009 / porta `cmc_para()`) fica em `GATE-ECMC-U-MAIOR-CMC` (módulo `certificados` Wave A).

**Invariantes:** `INV-002` (escopo CMC), `INV-CAL-WORM-001`.

---

### US-CAL-003: Selecionar padrões com vigência válida

**Como** metrologista, **quero** selecionar padrões e o sistema validar vigência do certificado de cada padrão, **para** garantir rastreabilidade.

**Critérios de aceite:**
- **AC-CAL-003-1**: GIVEN padrão com certificado externo vencido, WHEN tenta selecionar, THEN sistema bloqueia.
- **AC-CAL-003-2**: GIVEN padrão dentro da verificação intermediária programada, WHEN sistema verifica, THEN libera.
- **AC-CAL-003-3**: GIVEN seleção concluída, WHEN salva, THEN snapshot de cada padrão (cert, validade, classe) fica anexo à calibração.

**Invariantes:** `INV-003` (rastreabilidade padrão), `INV-CAL-SNAP-001` (snapshot padrão externo), `INV-CAL-WORM-001`.

---

### US-CAL-004: Registrar leituras (manual ou integrada)

**Como** metrologista, **quero** registrar as leituras dos pontos calibrados (manual ou via integração com instrumento padrão), **para** ter dados primários da calibração.

**Critérios de aceite:**
- **AC-CAL-004-1**: GIVEN configuração com N pontos × M repetições, WHEN registra leituras, THEN sistema valida formato/unidade e armazena com timestamp.
- **AC-CAL-004-2**: GIVEN integração com balança/padrão via serial/USB, WHEN equipamento envia leitura, THEN sistema persiste automaticamente.
- **AC-CAL-004-3**: GIVEN leitura fora de faixa esperada, WHEN sistema detecta, THEN alerta metrologista mas NÃO bloqueia (decisão dele).

**Invariantes:** `INV-CAL-WORM-001`.

---

### US-CAL-005: Calcular erro e incerteza com orçamento por componente

**Como** metrologista, **quero** que o sistema calcule erro + incerteza expandida (k=2) com tabela de orçamento por componente, **para** ter resultado auditável conforme GUM.

**Critérios de aceite:**
- **AC-CAL-005-1**: GIVEN leituras + padrões + condições ambientais, WHEN sistema calcula, THEN gera tabela orçamento (componente, tipo A/B, distribuição, divisor, contribuição, grau de liberdade), combina pelo método RSS, expande com k=2 (95.45%) e mostra resultado final.
- **AC-CAL-005-2**: GIVEN cálculo executado, WHEN metrologista revisa, THEN cada componente do orçamento é editável (Tipo B vem de defaults configuráveis por padrão+grandeza).
- **AC-CAL-005-3**: GIVEN versão do algoritmo, WHEN calibração executada, THEN sistema salva versão do motor de cálculo no snapshot (validação de software ISO 17025 7.11).

**Invariantes:** `INV-004` (cálculo GUM), `INV-CAL-VERSAO-001` (versão software registrada), `INV-CAL-WORM-001`. Ver `validacao-software.md`.

---

### US-CAL-006: Avaliar conformidade com regra de decisão

**Como** metrologista, **quero** avaliar conformidade (atende/não atende especificação) considerando incerteza e regra de decisão configurada, **para** atender ISO 17025 7.8.6.

**Critérios de aceite:**
- **AC-CAL-006-1**: GIVEN especificação cliente + resultado + incerteza, WHEN sistema avalia com regra de decisão (Aceitação Simples / Banda de Guarda 30% / Risco Compartilhado), THEN classifica como CONFORME, NÃO CONFORME ou ZONA DE INCERTEZA.
- **AC-CAL-006-2**: GIVEN ZONA DE INCERTEZA, WHEN sistema mostra, THEN exige decisão explícita do metrologista (CONFORME COM RESERVA / NÃO CONFORME / NÃO AVALIAR).
- **AC-CAL-006-3**: GIVEN regra de decisão escolhida, WHEN certificado emitido, THEN regra fica documentada no certificado (citar ILAC G8).

**Invariantes:** `INV-CAL-DEC-001` (regra decisão ISO 7.8.6), ADR-0024.

---

### US-CAL-007: Revisão técnica (1ª conferência)

**Como** RT revisor, **quero** revisar a calibração antes de aprovação final, **para** detectar erros antes da emissão.

**Critérios de aceite:**
- **AC-CAL-007-1**: GIVEN calibração com cálculo concluído, WHEN RT abre revisão, THEN sistema mostra tudo (config, padrões, leituras, orçamento incerteza, avaliação) com botões aprovar/rejeitar/solicitar correção.
- **AC-CAL-007-2**: GIVEN rejeição ou correção solicitada, WHEN RT marca, THEN sistema volta calibração ao metrologista com nota.
- **AC-CAL-007-3 (revisado Onda 7D — ALTO-PEND-1 R2):** GIVEN revisor = executor da calibração, WHEN tenta revisar, THEN sistema valida conforme **ADR-0026 + INV-CAL-CONF-001** — exceção só aceita se as 4 condições cumulativas (único RT habilitado ATIVO na grandeza + prazo regulatório ≤7d úteis + tentativa de subcontratar documentada + justificativa ≥100 chars anti-PII) + dentro do limite 5%/mês; senão 412 `Excecao62_5InaceitavelSemCondicoes`.
- **AC-CAL-007-4 (novo Onda 7D — NOVO-MÉD-1 produto R2):** GIVEN consumer subscriber `Atividade.Iniciada(tipo=calibracao)`, WHEN evento entregue, THEN sistema cria `Calibracao` em status RECEPCIONADA + `RecepcaoItemCalibracao` automaticamente + dispara `Calibracao.Recepcionada`.

**Invariantes:** `INV-CAL-RT-001` (RT habilitado por grandeza), `INV-CAL-WORM-001`.

---

### US-CAL-008: Segunda conferência

**Como** RT independente, **quero** fazer segunda conferência da calibração (preferencialmente RT diferente do revisor), **para** atender boas práticas ISO 17025 7.7.

**Critérios de aceite:**
- **AC-CAL-008-1**: GIVEN calibração com 1ª revisão aprovada, WHEN passa pra 2ª conferência, THEN sistema mostra os mesmos dados + nota da 1ª revisão + botão aprovar/rejeitar.
- **AC-CAL-008-2**: GIVEN aprovação da 2ª conferência, WHEN executada, THEN calibração vira APROVADA + libera emissão de certificado.
- **AC-CAL-008-3**: GIVEN único RT disponível executou todas as etapas, WHEN tenta concluir, THEN sistema registra exceção em log de auditoria pra explicação posterior.

**Invariantes:** `INV-CAL-CONF-001` (2ª conferência obrigatória), `INV-CAL-WORM-001`. Ver `garantia-validade-7.7.md`.

---

### US-CAL-009: Histórico de calibrações por instrumento

**Como** RT, **quero** ver histórico de calibrações de um instrumento, **para** detectar drift, repetibilidade entre calibrações.

**Critérios de aceite:**
- **AC-CAL-009-1**: GIVEN instrumento com N calibrações, WHEN consulta histórico, THEN sistema mostra timeline com resultado, incerteza, decisão, certificado emitido.

**Invariantes:** `INV-CAL-WORM-001`, `INV-TENANT-001`.

---

### US-CAL-010: Controle de pesos padrão (catálogo)

**Como** RT, **quero** gerenciar pesos padrão (cadastro, classe E1/E2/F1/F2/M1/M2/M3, valor nominal, valor convencional, validade do certificado, localização física), **para** ter inventário rastreável.

**Critérios de aceite:**
- **AC-CAL-010-1**: GIVEN cadastro de peso padrão, WHEN preenche, THEN exige classe + valor nominal + cert externo + validade + localização.
- **AC-CAL-010-2**: GIVEN peso com cert externo vencido, WHEN aparece em seleção de padrões, THEN marcado como INDISPONÍVEL.

**Invariantes:** `INV-CAL-RAST-001` (rastreabilidade padrão), `INV-CAL-WORM-001`.

---

### US-CAL-011: Registrar calibração externa do padrão

**Como** RT, **quero** registrar envio do padrão pra calibração externa (lab acreditado) e recebimento do certificado, **para** manter rastreabilidade.

**Critérios de aceite:**
- **AC-CAL-011-1**: GIVEN padrão indo pra calibração externa, WHEN registra envio (laboratório destino, data envio, NF/protocolo), THEN sistema marca padrão INDISPONÍVEL.
- **AC-CAL-011-2**: GIVEN recebimento + novo certificado externo, WHEN registra (cert, validade, anexo PDF, valor convencional, incerteza), THEN sistema marca padrão DISPONÍVEL com nova vigência.

**Invariantes:** `INV-CAL-RAST-001`, `INV-CAL-WORM-001`.

---

### US-CAL-012: Verificação intermediária

**Como** RT, **quero** registrar verificações intermediárias do padrão (entre calibrações externas), **para** comprovar estabilidade.

**Critérios de aceite:**
- **AC-CAL-012-1**: GIVEN padrão com programa de verificação intermediária, WHEN data prevista chega, THEN sistema alerta RT.
- **AC-CAL-012-2**: GIVEN verificação executada, WHEN registra resultado, THEN sistema avalia critério de aceitação configurado; se reprovado, padrão fica INDISPONÍVEL + dispara NC.

**Invariantes:** `INV-CAL-VI-001`, `INV-CAL-WORM-001`.

---

### US-CAL-013: Ensaios de linearidade, repetibilidade, excentricidade

**Como** RT, **quero** executar ensaios complementares (linearidade, repetibilidade, excentricidade) integrados ao registro de calibração, **para** atender métodos completos.

**Critérios de aceite:**
- **AC-CAL-013-1**: GIVEN método requer ensaio de linearidade, WHEN seleciona, THEN sistema gera template de pontos + calcula desvios + r².
- **AC-CAL-013-2**: GIVEN repetibilidade, WHEN executa N medições no mesmo ponto, THEN sistema calcula desvio padrão experimental + Tipo A.
- **AC-CAL-013-3**: GIVEN excentricidade (balanças), WHEN executa nas 4 posições + centro, THEN sistema calcula maior diferença vs ponto central.

**Invariantes:** `INV-CAL-WORM-001`.

---

### US-CAL-014: Comparação interlaboratorial / ensaio de proficiência

**Como** RT/gestor qualidade, **quero** registrar participação em comparação interlaboratorial e ensaios de proficiência, **para** evidenciar competência (ISO 17025 7.7.2).

**Critérios de aceite:**
- **AC-CAL-014-1**: GIVEN participação programada, WHEN registra (provedor, rodada, grandeza, faixa), THEN sistema cria registro pendente.
- **AC-CAL-014-2**: GIVEN resultado recebido (escore z, status PASSED/UNACCEPTABLE), WHEN registra, THEN sistema anexa relatório + se UNACCEPTABLE dispara NC.
- **AC-CAL-014-3 (novo Onda 7 — M2-CAL):** GIVEN resultado UNACCEPTABLE, WHEN registrado, THEN sistema **dispara análise de impacto retroativo** automaticamente: cria entidade `AnaliseImpactoNCProficiência(rodada_id, certs_no_periodo[], decisao)` listando todos os cert emitidos pela grandeza/faixa da rodada no intervalo da última PT PASSED→atual; gestor qualidade decide por cert se Recall (ADR-0045) / Suspensão / Sem impacto; decisão é audit-trail obrigatório.

**Invariantes:** `INV-CAL-WORM-001`, `INV-CAL-NC-PT-001` (análise de impacto retroativo obrigatória em UNACCEPTABLE), ISO 17025 7.7.2.

---

### US-CAL-015: Escopo de acreditação + CMC

**Como** admin tenant, **quero** cadastrar escopo de acreditação CGCRE + CMC por grandeza/faixa, **para** o sistema bloquear emissões fora do escopo RBC.

**Critérios de aceite:**
<!-- prd-ux-states: skip -- emenda pontual M6 (ADR-0073/0074) em AC do PRD M4; secao UX estados nao-felizes e debito proprio do M4 calibracao, rastreado a parte -->
- **AC-CAL-015-1**: GIVEN escopo cadastrado (grandeza, faixa min/max, CMC, método), WHEN calibração configurada, THEN sistema valida se cobre. **ADR-0073/0074 (M6 escopos-cmc — 2026-05-30)**: validação REAL via porta `escopos_cmc.query_service.cobre()` (módulo entregue — escopo é entidade Django persistida, não mais o STUB fail-open). Versionamento do escopo preservado (AC-CAL-015-2 / INV-ECMC-003).
<!-- prd-ux-states: skip -- emenda pontual M6 (ADR-0073) em AC do PRD M4; secao UX estados nao-felizes e debito proprio do M4 calibracao, rastreado a parte -->
- **AC-CAL-015-2**: GIVEN renovação/revisão do escopo CGCRE, WHEN admin atualiza, THEN versão anterior preservada com janela de calibrações antigas. **M6 escopos-cmc (2026-05-30)**: `revisar_escopo` = INSERT de nova `versao` preservando a anterior (WORM Padrão B — INV-ECMC-003); escopo CONFIRMADO é imutável exceto revogação one-shot.

**Invariantes:** `INV-002`, `INV-012` (vincula com Licenças), `INV-CAL-WORM-001`.

---

### US-CAL-016: Vincular procedimento vigente à calibração (NOVO Onda 7 — A5-CAL)

**Como** metrologista, **quero** que cada calibração referencie a versão vigente do `ProcedimentoCalibracao` aplicável à grandeza/faixa **na data de execução**, **para** atender ISO 17025 cl. 7.2.1 (procedimento documentado controlado) e permitir auditoria retroativa.

**Critérios de aceite:**
- **AC-CAL-016-1**: GIVEN configuração da calibração (US-CAL-002), WHEN metrologista seleciona grandeza+faixa, THEN sistema resolve `ProcedimentoCalibracao` vigente em `data_execucao` e vincula `Calibracao.procedimento_id` + `Calibracao.procedimento_versao_snapshot` (snapshot do código + versão + `numero_revisao` cl. 8.3.2c + sha256 do anexo PDF). **ADR-0073 (M7 procedimentos-calibracao Fatia 3 — 2026-05-31, substitui o fail-open lazy da ADR-0066)**: resolução REAL na **configuração** via porta `procedimentos_calibracao.query_service.cobre_procedimento()` injetada no use case `configurar_calibracao` (não no permission layer DRF). Só PUBLICADO vigente que CONTÉM a faixa (`faixa_contida`); snapshot preenchido server-side (fonte = procedimento resolvido, não payload — C-1). O predicate STUB `procedimento_vigente_para` está deprecado/no-op. `tipo_metodo` cl. 7.2.2 = INV-PROC-010 (fail-open lazy até `licencas-acreditacoes` — GATE-PROC-METODO-VALIDADO).
- **AC-CAL-016-2**: GIVEN nenhum `ProcedimentoCalibracao` PUBLICADO vigente na data que cubra a grandeza+faixa, WHEN tenta configurar como RBC, THEN sistema bloqueia com 412 `ProcedimentoVigenteAusente` + cita grandeza/faixa (erro de domínio DISTINTO de `EscopoNaoCobreFaixa` — lacuna de método cl. 7.2.1, não fraude de escopo). **ADR-0073 (M7 Fatia 3 — 2026-05-31)**: bloqueio 412 EM VIGOR (`GATE-CAL-PROC-VIGENTE-PREDICATE` fechado no portão de configuração); ordem escopo→procedimento (escopo falho interrompe antes). Só RBC; B/C/D = aviso degradante (D-PROC-1).
- **AC-CAL-016-3**: GIVEN procedimento ativo em superseção (RT aprova versão N+1 após calibração começar), WHEN calibração está em `EM_EXECUCAO`/`EM_REVISAO_1`, THEN snapshot original é preservado (lock — `INV-CAL-WORM-001` estendido); só calibrações nascidas após `vigencia_inicio` de N+1 usam a nova. **ADR-0073 (M7 Fatia 3 — 2026-05-31)**: snapshot preservation já entregue em P4 (CalibracaoSnapshot.procedimento_versao_snapshot imutável); resolução do procedimento vigente na configuração ENTREGUE na Fatia 3 (porta `cobre_procedimento` — ver AC-CAL-016-1/2); superseção real (N+1 encerra vigência da anterior na mesma transação) = INV-PROC-008 no módulo `procedimentos-calibracao`.

**Invariantes:** `INV-PROC-001` (procedimento vigente na data — referência módulo `procedimentos`), `INV-CAL-WORM-001`, `INV-CAL-VERSAO-001`.

---

### US-CAL-017: Subcontratar calibração fora do escopo CMC (ISO 17025 cl. 6.6) — NOVO 2026-05-25

**Como** gestor do laboratório, **quero** aceitar instrumento do cliente cuja calibração não está no meu escopo CMC e despachar para outro laboratório acreditado (subcontratado), **mantendo a relação contratual com o cliente final**, **para** atender ISO 17025 cl. 6.6 (provisão externa de produtos e serviços) sem perder o cliente nem ferir as restrições do escopo RBC.

**Contexto regulatório:** ISO/IEC 17025 cl. 6.6 + NIT-DICLA-021 + RBC permitem subcontratação **temporária ou permanente** desde que: (a) subcontratado seja acreditado para o mesmo escopo/grandeza; (b) cliente seja **informado** e dê consentimento documentado; (c) certificado final declare claramente que serviço foi subcontratado; (d) lab principal mantém responsabilidade técnica total perante o cliente.

**Critérios de aceite:**

- **AC-CAL-017-1**: GIVEN configuração de calibração (US-CAL-002) onde grandeza+faixa está FORA do escopo CMC do tenant principal, WHEN gestor seleciona "subcontratar para lab externo acreditado", THEN sistema exige (a) escolha de `LaboratorioSubcontratado` cadastrado + (b) consentimento documentado do cliente (texto canônico `aceite-subcontratacao-v1.0.md` com hash + assinatura cliente) + (c) campo `motivo_subcontratacao` (≥30 chars, anti-PII INV-CAL-TXT-001).
- **AC-CAL-017-2**: GIVEN subcontratação aceita pelo cliente, WHEN calibração sai pra subcontratado, THEN status `Calibracao.status = AGUARDANDO_SUBCONTRATADO` + campo `subcontratado_id` (FK `LaboratorioSubcontratado`) + evento `Calibracao.SubcontratadaParaLab` publicado + `RecepcaoItemCalibracao.fluxo_subcontratacao_id` preenchido.
- **AC-CAL-017-3**: GIVEN certificado externo recebido do subcontratado (PDF anexo + número certificado externo + escopo declarado), WHEN gestor registra recebimento, THEN sistema valida: (a) acreditação do subcontratado está VIGENTE para a grandeza/faixa na data do serviço (consulta `LaboratorioSubcontratado.acreditacoes_vigentes`); (b) snapshot do certificado externo cravado em `Calibracao.certificado_subcontratado_snapshot_json` (imutável); (c) status muda para `RECEBIDA_DO_SUBCONTRATADO`.
- **AC-CAL-017-4**: GIVEN certificado final do tenant principal a ser emitido com base em serviço subcontratado, WHEN módulo Certificados (Marco 5) emite, THEN texto do certificado declara obrigatoriamente: "Esta calibração foi realizada pelo laboratório acreditado <nome+credenciamento>, sob responsabilidade técnica de <RT subcontratado>. Lab principal: <tenant principal+credenciamento>." (cl. 6.6.2 e ILAC G18).
- **AC-CAL-017-5**: GIVEN subcontratado tenta calibrar fora do próprio escopo dele (descoberto na verificação do snapshot), WHEN sistema detecta, THEN bloqueia recebimento com 412 `SubcontratadoFaixaForaEscopo` + dispara NC interna (CAPA aberta).
- **AC-CAL-017-6**: GIVEN cliente não consentiu subcontratação (recusou aceite v1.0), WHEN gestor tenta subcontratar mesmo assim, THEN sistema bloqueia com 412 `SubcontratacaoSemConsentimentoCliente`.

**Invariantes:** `INV-CAL-SUBC-001` (consentimento cliente obrigatório, hash+IP+timestamp), `INV-CAL-SUBC-002` (subcontratado vigente na data do serviço — não-CMC=409), `INV-CAL-SUBC-003` (snapshot certificado externo imutável), `INV-CAL-SUBC-004` (texto certificado final declara subcontratação — cl. 6.6.2), `INV-CAL-WORM-001`.

**Non-goals da US:**

- NÃO substitui módulo `licencas-acreditacoes` — `LaboratorioSubcontratado.acreditacoes_vigentes` é snapshot, não cadastro completo do subcontratado.
- NÃO trata pagamento subcontratado → tenant principal (financeiro Wave B).
- NÃO trata responsabilidade civil disputada — apólice E&O ampliada (ADR-0028 + GATE-SEG-* Wave A).
- NÃO trata sub-subcontratação (subcontratado terceiriza pra outro) — non-goal Wave A (ADR adicional se aparecer demanda).

**Entidades novas (modelo de domínio):**

- `LaboratorioSubcontratado` (cadastrado pelo tenant principal; nome, CNPJ, credenciamento atual, acreditações vigentes snapshot, contato comercial, contato técnico, DPA cl. 4.7).
- `AceiteSubcontratacao` (FK Calibracao + FK Cliente + hash texto v1.0 + IP_hash + assinatura touch ou A3 cliente + correlation_id).

**Eventos novos:**

- `Calibracao.SubcontratadaParaLab` (payload: `calibracao_id`, `subcontratado_id`, `motivo_hash`, `aceite_cliente_id`).
- `Calibracao.RecebidaDoSubcontratado` (payload: `calibracao_id`, `cert_externo_snapshot_hash`, `validacao_acreditacao_ok`).

**Bloqueios cross-módulo:**

- Subcontratação não exime cobrança do cliente — mesmo fluxo financeiro (ADR-0043).
- Cliente sob inadimplência dura NÃO pode subcontratar (bloqueio INV-CLI-BLOQ-001 herdado).
- Certificado emitido com declaração subcontratação ainda é WORM no tenant principal (INV-CAL-WORM-001).

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Tempo médio entrada→aprovação ≤ 3 dias úteis (target).
- Taxa de rejeição em 2ª conferência ≤ 5% (qualidade da 1ª).
- Zero calibrações RBC emitidas fora do escopo (target: 100%).
- Zero padrões usados fora da vigência (target: 100%).

## 8. NFR

- **Performance:** cálculo de incerteza < 1s p95 para ≤ 100 pontos.
- **Disponibilidade:** 99.9%.
- **Segurança:** SEC-001, SEC-002; trilha WORM; multi-tenancy RLS.
- **Validação de software:** ISO 17025 7.11 — ver `validacao-software.md`. Versão do motor de cálculo registrada por calibração.
- **Acessibilidade:** WCAG AA.

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo `US-CAL-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança no motor de cálculo → ADR + bump versão + validação ISO 17025 7.11.

---

## 11. Revisão P3 (2026-05-25) — ACs novos e modificados absorvidos do ritual Spec Kit M4

> **Esta seção é fonte de verdade pós-P3 ritual Spec Kit do Marco 4** — qualquer divergência com §6 acima resolve em favor de §11. ACs originais permanecem em §6 por rastreabilidade; §11 adiciona/modifica conforme reviews paralelos `docs/faseamento/M4-calibracao/reviews/{tech-lead,advogado,corretora,rbc}.md` e plano consolidado `docs/faseamento/M4-calibracao/plan.md`.

### 11.1 ACs novos por US

**US-CAL-001 (Recepcionar instrumento) — 1 AC novo**

- **AC-CAL-001-3** (P-CAL-R4 RBC + P-CAL-A5 advogado): GIVEN recepção AVULSA (`atividade_os_id IS NULL`), WHEN `recepcionarInstrumento`, THEN sistema exige (a) `analise_critica_pedido_inline_hash` (texto ≥100 chars + anti-PII INV-CAL-TXT-001 + canonicalização INV-DOC-CANON-001 declarando capacidade técnica + regra de decisão + escopo confirmado) + (b) `capacidade_tecnica_confirmada_por_user_id NOT NULL` + (c) renderiza texto canônico `aviso-foto-recepcao-v1.0.md` antes da captura de foto; cliente concorda (foto entra em `RecepcaoItemCalibracao.foto_evidencia_id`) OU recusa (entra em `ConsentimentoFotoRecusado.id`); ausente → 412 `AnaliseCriticaPedidoAusente`.

**US-CAL-002 (Configurar calibração) — 1 AC novo**

- **AC-CAL-002-3** (P-CAL-A3 advogado + ADR-0024 revisado): GIVEN cliente requisita override de regra de decisão (`regra_decisao_override_cliente=true`), WHEN tenant tenta aceitar em `configurarCalibracao`, THEN sistema exige (a) cláusula contratual ativa vigente — predicate `clausula_override_vigente(cliente_id, em_data)`; (b) assinatura A3 do cliente (NÃO touch — Lei 14.063 art. 4º alto risco); (c) justificativa canonicalizada ≥100 chars anti-PII; ausente → 412 `OverrideSemContratoOuA3`. Cria entidade `OverrideRegraDecisaoCliente` (Padrão B imutável).

**US-CAL-004 (Registrar leituras) — 2 ACs novos**

- **AC-CAL-004-7** (P-CAL-T1 tech-lead + ADR-0065): GIVEN tentativa de registrar `(calibracao_id, ponto_calibracao, numero_repeticao)` que já existe, WHEN INSERT em `leitura`, THEN sistema retorna 412 `LeituraDuplicada` via UNIQUE composto `idx_leitura_unica`. Replay com mesmo `Idempotency-Key` retorna 200 idempotente.
- **AC-CAL-004-8** (P-CAL-R13 RBC): GIVEN `ConfiguracaoCalibracao.condicoes_ambientais_alvo_id NOT NULL` E `CondicoesAmbientais.dentro_tolerancia=false`, WHEN `registrarLeitura`, THEN bloqueia leitura com 412 `CondicoesAmbientaisForaTolerancia`; override possível com justificativa ≥50 chars + audit `EventoDeCalibracao(tipo=condicoes_fora_override)` + alerta P2 Qualidade.

**US-CAL-005 (Calcular incerteza) — 4 ACs novos**

- **AC-CAL-005-4** (P-CAL-R2 RBC + NIT-DICLA-030 §6.3): GIVEN `OrcamentoIncerteza` calculado, WHEN `solicitarRevisao`, THEN sistema valida matriz componentes-obrigatórios por grandeza+padrão (`docs/dominios/metrologia/modulos/calibracao/componentes-obrigatorios-por-grandeza.md` — minuta preliminar pelo agente; REQUER CGCRE humano); ausência → 412 `ComponentesMinimosAusentes: [lista]`.
- **AC-CAL-005-5** (P-CAL-R7 RBC): GIVEN `ComponenteIncerteza.tipo_componente='A'`, WHEN INSERT, THEN exige `n_amostras ≥ 6` (NIT-DICLA-030 §7.4) + `s_x NOT NULL`; ausência → 412 `TipoAIncompleto`.
- **AC-CAL-005-6** (P-CAL-R7 RBC + GUM §5.2.2): GIVEN 2+ `ComponenteIncerteza` com mesmo `fonte_default_padrao_id`, WHEN cálculo de `OrcamentoIncerteza`, THEN sistema verifica `correlacao_com_componente_id` em pelo menos um; ausente → alerta P2 Qualidade (não bloqueia mas registra `EventoDeCalibracao(tipo=correlacao_nao_declarada)`).
- **AC-CAL-005-7** (P-CAL-R7 RBC + cl. 7.8.3.1.h): GIVEN `OrcamentoIncerteza.U_expandida` calculado, WHEN cravado em snapshot, THEN aplica regra de arredondamento `NIT_DICLA_030_2_DIGITOS_SIG` (incerteza com ≤2 dígitos significativos, valor reportado arredondado ao mesmo nível); valor pré-arredondamento preservado em `algoritmo_1_resultado JSONB`.

**US-CAL-006 (Avaliar conformidade) — 1 AC novo + 1 AC modificado**

- **AC-CAL-006-1 MODIFICADO** (P-CAL-R1 RBC + ADR-0024 revisado): GIVEN `OrcamentoIncerteza` cravado, WHEN `avaliarConformidade`, THEN sistema calcula `zona_ilac_g8 IN ('PASS', 'CONDITIONAL_PASS', 'PASS_COM_RESSALVA', 'CONDITIONAL_FAIL', 'FAIL_COM_RESSALVA', 'FAIL', 'NA')` (6 zonas ILAC G8 + NA) + popula `decisao` correspondente.
- **AC-CAL-006-4** (P-CAL-R1 RBC + ILAC G8 §4.4 + JCGM 106 §9): GIVEN `regra_decisao = BANDA_GUARDA_30`, WHEN `avaliarConformidade`, THEN exige `pfa_calculada NOT NULL` (probabilidade de aceitação falsa); GIVEN `regra_decisao = RISCO_COMPARTILHADO`, THEN exige `pra_calculada NOT NULL`; ausente → 412 `PFANaoCalculada` / `PRANaoCalculada`.

**US-CAL-007 (Revisão técnica) — 1 AC novo**

- **AC-CAL-007-5** (P-CAL-R10 RBC + cl. 6.2): GIVEN `aprovarRevisao`, WHEN UPDATE para `aguardando_2a_conferencia`, THEN captura `Calibracao.snapshot_competencia_revisor_json` imutável contendo (grandeza, faixa, vigência da `RTCompetencia` do revisor NA DATA da aprovação); paralelo invoca predicate `rt_competencia_cobre(revisor_user_id, calibracao.grandeza, em_data=hoje)` (ADR-0063 Opção A); falha → 422 `RTSemCompetencia`.

**US-CAL-008 (Segunda conferência) — 2 ACs novos**

- **AC-CAL-008-4** (P-CAL-R10 RBC + cl. 6.2.5): GIVEN `aprovar2aConferencia`, WHEN UPDATE para `aprovada`, THEN captura `snapshot_competencia_conferente_json` imutável + invoca `rt_competencia_cobre(conferente_user_id, calibracao.grandeza, em_data=hoje)` + valida `conferente_id != revisor_id` (ou ADR-0026 4 condições objetivas); falha → 422 `ConferenteSemCompetencia` / 422 `Excecao62_5InaceitavelSemCondicoes`.
- **AC-CAL-008-5** (P-CAL-S9 corretora — alerta exceção): GIVEN tenant usa exceção 2ª conferência (ADR-0026), WHEN sistema computa uso mensal, THEN dispara alerta P2 Qualidade quando uso atinge 3%/mês (1/3 do limite ADR-0026 5%/mês) — janela móvel 30 dias.

**US-CAL-014 (Comparação interlaboratorial / proficiência) — 1 AC novo**

- **AC-CAL-014-5** (P-CAL-R6 RBC + cl. 7.10.1/2): GIVEN `marcarNaoConformidade(decisao_continuar_ou_parar)`, WHEN transição `→ ACAO_EXECUTADA`, THEN exige `decisao_continuar_ou_parar != 'A_DEFINIR'`; quando `PARAR_TRABALHO`, exige `cliente_notificado_em NOT NULL` antes; consumer `Calibracao.NCAberta(PARAR_TRABALHO)` publica `Cliente.NotificacaoPendente`.

**US-CAL-017 (Subcontratar calibração cl. 6.6) — 2 ACs novos**

- **AC-CAL-017-7** (P-CAL-A1 advogado + Lei 14.063 art. 4º): GIVEN subcontratação iniciada, WHEN `assinatura_modo='TOUCH'` em vez de A3, THEN sistema marca alerta P3 + grava no audit indicação `touch-em-alto-risco` + exige `declaracao_aceite_touch_alto_risco_id NOT NULL` (texto canônico extra `aceite-subcontratacao-touch-alto-risco-v1.0.md` — REQUER OAB). Default `A3`.
- **AC-CAL-017-8** (P-CAL-A1 advogado + LGPD art. 33): GIVEN `LaboratorioSubcontratado.pais != 'BR'`, WHEN `subcontratarCalibracao`, THEN sistema bloqueia 412 `SubcontratadoForaBR_TransferenciaInternacionalSemBase` quando `dpa_clausulas_internacionais_id IS NULL`; destrava com cláusulas-padrão ANPD aprovadas.

### 11.2 US nova — US-CAL-018: Reclamação do cliente sobre calibração emitida

| Campo | Valor |
|---|---|
| **Persona** | Cliente (titular ou contato técnico PJ) |
| **Necessidade** | Contestar formalmente cert emitido com erro técnico suspeito |
| **Resultado esperado** | Reclamação registrada + RT independente atribui + resposta fundamentada ≤15 dias úteis |
| **Base normativa** | ISO 17025 cl. 7.9 (Reclamações) + CDC art. 26 (30 dias serviço aparente / 90 dias vício oculto) |

**AC-CAL-018-1:** GIVEN cert emitido há ≤90 dias, WHEN cliente abre reclamação via portal-cliente, THEN cria `ReclamacaoCalibracao` em estado `RECEBIDA` + publica `Calibracao.ReclamacaoAberta`. Descrição canonicalizada ≥30 chars + anti-PII INV-CAL-TXT-001.

**AC-CAL-018-2:** GIVEN reclamação aberta, WHEN sistema atribui RT, THEN preferência por RT independente (`revisor_id != calibracao_original.revisor_id` E `revisor_id != calibracao_original.conferente_id`); RT atribuído é notificado.

**AC-CAL-018-3:** GIVEN reclamação em análise, WHEN `prazo_resposta_dia_util` excedido (15 dias úteis), THEN alerta P1 gerente qualidade + DPO.

**AC-CAL-018-4:** GIVEN reclamação respondida, WHEN `decisao IN ('PROCEDENTE_RECALL', 'PROCEDENTE_ERRATA', 'IMPROCEDENTE_FUNDAMENTADA')`, THEN publica `Calibracao.ReclamacaoRespondida` → quando PROCEDENTE_RECALL, Marco 5 dispara saga recall ADR-0045.

### 11.3 Decisões ADR aplicadas

- **ADR-0024 revisado:** 6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao + INV-CAL-DEC-004..006.
- **ADR-0063 esclarecida:** Opção A lazy — predicate em `configurar_calibracao` + `aprovar_revisao` + `aprovar_2a_conferencia` (NÃO em `iniciar_atividade`).
- **ADR-0065 NOVA:** Concorrência metrológica (UNIQUE composto + CAS + advisory lock).

### 11.4 GATEs Wave A do PRD (não bloqueiam M4 dogfooding)

Lista completa em `docs/faseamento/M4-calibracao/plan.md` §"Bloqueantes Wave A" — 32 GATEs novos. Itens críticos pré-1º tenant externo pago (todos 🔴):

- 🔴 6 GATE-CAL-*-OAB (P-CAL-A1, A2, A3, A5, A6 + DPIA).
- 🔴 9 GATE-SEG-* SUSEP (cláusulas E&O multi-tier, Cyber HMAC 25a, Modalidade 8 Property padrão próprio).
- 🔴 5 GATE-CAL-*-CGCRE (componentes-obrigatórios por grandeza, fórmula por grandeza, política critério-seleção subcontratado, declaração subcontratação cert, matriz CGCRE).

### 11.5 INVs novas aplicáveis ao PRD (gravadas em REGRAS-INEGOCIAVEIS.md)

24 INVs CAL novas cravadas em commit `b1c1d6a`:

CONC-001..004, AUD-002, DEC-004..006, INC-002..004, ANAL-001, RT-002, RAST-002, SUBC-005..006, NC-002..003, AMB-001, BACKUP-001, PAD-CASCADE-001, ANON-001, IDEMP-001, CONT-001, FRAUDE-RECEB-001.
