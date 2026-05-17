---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Integrações externas — visão geral

> **Pra quê:** índice + critérios comuns das integrações com parceiros externos. Cada parceiro tem seu próprio doc nesta pasta.

---

## Critérios padrão por integração

| Item | Obrigatório? |
|------|--------------|
| Auth (chave, OAuth, certificado) | sim |
| Retry policy (`retry.md`) | sim |
| Timeout (`timeout.md`) | sim |
| Idempotência (`idempotencia.md`) | sim |
| Circuit breaker | sim quando crítico |
| Fallback / segundo provider | sim quando obrigatório de negócio |
| Audit log de toda chamada | sim |
| DPA com parceiro | sim quando trata dado pessoal |
| Custo $/chamada documentado | sim |
| Sandbox/staging | sim |
| Anti-corrosion layer (porta dedicada) | sim |
| Monitoramento de SLA do parceiro | sim |

---

## Lista de parceiros (cada um detalhado em arquivo próprio)

| Parceiro | Função | Status doc | Status integração |
|----------|--------|------------|---------------------|
| [PlugNotas](plugnotas.md) | NFS-e (1ª implementação `FiscalProvider`) | ✅ rascunho | ⏳ Wave A |
| [Focus NFe](focus-nfe.md) | NFS-e (smoke test trimestral + fallback) | ✅ rascunho | ⏳ Wave A |
| [Lacuna Web PKI](lacuna.md) | Assinatura A3 cliente-side | ✅ rascunho | ⏳ Wave A |
| [WhatsApp BSP](whatsapp.md) | Mensageria transacional | ✅ rascunho | ⏳ F-E |
| [Pluggy / Belvo](pluggy-belvo.md) | Open Banking BaaS | ✅ rascunho | ⏳ Wave B |
| [Anthropic API](anthropic.md) | LLM (uso já em desenvolvimento) | ✅ rascunho | ✅ ativo (dev) |
| [SEFAZ / municípios](sefaz-municipios.md) | NF-e estadual + NFS-e municipal | ✅ rascunho | via PlugNotas/Focus |

---

## Princípios

1. **Anti-corrosion layer obrigatório:** módulo Django nunca chama API parceiro direto. Sempre via interface em `infrastructure/` (ver `docs/arquitetura/anti-corrosion-layer.md`).
2. **Fallback pra crítico:** integração crítica (fiscal, A3) tem segundo provedor de prontidão.
3. **Idempotência:** toda chamada usa chave idempotente (parceiro suporta ou Aferê implementa).
4. **Custo monitorado:** painel Grafana mostra $/mês por parceiro; alerta se sobe > 50% do esperado.
5. **DPA atualizado:** lista versionada de subprocessadores compartilhada com tenants (V2).

---

## Quando adicionar novo parceiro

1. Abrir ADR `docs/adr/NNNN-integracao-<parceiro>.md`
2. Justificar necessidade + alternativas consideradas
3. Threat model (segurança, vazamento, dependência)
4. Anti-corrosion: porta nova ou estende existente?
5. Custo $/chamada
6. SLA do parceiro
7. DPA / cláusulas contratuais
8. Roldão aprova
9. Adicionar entrada nesta pasta

---

## Referências

- `docs/arquitetura/anti-corrosion-layer.md` (9 portas)
- `docs/arquitetura/cross-cutting/{retry,timeout,idempotencia}.md`
- `docs/conformidade/comum/transferencia-internacional.md`
- ADR-0008 (fiscal pluggable)
- ADR-0009 (onde A3 assina)
