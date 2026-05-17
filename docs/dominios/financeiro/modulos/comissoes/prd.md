---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# PRD — Comissões

## 1. O que é

Cálculo automático, exibição e pagamento de comissão variável a vendedores e técnicos por OS gerada/executada. **Gatilho por recebimento**: comissão só fica devida quando cliente paga (não quando OS é concluída).

## 2. Por que existe

Dor #15 (BIG-09): tenants pagam comissão errada ou atrasada hoje (planilha manual); vendedor desconfia, contestações constantes, vínculo emocional ruim entre dono e equipe comercial. JTBD-072 (previsão própria), JTBD-078 (contestar histórico), JTBD-082 (gatilho por recebimento).

## 3. Personas

P-FIN-01 (financeiro — configura, fecha mês, paga), P-FIN-02 (dono — vê total devido), P-COM-02 (vendedor — vê própria comissão), P-OP-01 (técnico — vê comissão de serviço executado).

## 4. Escopo MVP-1 (Wave A — 1 fórmula apenas)

- 1 fórmula: **% sobre valor bruto da OS, gatilho por recebimento (`Pago`)**
- 1 beneficiário por OS (vendedor responsável atribuído na OS)
- Cadastro de regra por beneficiário (% fixo)
- Cálculo automático no momento `OSConcluida` → status `prevista`
- Mudança pra `devida` quando `Pago` chega
- Demonstrativo individual filtrado por mês
- Aba "Minha comissão" no app vendedor/técnico
- Estorno automático se título cancelado

## 5. Non-goals MVP-1 (explícito)

- **As 7 fórmulas adicionais** listadas no glossário → Wave B/MVP-2.
- Comissão por equipe / rateio entre N pessoas → Wave B.
- Comissão sobre margem (não temos custeio confiável ainda) → MVP-2.
- Comissão escalonada por meta → Wave B.
- Aprovação por dono antes de virar devida → V2.
- Folha de pagamento / integração holerite → V2 (RH).
- Comissão de retenção contratual → Wave B (depende OP8).

## 6. User Stories

- **US-COM-001:** vendedor abre app, vê "Minha comissão" do mês: previsto + devido + pago.
- **US-COM-002:** OS concluída → comissão prevista calculada automaticamente conforme regra ativa.
- **US-COM-003:** título da OS é pago → comissão muda de `prevista` pra `devida` em < 60s.
- **US-COM-004:** título cancelado após comissão paga → estorno automático cria contra-lançamento.
- **US-COM-005:** vendedor contesta valor → consegue ver histórico granular (cada OS, % aplicado, base, gatilho).
- **US-COM-006:** financeiro fecha mês: gera lote de comissões devidas → exporta pra pagamento.

AC binários: status observável + audit log + evento emitido.

## 7. NFR

- Cálculo OS concluída → comissão prevista: < 2s
- Webhook Pago → comissão devida: p95 < 60s
- Demonstrativo reconstruível 100% (rastreabilidade — JTBD-078)
- Mudança de regra **não-retroativa** (INV-026 análogo)

## 8. Invariantes

- INV-008 (audit log de toda mudança de regra + cálculo).
- Regra alterada hoje só aplica em OSs concluídas a partir de hoje (não recalcula passado).
- Cancelamento de OS pós-pagamento de comissão sempre gera estorno explícito (nunca silencioso).

## 9. Dependências

- OP-FIN (recebe `Pago`)
- OS (recebe `OSConcluida`)
- Cadastro de vendedor/técnico (Comercial/Operação)

## 10. Roadmap pós-MVP-1

Ver glossário. 7 fórmulas em backlog Wave B/MVP-2; abrir entrevistas dedicadas com 5 tenants antes de cada uma.
