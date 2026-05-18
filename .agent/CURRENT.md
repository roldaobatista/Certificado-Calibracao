# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Foundation/Wave/Marco.

**Fase:** **Wave A em andamento** — Marco 1 (`clientes`) FECHADO verde 2026-05-18 noite
**Modo:** AUTÔNOMO (Roldão "vamos iniciar")

**Marco 1 — clientes (Wave A):**
- ✅ VOs `CNPJ` (alfanumérico ADR-0017 + numérico retrocompatível) e `CPF` (Receita)
- ✅ Modelo `Cliente` PF/PJ com dedup INV-024 + UNIQUE INV-036 + RLS pattern v2
- ✅ API REST `/api/v1/clientes/` (CRUD) com `RequireAuthz` deny-by-default
- ✅ Matriz authz seed por migration do próprio módulo (4 ações × 4 perfis)
- ✅ 39 testes novos: 21 VOs (vetores numéricos + alfanuméricos Serpro + edge) + 11 modelo/isolamento (UNHAPPY paths cravados) + 7 E2E API
- ✅ Bug LATENTE de F-A corrigido: middleware fazia `SET LOCAL` sem transaction.atomic — RLS bloqueava resolução de tenants. Só apareceu agora com primeiro endpoint protegido real

**Suite total: 127 passed + 1 skipped + hooks 103/103.**

**Estado do sistema:**
- Containers `afere-db` + `afere-app` rodando
- Banco `afere` com schema clientes + matriz authz seed
- `test_afere` migrado em paralelo
- Pra parar: `docker compose down`

**Próximo passo lógico (autônomo, sem precisar perguntar):**
Continuar Wave A com próximo módulo. Candidato natural: `equipamentos` (entidade base que OS e certificado referenciam, junto com clientes). Ou `orcamentos` (próximo passo comercial).

**Bloqueios reais (gates):**
- 17 PRDs Wave A em `stable` (escrever conforme módulos entrarem)
- 6 ADRs ainda em proposta destravam módulos específicos: 0003 (mobile→app-tecnico), 0004 (sync→app-tecnico), 0008 (fiscal→fiscal/NFS-e), 0009 (A3→certificados), 0010 (telas), 0014/0015/0016 (integrações)
- Não bloqueiam módulos isolados como `equipamentos`, `orcamentos`, `chamados`
