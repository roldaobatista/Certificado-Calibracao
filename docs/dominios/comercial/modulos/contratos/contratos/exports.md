---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
---

# Contratos Export — Módulo Contratos (recorrentes)

## Exports

### 1. Contrato PDF — versão cliente
**Propósito:** documento jurídico anexado por e-mail ou link público.
**Formato:** PDF (template configurável pelo tenant — cabeçalho com logo, dados tenant, dados cliente).
**Campos:** identificação das partes, escopo detalhado (equipamentos + serviços + periodicidade), valor total + parcelamento, vigência, reajuste, cláusulas (incl. **cláusula anti-fidelidade obrigatória padronizada**), foro, data + assinaturas (digital ou caneta).
**Sem:** dados internos (comissão, custo, margem).
**Imutabilidade pós-aprovação:** sim — versão aprovada é snapshot (INV-026).
**Retenção:** 5 anos pós-encerramento (LGPD + fiscal).
**Assinatura digital:** não no MVP-1 (V2 ICP-Br).
**Cláusula anti-fidelidade:** texto obrigatório padrão — *"Cliente pode encerrar este contrato a qualquer momento, mediante prévio aviso de [N] dias, sem multa abusiva. Eventual cobrança limita-se ao prejuízo concreto comprovado (serviço já agendado/em execução)."*

### 2. Contrato PDF — visão interna
**Propósito:** dono/auditoria imprime com dados internos.
**Diferença:** inclui comissão prevista, margem, custos.
**Permissão:** dono.

### 3. Lista de contratos — XLSX
**Campos:** número, cliente, estado, vigência, valor mensal equivalente, próxima execução, responsável, aditivos, próximo alerta.
**Permissão:** dono, vendedor (filtrado), financeiro.

### 4. Forecast MRR — XLSX
**Propósito:** financeiro projeta receita recorrente.
**Campos:** mês, MRR previsto, novos contratos, renovações, encerramentos, churn esperado.
**Permissão:** dono, financeiro.
**Frequência:** consultado mensal.

### 5. Bandeja pré-OS — CSV
**Propósito:** export para revisão offline (raro — bandeja é online).
**Campos:** contrato, cliente, ciclo, data prevista, pré-OS gerada em, status, observações.

### 6. Histórico de versões/aditivos — CSV (interno)
**Propósito:** auditoria fiscal e regulatória.
**Campos:** contrato, versão, motivo, valor anterior, valor novo, escopo diff, aprovado por, em.
**Retenção:** 5 anos.

### 7. Encerramentos — CSV
**Propósito:** análise de churn + auditoria anti-fidelidade.
**Campos:** contrato, cliente, motivo, prejuízo cobrado, vendedor, fim_vigência_original, encerrado_em, dias_antes_fim.
**Permissão:** dono, gerente.

### 8. Aviso de renovação — payload WhatsApp/e-mail
**Propósito:** alerta automático ao cliente 60d antes do vencimento.
**Template Meta BSP:** `aviso_renovacao_contrato` com variáveis ({{nome}}, {{numero_contrato}}, {{vencimento}}).
**Aprovação Meta:** obrigatória — categoria utilidade.
**LGPD:** RAT-06.

## Exports inter-módulos

- `Contrato.PreOSGerada` → módulo `operacao/os` materializa OS rascunho.
- `Contrato.Renovado` → módulo `financeiro` atualiza forecast.
- `Contrato.Encerrado` → módulo `crm` registra motivo de churn + módulo `financeiro` encerra cobrança recorrente.
- Lista de contratos → módulo `financeiro/comissoes` (cálculo).

## Mensagens WhatsApp (templates regulados Meta)

| Template | Variáveis | Quando |
|---|---|---|
| `aviso_renovacao_contrato` | nome, contrato, vencimento | 90/60/30 dias antes |
| `pre_os_agendada` | nome, equipamento, data_prevista | confirmação de visita |
| `aviso_encerramento_processado` | nome, contrato, motivo | após encerramento via portal |

Todos exigem aprovação Meta BSP.

## Versionamento

- Template PDF é versionado pelo tenant. Cláusula anti-fidelidade **não é editável pelo tenant** (princípio fundador).
- Mudança no schema → ADR + janela 6 meses.

## Imutabilidade

Versão aprovada gera PDF idêntico permanentemente. Mudança em template pelo tenant **não afeta** PDFs já emitidos.

## Como evolui

Export novo → adicionar + RBAC. Template WhatsApp novo → submeter Meta.
