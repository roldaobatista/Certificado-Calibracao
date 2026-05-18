---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 7-segurabilidade
auditor: corretora-seguros-saas
veredito: SEGURÁVEL COM RESSALVAS
---

# AUDIT-07 — Risco / Segurabilidade (Cyber + RC profissional)

> Lente 7 de 10. Planejamento de risco — emissão de apólice exige corretora SUSEP licenciada.

## VEREDITO

**SEGURÁVEL COM RESSALVAS** — defesa em profundidade real e trilha forense defensável elevam segurabilidade acima do baseline SaaS BR. Mas 2 pré-requisitos do ADR-0019 não materializados em código + 1 concentração de risco no serviço de auditoria. Cotaria com sublimite no evento "falha sistêmica da trilha" até R-CLI-01/02/03 fecharem.

## O que está bom (manter)

- Defesa em profundidade genuína (audit imutável em 3 camadas: Python + trigger PG + hook; isolamento tenant duplo).
- Trilha forense juridicamente defensável (hash chain + advisory lock + verificador detecta todos os elos).
- PII nunca crua no audit (hash salgado + sanitização). Dump vazado não expõe titulares.
- CSV import com superfície controlada + declaração de procedência (transfere risco LGPD ao tenant de forma auditável).
- Trilha de pareceres de subagentes preservada (Controle 6 ADR-0019).

## Débitos

| ID | Descrição | Gravidade | Risco | Arquivo | Replicar M2? | Controle compensatório |
|---|---|---|---|---|---|---|
| R-CLI-01 | Suite anti-regressão tests/regressao/inv_*.py não existe. Critério 4 ADR-0019 / Controle 2 declarados, não materializados. | Alta | RC profissional (neutraliza "ausência de revisão humana = neglect") | (ausente) | NÃO replicar a ausência | Criar tests/regressao/inv_*.py + linter CI grepando INV-NNN (TST-004 real). |
| R-CLI-02 | `registrar_auditoria` lê order_by("-timestamp").first() — único ponto que sustenta a cadeia de TODOS os tenants (tabela global). Falha = risco sistêmico cross-tenant não-segurável como evento único. | Alta | Cyber (concentração de risco; underwriter recusa/sublimita) | services.py:127-146 | mitigar antes | Idempotência por correlation_id UNIQUE; job de verificação agendado; alerta se cadeia quebrar. |
| R-CLI-03 | Hook `equipamento-imutabilidade-check.sh` (Critério 3 ADR-0019) não existe — só documentado "a criar". | Média | RC (INV-025 é o risco-âncora do ADR-0019) | (ausente) | pré-condição M2 | Criar o hook antes do 1º /implement de equipamentos. |
| R-CLI-04 | sanitizar_payload_audit por denylist não cobre PII em chave fora da denylist. | Baixa | Cyber (severidade residual baixa) | services.py:54-101 | replicar reforçando | Allowlist de chaves para payloads devolvidos em API. |
| R-CLI-05 | hashers PII aceitam tenant_id=None "retrocompat" — hash sem sal invertível. | Média | Cyber (regressão silenciosa) | views.py:52-68 | NÃO a brecha | tenant_id obrigatório; hook anti-regressão grep. |

## Recomendação final

Cotaria RC E&O + cyber com desconto pelos controles (acima da média BR), MAS condicionada ao fechamento de R-CLI-01/02/03 antes do 1º tenant externo pago. Não são cosméticos — são os controles do ADR-0019 que transformam "100% IA" de exclusão em risco segurável; documentá-los sem materializar reabre a cláusula de exclusão por neglect. Underwriter recusaria cobrir hoje sem ressalva: falha sistêmica da trilha global (R-CLI-02). Limite legal: emissão/sublimite/cláusula de equiparação exigem corretora SUSEP — contratar Tech E&O (Marsh/AON/Howden) quando 1º tenant pago entrar.
