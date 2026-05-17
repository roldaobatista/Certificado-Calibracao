---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Relatórios Financeiros

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Dono / gestor financeiro

**Identidade:** Dono da empresa de assistência técnica ou gestor financeiro responsável (em empresas maiores). Foco em resultado, fluxo de caixa e lucratividade por linha de negócio. 35–60 anos. Não necessariamente contabilista.

**Goals deste módulo:**
- Saber, em 30 segundos, se o mês foi positivo.
- Antecipar aperto de caixa nos próximos 60 dias.
- Identificar cliente / técnico / serviço que dá prejuízo.

**Frustrations específicas:**
- Esperar o contador fechar o mês para saber resultado.
- Olhar planilha velha de 15 dias.
- Não conseguir "abrir" um número (drill-down ausente).

**Jornada típica:**
1. Abre módulo no início do dia (web desktop).
2. Olha card de DRE do mês corrente.
3. Vê fluxo projetado 30 dias.
4. Drill em alerta de cliente vencendo.
5. Exporta visão pra mandar pro sócio.

**Devices:** web desktop principal; mobile pra checagem rápida.
**Frequência:** diário/semanal.

---

## Persona 2: Analista financeiro / controller

**Identidade:** Responsável operacional do financeiro. Concilia, fecha mês, prepara material para o contador e para o dono. 25–45 anos.

**Goals deste módulo:**
- Conciliar banco vs. sistema rapidamente.
- Fechar aging semanal sem cruzar planilha manualmente.
- Exportar pacote mensal para o contador (XLSX + PDF).

**Frustrations específicas:**
- Importar OFX e cruzar à mão.
- Aging em planilha que envelhece rápido.

**Devices:** web desktop.
**Frequência:** diário.

---

## Persona 3: Contador externo (read-only sob NDA)

**Identidade:** Escritório contábil terceirizado que recebe pacote mensal ou acesso read-only para fechar contabilidade oficial. 30–60 anos.

**Goals deste módulo:**
- Receber pacote fechado e padronizado (DRE, razão sintético, conciliação).
- Acessar drill-down para validar lançamento dúbio.

**Frustrations específicas:**
- Receber Excel diferente todo mês.
- Não ter acesso ao detalhe quando preciso.

**Devices:** web desktop.
**Frequência:** mensal (fechamento) + ad hoc.

---

## Convenções

- Persona em ≥2 módulos com mesma responsabilidade → promover para `../../personas.md`.
- Persona em ≥2 domínios → promover para `docs/comum/personas.md`.
