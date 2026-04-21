# 0028 — Owner de governanca normativa com RACI e orcamento pre-go-live

## Contexto

O PRD §13.22 exige que a governanca normativa tenha owner explicito, RACI e orcamento aprovados antes do go-live. O repositorio ja possui watchlist, SLA e ownership tecnico do pacote normativo em `adr/0004-normative-package-governance.md`, mas ainda nao havia um artefato canonico unico que consolidasse:

- owner accountable da governanca;
- separacao entre governanca do processo e ownership tecnico do pacote;
- comite normativo e cadence;
- RACI das etapas de §16.4;
- baseline de orcamento operacional antes da primeira emissao produtiva.

Sem esse artefato, `REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER` permanecia apenas mapeado, sem validacao ativa.

## Escopo

- Criar um dossie canonico pre-go-live em `compliance/release-norm/pre-go-live-normative-governance.yaml`.
- Formalizar em ADR a separacao entre `product-governance` como accountable do rito e `regulator` como owner tecnico do conteudo do pacote normativo.
- Adicionar teste ativo em `evals/regulatory/prd-13-22-normative-governance-owner.test.ts`.
- Promover `REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER` para `validated` no dossie se o teste passar.

## Fora de escopo

- Provisionar KMS real para assinatura de pacote normativo.
- Criar workflow operacional de release normativa trimestral completo.
- Nomear pessoas fisicas fora dos papeis formais ja aprovados no repositorio.
- Fechar P0-2, P0-3 ou P0-6 por completo.

## Critérios de aceite

- O artefato `compliance/release-norm/pre-go-live-normative-governance.yaml` existe e fica sob ownership de `product-governance`.
- O artefato declara explicitamente:
  - owner accountable da governanca;
  - fonte formal da designacao;
  - owner tecnico do conteudo do pacote normativo;
  - composicao e cadence do comite normativo;
  - watchlist normativa;
  - RACI das etapas de monitoracao, analise, planejamento, implementacao, validacao e comunicacao;
  - orcamento aprovado com valores positivos em BRL.
- O teste `evals/regulatory/prd-13-22-normative-governance-owner.test.ts` falha fechado se qualquer item acima desaparecer.
- `REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER` passa de `planned` para `validated` apenas com `linked_tests` apontando para o teste ativo novo.

## Evidência

- `pnpm exec tsx --test evals/regulatory/prd-13-22-normative-governance-owner.test.ts`
- `pnpm validation-dossier:check -- --strict-prd`
- `pnpm check:all`
