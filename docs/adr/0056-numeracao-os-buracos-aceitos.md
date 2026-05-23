---
adr: 0056
titulo: Numeração de OS — sequence global + unique composto, buracos aceitos
status: aceito
data-decisao: 2026-05-23
decisor: roldao
contexto-marco: Wave A Marco 3 — operacao/os
relacionados:
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0023-os-com-atividades.md
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M3-os/plan.md
  - docs/faseamento/M3-os/reviews/tech-lead.md
---

# ADR-0056 — Numeração de OS — sequence global + unique composto, buracos aceitos

## Status

**ACEITO** em 2026-05-23 (decisão Roldão D-M3-1 após review tech-lead P-OS-T2 no ritual P2 do Marco 3).

## Contexto

A spec.md do Marco 3 (`operacao/os`) §3.2 declara que `OS.numero_os` é gerado por uma "sequence `os_numero_seq_<tenant>`" sem detalhar:

- Comportamento em rollback (sequence PG é não-transacional → rollback deixa buraco).
- Provisionamento (cria no `Tenant.Criado` consumer? na 1ª OS? migração one-shot?).
- Cleanup quando `Tenant.Encerrado`.
- Concorrência multi-tenant em DDL (`CREATE SEQUENCE` por tenant não escala — 1000 tenants = 1000 sequences no `pg_class`).

O review tech-lead (P-OS-T2 — bloqueante) apontou 3 padrões reais e a spec deixava indefinido qual escolher:

| Padrão | Gap-less? | Escala? | Complexidade |
|---|---|---|---|
| `CREATE SEQUENCE` por tenant | NÃO (rollback fura) | mal (DDL por tenant) | baixa |
| `CREATE SEQUENCE` global + (tenant_id, numero) unique | NÃO | bem | baixa |
| Tabela `numerador_os(tenant_id, ultimo)` com `SELECT … FOR UPDATE` | SIM | bem (contém-se na linha) | média |

## Decisão

**Adotar padrão "sequence global + unique composto (tenant_id, numero), buracos aceitos".**

### Mecanismo

1. Coluna `OS.numero_os` populada via expressão `nextval('os_numero_seq_global')` no INSERT.
2. Sequence única global `os_numero_seq_global` (não há sequence por tenant — escala melhor; rollback gera buraco numérico aceito).
3. Constraint `UNIQUE(tenant_id, numero_os)` garante unicidade dentro do tenant.
4. Formato exibido ao usuário: `OS-YYYY-NNNNNN` (ex: `OS-2026-001042`) — usar `tenant_id` interno como chave, mas exibir formato amigável ao operador.
5. Nenhuma operação cria buracos artificiais; buracos só por rollback de transação que tenha pegado um valor.

### Justificativa

- **Receita Federal não exige gap-less em OS.** Exigência de numeração contínua é específica para NFS-e / NFC-e / CT-e — escopo do Marco 4 (`fiscal`), tratado em ADR-0008/0049 com mecanismo próprio (tabela `numerador_fiscal`).
- **Auditor RBC/CGCRE não questiona buracos em OS** desde que a rastreabilidade (FK orçamento → OS → atividade → calibração → certificado) esteja preservada. O número da OS é identificador operacional, não regulatório.
- **Performance: escalável** — sequence global PG é lock-free; 1000 tenants concorrentes não geram contenção. Tabela `numerador_os(tenant_id, ultimo) FOR UPDATE` (alternativa gap-less) gera lock por linha — sob 50 OS/min/tenant cria fila de espera 100-300ms.
- **Operação: simples** — sem DDL por tenant; sem necessidade de provisionamento explícito em `Tenant.Criado` consumer; sem cleanup em `Tenant.Encerrado`.

### Trade-offs aceitos

- **Buracos aparecem em uso real** quando transação que pegou número faz rollback. Exemplo: OS 1042 criada, rollback por validation error → próxima OS é 1044, deixando 1043 vazio.
- **Auditor curioso pode perguntar** "por que pulou de 1042 para 1044?". Resposta documentada: "rollback de transação em criação concorrente; rastreabilidade ISO 17025 preservada via correlation_id + event log". Esta ADR é a evidência da decisão.
- **Formato exibido (`OS-YYYY-NNNNNN`)** usa o ano da criação para mitigar percepção de buracos (ano novo, contagem nova subjetiva).

## INVs (em REGRAS-INEGOCIAVEIS.md)

- **INV-OS-NUM-001**: `OS.numero_os` é gerado por `nextval('os_numero_seq_global')` no INSERT; `UNIQUE(tenant_id, numero_os)` garante unicidade por tenant; buracos por rollback são aceitos e não devem ser preenchidos artificialmente.

## Alternativas consideradas (rejeitadas)

### Alt 1 — `CREATE SEQUENCE` por tenant

Rejeitada por não escalar. 1000 tenants = 1000 entradas em `pg_class`; DDL no provisionamento de cada tenant aumenta complexidade do bootstrap; cleanup em `Tenant.Encerrado` requer DROP SEQUENCE (operação destrutiva que requer cuidado em ambiente multi-tenant).

### Alt 2 — Tabela `numerador_os(tenant_id, ultimo)` com `SELECT … FOR UPDATE`

Rejeitada para Marco 3, **mas reaproveitada para Marco 4 fiscal** (`numerador_fiscal`) onde gap-less é obrigatório por lei. A complexidade adicional (lock por linha + contenção sob carga) é justificável só onde a regulação exige.

## Impacto na spec.md M3

§3.2 reescrito:

```diff
- `numero_os VARCHAR(20)` — gerado pela sequence `os_numero_seq_<tenant>`
+ `numero_os BIGINT NOT NULL DEFAULT nextval('os_numero_seq_global')` — sequence global PG; UNIQUE(tenant_id, numero_os); buracos por rollback aceitos (ADR-0056)
+ `numero_os_exibido VARCHAR(20)` GENERATED ALWAYS AS (`'OS-' || EXTRACT(YEAR FROM criada_em) || '-' || LPAD(numero_os::text, 6, '0')`) STORED
```

§13 drill `validar_m3_os` item 9 reescrito:

```diff
- Sequence `os_numero_seq_<tenant>` por tenant ativo.
+ Sequence global `os_numero_seq_global` existe + UNIQUE(tenant_id, numero_os) ativa.
```

## Teste de regressão

`tests/regressao/test_inv_os_num_001_buracos_aceitos.py`:

1. Cria 5 OS sequenciais (espera 1, 2, 3, 4, 5).
2. Provoca rollback no meio (uma INSERT pega número 6, transação faz rollback).
3. Próxima OS pega número 7 (não 6 — buraco intencional).
4. Verifica que `SELECT MAX(numero_os) FROM os WHERE tenant_id = X` retorna 7.

## Revisão futura

Esta ADR pode ser revista se:

- ANPD ou CGCRE publicar orientação que exija gap-less em OS (não há tal exigência hoje).
- Pesquisa de mercado mostrar que clientes-alvo (laboratórios farma top-3) recusam OS com buracos por preferência cultural.
- Migração para Postgres 17+ com identity columns explicit alternative tornar gap-less performático.
