---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: glossário PT-BR canônico do produto Aferê com correspondências EN (libs/integrações) e ISO/VIM (metrologia). Fonte única do nome de classe de domínio.
relacionados:
  - ADR-0037 (glossário PT-EN canônico)
  - D3 (nomenclatura híbrida)
  - ADR-0029 (canonicalização texto probatório)
---

# Glossário canônico Aferê

> **Pra quê:** evitar drift "Cliente vs Customer", "Equipamento vs Asset", "OS vs WorkOrder". Toda classe de domínio nova consulta esta tabela antes de nascer.

---

## 1. Conceitos comerciais

| PT-BR canônico | EN (apenas em adapter/borda) | ISO/Vim/Padrão | Notas |
|---|---|---|---|
| Cliente | Customer (adapter) | n/a | Pessoa/empresa que contrata o tenant. **Nunca** "Customer" em domínio. |
| Tenant | Tenant (mantém EN — D3) | n/a | Empresa cliente do Aferê (SaaS). |
| Orçamento | Quote (adapter) | n/a | Proposta comercial pré-OS. |
| Contrato | Contract (adapter) | n/a | Vínculo comercial recorrente. |
| Assinatura (SaaS) | Subscription (adapter) | n/a | Vínculo billing-saas do tenant. |
| Plano | Plan (adapter) | n/a | Catálogo de planos comerciais (billing-saas). |
| Fatura | Invoice (adapter) | n/a | Cobrança billing-saas (Aferê → tenant). |

## 2. Operação

| PT-BR canônico | EN | ISO/Vim | Notas |
|---|---|---|---|
| Ordem de Serviço (OS) | Service Order / Work Order (adapter) | n/a | Ver ADR-0023. **Nunca** `WorkOrder` em domínio. |
| Atividade da OS | Activity | n/a | ADR-0023 — 1 OS contém N atividades. |
| Técnico | Technician | n/a | Colaborador do tenant que executa atividade. |
| Agenda | Schedule | n/a | Planejamento de alocação de técnico. |
| Recebimento Provisório | Provisional Receipt | n/a | Item recebido sem cadastro completo (US-EQP-006). |

## 3. Metrologia (ISO/IEC 17025 + VIM 4ª ed.)

| PT-BR canônico | EN | VIM/ISO ref | Notas |
|---|---|---|---|
| Calibração | Calibration | VIM 2.39 | **Mantém PT em domínio**; EN só na borda. |
| Equipamento | Instrument / Asset (borda externa) | VIM 4.1 (instrumento de medição) | Em domínio Aferê = `Equipamento`. |
| Padrão | Measurement Standard | VIM 5.1 | Padrão metrológico (não "template"). |
| Procedimento | Procedure | ISO 17025 cl. 7.2 | Método/instrução de trabalho. |
| Certificado | Certificate | ISO 17025 cl. 7.8 | Certificado de calibração. |
| Incerteza Expandida | Expanded Uncertainty | VIM 2.35 + GUM | VO `IncertezaExpandida` (U + k + nível). |
| Grandeza | Quantity | VIM 1.1 | Grandeza física (massa, comprimento, ...). |
| Faixa de medição | Measurement Range | VIM 4.7 | VO `FaixaMedicao`. |
| Rastreabilidade Metrológica | Metrological Traceability | VIM 2.41 | Cadeia até INMETRO/RBC/SI. |
| Não Conformidade (NC) | Nonconformity | ISO 17025 cl. 7.10 + 8.7 | Entidade **única** cross-módulo (`qualidade.NaoConformidade`). |
| Responsável Técnico (RT) | Technical Manager (adapter) | ISO 17025 cl. 6.2 + NIT-DICLA-021 | Domínio = `ResponsavelTecnicoTenant`. |
| Verificação Intermediária | Intermediate Check | ISO 17025 cl. 6.4.10 | Controle periódico de padrão. |
| Comparação Interlaboratorial | Proficiency Testing (PT) | ISO/IEC 17043 | Acreditação RBC. |
| Regra de Decisão | Decision Rule | ISO 17025 cl. 7.8.6 + JCGM 106 | Ver ADR-0024. |

## 4. Financeiro / Fiscal

| PT-BR canônico | EN | Padrão | Notas |
|---|---|---|---|
| Conta a Receber | Accounts Receivable (adapter) | n/a | Domínio = `ContasReceber`. |
| Conta a Pagar | Accounts Payable (adapter) | n/a | Domínio = `ContasPagar`. |
| NF-e / NFS-e | n/a (sigla canônica) | ENCAT NT 2013/007 | Mantém sigla PT. |
| Carta de Correção (CC-e) | n/a (sigla canônica) | n/a | Mantém sigla PT. |
| Comissão | Commission (adapter) | n/a | Domínio = `Comissao`/`Comissoes`. |
| Despesa | Expense (adapter) | n/a | Domínio = `Despesa`. |
| Caixa do Técnico | Technician Cash (adapter) | n/a | Domínio = `CaixaTecnico`. |

## 5. Segurança / Compliance

| PT-BR canônico | EN | Padrão | Notas |
|---|---|---|---|
| Titular (LGPD) | Data Subject | LGPD art. 5º V | Pessoa cujo dado é tratado. **Nunca** "Subject" em domínio. |
| Operador / Controlador | Operator / Controller | LGPD art. 5º VI/VII | Aferê = operador (na maioria); tenant = controlador. |
| Encarregado (DPO) | Data Protection Officer | LGPD art. 41 | Domínio = `Encarregado` (PT canônico). |
| Anonimização | Anonymization | LGPD art. 5º XI | Ver ADR-0021. |
| Pseudonimização | Pseudonymization | LGPD art. 13 §4º | Hash com chave separada. |
| Base Legal | Lawful Basis | LGPD art. 7º/11 | Domínio = `BaseLegal` (PT canônico). |
| Assinatura Digital A3 | A3 Digital Signature | MP 2.200-2 + Lei 14.063 | Mantém A3 (sigla canônica). |
| Trilha de Auditoria | Audit Trail | LGPD art. 37 | Domínio = `auditoria` / `audit_trail`. |
| Auditor | Auditor | n/a | Família 5 — auditor mecânico (não confundir com auditor RBC/CGCRE). |

## 6. Bus / Integração

| PT-BR canônico | EN | Notas |
|---|---|---|
| Evento de Domínio | Domain Event | Mudou estado dentro do bounded context (não publica externo). |
| Evento de Integração | Integration Event | Cruza bounded context (entra em `outbox_events`). |
| Notificação | Notification | Comunicação com humano (WhatsApp, e-mail). |
| Comando | Command | Pedido para o sistema agir (não usado como nome de tabela). |
| Saga | Saga / Process Manager | Ver ADR-0034. Mantém EN (termo técnico). |
| Compensação | Compensation | Ver ADR-0034. PT canônico. |
| Outbox | Outbox (mantém EN — termo técnico) | Tabela `outbox_events`. |
| Dead-letter | Dead-letter (mantém EN) | Tabela `dead_letter_events` — ADR-0033. |
| Idempotência | Idempotency | Mantém PT (`consumer_idempotencia`). |

## 7. Vigência / Soft-delete (ADRs 0030/0031)

| Conceito | Campo canônico | ADR |
|---|---|---|
| Início de vigência | `vigencia_inicio` | 0030 |
| Fim de vigência | `vigencia_fim` | 0030 |
| Revogação (Padrão B) | `revogado_em` + `motivo_revogacao` | 0030/0031 |
| Soft-delete (Padrão C) | `deletado_em` | 0031 |
| Estado-máquina (Padrão A) | `estado` + `<Entidade>EventoStatus` | 0031 |

## 8. Como navegar

- Vou criar classe `Customer` em `src/domain/comercial/`. → Não. Consultar §1 → `Cliente`.
- Vou criar `WorkOrder` em `src/domain/operacao/`. → Não. Consultar §2 → `OrdemServico` (em código: `OS` é nome do app/módulo; classe = `OrdemServico` ou `OS`).
- Vou nomear coluna `deleted_at` no banco. → Não. Consultar §7 → `deletado_em`.
- Vou nomear tabela `dead_letters`. → Sim. §6 permite EN técnico.

## 9. Como adicionar termo

1. PR adiciona linha na seção apropriada.
2. CODEOWNERS (`docs/comum/glossario.md` listado) força review do tech-lead.
3. Hook `glossario-dominio-check.sh` (a criar Onda 4) bloqueia nome de classe de domínio inexistente no glossário **se** termo está mapeado (não bloqueia nomes novos — só drifts em termos catalogados).
