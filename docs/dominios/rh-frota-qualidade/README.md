---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Domínio: RH + Frota + Qualidade

## O que é este domínio

Agrupa **3 sub-áreas que orbitam o operacional mas não são Operação direta**:
1. **RH / Colaboradores** — cadastro de pessoa que trabalha no tenant, papéis, habilidades, ponto, vagas (V2+)
2. **Frota / Veículos** — UMC (unidade móvel de calibração), carros, motos, manutenção, abastecimento, GPS
3. **Qualidade** — auditorias internas, NC, ações corretivas, NPS, controle estatístico

> **Por que agrupar:** as 3 são habilitadoras transversais sem peso pra serem domínios separados no MVP-1. Em V2/Wave C podem virar domínios autônomos se complexidade justificar.

## Fronteiras com outros domínios

- **Entra:** colaborador, veículo, manutenção veicular, abastecimento, NC interna, auditoria interna, NPS pós-serviço, pesquisa satisfação.
- **NÃO entra (vai pra Operação):** OS aberta pela qualidade (mesmo se causa for NC).
- **NÃO entra (vai pra Financeiro):** folha de pagamento (non-goal MVP-1); comissão liquidada.
- **NÃO entra (vai pra Comercial):** NPS pré-venda (lead).
- **NÃO entra (vai pra Suporte-Plataforma):** equipamento do cliente — embora frota seja "equipamento do tenant".

## Módulos deste domínio

| Módulo | Status | Pasta | Cobertura discovery |
|---|---|---|---|
| Colaboradores (RH mínimo) | ⏳ a especificar | `modulos/colaboradores/` | Cadastro mínimo p/ comissões + técnico; resto MVP-2 |
| Frota / Veículos | ⏳ a especificar | `modulos/frota/` | OP3.2 caixa + INV-020 motorista; TCO completo Wave C |
| Qualidade | ⏳ a especificar | `modulos/qualidade/` | INV-012 NC; ISO 17025 cl. 7.10, 8.5-8.7 |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Núcleo:
- **Dono** (autoriza colaborador novo + aprova frota nova)
- **Gerente** (atribui veículo, aprova checklist, fecha NC)
- **Motorista UMC** (compliance Lei 13.103/2015 — INV-020)
- **Responsável pela qualidade** (auditoria interna, plano de ação)

## Compliance específico

- **Lei 13.103/2015 (motorista profissional UMC):** jornada 11h ininterruptas + descanso 30min/5h30. **INV-020** hook valida agenda + bloqueio.
- **eSocial (V2):** folha + ponto + benefícios (non-goal MVP-1).
- **ISO 17025 cláusulas:**
  - 6.2 (pessoal qualificado) — `responsabilidade-tecnica.md`
  - 7.10 (NC) — INV-012 bloqueia emissão
  - 8.5 (riscos e oportunidades) — RIPD obrigatório em alguns RATs
  - 8.6 (melhoria contínua)
  - 8.7 (ações corretivas) — postmortem dispara regra nova
- **RBC NIT-DICLA-021 (signatário):** ver `responsabilidade-tecnica.md`

## Integrações com outros domínios

- RH → Operação: colaborador é técnico/atendente/signatário (RBAC)
- RH → Financeiro: comissão calculada por colaborador
- Frota → Operação: veículo atribuído à OS (UMC pra calibração em campo)
- Frota → Financeiro: pedágio + combustível repassado ao cliente
- Qualidade ← Operação: OS marca NC quando aplicável
- Qualidade → Metrologia: NC em padrão dispara verificação intermediária (INV-022)

## ADRs específicos do domínio

Nenhum hoje. Possíveis V2:
- ADR sobre integração eSocial (quando V2 ativar)
- ADR sobre rastreador GPS de frota (provedor + custo)

## Status do domínio

🟡 **RH mínimo + Caixa do técnico + INV-020 motorista cobrem MVP-1; restante é Wave B/C.** Qualidade tem INV-012 bloqueio NC mas controle estatístico/cartas controle são MVP-2.
