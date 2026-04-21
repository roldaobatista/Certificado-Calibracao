# ADR 0034 — Politica executavel de bloqueio por escopo e CMC

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0031-prd-13-10-scope-cmc-block.md`, `PRD.md` §6.5, §13.10 e §17.5.10

## Contexto

O PRD estabelece que laboratorio acreditado Tipo A so pode emitir certificado com simbolo Cgcre/RBC quando o item estiver dentro do escopo acreditado e a `U` expandida nao violar a CMC declarada. O mesmo documento diferencia dois comportamentos:

- item fora do escopo ou acreditacao vencida: emissao ainda pode ocorrer, mas sem simbolo;
- `U < CMC`: trata-se de inconsistencia tecnica e a emissao do ponto deve ser bloqueada.

O repositório ja possuia o requisito textual e a regra geral `RULE-CGCRE-SYMBOL-SCOPE` no pacote normativo baseline, mas faltava uma API pequena e testavel que transformasse esse criterio em decisao executavel.

## Decisão

1. `@afere/normative-rules` passa a exportar `evaluateAccreditedScopeCmc()`.
2. A funcao retorna, no minimo:
   - `canEmitCertificate`;
   - `canUseAccreditationSymbol`;
   - `symbolPolicy`;
   - `blockers`;
   - `warnings`.
3. Para perfil `A`:
   - ausencia de cadastro formal de escopo ou CMC bloqueia a emissao;
   - `U < CMC` bloqueia a emissao do ponto com blocker explicito;
   - item fora do escopo acreditado ou acreditacao vencida suprime o simbolo e registra aviso.
4. Para perfis nao acreditados, a funcao responde em modo nao aplicavel, mantendo simbolo bloqueado por arquitetura.

## Consequências

- O PRD §13.10 deixa de depender apenas de texto e passa a ter evidencia executavel.
- `apps/api` ganha um contrato futuro unico para decidir se a emissao Tipo A sai com simbolo, sem simbolo ou bloqueada.
- O requisito fica alinhado ao fail-closed: inconsistencia de CMC nao e mascarada por emissao silenciosa sem simbolo.

## Limitações honestas

- Esta ADR nao implementa matching real de `scope_items` por faixa, instrumento e classe; recebe apenas o resultado booleano `withinAccreditedScope`.
- A fila de revisao do Gestor da Qualidade continua fora desta fatia.
- A funcao nao consulta servicos externos da Cgcre nem altera o fluxo real de emissao em `apps/api`.
