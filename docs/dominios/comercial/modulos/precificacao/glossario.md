---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/dominios/financeiro/modulos/custeio-real/glossario.md
---

# Glossário do módulo Precificação

> Termos específicos. Termos transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| custo direto | custo do insumo + mão de obra + deslocamento atribuído ao item | "custo total" sem qualificar | base do cálculo cost-plus | módulo `custeio-real` |
| markup | percentual aplicado sobre o custo para chegar ao preço (preço = custo × (1 + markup)) | "margem" — markup ≠ margem | percentual aplicado sobre custo | contabilidade |
| margem líquida | (preço − custo − impostos − comissão) / preço | "lucro" sem qualificar | percentual real de ganho após todos os encargos | contabilidade |
| preço mínimo | menor valor que o sistema aceita salvar sem bloquear (margem ≥ 0 ou ≥ piso definido) | "preço de custo", "break-even" sem qualificar | chão absoluto — abaixo dele o sistema bloqueia | US-PRC-002 |
| preço sugerido | valor calculado pela regra do gestor (margem-alvo) — exibido como default | "preço de tabela" sem qualificar | preço pré-preenchido no orçamento | US-PRC-002 |
| desconto máximo permitido | maior desconto que um papel pode aplicar sem aprovação | "desconto livre" | limite por papel/cliente/item | US-PRC-004 |
| faixa de aprovação | intervalo de desconto que exige aprovação de superior | "alçada" sem qualificar | range que dispara workflow de aprovação | US-PRC-004 |
| regra de formação de preço | fórmula que define como o preço é calculado (cost-plus / margem-alvo / fixo) | "fórmula" sem qualificar | configuração versionada por item | US-PRC-001 |
| tabela de preço | conjunto de preços efetivos aplicáveis por região/segmento/contrato | "lista de preço" sem qualificar | conjunto versionado de preços | US-PRC-005 |
| versão de tabela | snapshot imutável de uma tabela em um momento | "histórico de tabela" sem qualificar | versão que orçamentos emitidos preservam (INV-026) | INV-026 |
| simulação fiscal | estimativa de alíquota efetiva baseada no regime do cliente (NÃO é cálculo definitivo) | "imposto", "tributo" sem qualificar | número estimativo, sujeito a recálculo na NF | ADR-0008 |
| comissão simulada | percentual de comissão previsto para o vendedor neste orçamento | "comissão" sem qualificar | valor previsto, não devido (devida só pelo módulo `comissoes` após fechamento) | US-PRC-006 |
| custo de deslocamento | custo por km × distância configurada | "frete" | parcela somada ao custo direto | US-PRC-006 |
| histórico de preço praticado | série temporal imutável dos preços efetivamente fechados por item/cliente | "histórico de venda" sem qualificar | timeline WORM para análise | US-PRC-008 |
| margem realizada | margem efetivamente obtida após fechamento (não a planejada) | "margem real" sem qualificar | número obtido após confronto preço × custo real | módulo `custeio-real` |
| aprovação de desconto | registro imutável de quem aprovou/negou pedido de desconto fora da faixa | "ok do gerente" | evento auditável | US-PRC-004 |

---

## Fórmulas-chave (referência)

```
preço_mínimo = (custo_direto + custo_deslocamento) / (1 − %imposto − %comissão − %margem_piso)
preço_sugerido = (custo_direto + custo_deslocamento) / (1 − %imposto − %comissão − %margem_alvo)
margem_líquida = (preço_final − custo_direto − custo_deslocamento − imposto − comissão) / preço_final
```

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → `@deprecated` + janela 3 meses.
- Fórmula alterada → ADR + bump CHANGELOG.

## Convenções

- Termos em PT-BR.
- Definição em 1 linha.
- Origem obrigatória para termos com norma/contabilidade.
