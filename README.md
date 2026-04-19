# Certificado de Calibração

Repositório de estudo e especificação para um **aplicativo Android de emissão de certificados de calibração de balanças**, com base na ABNT NBR ISO/IEC 17025 e no ecossistema regulatório do Inmetro/Cgcre.

O objetivo é tratar o produto como **plataforma metrológica móvel** — não apenas como gerador de PDF — cobrindo ciclo completo: cadastro, execução guiada, cálculo com incerteza, revisão técnica, assinatura, emissão e verificação do certificado.

## Estrutura do repositório

| Pasta / Arquivo | Conteúdo |
|-----------------|----------|
| [`ideia.md`](./ideia.md) | PRD funcional do app: arquitetura, módulos, telas, fluxos, regras de negócio, backlog e critérios de aceite do MVP |
| [`iso 17025/`](./iso%2017025) | Material de apoio sobre a norma — visão geral, requisitos, checklists, templates, atualizações e referências |
| [`normas e portarias inmetro/`](./normas%20e%20portarias%20inmetro) | Índices oficiais de portarias, RTAC, RTM, DOQ-CGCRE, NIT-DICLA e resoluções Conmetro aplicáveis a laboratórios de calibração |

## Como navegar

1. Comece por [`ideia.md`](./ideia.md) para entender o escopo do produto e as regras de negócio.
2. Consulte [`iso 17025/`](./iso%2017025) para os requisitos normativos que o app precisa sustentar.
3. Use [`normas e portarias inmetro/`](./normas%20e%20portarias%20inmetro) como referência regulatória brasileira (RTM de IPNA, orientações Cgcre, etc.).

## Base normativa

- **ABNT NBR ISO/IEC 17025:2017** — competência, imparcialidade e operação consistente de laboratórios.
- **Portaria Inmetro nº 157/2022** — Regulamento Técnico Metrológico para instrumentos de pesagem não automáticos (IPNA).
- **Cgcre/Inmetro** — rastreabilidade, relato de resultados, declaração de conformidade, CMC e consulta pública de escopo RBC.
- **ILAC P10 / P14** — rastreabilidade e incerteza de medição.
- **EURAMET cg-18** — boa prática para calibração de NAWI (referência, não obrigatória).

## Premissas do produto

- Resultado e incerteza **nunca** são omitidos em certificado com declaração de conformidade.
- Certificado de calibração **não tem validade automática** — a periodicidade é do proprietário.
- Padrão vencido, sem certificado ou fora da faixa **bloqueia** a emissão.
- Execução offline com sincronização posterior; "oficial" só após validação do backend.
- Arquitetura preparada para **DCC (Digital Calibration Certificate)**.

## Status

Projeto em fase de **especificação**. Próximos passos estão listados na seção final de [`ideia.md`](./ideia.md).

## Contribuição

Este repositório concentra material de estudo e especificação. Sugestões técnicas e referências normativas adicionais são bem-vindas via pull request.
