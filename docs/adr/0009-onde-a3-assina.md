# ADR-0009 — Onde a assinatura digital A3 (token físico ICP-Brasil) acontece

> **Status:** rascunho (17/05/2026) — bloqueante do Portão 2 da ADR-0001
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Parecer 1 da 2ª auditoria — "**nenhuma stack faz A3 server-side bonito**". Padrão de mercado em ERP regulado é assinar A3 no cliente (Web PKI no browser ou app desktop com token local), não no servidor. ADR-0001 v2 propôs `python-pkcs11` server-side sem confrontar com a opção cliente-side.
> **Depende de:** ADR-0001 v2 (stack Django + Flutter)

---

## Contexto

Perfil A (laboratório acreditado RBC) exige certificado digital ICP-Brasil — A1 (arquivo PKCS#12) **ou A3** (token físico hardware). INV-017 marca obrigatório.

**Problema A3 server-side:**
- Token físico fica fisicamente conectado a uma máquina — não dá pra "ter um A3 no servidor" multi-tenant.
- Drivers PKCS#11 do token (SafeNet/Aladdin/Watchdata) precisam estar no servidor.
- Cada cliente teria que enviar token físico pro datacenter? Inviável.

**Problema A3 cliente-side:**
- Browser → Web PKI (Lacuna BRy) chama o token local do usuário.
- App desktop (Flutter desktop ou .NET) → invoca PKCS#11 nativo do SO.
- Servidor só recebe o **hash assinado** (CMS/PKCS#7) e o anexa ao PDF/XML.
- Esse é o padrão de mercado (e-CAC, NF-e webservices, NFS-e via browser).

---

## Decisão proposta (a fechar)

**A3 sempre cliente-side. Servidor nunca toca token físico.**

### Fluxo:
1. Servidor gera "documento a assinar" (hash + estrutura PAdES/XMLDSig).
2. Cliente (Web PKI no browser ou Flutter desktop) invoca o token local.
3. Token assina o hash; cliente devolve a assinatura CMS.
4. Servidor anexa assinatura ao PDF/XML via `pyhanko` (PAdES-LTV completo com a assinatura já feita) ou lib equivalente XMLDSig.

### Implementações
- **Browser (escritório):** Web PKI Lacuna ou BRy (componente JS, há quase 20 anos no mercado).
- **Flutter desktop (Roldão e signatários técnicos):** invoca PKCS#11 via FFI Dart nativo.
- **A1 (perfil B/C/D):** servidor pode armazenar PKCS#12 em B2 + chave KMS desencriptando on-demand. Esse caminho é OK porque A1 não é token físico.

### Interface `SignatureProvider`
- `A3ClientSideProvider` (browser + desktop) — produção
- `A1ServerSideProvider` — A1 only
- `MockSignatureProvider` — testes

---

## Consequências

### Positivas
- Token físico nunca sai do cliente → soberania perfeita.
- Custo de driver PKCS#11 no servidor zero.
- Sem ataque a token central.

### Negativas
- Web PKI Lacuna/BRy é pago (licença por usuário) — ~R$ 30-80/usuário/mês ou contrato volumétrico. Orçar.
- Flutter desktop com FFI PKCS#11 exige binding nativo (Windows + macOS + Linux). Trabalho de F-D.
- Cliente perde token = não assina (mas é problema do cliente, não nosso).

---

## Itens a fazer
- [ ] Cotação Web PKI Lacuna + BRy
- [ ] PoC Flutter desktop + token físico (SafeNet 5110)
- [ ] Interface `SignatureProvider`
- [ ] Documentação de fluxo CMS/PKCS#7 pra Roldão entender

---

## Aprovação
- [ ] Roldão — pendente
- [ ] Auditor 5 (compliance) — pendente
- [ ] Auditor 6 (segurança) — pendente
