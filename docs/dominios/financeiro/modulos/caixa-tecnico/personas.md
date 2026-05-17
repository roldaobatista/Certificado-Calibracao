---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Personas — Caixa do Técnico

## P-OP-01 — Técnico de campo (primária)

**Quem é:** 25-55 anos. Faz calibração em cliente final. Pega adiantamento, dirige, calibra, gasta com combustível/alimentação/pedágio, volta. Quer fechar caixa rápido.

**Jornada:**
1. Antes da viagem: solicita adiantamento (R$ 500-2000) via app
2. Em campo: tira foto do recibo, lança despesa, escolhe categoria, vincula OS
3. Sem sinal: app salva offline; sincroniza no hotel/oficina
4. Fim do mês: abre prestação, confere saldo, dispara fechamento (5 min)
5. Recebe diferença (devolve ou é reembolsado)

**Frustrations:**
- "Perdi recibo na chuva"
- "Fechei caixa 4 horas no fim do mês"
- "Esqueci de qual OS era essa despesa — tive que ligar pro colega"
- "Não recebi reembolso há 60 dias"

**Permissões:** lançar próprias despesas, solicitar adiantamento, fechar prestação própria.

## P-FIN-01 — Financeiro do tenant

**Jornada:**
1. Recebe solicitação de adiantamento → aprova/encaminha pra dono
2. Valida despesas pendentes (swipe validar/rejeitar)
3. No fim do mês: confere prestação, libera diferença
4. Audita despesas suspeitas

**Frustrations (mundo atual):**
- "Pasta de papel — gasto 6h conciliando"
- "Recibo ilegível — não consigo prestar conta com contador"
- "Técnico gastou R$ 300 em combustível em 1 dia — verdade?"

**Permissões:** validar/rejeitar, ver tudo, fechar lote.

## P-FIN-02 — Dono

**Toca o módulo:**
- Aprovar adiantamento > alçada
- Ver total adiantado vs em prestação (controle de exposição)
- Ajustar política (limites, categorias, alçada)

**Permissões:** ver tudo + aprovar + configurar política.

## P-COM-02 — Vendedor (indireto)

Não toca diretamente, mas custo da OS dele virá daqui (relevante pra comissão sobre margem — Wave B).

## Anti-personas

- Técnico tentando lançar despesa sem foto → bloqueado por INV
- Técnico lançando despesa de OS de outro tenant → multi-tenant isolation
- Financeiro tentando editar despesa já validada → bloqueado (só nova despesa de correção)
- Auditor externo pedindo acesso direto aos recibos sem consentimento → bloqueado

## Referências

- JTBD-060/061/062/064
- BIG-08
- `docs/dominios/operacao/personas.md` P-OP-01
