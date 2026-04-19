# RTMs por Instrumento — Referência para Calibração

> Lista dos **Regulamentos Técnicos Metrológicos** mais relevantes por tipo de instrumento. Laboratórios que calibram estes instrumentos devem conhecer o RTM aplicável porque ele define **erros máximos admissíveis (EMA)**, **classes de exatidão**, **condições de ensaio** e **requisitos metrológicos** que servem de referência técnica.

> **Verificar vigência em https://www.gov.br/inmetro/pt-br/assuntos/metrologia-legal**

## Massa e pesagem

| Instrumento | Portaria de aprovação do RTM | Observação |
|-------------|------------------------------|------------|
| **Balanças não automáticas (IPNA)** | **Portaria Inmetro nº 157/2022** — vigente desde 02/01/2023. Revogou a Portaria 236/1994 | Classes I, II, III, IIII (base OIML R 76). Ver [ficha](../portarias/portaria-157-2022.md) |
| Balanças automáticas | Portarias específicas por tipo (ensacadeiras, seletoras, rodoviárias, ferroviárias) | Verificar portaria vigente por tipo |
| **Pesos padrão (massas)** | **Portaria Inmetro nº 289/2021** | 1 mg a 50 kg; classes E1, E2, F1, F2, M1, M2, M3 (base OIML R 111). Ver [ficha](../portarias/portaria-289-2021.md) |
| Pré-medidos por massa/volume | Portaria Inmetro nº 248/2008 + Portaria 350/2012 (Portaria 93/2022 que as substituiria foi suspensa pela 70/2024) | Ver [ficha 248/2008](../portarias/portaria-248-2008.md) |

## Pressão

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Manômetros, vacuômetros e manovacuômetros | Portaria Inmetro nº 470/2008 |
| Esfigmomanômetros (pressão arterial) | Portaria específica — verificar vigente |

## Temperatura

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Termômetros clínicos de mercúrio/digitais | Portaria Inmetro nº 154/2005 |
| Termo-higrômetros | Portaria Inmetro nº 30/2007 |

## Dimensional

| Instrumento | Observação |
|-------------|------------|
| Paquímetros, micrômetros, trenas | Raramente sujeitos a metrologia legal, mas a calibração segue normas ISO/ABNT |
| Trenas usadas em comércio | Portarias específicas — verificar |

## Volume / Vazão

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Hidrômetros | Portaria Inmetro nº 246/2000 e atualizações |
| Medidores de gás tipo diafragma/residenciais | Portaria específica |
| Medidores de gás industriais (turbina, rotativo) | Portaria específica |
| Bombas medidoras de combustíveis líquidos | Portaria específica |
| Medidores tipo Coriolis / ultrassônicos (fiscais) | Portarias específicas |
| Medidores de água quente | Portaria específica |

## Eletricidade

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Medidores de energia elétrica (eletromecânicos e eletrônicos) | Portarias específicas |
| Medidores multifuncionais | Portaria específica |
| Etilômetros (bafômetros) | Portaria Inmetro nº 587/2012 |

## Tempo

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Cronotacógrafos | Portaria Inmetro nº 222/2009 |
| Taxímetros | Portaria específica |

## Trânsito / Velocidade

| Instrumento | Portaria de aprovação do RTM |
|-------------|------------------------------|
| Medidores de velocidade (radares) | Portaria Inmetro nº 115/1998 e atualizações |

## Outros

| Instrumento | Observação |
|-------------|------------|
| Opacímetros | Controle de emissão veicular |
| Analisadores de gases veiculares | Controle de emissão |
| Densímetros | Controle de combustíveis |

## Estrutura típica de um RTM — o que o laboratório encontra

1. **Escopo e campo de aplicação**
2. **Definições metrológicas** (mensurando, campo de medição)
3. **Classe de exatidão / classe metrológica**
4. **Erros máximos admissíveis (EMA)** em cada etapa (aprovação de modelo, verificação inicial, em serviço)
5. **Condições de referência** (T, UR, estabilização)
6. **Condições limites de funcionamento**
7. **Procedimentos de ensaio** para aprovação e verificação
8. **Selagem e marcas obrigatórias**

## Uso prático no laboratório

- **Critério de aceitação na calibração:** EMA do RTM pode ser usado como especificação quando solicitado pelo cliente.
- **Regra de decisão (7.8.6 da ISO 17025):** quando o cliente solicita declaração de conformidade, pode-se referenciar o EMA do RTM.
- **Periodicidade de calibração:** RTMs estabelecem periodicidade da **verificação metrológica**, que é diferente da calibração — mas geralmente define limite prático para intervalos.

## Diferença: Calibração vs. Verificação Metrológica

| Aspecto | Calibração | Verificação Metrológica |
|---------|------------|-------------------------|
| Quem faz | Lab acreditado ISO 17025 | Inmetro/IPEM ou delegado |
| Resultado | Certificado de calibração com erros e incerteza | Aprovado/Reprovado |
| Obrigatoriedade | Voluntária (ou exigida contratualmente) | Obrigatória para instrumentos sujeitos |
| Periodicidade | Definida pelo usuário/critério técnico | Definida por RTM/portaria |
| Objetivo | Quantificar erro para correção/rastreabilidade | Atestar conformidade com RTM |

## Como anexar um RTM nesta pasta

1. Baixar o PDF do anexo técnico da portaria que aprovou o RTM.
2. Salvar como `rtm-<instrumento>-portaria-<num>-<ano>.pdf`.
3. Criar ficha `rtm-<instrumento>.md` com:
   - Portaria de aprovação
   - Campo de medição
   - Classes de exatidão
   - EMA por classe/etapa
   - Condições de ensaio
   - Periodicidade de verificação
