---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# PRD — Módulo Estoque multi-local

## 1. O que este módulo é

Controle de saldo físico de peças/padrões em **múltiplos locais** (central, veículos, técnicos em campo, com cliente). Suporta **lote**, **validade**, **número de série** e **transferência 2-etapas** com aceite + foto obrigatória (BIG-12, JTBD-104). Mantém **kardex** (linha do tempo de movimentos) e suporta inventário. **Wave B**.

## 2. Por que existe

- BIG-12 (estoque rastreável é diferencial real — selo INMETRO rastreável).
- JTBD-098..109 (6 jobs Wave B): "saber onde está cada peça", "transferir com aceite", "alertar mínimo", "bloquear vencido", etc.
- Dor: "técnico levou peça e sumiu"; "peça vencida em calibração"; inventário físico demora 8h.

## 3. Personas

Ver `personas.md` + `../../personas.md` (P-SUP-01 almoxarife, P-OP-01 técnico, P-SUP-02 metrologista).

## 4. Escopo (o que ESTÁ)

- Cadastro de locais de estoque (central + N veículos + N técnicos + cliente como local)
- Saldo por (item, local, lote, NS)
- Movimentos append-only: entrada / saída / transferência / ajuste de inventário
- Transferência 2-etapas: emissão → trânsito → aceite com foto obrigatória
- Bloqueio de consumo de lote vencido
- Reservas para OS
- Alerta de estoque mínimo (por item por local)
- Inventário com tela de conferência
- Kardex por item ou por local
- Custo médio ponderado (CMP) recalculado em cada entrada [INFERÊNCIA] confirmar V2

## 5. Non-goals

- NÃO emite NF de entrada (Financeiro)
- NÃO cota com fornecedor (Fornecedores)
- NÃO cadastra catálogo (Produtos/Peças/Serviços)
- NÃO faz logística de transporte detalhada (V2)

## 6. User Stories

### US-EST-001: Cadastrar local e ver saldo

**Como** almoxarife, **quero** cadastrar locais e ver saldo, **para** saber onde está cada peça em < 30s.

- **AC-EST-001-1**: GIVEN cadastrei "Central" + "Veículo João", WHEN abro lista de saldos, THEN vejo saldo por (item, local).

### US-EST-002: Entrada de peça com lote e validade

**Como** almoxarife, **quero** dar entrada com lote + validade, **para** rastrear origem.

- **AC-EST-002-1**: GIVEN entrada com lote=L123 + validade=2027-01-01, WHEN salvo, THEN movimento append-only é criado; saldo do local sobe.
- **AC-EST-002-2**: GIVEN consumo de lote vencido, THEN sistema bloqueia (mensagem PT "lote vencido em DD/MM/AAAA").

### US-EST-003: Transferência 2-etapas com foto

**Como** almoxarife, **quero** transferir peça pro veículo do técnico com aceite, **para** rastrear (BIG-12 JTBD-104).

- **AC-EST-003-1**: GIVEN crio transferência (origem=Central, destino=Veículo João, qtd=2), WHEN confirmo emissão, THEN saldo origem cai 2, saldo "em trânsito" sobe 2.
- **AC-EST-003-2**: GIVEN transferência em trânsito, WHEN técnico aceita + anexa foto do lacre, THEN saldo destino sobe 2, "em trânsito" zera; movimento "aceite" salvo com foto.
- **AC-EST-003-3**: GIVEN aceite sem foto, THEN sistema rejeita ("foto do lacre obrigatória").
- **AC-EST-003-4**: GIVEN técnico recusa, THEN saldo retorna ao origem; motivo registrado.

### US-EST-004: Inventário físico

**Como** almoxarife, **quero** rodar inventário e ajustar diferenças, **para** alinhar sistema ↔ físico.

- **AC-EST-004-1**: GIVEN inicio inventário do local Central, WHEN registro contagem por item, THEN sistema mostra diferença (sistema − físico) + cria movimento de ajuste com motivo obrigatório.

### US-EST-005: Reserva para OS

**Como** atendente, **quero** reservar peça pra OS, **para** garantir disponibilidade.

- **AC-EST-005-1**: GIVEN saldo=5, reservo 2 pra OS-789, THEN saldo disponível=3, reservado=2.
- **AC-EST-005-2**: GIVEN OS-789 fechada, THEN reservas viram consumo (movimento de saída).

### US-EST-006: Alerta de mínimo

**Como** almoxarife, **quero** configurar mínimo por item, **para** receber alerta antes de zerar.

- **AC-EST-006-1**: GIVEN mínimo=10, saldo cai pra 9, THEN alerta dispara (notificação + dashboard).

## 7. Métricas

Ver `metricas.md`.

## 8. NFR

- Performance: kardex p95 ≤ 1.5s, lista saldos ≤ 1s
- Foto da transferência: ≤ 5MB, compressão server-side
- Segurança: foto fica em storage com acesso autenticado (`INV-TENANT-001`)

## 9. Glossário

Ver `glossario.md`.
