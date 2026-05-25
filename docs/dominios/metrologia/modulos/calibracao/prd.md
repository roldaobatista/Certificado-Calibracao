---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
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
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0044-exportacao-regulatoria-anvisa-saude.md
  - docs/adr/0045-certificado-recall-suspensao-errata.md
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
- **AC-CAL-001-2**: GIVEN escopo de acreditação NÃO cobre o instrumento, WHEN tenta cadastrar como calibração RBC, THEN sistema avisa e permite seguir como NÃO-RBC.

**Invariantes:** `INV-TENANT-001`, `INV-CAL-WORM-001`.

---

### US-CAL-002: Configurar calibração

**Como** metrologista, **quero** configurar a calibração (grandeza, faixa, pontos, método, condições ambientais alvo), **para** padronizar a execução.

**Critérios de aceite:**
- **AC-CAL-002-1**: GIVEN configuração nova, WHEN seleciona grandeza+faixa, THEN sistema oferece métodos disponíveis (NIT-DICLA / norma técnica) e padrões compatíveis.
- **AC-CAL-002-2**: GIVEN faixa fora do escopo CMC, WHEN tenta salvar como RBC, THEN sistema bloqueia citando CMC oficial.

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
- **AC-CAL-015-1**: GIVEN escopo cadastrado (grandeza, faixa min/max, CMC, método), WHEN calibração configurada, THEN sistema valida se cobre.
- **AC-CAL-015-2**: GIVEN renovação/revisão do escopo CGCRE, WHEN admin atualiza, THEN versão anterior preservada com janela de calibrações antigas.

**Invariantes:** `INV-002`, `INV-012` (vincula com Licenças), `INV-CAL-WORM-001`.

---

### US-CAL-016: Vincular procedimento vigente à calibração (NOVO Onda 7 — A5-CAL)

**Como** metrologista, **quero** que cada calibração referencie a versão vigente do `ProcedimentoCalibracao` aplicável à grandeza/faixa **na data de execução**, **para** atender ISO 17025 cl. 7.2.1 (procedimento documentado controlado) e permitir auditoria retroativa.

**Critérios de aceite:**
- **AC-CAL-016-1**: GIVEN configuração da calibração (US-CAL-002), WHEN metrologista seleciona grandeza+faixa, THEN sistema resolve `ProcedimentoCalibracao` vigente em `data_execucao` via predicate `procedimento_vigente_para(grandeza, faixa, em_data)` (referência `INV-VIG-001`/`INV-VIG-004` + ADR-0030) e vincula `Calibracao.procedimento_id` + `Calibracao.procedimento_versao_snapshot` (snapshot do código + versão + hash do anexo PDF).
- **AC-CAL-016-2**: GIVEN nenhum `ProcedimentoCalibracao` vigente na data, WHEN tenta configurar como RBC, THEN sistema bloqueia com 412 `ProcedimentoVigenteAusente` + cita grandeza/faixa.
- **AC-CAL-016-3**: GIVEN procedimento ativo em superseção (RT aprova versão N+1 após calibração começar), WHEN calibração está em `EM_EXECUCAO`/`EM_REVISAO_1`, THEN snapshot original é preservado (lock — `INV-CAL-WORM-001` estendido); só calibrações nascidas após `vigencia_inicio` de N+1 usam a nova.

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
