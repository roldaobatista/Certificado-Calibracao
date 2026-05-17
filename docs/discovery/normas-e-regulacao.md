# Discovery — Normas e regulação

> **Artefato Rodada 0** (agente faz sozinho). Mapeamento de TODAS as normas e regulações que afetam cada módulo do produto.

---

## Pra preencher quando Rodada 0 iniciar

### Por módulo / domínio

#### Domínio Metrologia (Calibração)
- **ISO/IEC 17025:2017** — cláusulas relevantes (já mapeadas no draft):
  - 4.2 Confidencialidade
  - 6.2 Pessoal
  - 6.5 Rastreabilidade metrológica
  - 7.7 Garantia da validade dos resultados
  - 7.8 Relato dos resultados
  - 7.10 Trabalho não conforme
  - 7.11 Controle de dados e gerenciamento da informação
  - 8.3 Controle de documentos
  - 8.4 Controle de registros
  - 8.5 Ações para abordar riscos e oportunidades
  - 8.6 Melhoria
  - 8.7 Ação corretiva
- **RBC NIT-DICLA-021** — requisitos pra signatário técnico
- **VIM 4ª ed.** — Vocabulário Internacional de Metrologia (glossário)
- **ILAC G8 / EURACHEM** — validação de software metrológico
- **NIT-DICLA-030** — emissão de certificados

#### Domínio Financeiro
- **Lei Complementar 116/2003** — ISS / NFS-e
- **NF-e — Modelo 55** — Ajuste SINIEF 07/05, Manual de Orientação
- **NFS-e Nacional** — Resolução CGSN 169/2022 (cutover 2026)
- **NFS-e municipal** — padrão por município (ABRASF 2.x, próprio, ISSNet, Ginfes, Tinus)
- **SPED Fiscal / Contábil** — exigências de retenção
- **eFinanceira** — se aplicável
- **Receita Federal** — retenção 5 anos (Decreto 3000/99 + LC 116)
- **Bacen 4.658/2018** — cibersegurança se integrar bancos
- **Open Finance** — Resolução BCB 32/2020

#### Domínio Operação (OS, Chamados)
- (sem regulação específica direta, mas LGPD se aplica a dados de cliente)

#### Domínio Comercial (CRM, Orçamentos)
- **LGPD** — base legal pra dados de prospect
- **CDC** — quando orçamento aprovado virar contrato

#### Transversal
- **LGPD (Lei 13.709/2018)** + Resolução ANPD 15/2024 (comunicação incidente 72h)
- **Marco Civil da Internet (Lei 12.965/2014)** — log retention
- **PCI-DSS** — se aceitar pagamento online
- **Acessibilidade (Lei 13.146/2015 + WCAG)**

### Matriz município × padrão NFS-e (Auditor 5 v2 alertou)

| Município | Padrão | Provedor homologado | Plano fallback |
|---|---|---|---|
| São Paulo SP | (próprio) | (a confirmar) | |
| Rio de Janeiro RJ | (próprio) | | |
| Belo Horizonte MG | (próprio) | | |
| Curitiba PR | (próprio) | | |
| Demais | ABRASF 2.x ou Nacional | | |

### Contingência fiscal (a detalhar em `conformidade/comum/fiscal-contingencia.md`)

- SVC-AN / SVC-RS (SCAN desativado em 2018)
- EPEC (Evento Prévio de Emissão em Contingência)
- CC-e (Carta de Correção, art. 7º Ajuste SINIEF 07/05)
- Cancelamento NF-e (até 24h)
- Inutilização de numeração

### Retenção (a detalhar em `conformidade/comum/retencao-matriz.md`)

Matriz `dado × base legal × prazo × destino pós-prazo`:
- NF-e XML: 5 anos (Receita) + arquivo permanente
- Certificado calibração: 5 anos mínimo / ciclo de vida do instrumento (RBC NIT-DICLA-021)
- Log Marco Civil: 6 meses
- Dado pessoal de cliente PF: até término do contrato + (5 anos fiscal OU exclusão LGPD a pedido)
- Dado de técnico signatário: 25 anos (rastreabilidade certificado)

---

## Como preencher

- Agente lê documentos oficiais (INMETRO, ANPD, Receita, Bacen).
- Cita fonte de cada cláusula.
- Valida com `discovery/spikes-tecnicos/` quando aplicável (ex: emitir NF-e teste em município com padrão próprio).

## Saída esperada

- Lista completa de normas
- Matriz município × padrão NFS-e priorizada
- Lista de invariantes a criar (entrada pra `REGRAS-INEGOCIAVEIS.md`)
- Lista de docs a criar em `conformidade/comum/` e `dominios/metrologia/modulos/calibracao/`
