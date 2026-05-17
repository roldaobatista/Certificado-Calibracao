---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# PRD — Frota / Veículos

## Problema

Tenant que opera com UMC (laboratório móvel) tem 3 dores recorrentes hoje:
1. **Risco trabalhista (INV-020)** — Gerente marca OS sem ver jornada legal do motorista; passivo trabalhista + Roldão arrolado solidariamente (R-058 — `risco-vendor-solidariedade.md`).
2. **Custo do técnico em viagem (OP3.2)** — Adiantamento de R$ + pedágio + combustível ficam em papel ou WhatsApp; reconciliação no fim do mês perde 4-6h.
3. **Manutenção esquecida** — Veículo passa do prazo de revisão e quebra em campo; OS atrasa + cliente reclama.

## Goals Wave A (MVP-1 mínimo)

- CRUD de veículo (placa, modelo, ano, chassi, RENAVAM, categoria, foto, CRLV anexo).
- Atribuição veículo × colaborador × período.
- Registro de abastecimento (data, km, litros, R$, posto, anexo nota).
- Registro de manutenção (preventiva + corretiva — data, km, custo, oficina, anexo).
- **INV-020 — motor de jornada legal:**
  - Cadastro de motorista UMC com CNH + categoria.
  - Registro de jornada (início direção, parada, fim).
  - Hook valida ao agendar OS: bloqueia se viola 11h ininterruptas OU 30min/5h30.
  - Alerta motorista no app no minuto 5h25 de direção.
  - Comprovante de jornada exportável (PDF) pra fiscalização rodoviária.
- Checklist pré-viagem (livre + itens críticos bloqueantes — padrões calibrados a bordo).
- Caixa do técnico (OP3.2 — integração com Financeiro): solicitar adiantamento + reconciliar gastos.

## Goals Wave B (M+3 a M+6)

- Lembretes automáticos (revisão por km, IPVA, CRLV vencendo).
- Registro de multa + atribuição ao motorista.
- Registro de sinistro básico.
- GPS — discovery de provedor + ADR.

## Non-goals MVP-1 (explícitos)

- **TCO consolidado** — Wave C.
- **GPS / rastreamento em tempo real** — Wave B+ com ADR.
- **Gestão completa de seguro** — V2.
- **Processo administrativo de multa** — V2.
- **Roteirização (otimização de rota)** — V2+.
- **Telemetria veicular (OBD-II)** — V2+.
- **Pagamento automático de pedágio** — V2.
- **Gestão de pneus por número de série** — V2.

## Critérios de aceitação (binários)

- [ ] AC-FRT-01: Agendar OS pra motorista com violação iminente de 11h é bloqueado (INV-020 — hook).
- [ ] AC-FRT-02: Agendar trecho > 5h30 sem parada de 30 min na agenda é bloqueado (INV-020).
- [ ] AC-FRT-03: Comprovante de jornada exporta PDF assinável em ≤ 5s.
- [ ] AC-FRT-04: Checklist pré-viagem bloqueia "iniciar OS" se item crítico não marcado.
- [ ] AC-FRT-05: Atribuir veículo a colaborador sem papel "motorista" é bloqueado.
- [ ] AC-FRT-06: Registro de abastecimento sem km é bloqueado (cálculo de consumo precisa).
- [ ] AC-FRT-07: Caixa do técnico reconcilia 100% das despesas pré-aprovadas; saldo divergente abre pendência no Financeiro.
- [ ] AC-FRT-08: Conformidade WCAG 2.1 AA (INV-016) — relevante pro app do motorista em campo.

## Métricas

Ver `metricas.md`.

## Discovery / referências

- BIG-08; OP3.2; Persona 9 motorista UMC
- INV-020; CLT 235-C §9; Lei 13.103/2015
- R-058 (passivo trabalhista solidário)
