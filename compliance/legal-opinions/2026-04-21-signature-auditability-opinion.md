---
id: LEGAL-OP-PRD-13-21
status: approved
owner: legal-counsel
subject: assinatura-eletronica-auditavel
date: 2026-04-21T05:30:00-04:00
reviewed_artifacts:
  - PRD.md
  - compliance/legal-opinions/dpa-template.md
  - compliance/legal-opinions/lgpd-matrix.md
  - packages/audit-log/**
---

# Parecer juridico formal — assinatura eletronica auditavel

## Escopo

Revisao juridica da estrategia do MVP para assinatura eletronica auditavel em certificados e eventos de aprovacao, com foco em admissibilidade contratual e forca probatoria do registro tecnico.

## Base normativa revisada

- `MP 2.200-2/2001`, especialmente `art. 10, § 2º`.
- `Lei nº 14.063/2020`, com enquadramento de assinatura eletronica adequada ao contexto e ao risco.
- `LGPD`, com reflexos de autenticacao, trilha e minimizacao para dados pessoais associados ao ato de assinatura.

## Entendimento juridico

Os documentos eletronicos do MVP podem ser admitidos entre as partes desde que o fluxo preserve evidencia suficiente de integridade, autoria e trilha de auditoria. A leitura juridica adotada para o Aferê e que a `MP 2.200-2/2001`, no `art. 10, § 2º`, permite outro meio de comprovacao de autoria e integridade quando admitido pelas partes como valido.

No desenho atual, a estrategia probatoria nao depende apenas do clique de assinatura. Ela depende do conjunto de registros tecnicos encadeados: identidade do ator, data e hora, dispositivo, hash do certificado, historico de revisao e audit log imutavel. Em termos juridicos, isso reforca integridade, autoria e trilha de auditoria.

A `Lei nº 14.063/2020` reforca a necessidade de adequacao do metodo de assinatura ao risco do ato. Para o MVP, a opiniao e que a assinatura eletronica auditavel e defensavel para o fluxo privado entre as partes contratantes, desde que os termos contratuais e o DPA espelhem a arquitetura de evidencia adotada.

## Limites e claims proibidos

Este parecer nao equipara o MVP a assinatura qualificada ICP-Brasil e nao autoriza claim comercial de equivalencia universal. O parecer tambem nao afirma validade irrestrita para qualquer litigio ou orgao sem analise do caso concreto.

Em linguagem objetiva: o parecer entende que a arquitetura proposta sustenta assinatura eletronica auditavel, mas não exige ICP-Brasil para o MVP. O repositorio deve continuar bloqueando claims absolutos e qualquer promessa de "aceitacao garantida" fora do contexto contratual e probatorio descrito.

## Veredito

PASS. A estrategia do MVP e juridicamente defensavel para assinatura eletronica auditavel, desde que:

- haja aceite contratual expresso das partes;
- o DPA e a matriz LGPD permaneçam consistentes com os suboperadores efetivos;
- o audit log preserve integridade, autoria e trilha de auditoria;
- o produto nao prometa ICP-Brasil, assinatura qualificada ou aceitacao universal.
