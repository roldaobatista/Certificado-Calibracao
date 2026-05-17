---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Integrações entre módulos — eventos + contratos

> **Pra quê:** módulos do Aferê (`os`, `calibracao`, `fiscal`, `financeiro`, etc.) se comunicam via eventos. Sem contrato versionado, mudança em `os` quebra `calibracao` silenciosamente.

---

## Princípio

Módulo NÃO chama módulo direto.

- ❌ `calibracao.views.emit` importa `os.models.OS` → acoplamento direto
- ✅ `os.tasks` publica evento `OSConcluida` → handler em `calibracao` cria certificado

---

## Bus de eventos

Implementação (ADR-0007): **outbox pattern com procrastinate**.

```
1. App muda estado no DB + insere linha em `outbox_events` (mesma transação)
2. procrastinate worker lê outbox + dispatcha handlers
3. Handler é idempotente (chave do evento)
4. Outbox marca evento como processado
```

Vantagem: sem broker externo (Kafka, RabbitMQ) no MVP-1; PostgreSQL basta. Pode migrar pra broker quando volume justificar.

---

## Catálogo de eventos (incremental — ampliar quando módulo existir)

### Domínio: OS

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `OSAberta` | `os.usecase.abrir_os` | `{tenant_id, os_id, cliente_id, tipo, abertura_at}` | `crm` (atualiza timeline), `mobile.sync` |
| `OSAtribuida` | `os.usecase.atribuir_tecnico` | `{tenant_id, os_id, tecnico_id, atribuicao_at}` | `mobile.sync` (push) |
| `OSConcluida` | `os.usecase.concluir_os` | `{tenant_id, os_id, conclusao_at, tipo}` | `calibracao` (cria certificado rascunho se tipo=calibração), `crm`, `mobile.sync` |
| `OSCancelada` | `os.usecase.cancelar_os` | `{tenant_id, os_id, razao, cancelamento_at}` | `financeiro` (cancela cobrança se aplicável), `crm` |

### Domínio: Calibração

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `CertificadoEmitido` | `calibracao.usecase.emitir` | `{tenant_id, certificado_id, os_id, hash_pdf, emissao_at, signatario_id}` | `fiscal` (NFS-e opcional), `crm` (timeline), `financeiro` (cobrança) |
| `CertificadoRevisado` | `calibracao.usecase.revisar` | `{tenant_id, certificado_id, versao_anterior, versao_nova, razao}` | `crm`, audit log |
| `CertificadoCancelado` | `calibracao.usecase.cancelar` | `{tenant_id, certificado_id, razao}` | `fiscal` (CC-e se NFS-e foi emitida), audit log |

### Domínio: Fiscal

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `NFSeEmitida` | `fiscal.usecase.emitir_nfse` | `{tenant_id, nfse_id, certificado_id?, valor, emissao_at, plataforma}` | `financeiro` (conta a receber) |
| `NFSeCancelada` | `fiscal.usecase.cancelar_nfse` | `{tenant_id, nfse_id, razao}` | `financeiro` |
| `NFSeFalhou` | `fiscal.usecase.tentar_emitir` | `{tenant_id, certificado_id, erro, tentativas}` | Roldão (alerta SEV-2) |

### Domínio: Financeiro

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `BoletoGerado` | `financeiro.usecase.gerar_boleto` | `{tenant_id, boleto_id, valor, vencimento_at}` | `crm.recalibracao` (lembrete) |
| `Pago` | `financeiro.usecase.confirmar_pagamento` | `{tenant_id, conta_a_receber_id, pagamento_at}` | `crm.timeline` |

### Domínio: CRM

| Evento | Origem | Schema | Quem consome |
|--------|--------|--------|--------------|
| `LembreteRecalibracaoEnviado` | `crm.scheduler.dispatch_lembrete` | `{tenant_id, cliente_id, certificado_id, canal: whatsapp\|email, enviado_at}` | audit log |

---

## Versionamento de schema

Cada evento tem versão (`v1`, `v2`):
- Campo novo OPCIONAL → mesma versão (backward compatible)
- Campo OBRIGATÓRIO novo OU mudança de tipo → nova versão (`OSConcluidaV2`)
- Handlers escutam versões específicas; transition period suporta ambas

Migrations de schema obrigatórias revisadas pelo subagent `tech-lead-saas-regulado`.

---

## Idempotência

Cada evento tem `event_id` UUID (gerado no publish). Handler verifica `event_id` antes de processar → safe pra reprocessar.

---

## Ordem garantida?

**Por tenant + por entidade:** sim (procrastinate processa em ordem; outbox preserva ordem de insert).
**Cross-entity:** não — handler deve ser tolerante a out-of-order ou consultar estado atualizado do DB.

---

## Dead letter

Handler falha 5x → evento vai pra `dead_letter_events`. Roldão notificado SEV-2. Investigação manual.

---

## Auditor

Auditor Segurança em pre-commit:
- Import direto de model de outro módulo (e.g., `from os.models import OS` em `calibracao/`) → CONCERN
- Handler sem chave de idempotência → FAIL
- Mudança de schema sem nova versão → FAIL (auditor compara `EventSchema` com versão anterior)

---

## Referências

- ADR-0007 (camada domínio + outbox)
- `idempotencia.md`
- `retry.md`
- `governanca-modelo-comum.md` (fronteira comum vs módulo)
- `arquitetura/anti-corrosion-layer.md` (porta Queue)
