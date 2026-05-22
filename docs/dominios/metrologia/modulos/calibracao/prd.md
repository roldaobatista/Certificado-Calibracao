---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md
  - docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
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

**Invariantes:** `INV-TENANT-001`, `INV-022`.

---

### US-CAL-002: Configurar calibração

**Como** metrologista, **quero** configurar a calibração (grandeza, faixa, pontos, método, condições ambientais alvo), **para** padronizar a execução.

**Critérios de aceite:**
- **AC-CAL-002-1**: GIVEN configuração nova, WHEN seleciona grandeza+faixa, THEN sistema oferece métodos disponíveis (NIT-DICLA / norma técnica) e padrões compatíveis.
- **AC-CAL-002-2**: GIVEN faixa fora do escopo CMC, WHEN tenta salvar como RBC, THEN sistema bloqueia citando CMC oficial.

**Invariantes:** `INV-002` (escopo CMC), `INV-022`.

---

### US-CAL-003: Selecionar padrões com vigência válida

**Como** metrologista, **quero** selecionar padrões e o sistema validar vigência do certificado de cada padrão, **para** garantir rastreabilidade.

**Critérios de aceite:**
- **AC-CAL-003-1**: GIVEN padrão com certificado externo vencido, WHEN tenta selecionar, THEN sistema bloqueia.
- **AC-CAL-003-2**: GIVEN padrão dentro da verificação intermediária programada, WHEN sistema verifica, THEN libera.
- **AC-CAL-003-3**: GIVEN seleção concluída, WHEN salva, THEN snapshot de cada padrão (cert, validade, classe) fica anexo à calibração.

**Invariantes:** `INV-003` (rastreabilidade padrão), `INV-014` (snapshot), `INV-022`.

---

### US-CAL-004: Registrar leituras (manual ou integrada)

**Como** metrologista, **quero** registrar as leituras dos pontos calibrados (manual ou via integração com instrumento padrão), **para** ter dados primários da calibração.

**Critérios de aceite:**
- **AC-CAL-004-1**: GIVEN configuração com N pontos × M repetições, WHEN registra leituras, THEN sistema valida formato/unidade e armazena com timestamp.
- **AC-CAL-004-2**: GIVEN integração com balança/padrão via serial/USB, WHEN equipamento envia leitura, THEN sistema persiste automaticamente.
- **AC-CAL-004-3**: GIVEN leitura fora de faixa esperada, WHEN sistema detecta, THEN alerta metrologista mas NÃO bloqueia (decisão dele).

**Invariantes:** `INV-022`.

---

### US-CAL-005: Calcular erro e incerteza com orçamento por componente

**Como** metrologista, **quero** que o sistema calcule erro + incerteza expandida (k=2) com tabela de orçamento por componente, **para** ter resultado auditável conforme GUM.

**Critérios de aceite:**
- **AC-CAL-005-1**: GIVEN leituras + padrões + condições ambientais, WHEN sistema calcula, THEN gera tabela orçamento (componente, tipo A/B, distribuição, divisor, contribuição, grau de liberdade), combina pelo método RSS, expande com k=2 (95.45%) e mostra resultado final.
- **AC-CAL-005-2**: GIVEN cálculo executado, WHEN metrologista revisa, THEN cada componente do orçamento é editável (Tipo B vem de defaults configuráveis por padrão+grandeza).
- **AC-CAL-005-3**: GIVEN versão do algoritmo, WHEN calibração executada, THEN sistema salva versão do motor de cálculo no snapshot (validação de software ISO 17025 7.11).

**Invariantes:** `INV-004` (cálculo GUM), `INV-005` (versão software registrada), `INV-022`. Ver `validacao-software.md`.

---

### US-CAL-006: Avaliar conformidade com regra de decisão

**Como** metrologista, **quero** avaliar conformidade (atende/não atende especificação) considerando incerteza e regra de decisão configurada, **para** atender ISO 17025 7.8.6.

**Critérios de aceite:**
- **AC-CAL-006-1**: GIVEN especificação cliente + resultado + incerteza, WHEN sistema avalia com regra de decisão (Aceitação Simples / Banda de Guarda 30% / Risco Compartilhado), THEN classifica como CONFORME, NÃO CONFORME ou ZONA DE INCERTEZA.
- **AC-CAL-006-2**: GIVEN ZONA DE INCERTEZA, WHEN sistema mostra, THEN exige decisão explícita do metrologista (CONFORME COM RESERVA / NÃO CONFORME / NÃO AVALIAR).
- **AC-CAL-006-3**: GIVEN regra de decisão escolhida, WHEN certificado emitido, THEN regra fica documentada no certificado (citar ILAC G8).

**Invariantes:** `INV-006`, ISO 17025 7.8.6.

---

### US-CAL-007: Revisão técnica (1ª conferência)

**Como** RT revisor, **quero** revisar a calibração antes de aprovação final, **para** detectar erros antes da emissão.

**Critérios de aceite:**
- **AC-CAL-007-1**: GIVEN calibração com cálculo concluído, WHEN RT abre revisão, THEN sistema mostra tudo (config, padrões, leituras, orçamento incerteza, avaliação) com botões aprovar/rejeitar/solicitar correção.
- **AC-CAL-007-2**: GIVEN rejeição ou correção solicitada, WHEN RT marca, THEN sistema volta calibração ao metrologista com nota.
- **AC-CAL-007-3**: GIVEN revisor = executor da calibração, WHEN tenta revisar, THEN sistema avisa (independência ideal — mas não bloqueia se único RT habilitado disponível, registra exceção).

**Invariantes:** `INV-019` (RT habilitado), `INV-022`.

---

### US-CAL-008: Segunda conferência

**Como** RT independente, **quero** fazer segunda conferência da calibração (preferencialmente RT diferente do revisor), **para** atender boas práticas ISO 17025 7.7.

**Critérios de aceite:**
- **AC-CAL-008-1**: GIVEN calibração com 1ª revisão aprovada, WHEN passa pra 2ª conferência, THEN sistema mostra os mesmos dados + nota da 1ª revisão + botão aprovar/rejeitar.
- **AC-CAL-008-2**: GIVEN aprovação da 2ª conferência, WHEN executada, THEN calibração vira APROVADA + libera emissão de certificado.
- **AC-CAL-008-3**: GIVEN único RT disponível executou todas as etapas, WHEN tenta concluir, THEN sistema registra exceção em log de auditoria pra explicação posterior.

**Invariantes:** `INV-007` (2ª conferência obrigatória), `INV-022`. Ver `garantia-validade-7.7.md`.

---

### US-CAL-009: Histórico de calibrações por instrumento

**Como** RT, **quero** ver histórico de calibrações de um instrumento, **para** detectar drift, repetibilidade entre calibrações.

**Critérios de aceite:**
- **AC-CAL-009-1**: GIVEN instrumento com N calibrações, WHEN consulta histórico, THEN sistema mostra timeline com resultado, incerteza, decisão, certificado emitido.

**Invariantes:** `INV-022`, `INV-TENANT-001`.

---

### US-CAL-010: Controle de pesos padrão (catálogo)

**Como** RT, **quero** gerenciar pesos padrão (cadastro, classe E1/E2/F1/F2/M1/M2/M3, valor nominal, valor convencional, validade do certificado, localização física), **para** ter inventário rastreável.

**Critérios de aceite:**
- **AC-CAL-010-1**: GIVEN cadastro de peso padrão, WHEN preenche, THEN exige classe + valor nominal + cert externo + validade + localização.
- **AC-CAL-010-2**: GIVEN peso com cert externo vencido, WHEN aparece em seleção de padrões, THEN marcado como INDISPONÍVEL.

**Invariantes:** `INV-008` (rastreabilidade padrão), `INV-022`.

---

### US-CAL-011: Registrar calibração externa do padrão

**Como** RT, **quero** registrar envio do padrão pra calibração externa (lab acreditado) e recebimento do certificado, **para** manter rastreabilidade.

**Critérios de aceite:**
- **AC-CAL-011-1**: GIVEN padrão indo pra calibração externa, WHEN registra envio (laboratório destino, data envio, NF/protocolo), THEN sistema marca padrão INDISPONÍVEL.
- **AC-CAL-011-2**: GIVEN recebimento + novo certificado externo, WHEN registra (cert, validade, anexo PDF, valor convencional, incerteza), THEN sistema marca padrão DISPONÍVEL com nova vigência.

**Invariantes:** `INV-008`, `INV-022`.

---

### US-CAL-012: Verificação intermediária

**Como** RT, **quero** registrar verificações intermediárias do padrão (entre calibrações externas), **para** comprovar estabilidade.

**Critérios de aceite:**
- **AC-CAL-012-1**: GIVEN padrão com programa de verificação intermediária, WHEN data prevista chega, THEN sistema alerta RT.
- **AC-CAL-012-2**: GIVEN verificação executada, WHEN registra resultado, THEN sistema avalia critério de aceitação configurado; se reprovado, padrão fica INDISPONÍVEL + dispara NC.

**Invariantes:** `INV-009`, `INV-022`.

---

### US-CAL-013: Ensaios de linearidade, repetibilidade, excentricidade

**Como** RT, **quero** executar ensaios complementares (linearidade, repetibilidade, excentricidade) integrados ao registro de calibração, **para** atender métodos completos.

**Critérios de aceite:**
- **AC-CAL-013-1**: GIVEN método requer ensaio de linearidade, WHEN seleciona, THEN sistema gera template de pontos + calcula desvios + r².
- **AC-CAL-013-2**: GIVEN repetibilidade, WHEN executa N medições no mesmo ponto, THEN sistema calcula desvio padrão experimental + Tipo A.
- **AC-CAL-013-3**: GIVEN excentricidade (balanças), WHEN executa nas 4 posições + centro, THEN sistema calcula maior diferença vs ponto central.

**Invariantes:** `INV-022`.

---

### US-CAL-014: Comparação interlaboratorial / ensaio de proficiência

**Como** RT/gestor qualidade, **quero** registrar participação em comparação interlaboratorial e ensaios de proficiência, **para** evidenciar competência (ISO 17025 7.7.2).

**Critérios de aceite:**
- **AC-CAL-014-1**: GIVEN participação programada, WHEN registra (provedor, rodada, grandeza, faixa), THEN sistema cria registro pendente.
- **AC-CAL-014-2**: GIVEN resultado recebido (escore z, status PASSED/UNACCEPTABLE), WHEN registra, THEN sistema anexa relatório + se UNACCEPTABLE dispara NC.

**Invariantes:** `INV-022`, ISO 17025 7.7.2.

---

### US-CAL-015: Escopo de acreditação + CMC

**Como** admin tenant, **quero** cadastrar escopo de acreditação CGCRE + CMC por grandeza/faixa, **para** o sistema bloquear emissões fora do escopo RBC.

**Critérios de aceite:**
- **AC-CAL-015-1**: GIVEN escopo cadastrado (grandeza, faixa min/max, CMC, método), WHEN calibração configurada, THEN sistema valida se cobre.
- **AC-CAL-015-2**: GIVEN renovação/revisão do escopo CGCRE, WHEN admin atualiza, THEN versão anterior preservada com janela de calibrações antigas.

**Invariantes:** `INV-002`, `INV-012` (vincula com Licenças), `INV-022`.

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
