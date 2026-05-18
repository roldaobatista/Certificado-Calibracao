---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 3-qualidade-testes
auditor: auditor-qualidade
veredito: SÓLIDO COM RESSALVAS
---

# AUDIT-03 — Qualidade de testes / Cobertura / Mascaramento

> Lente 3 de 10. Régua: TST-001..004.

## VEREDITO

**SÓLIDO COM RESSALVAS** — os testes provam comportamento real, não teatro. Exercitam RLS no banco com transação real, unhappy paths explícitos, PII por ausência, rollback atômico forçando falha real. Sem mascaramento estrutural. Ressalvas: drift de números reportados, uma asserção frouxa, código morto, e a suite não roda verde no fluxo default.

## O que está bom (manter)

- RLS testada de verdade: `pytest.raises(ProgrammingError)` em INSERT cross-tenant; `@pytest.mark.django_db(transaction=True)` + contexto real.
- Cross-tenant prova não-vazamento por conteúdo (`assert items == []`, 409→201 cross-tenant, 404 via RLS).
- PII-em-audit honesta: CNPJ/justificativa cru ausente + hash 64 chars + valida salt por tenant (regressão do FAIL coberta).
- Rollback atômico não-tautológico (monkeypatch real, dispara 500, verifica que soft-delete não ocorreu).
- Vetores Serpro com DV calculado à mão.

## Débitos

| ID | Descrição | Gravidade | Arquivo:linha | TST | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| Q1 | Suite default quebra: pyproject fixa DJANGO_SETTINGS_MODULE=config.settings.dev; dev falha com ModuleNotFoundError: redis (commit a27aa06). Só roda verde com --ds=config.settings.test. Gate --cov-fail-under nunca exercido no fluxo default. | ALTA | pyproject.toml:148 / config/settings/dev.py | gate neutralizado | NÃO | test como settings default do pytest OU instalar redis no dev; rodar suite sem override. |
| Q2 | Números em drift: AGENTS diz "295 passed + 3 skipped"; Marco 1 "207 passed + 2 skipped". Real hoje: 213 passed, 1 FAILED, 0 skipped. Clientes = 123 passed, 0 skipped (não 207). | ALTA | AGENTS.md / memória sessão | alegação não verificada | NÃO | Recontar e reescrever; nunca herdar número não re-rodado. |
| Q3 | `test_argon2_eh_primeiro_password_hasher` FALHA: settings.test usa MD5 hasher, smoke cobra Argon2 sem condicionar ao ambiente. | MÉDIA | tests/test_smoke_esqueleto.py:29 | causa não mascarada (bom), mas suite vermelha | fora escopo clientes | Condicionar assert ao ambiente OU separar smoke prod-config. |
| Q4 | Asserção frouxa: parametrizado aceita qualquer um de 2 valores independente do input. | BAIXA | test_clientes_value_objects.py:35 | TST-002 (espírito) | NÃO | `assert cnpj.value == esperado` por parâmetro. |
| Q5 | Código morto `for i in range(3): pass`. | BAIXA | test_clientes_isolamento.py:47 | — | NÃO | Remover. |
| Q6 | `omit` em coverage exclui 4 management commands "pra subir número". | BAIXA | pyproject.toml:178-184 | maquiagem de cobertura | revisar | Cobrir os commands ou declarar % real honesta. |

TST-004 verificado: INV-024/036/013/TENANT-001/AUTHZ-001 têm teste nomeado citando o ID que falharia se violada. Conforme. Sem teste só-pra-cobertura no clientes.

## Recomendação final

Padrão de testes é replicável e honesto — copie (RLS com transaction=True, unhappy pytest.raises, PII por ausência, monkeypatch real). Mas NÃO replique antes de fechar Q1 e Q2: a suite não roda verde no default e os números de aprovação do Marco 1 estão em drift. Prioridade: settings default + redis, smoke argon2, recontar números, limpar Q4/Q5.
