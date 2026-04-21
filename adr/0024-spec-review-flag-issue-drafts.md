# ADR 0024 — `spec-review-flag` executável na cascata de verificação

Status: Aprovado

Data: 2026-04-20

## Contexto

`harness/14-verification-cascade.md` e `harness/04-compliance-pipeline.md` já definiam o gatilho `spec-review-flag`: três correções consecutivas na mesma spec, alterando AC ou REQs, devem reabrir L1 para re-auditoria.

Depois da ADR 0023, o repositório já conseguia gerar drafts automáticos para `CASCADE-003`, mas ainda faltavam:

- uma base canônica para abrir e atualizar arquivos de `verification-log`;
- um gatilho executável para `CASCADE-007`;
- um template de issue que aceitasse mais de um tipo de finding.

## Decisão

Adicionar `compliance/verification-log/_template.yaml` como artefato obrigatório da árvore canônica e fazer `tools/verification-cascade.ts`:

- ler todos os `compliance/verification-log/*.yaml`, exceto o `_template.yaml`;
- validar a estrutura mínima de cada entrada de propagação;
- calcular o streak mais recente de correções com `ac_changed` ou `reqs_changed`;
- emitir `CASCADE-007` quando esse streak atingir 3 sem evidência de `L1/` em `re_audits_completed`;
- gerar draft determinístico de issue para `spec-review-flag` na mesma raiz `compliance/verification-log/issues/drafts/`.

O template `compliance/verification-log/issues/_template.md` passa a ser genérico, preenchido por placeholders comuns a qualquer finding elegível.

## Consequências

O gatilho de re-auditoria L1 deixa de ser apenas texto no harness e vira regra executável no gate estrutural de P0-10.

O contrato do diretório continua estável: novos findings de cascata podem reutilizar a mesma raiz e o mesmo template genérico sem proliferar formatos.

## Limitação

Esta fatia cobre apenas o nível de spec L1. O caso análogo de épico L0 continua pendente, assim como a bateria final de 30 certificados canônicos em PDF/A.
