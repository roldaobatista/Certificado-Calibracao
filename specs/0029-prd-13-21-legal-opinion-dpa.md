# 0029 — Parecer juridico formal, DPA e matriz LGPD para o PRD §13.21

## Contexto

O PRD §13.21 exige tres artefatos juridicos antes do go-live:

- parecer juridico formal sobre assinatura eletronica auditavel;
- minuta de DPA;
- matriz controlador/operador revisada por advogado LGPD.

O repositorio ja declarava o requisito no dossie e citava em `adr/0003-hosting-and-security-services.md` a necessidade de um parecer em `compliance/legal-opinions/lgpd-matrix.md`, mas `compliance/legal-opinions/` ainda nao possuia o pacote documental minimo para validacao ativa.

## Escopo

- Criar um bundle canonico em `compliance/legal-opinions/prd-13-21-legal-bundle.yaml`.
- Adicionar o parecer juridico formal sobre assinatura eletronica auditavel.
- Adicionar a minuta de DPA.
- Adicionar a matriz controlador/operador e suboperadores.
- Validar tudo com teste ativo em `evals/regulatory/prd-13-21-legal-opinion-dpa.test.ts`.
- Promover `REQ-PRD-13-21-LEGAL-OPINION-DPA` para `validated` quando o teste estiver verde.

## Fora de escopo

- Assinatura ICP-Brasil.
- Negociacao comercial de DPA customizado Enterprise.
- Implementacao de DSAR, portal do DPO ou fluxos de onboarding.
- Qualquer mudanca de codigo em autenticação, assinatura ou audit log.

## Critérios de aceite

- Existe um indice canonico ligando formalmente os tres artefatos juridicos do requisito.
- O parecer juridico cita `MP 2.200-2/2001`, `art. 10, § 2º`, `Lei nº 14.063/2020` e limita honestamente o MVP sem prometer ICP-Brasil.
- A minuta de DPA explicita papeis de Controlador, Operador, Suboperadores, instrucoes documentadas e direitos dos titulares.
- A matriz LGPD cobre ao menos as cinco classes de dados declaradas no PRD §11.4.
- O bundle registra revisao por `legal-counsel` com qualificacao `advogado-lgpd`.

## Evidência

- `pnpm exec tsx --test evals/regulatory/prd-13-21-legal-opinion-dpa.test.ts`
- `pnpm test:regulatory`
- `pnpm validation-dossier:check -- --strict-prd`
