---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
---

# Glossário do módulo Auditoria Externa

> Termos **específicos** deste módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| auditoria externa | Avaliação por organismo de terceira parte (CGCRE, certificadora ISO, cliente) | "fiscalização", "vistoria" | Auditor de fora vai avaliar a empresa | escopo do módulo |
| auditoria interna | Avaliação feita pela própria empresa, recorrente, para preparar a externa | — | NÃO é este módulo — ver `docs/governanca/` | escopo |
| checklist por norma | Lista de requisitos a verificar, baseada em norma específica | "roteiro", "questionário" | Conjunto de itens da norma X | US-AUD-002 |
| evidência | Documento/registro que comprova atendimento a um requisito | "prova", "anexo" | Arquivo vinculado ao requisito | US-AUD-004 |
| não-conformidade maior (NC maior) | Falha grave que compromete sistema da qualidade ou requisito crítico | "NC crítica" | Pode reprovar a certificação | ISO 17025 / 9001 |
| não-conformidade menor (NC menor) | Falha pontual sem impacto sistêmico | — | Plano de ação obrigatório, não reprova | ISO 17025 / 9001 |
| observação | Apontamento sem caráter de NC, alerta preventivo | "comentário" | Atenção sem obrigação imediata | ISO 17025 / 9001 |
| oportunidade de melhoria | Sugestão do auditor pra evoluir o sistema | "sugestão" | Não obriga ação, mas é registrado | ISO 17025 / 9001 |
| plano de ação | Conjunto causa-raiz + ação corretiva + responsável + prazo + evidência de fechamento | "plano de tratativa", "ação corretiva" | Resposta da empresa a uma NC | US-AUD-007 |
| 5-porquês | Método de causa raiz: pergunta "por quê" 5x até causa primária | "five why's" | Obrigatório para NC maior | US-AUD-007 |
| simulação / drill | Auditoria simulada interna pra detectar gaps | "ensaio", "mock audit" | Treino antes da auditoria real | US-AUD-012 |
| matriz de conformidade | Tabela cláusula × status em tempo real | "matriz de aderência" | Visão consolidada da conformidade | US-AUD-010 |
| documento controlado | Documento com versão, aprovação e distribuição rastreáveis | "doc oficial" | Procedimento/instrução com governança | módulo Qualidade |
| painel de prontidão | Dashboard semafórico por norma | "dashboard de aderência" | Verde/amarelo/vermelho por norma ativa | US-AUD-013 |
| CGCRE | Coordenação Geral de Acreditação do INMETRO — acredita laboratórios RBC | — | Organismo que credencia ISO 17025 no Brasil | INMETRO |
| follow-up | Verificação pelo organismo se NCs foram fechadas | "verificação posterior" | Auditoria de retorno menor | ISO 17025 |

---

## Como esta lista evolui

- Termo novo → verificar conflito com glossário comum (hook valida).
- Termo descontinuado → `@deprecated` + janela 3 meses.
- Mudança de definição → CHANGELOG "Modificado".

## Convenções

- PT-BR. Termos das normas em PT-BR oficial (ABNT NBR ISO/IEC 17025:2017).
- Definição em 1 linha; mais detalhe em `docs/explicacoes/<termo>.md` se necessário.
- Origem obrigatória para termos regulados.
