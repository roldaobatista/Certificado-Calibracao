---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: mapa formal das 4 sagas cross-módulo críticas do Aferê (passo → evento → handler → compensação → dono). Operacionaliza ADR-0034.
relacionados:
  - ADR-0034 (saga + compensação)
  - ADR-0033 (idempotência consumer + dead-letter)
  - ADR-0035 (tenant suspenso — saga 4)
  - ADR-0015 (lifecycle tenant)
---

# Sagas cross-módulo críticas

> **Pra quê:** auditoria Onda 1 C-INT-03 detectou que 4 fluxos cross-módulo não tinham mapa formal. Sem mapa: cada Marco implementa pedaço sem orquestrador, bug em handler N gera cascata muda. Esta doc é a fonte única — toda saga citada aqui tem code-owner declarado.

---

## Saga 1 — Orçamento → OS → Certificado → NF-e → Conta a Receber → Pagamento

**Dono:** `comercial/orcamentos` (publicador inicial); orquestrador em `operacao/os` após `Orcamento.Aprovado`.

**State machine:** `criada → os_em_execucao → cert_emitido → nf_emitida → cr_aberta → paga` (terminal) | `falhou` (terminal com motivo).

| # | Passo | Evento gatilho | Handler / efeito | Compensação | Janela compensação | Dono passo |
|---|---|---|---|---|---|---|
| 1 | Aprovar orçamento | `Orcamento.Aprovado` | Cria OS rascunho | `OS.Cancelada` (motivo ≥30 chars + audit) | Sempre disponível | `comercial/orcamentos` |
| 2 | Executar OS | `OS.Iniciada` → `OS.Concluida` | Dispara solicitação emissão cert se atividade=`calibracao` | `OS.Cancelada` + Saga.Falhou | Até `Certificado.Emitido` | `operacao/os` |
| 3 | Emitir certificado | `Atividade.Concluida` (tipo=calibracao) | `metrologia/certificados` emite + assina A3 | `Certificado.Revogado` (motivo + A3 admin + audit) | 24h sem ônus; >24h exige carta + audit cliente | `metrologia/certificados` |
| 4 | Emitir NF-e | `Certificado.Emitido` (filter `tipo_servico=calibracao`) | `fiscal` chama SEFAZ + recebe protocolo | CC-e (24h pós-emissão) ou NF-e Cancelada (≤7d SEFAZ) | 24h CC-e; ≤7d cancelamento | `fiscal` |
| 5 | Abrir conta a receber | `Fiscal.NFSeEmitida` | `financeiro/contas-receber` abre título | `ContasReceber.Estornado` se NF cancelada | Até pagamento confirmado | `financeiro/contas-receber` |
| 6 | Pagar | `ContasReceber.Pago` | Saga terminal — `concluida` | n/a (terminal) | n/a | `financeiro/contas-receber` |

**Compensação fora da janela** (>7d pós-NF-e): só via fluxo formal (devolução + nota de crédito + audit + assinatura A3 admin). INV-SAGA-003.

---

## Saga 2 — Cancelamento de certificado pós-NF emitida

**Dono:** `metrologia/certificados` (origem do cancelamento) + `fiscal` (efeito CC-e/NF cancelada).

**State machine:** `solicitada → bloqueio_uso_aplicado → cert_revogado → nf_compensada → concluida` | `falhou`.

| # | Passo | Evento gatilho | Handler / efeito | Compensação | Janela | Dono |
|---|---|---|---|---|---|---|
| 1 | Solicitar cancelamento | `Certificado.CancelamentoSolicitado` (operador + A3 + motivo ≥30 chars) | RT valida + abre Não-Conformidade ISO 17025 cl. 8.7 | n/a (passo pode ser arquivado se não aprovado) | n/a | `metrologia/certificados` |
| 2 | Aplicar bloqueio | `Certificado.BloqueioUsoAplicado` | `metrologia/equipamentos` marca certificado como "uso bloqueado"; cliente notificado | Reverter bloqueio (só antes do `Revogado`) | Antes do passo 3 | `metrologia/certificados` |
| 3 | Revogar cert | `Certificado.Revogado` | WORM: cert ganha `revogado_em` + `motivo`; PDF tem watermark; QR retorna "Revogado" | Impossível (WORM Padrão B ADR-0031) | n/a — terminal regulatório | `metrologia/certificados` |
| 4 | Compensar NF | `Certificado.Revogado` | `fiscal` decide: CC-e (≤24h pós-NF) ou Cancelamento (≤7d) ou Nota de Crédito + audit (>7d) | Re-emissão de NF se Roldão+advogado validar | conforme matriz fiscal | `fiscal` |
| 5 | Reverter CR (se aplicável) | `Fiscal.NFCancelada` ou `Fiscal.NotaCreditoEmitida` | `financeiro/contas-receber` estorna título | n/a | n/a | `financeiro/contas-receber` |

**Importante:** passo 3 (revogação) é WORM — INV-SOFT-002. Não há "des-revogar". Erro humano = nova OS de recalibração + novo cert.

---

## Saga 3 — M&A de cliente com OS aberta

**Dono:** `comercial/clientes` (origem da mescla) + `operacao/os` (efeito).

**State machine:** `mescla_solicitada → autorização_RT → mescla_aplicada → os_realocada → cert_referencia_preservada → concluida`.

| # | Passo | Evento gatilho | Handler / efeito | Compensação | Dono |
|---|---|---|---|---|---|
| 1 | Operador solicita mescla A → B | `Cliente.MesclaSolicitada` | Trava ambos clientes em `aguardando_mescla` (bloqueia novas OS) | `Cliente.MesclaAbortada` (libera trava) | `comercial/clientes` |
| 2 | Validar OS abertas | `Cliente.MesclaPreValidada` | Sistema lista OS abertas de A; exige confirmação operador | Abort se admin recusar | `comercial/clientes` |
| 3 | Aplicar mescla | `Cliente.Mesclado(vencedor=B, perdedor=A)` | Trigger PG cravado em INV-CLI-001; perdedor.cliente_canonico_id = B | Impossível pós-mescla (trigger imutável). Erro → audit + nova mescla reversa via processo manual | `comercial/clientes` |
| 4 | Realocar OS abertas | `Cliente.Mesclado` | `operacao/os` atualiza `OS.cliente_atual_id = B` (FK operacional ADR-0032 §9.1); audit grava transição | n/a | `operacao/os` |
| 5 | Preservar referência probatória | n/a (preservação por construção) | Certificados de A continuam com `cliente_referencia_hash` original (ADR-0032 §9.2) — não muta | n/a (WORM Padrão B) | `metrologia/certificados` |
| 6 | Concluir saga | `Cliente.Mesclado` | Bloquear A para criação de novos registros; manter leitura via `resolver_cliente_canonico` | n/a (terminal) | `comercial/clientes` |

---

## Saga 4 — Suspensão de tenant com NFs em vôo

**Dono:** `billing-saas` (origem) — segue matriz ADR-0035.

**State machine:** `suspensao_decidida → sagas_em_voo_drenadas → modulos_comerciais_bloqueados → modulo_lgpd_preservado → suspenso` | `reativado`.

| # | Passo | Evento gatilho | Handler / efeito | Compensação | Dono |
|---|---|---|---|---|---|
| 1 | Decidir suspensão | `BillingSaas.TenantSuspenso(modo)` | Marca tenant; publica evento | `BillingSaas.TenantReativado` (até passo 5) | `billing-saas` |
| 2 | Drenar NFs em saga | n/a (consumer) | `fiscal` finaliza NFs em `aguardando_sefaz` (Receita não aceita meia-emissão) | n/a (Receita imutável após protocolo) | `fiscal` |
| 3 | Bloquear módulos comerciais | `BillingSaas.TenantSuspenso` | Conforme matriz ADR-0035 §"Matriz vinculante" | Reativação completa (passo 5) | `acesso-seguranca`, `feature-flags`, e demais módulos |
| 4 | Preservar LGPD + retenção regulatória | n/a (continua normal por construção) | Portal-cliente + export LGPD + audit trail + leitura cert/OS/NF continuam ativos (INV-BUS-TS-002) | n/a | módulos compliance |
| 5 | Reativar | `ContasReceber.Pago` (última fatura) → `BillingSaas.TenantReativado` | Ordem: billing → acesso → features → módulos consumidores. SLA ≤5min | n/a (terminal) | `billing-saas` |

---

## Categorização (atende M-INT-05 — Domain Event / Integration Event / Notification)

| Tipo | Definição | Exemplo | Tabela |
|---|---|---|---|
| **Domain Event** | Estado mudou dentro do bounded context; não cruza módulo | `OrdemServico.AtividadeAdicionada` (interno ao módulo `operacao/os`) | tabela local do módulo |
| **Integration Event** | Cruza bounded context — entra no `outbox_events` para outros módulos consumirem | `OS.Concluida`, `Certificado.Emitido`, `Cliente.Anonimizado` | `outbox_events` |
| **Notification** | Comunicação com humano (WhatsApp, e-mail, push, SMS) — porta `OmniChannelProvider` ou `EmailTemplateProvider` | Régua D+30 cobrança | `comunicacao-omnichannel` |

Auditor `auditor-llm-correctness` valida que evento publicado no `outbox_events` está marcado como Integration. Domain Events ficam isolados — não vazam.

---

## INV agregados desta doc

- **INV-SAGA-001..004** — definidos em ADR-0034.
- **INV-BUS-TS-001..003** — definidos em ADR-0035.
- **INV-CLI-001** — preservada na saga 3 (FK probatória ADR-0032).

## Como adicionar saga nova

1. Identifica fluxo cross-módulo (≥3 módulos, ≥3 passos, compensação possível).
2. Cria seção nova nesta doc com tabela (passo / evento / handler / compensação / dono).
3. ADR-irmã se houver decisão arquitetural nova (caso contrário, basta esta doc).
4. Hook (Onda 4) valida que toda implementação de saga em `src/**` está mapeada aqui.
