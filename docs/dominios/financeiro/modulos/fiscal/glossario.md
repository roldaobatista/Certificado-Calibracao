---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Glossário — Fiscal (NFS-e + NFe)

| Termo | Definição |
|---|---|
| **NFS-e** | Nota Fiscal de Serviço eletrônica — municipal. Padrão majoritário em calibração. |
| **NFe** | Nota Fiscal eletrônica — estadual. Aplicável quando tenant vende produtos (peças). |
| **ABRASF** | Padrão de NFS-e adotado por ~70% dos municípios brasileiros. |
| **Padrão CONFAZ 95/22** | Novo padrão nacional unificado de NFS-e — cutover 01/09/2026 (Dor #10). |
| **Município emissor** | Município onde o serviço é prestado; determina padrão NFS-e usado. |
| **PlugNotas / Focus NFe** | BaaS (NFe-as-a-service) escolhido pra abstrair padrões municipais — ver ADR-0008. |
| **CC-e** | Carta de Correção eletrônica — corrige erros não-monetários e não-identitários em NFS-e/NFe. |
| **Cancelamento** | Anulação da nota. Padrão: < 24h. Extemporâneo: variável por município. |
| **Inutilização de numeração** | Quando salta um número (emissão falhou); precisa registrar formalmente o "buraco". |
| **SVC-AN / SVC-RS** | Sefaz Virtual de Contingência (Nacional / Rio Grande do Sul). |
| **EPEC** | Evento Prévio de Emissão em Contingência — válido 168h, regulariza depois. |
| **Contingência** | Estado quando SEFAZ/município está fora; emissão continua via mecanismo alternativo (INV-007). |
| **A1 / A3** | Tipos de certificado digital ICP-Brasil. A1 = arquivo; A3 = token/cartão. Ver ADR-0009. |
| **ICP-Brasil** | Infraestrutura de Chaves Públicas brasileira; obrigatória pra assinar NF. |
| **ISS** | Imposto sobre Serviços; alíquota 2-5% varia por município (LC 116/2003). |
| **Código de serviço LC 116** | Classificação obrigatória do serviço prestado; calibração tem código específico. |
| **Substituição tributária** | Regime onde tomador retém imposto na fonte. |
| **WORM** | Write Once Read Many — armazenamento imutável de XML (retenção 5 anos). |
| **SPED** | Sistema Público de Escrituração Digital — export pra contador (V2). |

## Decisões críticas

- **Aferê NÃO calcula imposto** — exibe campos pra tenant configurar com contador dele (ver `modelo-de-dominio.md`).
- **Fiscal pluggable** — abstração via FiscalProvider (ADR-0008), troca entre PlugNotas/Focus sem mudar consumidor.
- **A3 assina onde?** — definido em ADR-0009 (impacta UX de assinatura).

## Referências

- ADR-0008, ADR-0009
- `docs/conformidade/comum/fiscal.md`
- `docs/conformidade/comum/fiscal-contingencia.md`
- `docs/comum/integracoes-externas/plugnotas.md`, `focus-nfe.md`, `sefaz-municipios.md`
- INV-007 (NF-e contingência desde dia 0)
