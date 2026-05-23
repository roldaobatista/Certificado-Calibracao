---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/arquitetura/anti-corrosion-layer.md
  - docs/adr/0013-pricing-composicional.md
  - docs/dominios/comercial/modulos/marketplace/prd.md
---

# ADR-0055 — Marketplace de extensões: curadoria + sandbox + revenue share

> **Status:** proposta. **NÃO Wave A** — V2/V3. Resolve achados **G-MKT-1, G-MKT-2, G-MKT-3**.
> **Decisor:** Roldão + `tech-lead-saas-regulado`.
> **Bloqueia:** abertura do marketplace para parceiros externos (sem este, marketplace fica só vitrine do próprio tenant — escopo já coberto pelo PRD `marketplace`).

---

## Contexto

`marketplace/prd.md` Wave A cobre "vitrine pública do TENANT" (catálogo de produtos/serviços do próprio cliente). V2/V3 abre **marketplace de extensões** (parceiros desenvolvem plugins; Aferê publica; tenants instalam). Sem governança, vira ANTI-11 (customização infinita), risco supply chain, LGPD subprocessador. Sem revenue share, sem incentivo a parceiro.

## Decisão

### 1. Curadoria (3 fases)

1. **Submissão:** parceiro submete via portal dev (código + testes + manifest + DPA assinado).
2. **Validação Aferê:** roda testes parceiro + scan security (Bandit/Snyk) + revisão manual `auditor-supplychain` + `auditor-conformidade-lgpd`.
3. **Publicação:** extensão entra no catálogo público; tenant instala via 1 clique.

### 2. Sandbox — INV-MKT-SANDBOX-001

**Extensão Python executa em sandbox isolado: `RestrictedPython` (AST sanitizer) + subprocess separado + cgroups (CPU 500ms, RAM 128MB, disk 0, rede default-deny — só APIs Aferê via allowlist).** Veredito: ALTO. Hook bloqueia release de extensão sem sandbox config.

```
extensao.run()
   ↓
subprocess.Popen([
    "firejail",  # ou nsjail/bwrap
    "--noprofile",
    "--net=none",
    "--rlimit-cpu=1",
    "--rlimit-as=134217728",
    "python", "-c", restricted_code
])
```

Hooks recebem `UntrustedInput[dict]` (porta #17 ACL `MarketplaceExtensionProvider` já modelada).

### 3. Revenue share — atualização ADR-0013

Adicionar **tipo 8** em ADR-0013:

```
ComponenteExtensaoMarketplace
├── extension_id: str
├── percentual_afere: Decimal = 30
├── percentual_desenvolvedor: Decimal = 70
├── preco_mensal: Money
```

Tenant paga R$ X/mês pela extensão; Aferê fica com 30%, desenvolvedor com 70%. Cobrança via `billing-saas` (mesmo gateway). Pagamento ao desenvolvedor mensal por D+30, via PIX (`PaymentGatewayProvider.reembolsar` invertida — payout, V3).

## Alternativas rejeitadas

1. **Marketplace aberto sem curadoria** — supply chain dispara; primeira extensão maliciosa quebra reputação.
2. **WebAssembly em vez de sandbox Python** — barreira pra desenvolvedor BR (Python é língua franca PME).
3. **Revenue share 50/50** — Stripe/Apple cobram 30%; mercado calibrou.

## Consequências

**Positivas:** ecossistema de parceiros; receita variável de Aferê (30% de R$ X × N tenants); especialização por nicho (extensão de balança rodoviária, extensão de cromatografia).
**Negativas:** revisão manual de cada extensão (custo operacional Aferê); responsabilidade compartilhada em incidente (ADR-0019 RC IA estende-se a extensões).

## Referências

- ACL porta #17 `MarketplaceExtensionProvider`
- ADR-0013 (tipo 8 a adicionar)
- ADR-0019 (RC IA)
- RestrictedPython (https://restrictedpython.readthedocs.io)
