# Governança do modelo comum (fronteira comum vs módulo)

> **Pra quê:** definir critério OBJETIVO de quando uma entidade/conceito sobe pra `docs/comum/` ou fica em `docs/dominios/<dom>/modulos/<mod>/`. Sem regra explícita, agentes vão decidir diferente a cada sessão e em 3 meses há 3 definições de "cliente" inconsistentes (Auditor 3 + 8 alertaram).

---

## Regra de promoção (módulo → comum)

Entidade é **promovida pra comum** quando todas as 3 condições valem:

1. **Uso múltiplo:** ≥2 módulos usam a entidade.
2. **Sem extensão obrigatória:** cada módulo usa a entidade SEM precisar adicionar campos próprios obrigatórios.
3. **Mesma semântica:** "cliente" em módulo A significa a mesma coisa que "cliente" em módulo B.

Se as 3 condições valem → criar em `docs/comum/modelo-de-dominio.md` + entrada no `docs/comum/glossario.md`.

---

## Regra de extensão (comum + módulo)

Quando entidade está em `comum/` mas módulo precisa de **campos próprios**:

### Opções de implementação (decidir caso a caso, registrar em ADR do módulo):
- **Extension table** — tabela auxiliar `cliente_calibracao_extra` linkada por FK. Melhor pra muitos campos.
- **JSONB** — coluna `metadata JSONB` na tabela `cliente`. Melhor pra poucos campos + flexibilidade.
- **Tabela própria** — `cliente_calibracao` separada. Só se semântica difere significativamente.
- **Herança via tabela** — patterns DDD (table-per-class / single-table inheritance).

### Proibido:
- **Duplicar tabela** com nomes diferentes pra mesma entidade lógica.
- **Sobrescrever** campos comuns no módulo (ex: módulo redefine `cliente.nome` como diferente).
- **Mudar** schema comum por necessidade de UM módulo sem ADR.

---

## Regra de rebaixamento (comum → módulo)

Entidade é **rebaixada pra módulo** quando:

1. Apenas 1 módulo usa, OU
2. Os módulos que usam têm semânticas conflitantes que não dá pra reconciliar.

Rebaixamento é raro mas necessário. Exige:
- ADR explicando por quê reconciliação falhou.
- Migration que move dados.
- Atualizar `glossario comum` removendo entrada.

---

## Casos típicos no domínio

| Entidade | Onde fica? | Por quê |
|---|---|---|
| **Cliente** | Comum (provável) | Usado por CRM, Orçamento, OS, Financeiro, Chamado. Semântica idêntica (a confirmar no discovery). |
| **Usuário interno** | Comum | Usado por todo módulo pra atribuir responsabilidade. |
| **Permissão / Role** | Comum | RBAC transversal. |
| **Tenant** | Comum (estrutural) | Isolamento multi-tenant. INV-TENANT-001. |
| **Padrão (instrumento de referência)** | Módulo Calibração | Só calibração usa. ISO 17025 cláusula 6.5 exige campos específicos. |
| **Incerteza de medição** | Módulo Calibração | Só calibração. |
| **NF-e** | Módulo Financeiro | Só financeiro emite. |
| **Ticket / Chamado** | Módulo Chamados | Específico, mas pode evoluir se Orçamento também adotar workflow de ticket. |
| **OS — Ordem de Serviço** | Módulo OS | Específica de execução. |
| **Funil de vendas** | Módulo CRM | Específico do comercial. |

> ⚠️ **Esta tabela é hipótese.** A síntese final do discovery vai confirmar/ajustar.

---

## Hook que valida (a criar — Rodada 4)

`pre-commit` que checa:
1. Entidade nova em `docs/dominios/<mod>/modelo-de-dominio.md` com nome que já existe em `docs/comum/modelo-de-dominio.md` → bloqueia (provável duplicação acidental).
2. Entidade em `comum/` usada por apenas 1 módulo → warning (candidato a rebaixamento).
3. Campo obrigatório adicionado em entidade comum sem ADR → bloqueia.

---

## Quem decide promoção/rebaixamento

- **Promoção** — agente propõe; Auditor de Produto valida; commit direto na main (não exige humano).
- **Rebaixamento** — agente propõe; ADR formal; Auditor de Produto + Auditor de Qualidade revisam; humano (Roldão) aprova via CODEOWNERS se afeta `REGRAS-INEGOCIAVEIS.md`.

---

## Versionamento

- Mudança em entidade comum (renomear campo, mudar tipo) afeta TODOS os módulos consumidores → exige migration + bump no `CHANGELOG.md` seção "Modificado".
- Deprecação de entidade comum: marcar `@deprecated` no doc + ADR + janela de transição (3 meses default).
