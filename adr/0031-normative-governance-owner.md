# ADR 0031 — Owner de governanca normativa pre-go-live

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0028-prd-13-22-normative-governance-owner.md`, `PRD.md` §13.22 e §16.4, `adr/0004-normative-package-governance.md`, `adr/0009-tiebreaker-designation.md`

## Contexto

O PRD exige que o processo de governanca normativa tenha owner nominal, RACI e orcamento antes do go-live. O repositorio ja tinha:

- ownership tecnico do pacote normativo em `adr/0004-normative-package-governance.md`;
- designacao formal do papel humano `Responsavel Tecnico do Produto` em `adr/0009-tiebreaker-designation.md`;
- estrutura de `compliance/release-norm/` sob ownership de `product-governance`.

O gap era a ausencia de um artefato unico que conectasse esses elementos em um gate pre-go-live verificavel por teste.

## Decisão

1. `product-governance` passa a ser o accountable formal da governanca normativa pre-go-live.
2. O owner nominal da governanca e registrado pelo papel humano designado `Responsavel Tecnico do Produto`, usando `adr/0009-tiebreaker-designation.md` como fonte formal da designacao.
3. `regulator` permanece owner tecnico do conteudo do pacote normativo e da watchlist materializada em `compliance/normative-packages/**`, conforme `adr/0004-normative-package-governance.md`.
4. O artefato canonico dessa decisao fica em `compliance/release-norm/pre-go-live-normative-governance.yaml`.
5. O artefato deve incluir:
   - comite normativo;
   - watchlist;
   - RACI do pipeline de §16.4;
   - baseline de orcamento em BRL;
   - referencias explicitas para `compliance/normative-packages/approved/` e `compliance/normative-packages/releases/manifest.yaml`.

## Consequências

- `REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER` pode ser validado por evidência automatizada, sem depender de interpretacao implícita de varias ADRs.
- O processo de governanca fica separado do ownership tecnico do conteudo normativo, evitando conflito com a ADR 0004.
- O orcamento passa a ser auditavel no repositorio antes da primeira emissao produtiva.

## Limitações honestas

- O owner nominal continua expresso como papel humano formal, nao como nome civil, porque o repositorio ainda nao versiona dados pessoais de governanca.
- O baseline de orcamento e um compromisso operacional do produto; execucao financeira real continua dependendo da organizacao operadora.
- Esta ADR nao substitui a futura implementacao do ciclo trimestral completo de `release-norm-YYYY-MM`.
