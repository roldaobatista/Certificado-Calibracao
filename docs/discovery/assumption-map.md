# Discovery — Assumption Mapping

> **Artefato Rodada 0** (Auditor 6 v2 — NOVO). Framework David Bland. Separa premissas em 4 quadrantes × 2 níveis de confiança. Destaca **leap-of-faith** (premissas críticas + baixa confiança).

---

## Quadrantes

Cada premissa do projeto se encaixa em:

| Quadrante | Pergunta |
|---|---|
| **Desejabilidade** | As pessoas QUEREM isso? |
| **Viabilidade** | É bom NEGÓCIO? (sustenta receita?) |
| **Factibilidade** | É possível CONSTRUIR? (técnica) |
| **Ética** | É CERTO fazer isso? (legal, regulatório, social) |

× níveis de confiança:

| Confiança | Significa |
|---|---|
| **Sabemos** | Evidência sólida (dado externo, validação ativa) |
| **Não sabemos** (leap-of-faith) | Especulação. PRECISA validar antes de comprometer recurso. |

---

## Matriz (a preencher após onda 1 das entrevistas)

### Desejabilidade

| Premissa | Confiança | Evidência (se sabemos) / Experiment (se não) |
|---|---|---|
| Donos de assistência técnica querem ERP integrado | Não sabemos | Validar em onda 1 de `entrevistas-clientes.md` |
| Diferencial calibração ISO 17025 é valorizado pelo mercado | Não sabemos (LEAP) | Validar com 5 laboratórios RBC + analizar concorrência |
| Operadores adotam mobile pra OS de campo | Não sabemos | Validar em onda 2 |

### Viabilidade

| Premissa | Confiança | Evidência / Experiment |
|---|---|---|
| TAM (laboratórios RBC × assistência técnica) é grande o suficiente pra sustentar SaaS | Não sabemos (LEAP) | Pesquisar dados ABRACAL, INMETRO, IBGE |
| Cliente paga R$ XXX/mês por essa solução | Não sabemos (LEAP) | `validacao-ativa.md` smoke test + WTP test |
| Modelo SaaS multi-tenant é aceito pelo público (vs on-premise) | Não sabemos | Validar em entrevistas |

### Factibilidade

| Premissa | Confiança | Evidência / Experiment |
|---|---|---|
| 1 pessoa não-técnica + IA entrega ERP completo em tempo viável | Não sabemos (LEAP CRÍTICO) | Validar com spike de 4 semanas em 1 módulo |
| Stack escolhida suporta multi-tenant em VPS Hostinger KVM 4 | Não sabemos | Spike técnico `spikes-tecnicos/multi-tenant.md` |
| Integração NF-e em município com padrão próprio é possível via Focus/NFE.io | Não sabemos | Spike `spikes-tecnicos/nfe-municipio-proprio.md` |
| Agentes IA conseguem manter código consistente ao longo de meses | Sabemos (parcial) | Plano-defesas-anti-erros-ia + auditores |

### Ética

| Premissa | Confiança | Evidência / Experiment |
|---|---|---|
| Emissão de certificado regulado por IA com signatário humano é juridicamente aceitável | Sabemos (parcial) | RBC NIT-DICLA-021 permite com responsabilidade técnica humana |
| LGPD permite uso de IA pra processar dado pessoal financeiro | Não sabemos | Consulta a DPO / advogado especializado |
| Cliente aceita transparência "este sistema é mantido por IA com supervisão humana" | Não sabemos | Validar em entrevistas (pergunta opcional) |

---

## Leap-of-Faith (resumo — premissas críticas com baixa confiança)

> Validar TODAS antes de comprometer recurso significativo.

1. **Diferencial calibração é valorizado** (Desejabilidade) — validar com 5 laboratórios RBC
2. **TAM sustenta SaaS** (Viabilidade) — pesquisar dados oficiais
3. **WTP suficiente** (Viabilidade) — smoke test + WTP test
4. **1 pessoa + IA entrega o escopo** (Factibilidade) — spike de 4 semanas
5. **LGPD permite IA processar PII financeiro** (Ética) — consulta jurídica

---

## Como esta lista evolui

- Premissa nova surge → adicionar com nível de confiança.
- Experiment dá resultado → mover premissa de "não sabemos" pra "sabemos" (com evidência) ou descartar.
- Premissa virada falsa → atualizar `riscos.md` + ajustar `sintese-final.md`.

---

## Saída esperada
- Matriz completa preenchida pós-onda 1
- Top 5 leap-of-faith priorizados pra experimento
- Validação de TODOS leap-of-faith antes da `sintese-final.md` travar MVP
