---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Focus NFe — NFS-e (fallback do PlugNotas + smoke test trimestral)

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Segundo `FiscalProvider` — fallback + smoke test |
| Status | ⏳ Wave A — segundo provider |
| Anti-corrosion | `infrastructure/fiscal/focus_provider.py` (a criar) |
| Custo aprox | R$ 0,40-1,00 por NFS-e |

---

## Por que existe

ADR-0008 exige **2 providers fiscais** com smoke test trimestral. Razão:
- PlugNotas pode falir, mudar termos abruptos, ter outage grave
- Tenant precisa de continuidade na emissão fiscal
- Anti-vendor-lock-in

Focus NFe é segundo provider de prontidão. Smoke test trimestral garante que troca funcione.

---

## Smoke test trimestral

A cada 3 meses:
1. Selecionar 1 tenant teste (Balanças Solution na janela atual)
2. Emitir 1 NF-e via Focus em vez de PlugNotas
3. Validar conteúdo + assinatura + retorno
4. Verificar que tenant não nota diferença
5. Registrar em `governanca/trilha-auditoria-agentes.md`

Se smoke falha → revisar interface; se passa 3x seguidas → confiança alta de fallback funcional.

---

## Auth / Endpoints / Retry / Idempotência

Mesmos critérios de PlugNotas (ver `plugnotas.md`). Detalhes específicos quando Wave A começar.

---

## DPA / LGPD

Idem PlugNotas — DPA comercial.

---

## Pendências

- [ ] Contrato Focus NFe (Wave A — não-bloqueante; criar antes do smoke trimestral)
- [ ] Implementação `FiscalProvider` para Focus
- [ ] Suite de testes que rode em ambos providers
- [ ] Calendário de smoke test trimestral

---

## Referências

- ADR-0008
- `plugnotas.md`
- `arquitetura/anti-corrosion-layer.md`
