---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Calibração

> Termos específicos. Transversais em `docs/comum/glossario.md`. Termos de emissão (numeração, reemissão, etc.) em `../certificados/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Calibração | Operação que estabelece relação entre valores indicados pelo instrumento e valores fornecidos por padrão | "aferição" (proibido — termo técnico distinto) | Procedimento metrológico em execução | VIM 2012 |
| Padrão | Material/instrumento/sistema que materializa uma unidade de medida com valor conhecido | "referência" (ambíguo) | Instrumento usado pra calibrar outro | VIM 2012 |
| Padrão primário | Padrão de mais alta qualidade metrológica no contexto | — | Topo da cadeia de rastreabilidade | VIM 2012 |
| Peso padrão | Massa padrão para calibração de balanças, classificada por OIML R111 | "peso de referência" | Massa rastreável | OIML R111 |
| Classe (E1/E2/F1/F2/M1/M2/M3) | Categoria de exatidão do peso padrão | — | Limites de erro definidos | OIML R111 |
| Valor convencional | Valor atribuído ao padrão no certificado da última calibração externa | "valor verdadeiro" (proibido — incerto) | Valor de uso no cálculo | VIM 2012 |
| Rastreabilidade metrológica | Propriedade do resultado relacionado a referências por cadeia ininterrupta de comparações com incertezas declaradas | — | Cadeia: instrumento → padrão lab → padrão externo → padrão nacional → SI | VIM 2012 + ISO 17025 6.5 |
| Incerteza de medição | Parâmetro associado ao resultado que caracteriza dispersão dos valores razoavelmente atribuíveis ao mensurando | "erro" (proibido — distinto) | Faixa em torno do valor medido | GUM (JCGM 100) |
| Incerteza padrão | Incerteza expressa como desvio padrão | "u" minúsculo | Componente individual | GUM |
| Incerteza combinada | Combinação RSS das incertezas-padrão de cada componente | "uc" | Antes da expansão | GUM |
| Incerteza expandida | Incerteza combinada multiplicada pelo fator de abrangência (geralmente k=2 para ~95%) | "U" maiúsculo | Reportada no certificado | GUM |
| Fator de abrangência (k) | Multiplicador (geralmente k=2 para 95.45%) | — | Define nível de confiança | GUM |
| Orçamento de incerteza | Tabela listando todos os componentes de incerteza, distribuição, tipo (A/B), contribuição | "tabela de incerteza" | Detalhamento auditável | GUM |
| Tipo A | Componente avaliado por análise estatística de série de observações | — | Calculado dos dados | GUM |
| Tipo B | Componente avaliado por outros meios (especificação, certificado, julgamento) | — | Vem de fonte externa | GUM |
| Regra de decisão | Critério pra declarar conformidade considerando incerteza | — | Configurada antes de calibrar | ILAC G8 + ISO 17025 7.8.6 |
| Banda de guarda | Método de regra de decisão que reduz a especificação pela incerteza para minimizar risco do consumidor | — | Critério mais conservador | ILAC G8 |
| Zona de incerteza | Resultado em que incerteza cruza a especificação — exige decisão explícita | — | Não-decidível automaticamente | ILAC G8 |
| Linearidade | Capacidade do instrumento manter erro constante ao longo da faixa | — | Ensaio típico de balanças | OIML R76 |
| Repetibilidade | Concordância entre resultados de medições sucessivas nas mesmas condições | "reprodutibilidade" (proibido — distinto) | Mesma operadora, curto prazo | VIM 2012 |
| Reprodutibilidade | Concordância em condições variadas (operador, hora, etc.) | — | Outra coisa: condições diferentes | VIM 2012 |
| Excentricidade | Variação da indicação quando carga é aplicada em posições diferentes do prato | "off-center" | Ensaio típico de balanças | OIML R76 |
| Verificação intermediária | Verificação simples entre calibrações externas pra confirmar estabilidade | — | Não substitui calibração externa | ISO 17025 6.4.10 |
| Comparação interlaboratorial | Comparação de medições entre laboratórios sobre mesmos itens | — | Programada periodicamente | ISO/IEC 17043 |
| Ensaio de proficiência | Avaliação do desempenho de laboratório por comparação interlaboratorial | — | Provedor terceiro avalia | ISO/IEC 17043 |
| Escore z | Indicador de desempenho em ensaio de proficiência: \|z\|≤2 satisfatório, 2<\|z\|<3 questionável, ≥3 insatisfatório | — | Resultado do ensaio | ISO 13528 |
| Escopo de acreditação | Documento CGCRE que define grandezas, faixas e métodos acreditados | — | Limita o que sai com RBC | NIT-DICLA-031 |
| CMC (Capacidade de Medição e Calibração) | Menor incerteza que o lab consegue oferecer em rotina | — | Limite inferior de incerteza | NIT-DICLA |
| Drift | Variação contínua da indicação ao longo do tempo | — | Detectável em histórico | VIM 2012 |
| Condições ambientais | Temperatura, umidade, pressão durante a calibração | — | Fonte de incerteza Tipo B | — |
| Segunda conferência | Revisão independente por outro RT, requisito de qualidade ISO 17025 7.7 | "dupla checagem" | Etapa obrigatória antes de aprovar | ISO 17025 7.7 |
| Mensurando | Grandeza que se pretende medir | "medido" (proibido) | O que está sendo calibrado | VIM 2012 |

---

## Como esta lista evolui

- Termo novo → verificar conflito com glossário comum + Certificados.
- Deprecado → `@deprecated` + janela 3 meses.
- Mudança de definição → CHANGELOG + aviso.

## Convenções

- PT-BR. Termos VIM/GUM com origem citada.
- 1 linha. Detalhes em `docs/explicacoes/`.
