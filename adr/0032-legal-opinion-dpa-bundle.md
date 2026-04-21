# ADR 0032 — Bundle juridico do PRD §13.21

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0029-prd-13-21-legal-opinion-dpa.md`, `PRD.md` §11.4 e §13.21, `adr/0003-hosting-and-security-services.md`

## Contexto

O Aferê ja assumia no PRD a existencia de parecer juridico formal sobre assinatura eletronica auditavel, DPA e matriz controlador/operador. Tambem havia uma pendencia expressa na ADR 0003 para `legal-counsel` emitir parecer sobre suboperadores em `compliance/legal-opinions/lgpd-matrix.md`.

O gap era a inexistencia de um pacote canonico e testavel reunindo esses artefatos com revisao juridica explicita.

## Decisão

1. O requisito `REQ-PRD-13-21-LEGAL-OPINION-DPA` passa a ser materializado por um bundle canonico em `compliance/legal-opinions/prd-13-21-legal-bundle.yaml`.
2. O bundle referencia exatamente tres artefatos:
   - parecer juridico formal sobre assinatura eletronica auditavel;
   - minuta de DPA;
   - matriz controlador/operador e suboperadores.
3. `legal-counsel` e o revisor juridico formal do bundle, com qualificacao declarada `advogado-lgpd`.
4. `lgpd-security` permanece owner operacional da matriz LGPD, com revisao juridica por `legal-counsel`.
5. O parecer formal deve registrar, de forma auditavel:
   - fundamento contratual e probatorio da assinatura eletronica auditavel;
   - ausencia de claim de ICP-Brasil no MVP;
   - dependencia de aceite contratual pelas partes e de evidencias de integridade, autoria e trilha.

## Consequências

- O requisito deixa de depender de texto espalhado no PRD e passa a ser verificavel por teste automatizado.
- A pendencia juridica aberta em `adr/0003-hosting-and-security-services.md` fica atendida por artefato versionado.
- O repositorio ganha baseline juridica minima sem prometer substituicao de revisao humana individualizada para contratos customizados.

## Limitações honestas

- O bundle nao substitui assessoria juridica caso a caso para contratos Enterprise ou litigio.
- O parecer valida a estrategia do MVP, nao confere equivalencia a assinatura qualificada ICP-Brasil.
- Os suboperadores refletidos no bundle seguem a topologia vigente da ADR 0003; mudanca de infraestrutura exige nova revisao.
