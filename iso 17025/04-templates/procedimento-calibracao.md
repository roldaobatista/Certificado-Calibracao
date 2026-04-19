# PT-XXX — Procedimento Técnico de Calibração [Grandeza/Equipamento]

| Código | PT-XXX | Revisão | 00 | Data | __/__/____ |
|--------|--------|---------|----|------|------------|

## 1. Objetivo
Estabelecer o método para calibração de [equipamento/grandeza], em conformidade com a ABNT NBR ISO/IEC 17025:2017, item 7.2.

## 2. Faixa de aplicação
- **Grandeza:** [ex.: temperatura, massa, pressão, comprimento]
- **Faixa nominal:** de ___ a ___
- **Resolução típica:** ___
- **Tipos de instrumento atendidos:** ___

## 3. Documentos de referência
- ABNT NBR ISO/IEC 17025:2017
- VIM — Vocabulário Internacional de Metrologia (ISO/IEC Guia 99)
- GUM — Guia para a Expressão da Incerteza de Medição (ISO/IEC Guia 98-3)
- DOQ-CGCRE-008 — Orientação para a expressão da incerteza
- Normas técnicas específicas: [ex.: ISO 376, OIML R 111, etc.]

## 4. Princípio do método
[Descrever o princípio físico/metrológico da calibração: comparação direta, comparação com padrão, etc.]

## 5. Padrões e equipamentos
| Item | Identificação | Faixa | Incerteza | Calibrado por | Validade |
|------|---------------|-------|-----------|---------------|----------|
| Padrão de referência | | | | | |
| Padrão de trabalho | | | | | |
| Equipamento auxiliar | | | | | |

## 6. Condições ambientais
| Parâmetro | Faixa requerida | Como monitorar |
|-----------|-----------------|----------------|
| Temperatura | (20 ± 2) °C | Termo-higrômetro calibrado |
| Umidade relativa | (50 ± 20) % | Termo-higrômetro calibrado |
| [Outros] | | |

Aguardar **estabilização térmica mínima de [tempo]** antes do início.

## 7. Preparação
7.1. Verificar identificação inequívoca do item recebido.
7.2. Inspeção visual: ausência de danos que comprometam a calibração.
7.3. Limpeza conforme [procedimento aplicável].
7.4. Tempo de estabilização no ambiente de calibração: ___.
7.5. Verificação inicial de funcionamento.

## 8. Procedimento de medição
8.1. Definir os pontos de calibração (mínimo 3, ou conforme método): ___, ___, ___.
8.2. Para cada ponto, realizar **n repetições** (mínimo 5 / conforme método).
8.3. Registrar leituras conforme FR-XXX.
8.4. Realizar leituras em ciclos crescente e decrescente quando aplicável (avaliar histerese).
8.5. Anotar observações relevantes (oscilações, tempo de resposta, anomalias).

## 9. Cálculo dos resultados
9.1. **Erro de indicação** em cada ponto:  
E = média(I) − Vref

9.2. **Repetibilidade** (desvio padrão experimental das leituras).

9.3. **Histerese** (quando aplicável):  
H = |média_crescente − média_decrescente|

9.4. **Correção** = − Erro

## 10. Avaliação da incerteza
Conforme PT-INC-001 / GUM. Componentes mínimos a considerar:
- Incerteza do padrão de referência (tipo B)
- Repetibilidade (tipo A)
- Resolução do indicador
- Estabilidade/deriva do padrão
- Efeitos das condições ambientais
- Histerese
- Influências específicas do mensurando

Incerteza expandida U = k · uc, com **k = 2** (nível de confiança aproximado de 95 %).

## 11. Critérios de aceitação
- O equipamento é considerado adequado se o erro corrigido for ≤ [tolerância especificada].
- Quando solicitada **declaração de conformidade**, aplicar a regra de decisão acordada com o cliente (ver PG-XXX).

## 12. Registro e relato
- Registro técnico em FR-XXX (com identificação do operador, data, condições, leituras brutas).
- Emissão de **certificado de calibração** conforme modelo CC-001 (ver `04-templates/certificado-calibracao.md`).

## 13. Trabalho não conforme
Caso seja detectada inconformidade no procedimento ou padrão durante a calibração, aplicar PG-XXX (Trabalho não conforme).

## 14. Histórico de revisões
| Revisão | Data | Descrição |
|---------|------|-----------|
| 00 | | Emissão inicial |
