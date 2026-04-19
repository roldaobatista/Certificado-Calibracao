# Principais DOQ-CGCRE para Laboratórios de Calibração

> Documentos da **Cgcre/Inmetro** mais aplicados em laboratórios de calibração acreditados ou em processo de acreditação. **Verificar revisão vigente** em https://www.gov.br/inmetro/pt-br/assuntos/acreditacao/documentos antes de aplicar.

## Documentos diretos da acreditação ISO/IEC 17025

| Código | Tema | Aplicação para lab de calibração |
|--------|------|----------------------------------|
| DOQ-CGCRE-001 | Critérios para acreditação de laboratórios | **Documento principal.** Detalha como a Cgcre aplica a 17025. Leitura obrigatória. |
| DOQ-CGCRE-002 | Tabela de equivalência terminológica | Glossário Cgcre × ISO × VIM |
| DOQ-CGCRE-008 | Orientação para expressão da incerteza em calibração | **Crítico.** Define como apresentar incerteza nos certificados |
| DOQ-CGCRE-019 | Validação de métodos analíticos | Mais aplicável a laboratórios químicos, mas usado como referência metodológica |
| DOQ-CGCRE-020 | Critérios para participação em ensaios de proficiência | Define obrigatoriedade e critérios de PT |
| DOQ-CGCRE-028 | Identificação visual / uso da marca Cgcre | Como aplicar selo em certificados e relatórios |

## Documentos sobre rastreabilidade e padrões

| Código | Tema |
|--------|------|
| DOQ-CGCRE relacionado a rastreabilidade metrológica | Política de rastreabilidade para laboratórios acreditados |
| Documentos sobre uso de materiais de referência | Critérios para MRC e MR |

## Documentos sobre incerteza

| Código | Tema |
|--------|------|
| DOQ-CGCRE-008 | Incerteza em calibração — abordagem GUM |
| Anexos para áreas específicas | Massa, dimensional, elétrica, química, etc. |

## Documentos sobre escopo de acreditação

| Código | Tema |
|--------|------|
| Documentos da série DOQ-CGCRE para laboratórios | Definição de escopo flexível e fixo |
| Política de "Calibration and Measurement Capability" (CMC) | Como declarar capacidade de medição |

## Documentos sobre transição de versões da norma

Quando a ISO/IEC 17025 é revisada, a Cgcre publica DOQ ou nota técnica orientando a transição. Para a versão 2017, foi feita transição de 3 anos encerrada em 2020.

## Documentos por área técnica de calibração

A Cgcre publica orientações específicas para algumas áreas. Verificar no portal:

| Área | Documento orientativo (verificar título atual) |
|------|------------------------------------------------|
| Massa | Orientações para calibração de balanças e pesos |
| Volume | Orientações para vidraria e medidores |
| Temperatura | Orientações para termômetros e fornos |
| Pressão | Orientações para manômetros e câmaras |
| Dimensional | Orientações para calibração dimensional |
| Elétrica | Orientações para multímetros, fontes |
| Química | Validação e MR para análises químicas |
| Acústica | Calibração de sonômetros |
| Tempo / Frequência | Calibração de osciladores |

> Nem todas essas áreas têm DOQ específico — algumas usam diretamente o DOQ-CGCRE-001 + ILAC G-series.

## Documentos ILAC adotados pela Cgcre

A Cgcre referencia diversos documentos ILAC. Consultar:

| Documento ILAC | Tema |
|----------------|------|
| ILAC P9 | Política para participação em PT |
| ILAC P10 | Política sobre rastreabilidade metrológica |
| ILAC P14 | Política sobre incerteza em calibração |
| ILAC G8 | Regras de decisão e declarações de conformidade |
| ILAC G17 | Conceito de incerteza em ensaios |
| ILAC G24 | Determinação de intervalos de calibração |

Disponíveis em: https://ilac.org/publications-and-resources

## Periodicidade de revisão

A Cgcre revisa os DOQ-CGCRE em intervalos variáveis, frequentemente em decorrência de:
- Atualização da ISO/IEC 17025.
- Atualização de documentos ILAC.
- Mudanças regulatórias internas.

**Recomendação:** revisar a lista do portal Cgcre **mensalmente** e atualizar os exemplares baixados.

## Como anexar um DOQ nesta pasta

1. Baixar o PDF da versão **vigente** (verificar campo "Revisão" no documento).
2. Salvar como `doq-cgcre-<numero>-rev<n>.pdf`.
3. Criar ficha resumo `doq-cgcre-<numero>.md` com:
   - Número e revisão
   - Data de aprovação e vigência
   - Objeto
   - Aplicabilidade
   - Resumo das principais exigências
   - Documentos relacionados (ISO, ILAC)
4. Quando houver mudança de revisão, criar `doq-cgcre-<numero>-changelog.md`.

## Fluxo recomendado de uso

```
Norma ISO/IEC 17025  ──►  DOQ-CGCRE-001  ──►  DOQ específico da área
       (base)              (interpretação)       (incerteza, validação,
                                                  PT, marca, etc.)
```
