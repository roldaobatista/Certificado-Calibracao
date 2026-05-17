---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Personas — Fiscal

## P-FIN-01 — Responsável financeiro (primária)

**Quem é:** opera emissão de NFS-e no dia a dia. Pode acumular com gerente/dono em tenant pequeno.

**Jornada:**
1. OS concluída + cliente pagou → 1 toque emite NFS-e (pré-preenchida do que sistema já sabe)
2. Em raros erros corrige (CC-e) ou cancela (< 24h)
3. Acompanha numeração; inutiliza buracos
4. Em contingência: vê banner amarelo, continua emitindo

**Frustrations (mundo atual):**
- "NFS-e de SP, RJ, BH — cada um é um inferno diferente"
- "Município caiu segunda à tarde — eu emiti mais 30 manuais à noite"
- "Errei descrição e não sei se conserto com CC-e ou cancela"

**Permissões:** emitir, cancelar, CC-e, configurar regime+alíquota, ver tudo do tenant.

## P-FIN-02 — Dono

**Toca o módulo:**
- Aprova configuração inicial (regime fiscal + alíquotas — orientado pelo contador)
- Vê painel emissões do mês (volume, cancelamentos, contingência)
- Decide se aceita tenant em município sem cobertura BaaS

**Permissões:** tudo + alteração de configuração fiscal.

## P-FIN-05 — Contador externo (V2)

**Quem é:** profissional externo que faz apuração mensal pra tenant.

**Jornada (V2):**
- Acesso read-only com audit reforçado
- Baixa lista de NFS-e emitidas + canceladas + corrigidas no mês
- Recebe XML originais via export estruturado / SPED
- Apura imposto fora do Aferê

**Permissões:** auditor read-only externo — V2.

## P-FIN-06 — Auditor fiscal (CONFAZ / Receita / municipal) — V2+

**Toca o módulo:** acesso indireto via tenant — Aferê fornece evidência estruturada. Nunca acesso direto.

## P-CLI — Cliente final do tenant

**Toca o módulo:** recebe XML + PDF da NFS-e por email/WhatsApp. Pode acessar via portal cliente (Wave B) e baixar 2ª via.

## Anti-personas

- Tenant em **Lucro Real complexo** ou **ZFM com SUFRAMA particular** — não-MVP.
- Tenant em **município FP2 sem cobertura BaaS** (Vitória) — bloqueado no onboarding até confirmar BaaS cobre.
- Auditor fiscal pedindo modificar NFS-e — bloqueado (read-only sempre).

## Compliance específico

- LGPD RAT-05 (NFS-e contém CPF/CNPJ + valor).
- LGPD RAT-08 (audit fiscal).
- Retenção 5 anos (Receita) — `retencao-matriz.md`.

## Referências

- Persona 4 financeiro (`docs/discovery/personas-detalhadas.md`)
- BIG-04
- `docs/dominios/financeiro/personas.md`
