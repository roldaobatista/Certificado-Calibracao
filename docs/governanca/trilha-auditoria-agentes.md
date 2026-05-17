---
owner: Roldão
revisado-em: 2026-05-17
status: draft
append-only: true
---

# Trilha de auditoria dos agentes

> **Pra quê:** registro **append-only** de cada decisão de auditor + cada drill + cada incidente envolvendo agente IA. Query padrão "quem tocou tenant Y entre HH:MM" testada em drill trimestral.
>
> **Retenção:** 2 anos governance + 5 anos se relacionado a dado regulado.

---

## Formato

```markdown
### YYYY-MM-DD HH:MM — [resumo]
- **Tipo:** veto_seguranca | veto_qualidade | veto_produto | drill | incidente | aprovacao_roldao | decisao_autonoma
- **Quem:** [auditor-segurança | auditor-qualidade | auditor-produto | watchdog | Roldão | ...]
- **O que aconteceu:** [descrição]
- **Tenant afetado:** [T_NN | n/a]
- **Resultado:** [bloqueou | aprovou | falso positivo | escalou]
- **Ação tomada:** [ação concreta]
- **Lição:** [se houver]
- **Link:** [PR / commit / sessão / postmortem]
```

---

## Princípios

1. **Append-only:** nunca editar entradas antigas. Correção entra como nova entrada referenciando a anterior.
2. **Imutável após 30 dias:** WORM B2 absorve (quando deploy autorizado).
3. **Sem PII direta:** usar `user_id_hash`, `tenant_id`, `request_id`.
4. **Toda decisão auditável:** auditor que vetar, drill que rodar, incidente que acontecer — TUDO entra.
5. **Query padrão funciona:** "listar tudo que tenant T_42 envolveu entre 2026-05-17 14:00 e 16:00" → resultado em ≤ 5 min.

---

## Entradas (cronológico reverso — mais recente em cima)

### 2026-05-17 — Inicialização do doc
- **Tipo:** marco
- **Quem:** Claude Code (agente principal)
- **O que aconteceu:** Doc criado em lote conforme Família 5 prescrita pelo `documentos-do-projeto.md` v6.
- **Tenant afetado:** n/a
- **Resultado:** doc disponível
- **Ação tomada:** registrado no INDEX.yaml; ativação real começa com Foundation F-A e auditores rodando.
- **Lição:** rastreio começa quando agentes começam a tomar decisões reais sobre código.
- **Link:** primeira versão deste doc

---

## Como começa a popular (gatilhos)

| Gatilho | Quem registra |
|---------|----------------|
| Auditor Segurança devolve FAIL em PR | Auditor (no GitHub Action) ou Claude Code local |
| Auditor Qualidade devolve FAIL | idem |
| Auditor Produto devolve FAIL (pre-merge) | idem |
| Drill trimestral roda | Roldão (manual) |
| Incidente SEV-0/1 | RACI define quem registra |
| Roldão derruba veto de auditor | Claude Code (ao processar `APROVADO POR ROLDAO`) |
| Watchdog despertou pra incidente | Watchdog (V2 quando ativado) |
| Decisão autônoma do agente (ver `auditoria-decisoes-autonomas.md`) | Claude Code |

---

## Drill trimestral

A cada 3 meses, executar:
1. Query padrão: tenant T_X entre HH-HH — esperar ≤ 5 min de resultado consolidado
2. Validar que entradas dos 30 dias mais recentes estão completas
3. Verificar que entradas com PII passaram por anonimização
4. Confirmar que retenção configurada bate com `retencao-matriz.md`

Resultado do drill **vira entrada nova** neste doc.

---

## Operação V2 (com deploy)

- WORM B2 absorve linhas antigas (> 30 dias)
- Painel Grafana "Trilha auditoria" agrega + filtra por tenant
- Query rápida via índices em PG + cold storage em B2
- Drill anual: tentar restaurar linha de 18 meses atrás → ≤ 30 min

---

## Referências

- `governanca/RACI-incidente-ai.md`
- `governanca/auditoria-decisoes-autonomas.md`
- `governanca/metricas-operacao-agentes.md`
- `conformidade/comum/retencao-matriz.md`
- `seguranca-dados.md` §7
