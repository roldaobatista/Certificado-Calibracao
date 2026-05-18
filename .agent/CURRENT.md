# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** Wave A em andamento — 4 das 5 US do módulo `clientes` FECHADAS verde, US-CLI-003 com plano escrito e reviews pendentes.
**Modo:** AUTÔNOMO; ritual orquestrador OBRIGATÓRIO (memória `feedback_ritual_orquestrador`).

## Estado do módulo clientes (Wave A · Marco 1)

| US | Tema | Status | Testes |
|---|---|---|---|
| US-CLI-001 | Cadastro PF/PJ + LGPD + evento Cliente.Criado | ✅ FECHADA | 8 |
| US-CLI-002 | Visão 360° + log acesso INV-013 | ✅ FECHADA | 7 |
| US-CLI-003 | Importação 1-clique CSV | 🟡 plano escrito; **reviews tech-lead + advogado PENDENTES** |
| US-CLI-004 | Bloqueio manual + automático ADR-0015 | ✅ FECHADA | 15 |
| US-CLI-005 | Dedup manual wizard + soft-delete | ✅ FECHADA | 9 |

**Suite total: 168 passed + 1 skipped. Hooks: 103/103.**

## Próximo passo (próxima sessão)

1. Invocar `tech-lead-saas-regulado` e `advogado-saas-regulado` em paralelo sobre `docs/dominios/comercial/modulos/clientes/planos/US-CLI-003.md` (plano já escrito + commitado).
2. Endereçar ressalvas no plano.
3. Implementar T-CLI-041 a T-CLI-048.
4. Após US-003 fechada: rodar os 3 auditores Família 5 (Qualidade + Segurança + Produto) sobre o módulo `clientes` inteiro (task #24).
5. Fechar módulo clientes (atualizar CURRENT + memória + commits).

## Estado do sistema

- Containers `afere-db` + `afere-app` rodando
- Banco `afere` + `test_afere` migrados até última migration (clientes.0011, audit.0006, tenant.0002)
- Pra parar: `docker compose down`

## ADRs ativas pendentes pra continuar Wave A

- Após clientes fechar: próximo módulo é provavelmente `orcamentos` ou `equipamentos` (auditor Produto recomenda começar pelos não-bloqueados por ADR — `orcamentos` depende de `precificacao` futuro; `equipamentos` é stand-alone).
