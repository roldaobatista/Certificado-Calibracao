# PT-INC-001 — Avaliação da Incerteza de Medição

| Código | PT-INC-001 | Revisão | 00 | Data | __/__/____ |
|--------|------------|---------|----|------|------------|

## 1. Objetivo
Estabelecer a metodologia para identificação, quantificação e combinação de fontes de incerteza, atendendo ao item 7.6 da ABNT NBR ISO/IEC 17025:2017 e aos princípios do GUM.

## 2. Documentos de referência
- ISO/IEC Guia 98-3 (GUM) — Avaliação da incerteza de medição
- ISO/IEC Guia 99 (VIM) — Vocabulário Internacional de Metrologia
- DOQ-CGCRE-008 — Orientação para a expressão da incerteza
- NIT-DICLA-021 — Expressão da incerteza de medição

## 3. Etapas

### 3.1 Modelagem do processo de medição
Definir o **modelo matemático** que relaciona o mensurando Y com as grandezas de entrada X1, X2, …, Xn:

> Y = f(X1, X2, …, Xn)

### 3.2 Identificação das fontes de incerteza
Diagrama de Ishikawa ou listagem estruturada. Fontes típicas:
- Padrão de referência (do certificado)
- Repetibilidade do procedimento
- Resolução do indicador
- Estabilidade/deriva do padrão
- Influências ambientais (T, UR, pressão)
- Histerese, linearidade, deriva do instrumento
- Operador
- Método (modelo aproximado)

### 3.3 Quantificação de cada fonte (componentes u(xi))

#### Tipo A — análise estatística de série de observações
- Desvio padrão experimental da média:  
  s(x̄) = s(x) / √n
- u(xi) = s(x̄)
- Graus de liberdade: ν = n − 1

#### Tipo B — informação prévia (certificado, especificação, julgamento)
| Distribuição | u(xi) |
|--------------|-------|
| Normal (do certificado, com k informado) | U / k |
| Retangular (limites ±a) | a / √3 |
| Triangular (limites ±a) | a / √6 |
| U (forma de U, ±a) | a / √2 |

### 3.4 Coeficientes de sensibilidade
ci = ∂Y / ∂Xi (avaliados nos valores nominais).

### 3.5 Incerteza combinada
Para fontes não correlacionadas:

> uc(y) = √( Σ (ci · u(xi))² )

### 3.6 Graus de liberdade efetivos (Welch–Satterthwaite)

> νef = uc⁴ / Σ ((ci · u(xi))⁴ / νi)

### 3.7 Fator de abrangência k
- Usual: **k = 2** para nível de confiança ≈ 95 % (νef alto).
- Quando νef baixo, consultar tabela t-Student bicaudal e adotar k = t(95 %; νef).

### 3.8 Incerteza expandida
> U = k · uc

### 3.9 Expressão final
> Y = y ± U, com k = ___, p ≈ 95 %, νef = ___

Arredondamento: 2 algarismos significativos para U; valor de y arredondado ao mesmo nível decimal.

## 4. Modelo de Balanço de Incerteza

| Fonte (Xi) | Estimativa xi | Distribuição | Limite ou s(x) | Divisor | u(xi) | ci | ci·u(xi) | ci·u(xi)² | νi |
|------------|---------------|--------------|----------------|---------|-------|----|----------|-----------|----|
| Padrão de referência | | Normal (k=2) | | 2 | | | | | ∞ |
| Repetibilidade | | Normal | | 1 | | | | | n−1 |
| Resolução | | Retangular | a = res/2 | √3 | | | | | ∞ |
| Deriva do padrão | | Retangular | | √3 | | | | | ∞ |
| Influência ambiental | | Retangular | | √3 | | | | | ∞ |
| ... | | | | | | | | | |
| **uc²** | | | | | | | | **Σ** | |
| **uc** | | | | | | | | √ Σ | |
| **νef** | | | | | | | | | |
| **k** | | | | | | | | | |
| **U** | | | | | | | | | |

## 5. Reavaliação
A avaliação deve ser revisada quando:
- O método ou equipamento mudar.
- Houver mudança significativa nas condições.
- A análise crítica indicar inadequação.
- Em prazo máximo de **2 anos** ainda que sem alterações.

## 6. Histórico de revisões
| Revisão | Data | Descrição |
|---------|------|-----------|
| 00 | | Emissão inicial |
