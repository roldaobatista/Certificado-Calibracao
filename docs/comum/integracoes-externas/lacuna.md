---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Lacuna Web PKI — assinatura A3 cliente-side

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Assinatura digital ICP-Brasil A3 cliente-side (desktop + Flutter FFI no mobile) |
| Status | ⏳ Wave A |
| Anti-corrosion | `infrastructure/signature/lacuna_provider.py` + cliente JS/Dart |
| Custo aprox | Licença comercial — varia por volume |

---

## Por que Lacuna

ADR-0009: A3 **sempre cliente-side** por segurança (chave privada nunca toca servidor). Lacuna é a referência BR de Web PKI:
- Suporta token físico + cartão + dispositivos USB
- Browser plugin maduro
- Mobile via Flutter FFI
- LTV (Long-Term Validation) nativo

---

## Defesa anti-replay

ADR-0009 cravou:
- **Nonce gerado pelo servidor** a cada assinatura (não reutilizável)
- **signing-time controlado pelo servidor** (não pelo cliente)
- **One-shot** (assinatura usada 1 vez; servidor invalida nonce)

Detalhes em ADR-0009.

---

## Auth

Licença Lacuna por tenant (ou por instalação). Verificar modelo comercial.

---

## Pendências

- [ ] Contrato Lacuna (Wave A)
- [ ] Integração JS (desktop)
- [ ] Integração Flutter FFI (mobile)
- [ ] Smoke test pyhanko + chain of trust
- [ ] PAdES-LTV configurado

---

## Referências

- ADR-0009
- `arquitetura/anti-corrosion-layer.md` (porta Signature)
- `dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md`
