---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Glossário — Comissões

| Termo | Definição |
|---|---|
| **Comissão** | Remuneração variável paga a vendedor/técnico/equipe sobre receita gerada por ele(s). |
| **Beneficiário** | Pessoa ou equipe que recebe a comissão (vendedor, técnico, gerente, equipe inteira). |
| **Base de cálculo** | Valor sobre o qual a comissão é calculada — no MVP-1 = **valor bruto da OS**. |
| **Percentual** | Taxa aplicada na base — único parâmetro da fórmula MVP-1. |
| **Gatilho de liberação** | Evento que torna a comissão efetivamente devida — no MVP-1 = **recebimento do título** (`Pago`). |
| **Comissão prevista** | Valor calculado mas ainda não liberado (OS concluída + título emitido + ainda não pago). |
| **Comissão devida** | Calculada + título pago → vira pagamento devido ao beneficiário. |
| **Comissão paga** | Liberada e baixada (pagamento ao beneficiário registrado). |
| **Estorno** | Reversão quando título é cancelado/devolvido após comissão paga. |
| **Demonstrativo** | Documento individual do beneficiário com lista de OSs + valores + status. |
| **Período de apuração** | Janela mensal padrão de fechamento da comissão. |
| **Regra de comissão** | Configuração do tenant: quem recebe, qual % sobre qual base. MVP-1 = 1 regra ativa por beneficiário. |

## Fórmulas futuras (Wave B / MVP-2 — non-goal MVP-1)

Documentadas no roadmap; **não implementar agora**:
- % escalonado por meta (atingiu 100% → 5%; atingiu 120% → 7%)
- % sobre margem (em vez de bruto) — requer custeio confiável
- Comissão por equipe (rateio entre N pessoas)
- Comissão de retenção (cliente renovou contrato)
- Comissão por tipo de serviço (calibração: 3%; venda peça: 5%)
- Comissão híbrida (% sobre venda + bônus de meta)
- Comissão por margem negativa bloqueada (cruzar com BIG-08)

## Referências

- OP4 (Wave A — 1 fórmula; Wave B — outras 7)
- BIG-09 (comissões configuráveis)
- `docs/discovery/jobs-to-be-done.md` JTBD-072, JTBD-078, JTBD-082
