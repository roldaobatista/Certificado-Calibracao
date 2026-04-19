# PG-VAL-001 — Validação e Verificação de Métodos

| Código | PG-VAL-001 | Revisão | 00 | Data | __/__/____ |
|--------|------------|---------|----|------|------------|

## 1. Objetivo
Estabelecer a sistemática para verificação de métodos normalizados e validação de métodos não normalizados, desenvolvidos internamente, modificados ou usados fora do escopo previsto, conforme item 7.2 da ABNT NBR ISO/IEC 17025:2017.

## 2. Critérios para decidir validar ou verificar

| Situação | Ação |
|----------|------|
| Método normalizado, sem alterações, dentro do escopo | **Verificação** |
| Método normalizado, com modificação | **Validação** dos parâmetros afetados |
| Método não normalizado | **Validação completa** |
| Método desenvolvido pelo laboratório | **Validação completa** |
| Método usado fora do escopo (matriz, faixa) | **Validação** dos parâmetros relevantes |

## 3. Parâmetros típicos

### Para ensaios químicos / instrumentais
| Parâmetro | Critério típico |
|-----------|-----------------|
| Seletividade / Especificidade | Sem interferência significativa |
| Linearidade / Faixa de trabalho | r² ≥ 0,995; resíduos aleatórios |
| Limite de detecção (LD) | 3 · s_branco / inclinação ou conforme método |
| Limite de quantificação (LQ) | 10 · s_branco / inclinação |
| Veracidade | Recuperação 80–120 % (ou conforme aplicação) |
| Repetibilidade (sr) | Conforme tabela Horwitz ou critério interno |
| Precisão intermediária | Avaliada em diferentes dias/analistas/equipamentos |
| Robustez | Plackett-Burman ou outro DOE |
| Incerteza | Conforme PT-INC-001 |

### Para ensaios físicos / mecânicos / calibração
| Parâmetro | Critério típico |
|-----------|-----------------|
| Repetibilidade | Conforme método |
| Reprodutibilidade | Conforme método |
| Histerese | Conforme método |
| Faixa | Definida e justificada |
| Incerteza | Conforme PT-INC-001 |

## 4. Plano de validação
Para cada validação, gerar um **Plano** contendo:
1. Identificação do método.
2. Justificativa.
3. Parâmetros a avaliar e critérios de aceitação.
4. Materiais, padrões e amostras.
5. Cronograma e responsáveis.
6. Tratamento estatístico previsto.

## 5. Execução
- Registro detalhado em FR-VAL-001.
- Dados brutos preservados.
- Análise estatística por planilha validada.

## 6. Relatório de validação
Inclui no mínimo:
- Procedimento de validação utilizado.
- Especificação dos requisitos.
- Determinação das características de desempenho.
- Resultados obtidos (com tratamento estatístico).
- Comparação com critérios de aceitação.
- **Declaração de validade** detalhando aptidão para o uso pretendido.
- Aprovação por pessoal autorizado.

## 7. Revalidação
Necessária quando:
- Mudança em equipamento crítico, reagente, fornecedor, matriz, faixa.
- Resultados de garantia da validade indicarem desvio.
- Após análise crítica que identifique necessidade.

## 8. Verificação (métodos normalizados)
Demonstrar capacidade de executar adequadamente. Mínimo:
- Repetibilidade no laboratório.
- Veracidade (material de referência ou comparação).
- Confirmação de LD/LQ quando aplicável.
- Avaliação de incerteza.

## 9. Histórico de revisões
| Revisão | Data | Descrição |
|---------|------|-----------|
| 00 | | Emissão inicial |
