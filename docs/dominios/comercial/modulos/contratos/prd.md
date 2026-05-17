---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: explanation
---

# PRD — Módulo Contratos (recorrentes)

## 1. O que este módulo é

Gestão de **contratos comerciais recorrentes** entre tenant e cliente: escopo (lista de equipamentos/serviços), vigência, periodicidade, valor, **geração automática de OS em ciclos**, alertas de vigência, renovação assistida e respeito ao princípio anti-fidelidade abusiva (cliente pode encerrar sem multa abusiva).

## 2. Por que existe

OP1 — Recalibração proativa: dor D-002 (R$ 3-8k/mês perdidos por esquecer renovação). Cliente PJ industrial com 50+ instrumentos precisa de calibração periódica — sem contrato, atendente esquece de abrir OS, cliente migra pra concorrente. Receita recorrente também sustenta plano de negócio (rev MRR > 60% no longo prazo).

## 3. Personas

Ver `../../personas.md`. Dominante: P-COM-05 Dono (configurador) + P-COM-02 Vendedor (negocia + renova) + P-COM-01 Atendente (revisa pré-OS geradas).

## 4. Escopo MVP-1

**Wave A (semanas 1-13) — depende de Foundation F-C + OP17 Equipamentos master:**
- Cadastro de contrato (cliente + escopo + valor + vigência + periodicidade)
- Geração automática de pré-OS no ciclo (rascunho pendente — não vira OS direto)
- Alerta vigência 30/60/90 dias antes do fim

**Wave B (semanas 14-22):**
- Renovação assistida (wizard 60d antes do vencimento)
- Suspensão temporária
- Aditivos (mudança escopo/valor durante vigência)
- Reajuste anual (IGP-M/IPCA/% fixo)
- PDF do contrato configurável pelo tenant
- Anti-fidelidade abusiva — cláusula padrão obrigatória + encerramento facilitado pelo cliente

## 5. Non-goals

- **Assinatura digital ICP-Brasil** — V2
- **Contrato com cláusula custom escrita por advogado** — MVP-1 usa template + variáveis (texto livre permitido no rodapé)
- **Faturamento / boleto / NFS-e** — pertence a `financeiro`
- **Conciliação bancária da parcela** — `financeiro`
- **Cobrança ativa de inadimplência** — `financeiro` (OP11 régua de cobrança)
- **Contrato com múltiplas moedas / internacional** — fora
- **Contrato de SLA com penalidade técnica** — V2 (apenas anotação simples no MVP)
- **Multa contratual abusiva** — proibido pelo princípio fundador (`prd.md §6` raiz)
- **Auto-renovação silenciosa** — proibido (anti-fidelidade): renovação **sempre** pede ação explícita

## 6. User Stories

### US-CTR-001: Cadastrar contrato recorrente
**Como** vendedor/dono, **quero** cadastrar contrato vinculado a cliente com escopo (equipamentos + serviços), valor, vigência e periodicidade, **para** sistema gerar OS automaticamente.
- AC-1: GIVEN cliente ativo (não-bloqueado) WHEN crio contrato com periodicidade=mensal/trimestral/semestral/anual/custom THEN sistema agenda próxima geração.
- AC-2: Vigência mínima 1 mês; vigência máxima 5 anos.
- **INV:** INV-026 (preço não retroage em OS já emitidas), INV-TENANT-001.

### US-CTR-002: Geração automática de pré-OS (OP1)
**Como** sistema, **quero** criar pré-OS rascunho 7d antes do ciclo (configurável), **para** atendente revisar e confirmar.
- AC-1: Job diário gera pré-OS para contratos vigentes cuja próxima execução está em ≤ 7d.
- AC-2: Cliente bloqueado/inadimplente → pré-OS marcada com flag "bloqueada — revisar antes" + alerta financeiro/vendedor.
- AC-3: Pré-OS NÃO vira OS formal sem confirmação humana (mitigação R-novo CRM-1 — disparo errado).

### US-CTR-003: Alerta de vigência a vencer
**Como** vendedor responsável e dono, **quero** receber alerta 90/60/30 dias antes do fim da vigência, **para** abrir renovação antes que cliente perceba.
- AC-1: Alertas configuráveis pelo tenant (default 90/60/30).
- AC-2: Aparece no MAPA-DO-DONO e na "Lista do dia" do vendedor.

### US-CTR-004: Renovação assistida (Wave B)
**Como** vendedor, **quero** wizard que carregue contrato atual, aplique reajuste configurado, deixe revisar escopo + valor + vigência, **para** renovar em < 5 min.
- AC-1: Reajuste aplicado mas editável.
- AC-2: Renovação cria NOVO contrato (com referência ao anterior); anterior fica como "renovado".
- AC-3: NUNCA renova sem ação humana (anti-fidelidade).

### US-CTR-005: Encerramento facilitado pelo cliente (anti-fidelidade)
**Como** cliente final, **quero** botão "encerrar contrato" no portal/link, **para** não depender de ligar e ouvir "vamos passar pro retenção".
- AC-1: Encerramento sem multa abusiva (apenas prejuízo concreto se houver — ex: custo de calibração já agendada).
- AC-2: Confirmação 2-step + janela 7d de "arrependimento".

### US-CTR-006: Aditivo (Wave B)
**Como** vendedor, **quero** alterar escopo/valor sem encerrar, **para** ajustar a meio de vigência.
- AC-1: Aditivo gera nova versão do contrato (snapshot) + motivo obrigatório.
- AC-2: Mudança de preço aplica somente em ciclos FUTUROS (INV-026 — não retroage).

### US-CTR-007: Suspensão temporária (Wave B)
**Como** dono/vendedor, **quero** suspender contrato (cliente vai viajar/parar atividade), **para** não gerar pré-OS no período.

## 7. Métricas

Ver `metricas.md`. Resumo: MRR de contratos, taxa renovação > 80%, % pré-OS confirmadas em até 48h > 90%, churn mensal < 3%.

## 8. NFR

- Performance: cadastro p95 < 1s; geração noturna processa 10k contratos em < 30 min.
- Disponibilidade: 99.5%.
- LGPD: contrato é documento jurídico — retenção 5 anos pós-encerramento.
- Imutabilidade: versão de contrato vigente em um ciclo gera OS com preço daquela versão (INV-026).
- Anti-fidelidade abusiva: princípio inviolável — proibição de cláusulas que prendem cliente.

## 9. Glossário

Ver `glossario.md`.
