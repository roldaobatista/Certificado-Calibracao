# Spec 0007 — Auditores externos como gate verificável

## Objetivo

Implementar o P0-12 como gate executável para preservar separação de funções: auditores externos emitem parecer, mas não editam o que auditam.

## Escopo

- Validar os três agentes auditores: `metrology-auditor`, `legal-counsel` e `senior-reviewer`.
- Validar diretórios e templates de parecer em `compliance/audits/{metrology,legal,code}/`.
- Validar template de escalonamento humano para os 5 casos-limite.
- Bloquear release quando qualquer parecer obrigatório estiver ausente, tiver `verdict: FAIL` ou possuir `blockers`.
- Integrar `pnpm external-auditors-gate` ao `pnpm check:all` e ao pre-commit.

## Critérios de aceite

- O gate falha se qualquer agente auditor estiver ausente.
- O gate falha se auditor tiver ferramenta de edição direta ou path de escrita fora do domínio permitido.
- O gate falha se templates de parecer ou escalonamento humano estiverem ausentes.
- O subcomando `release --release <versao>` falha quando faltar um dos três pareceres L5.
- O subcomando `release --release <versao>` falha se parecer tiver `FAIL` ou `blockers` não vazio.
- O gate passa quando os três agentes, os templates e os 5 casos-limite estão declarados.

## Fora de escopo

- Não substitui auditor CGCRE, advogado ou especialista humano nos 5 casos-limite.
- Não executa a auditoria em si; valida a estrutura e o bloqueio fail-closed.
- Não altera ownership dos executores internos.
