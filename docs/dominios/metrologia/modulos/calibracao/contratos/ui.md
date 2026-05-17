---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Calibração

> Telas. Descritivo enquanto stack candidata (ADR-0001).

---

## Telas

### Tela 1: Recepção de Instrumento

**Propósito:** registrar entrada do instrumento.
**Persona:** recepcionista.
**US:** `US-CAL-001`.

**Elementos:**
- Campo OS (autocomplete) ou marcar "avulso".
- Identificação instrumento: descrição, fabricante, modelo, série, ID interno (auto).
- Condições recebidas (rich text limitado): caixa/acessórios/danos.
- Foto de chegada (mobile via câmera).
- Botão "Imprimir etiqueta interna com QR".

**Estados:** padrão.
**Acessibilidade:** AA.
**Mobile:** sim, prioritário.

---

### Tela 2: Configuração da Calibração

**Propósito:** metrologista define grandeza, faixa, método, pontos.
**Persona:** metrologista.
**US:** `US-CAL-002`, `US-CAL-015`.

**Elementos:**
- Seletor grandeza (filtra escopo CMC).
- Faixa min/max + unidade.
- Método (lista filtrada pela grandeza — referência a NIT/norma).
- Pontos de calibração (gerador automático: 5 pontos uniformes / personalizado).
- Repetições por ponto.
- Regra de decisão (ACEITACAO_SIMPLES / BANDA_GUARDA_30 / RISCO_COMPARTILHADO) com explicação curta.
- Aviso visual se faixa fora do escopo CMC RBC.

**Estados:**
- Fora de escopo CMC: badge laranja "fora do escopo RBC — pode prosseguir como NÃO-RBC".

---

### Tela 3: Seleção de Padrões

**Propósito:** metrologista escolhe padrões a usar.
**US:** `US-CAL-003`.

**Elementos:**
- Lista de padrões disponíveis (filtrada por grandeza compatível + vigência).
- Cada item mostra: descrição, classe, valor convencional, validade do cert externo.
- Padrões INDISPONÍVEIS aparecem em cinza com motivo.
- Botão "Selecionar".

**Estados:** padrão.

---

### Tela 4: Registro de Leituras

**Propósito:** metrologista insere/captura leituras.
**US:** `US-CAL-004`.

**Elementos:**
- Tabela: ponto × repetição × valor lido (com unidade) × timestamp.
- Modo manual: clica na célula e digita.
- Modo integrado: indicador "esperando equipamento"; chega leitura, vai pra próxima célula.
- Aviso visual se leitura fora de faixa esperada (cor amarela — não bloqueia).
- Painel lateral com condições ambientais (T, UR, p) — auto via sensor ou manual.

**Estados:**
- Sensor desconectado: instrução pra conectar/manual.

---

### Tela 5: Cálculo + Orçamento de Incerteza

**Propósito:** mostra resultado calculado + tabela editável.
**US:** `US-CAL-005`.

**Elementos:**
- Tabela orçamento: componente, tipo A/B, distribuição, divisor, contribuição, % do total, grau de liberdade.
- Componentes Tipo B vêm preenchidos do default do padrão+grandeza — editáveis com justificativa.
- Resumo: u_combinada, grau de liberdade efetivo, k, U_expandida, nível de confiança.
- Versão do motor de cálculo exibida.
- Botão "Recalcular" / "Continuar pra avaliação".

---

### Tela 6: Avaliação de Conformidade

**Propósito:** sistema avalia + metrologista decide se Zona de Incerteza.
**US:** `US-CAL-006`.

**Elementos:**
- Especificação cliente (input).
- Resultado calculado + incerteza.
- Visualização gráfica: barra de especificação com banda de incerteza sobre o resultado.
- Veredito: CONFORME (verde) / NÃO CONFORME (vermelho) / ZONA DE INCERTEZA (amarelo — exige decisão manual).
- Se ZONA: dropdown "Decisão final" + campo justificativa obrigatória.

---

### Tela 7: Fila de Revisão Técnica

**Propósito:** RT vê calibrações pendentes de revisão.
**Persona:** RT.
**US:** `US-CAL-007`.

**Elementos:**
- Tabela: nº calibração, instrumento, cliente, executor, data conclusão, etapa (REVISAO_1 / CONFERENCIA_2), tempo na fila.
- Filtros: etapa, RT atribuído.

---

### Tela 8: Revisão de Calibração (RT)

**Propósito:** RT revisa tudo em uma tela.
**US:** `US-CAL-007`, `US-CAL-008`.

**Elementos:**
- Abas: Configuração | Padrões | Leituras | Condições | Orçamento incerteza | Avaliação | Ensaios complementares.
- Painel decisão (fixo no rodapé): aprovar | rejeitar | solicitar correção + textarea nota.
- Aviso se revisor = executor (ideal independência).
- Aviso se mesmo RT vai fazer 2ª conferência.

---

### Tela 9: Histórico do Instrumento

**Propósito:** ver calibrações anteriores do mesmo instrumento.
**US:** `US-CAL-009`.

**Elementos:**
- Timeline com cada calibração: data, decisão, incerteza, cert emitido (link).
- Gráfico de drift opcional: tendência do desvio no ponto principal.

---

### Tela 10: Catálogo de Padrões

**Propósito:** RT gerencia inventário.
**US:** `US-CAL-010`.

**Elementos:**
- Tabela: descrição, tipo, classe, valor nominal, status (com cor), validade próxima.
- Filtros: tipo, status, vencendo em N dias.
- Botão "Cadastrar padrão".

---

### Tela 11: Detalhe de Padrão

**Elementos:**
- Dados gerais + status + localização.
- Abas: Certificados externos (histórico) | Verificações intermediárias | Uso em calibrações.
- Botões: registrar envio para calibração externa | registrar recebimento | registrar verificação intermediária.

---

### Tela 12: Ensaios de Proficiência

**US:** `US-CAL-014`.

**Elementos:**
- Lista de participações: provedor, rodada, grandeza, data, escore z, status.
- Botão cadastrar nova participação.

---

### Tela 13: Escopo de Acreditação

**US:** `US-CAL-015`.

**Persona:** admin tenant.

**Elementos:**
- Tabela: grandeza, faixa min/max, unidade, CMC, método, vigência.
- Versionamento (qual versão estava ativa em DD/MM/AAAA).
- Botão atualizar (cria nova versão; antiga preservada).

---

## Componentes reutilizáveis

- Badge de status — compartilhado.
- Tabela editável incerteza — específica deste módulo.
- Gráfico drift — específica.

## Como esta lista evolui

- Tela nova → US.
- Mudança UX → CHANGELOG.
- Deprecada → `@deprecated`.
