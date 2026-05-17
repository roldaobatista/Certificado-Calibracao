# ADR-0008 — Camada fiscal pluggable (multi-país e multi-fornecedor)

> **Status:** rascunho (17/05/2026) — bloqueante do Portão 2 da ADR-0001
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Parecer 7 (crescimento futuro) + Parecer 4 (supply chain) + Parecer 8 (incidente: "PlugNotas sobe preço 10x") da 2ª auditoria de 10 agentes. ADR-0001 v2 cita PlugNotas como SDK Python mas sem porta/adapter agnóstica. Em 2-3 anos se sair pra Argentina/México, vira reescrita 6-12 meses.
> **Depende de:** ADR-0001 v2 (stack Django + DRF)

---

## Contexto

NFS-e BR tem deadline 01/09/2026 (Padrão Nacional ADN). PlugNotas é a recomendação de 1ª implementação por cobertura nacional + SDK Python oficial. Mas:

- **Bus factor:** PlugNotas é empresa única; se subir preço 10x ou sair, contrato fiscal trava.
- **LATAM:** Argentina (AFIP factura electrónica), México (CFDI SAT), Chile (DTE) — PlugNotas só cobre BR.
- **Vendor lock-in regulatório:** acoplar Django direto ao SDK PlugNotas obriga reescrita de domínio fiscal pra mudar fornecedor.

---

## Decisão (rascunho — a fechar)

### Interface `FiscalProvider` agnóstica de país

```python
# domain/fiscal/provider.py (rascunho)
class FiscalProvider(Protocol):
    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult: ...
    def cancel_invoice(self, invoice_id: str, reason: str) -> CancelResult: ...
    def query_status(self, invoice_id: str) -> Status: ...
    def store_xml(self, invoice_id: str, xml: bytes) -> StorageRef: ...
```

`InvoicePayload` é tipo agnóstico (não copia campos PlugNotas). Implementações:

- **`PlugNotasProvider`** — NFS-e BR (1ª implementação MVP-1)
- **`FocusNFeProvider`** — fallback BR homologado em sandbox (drill trimestral)
- **`AFIPProvider`** — Argentina factura electrónica (futuro V3+)
- **`CFDIProvider`** — México CFDI SAT (futuro V3+)
- **`MockProvider`** — testes pytest

### Armazenamento dos XMLs assinados

- **Cópia local em B2 próprio** (não só no PlugNotas) — saída do fornecedor garantida.
- WORM Object Lock + retenção 5 anos LGPD (INV-005).

### Smoke test trimestral

- CI roda E2E contra sandbox Focus NFe a cada release — comprova plano B funcional.
- Sem smoke verde → ADR-0008 desclassificado.

---

## Itens a fazer
- [ ] Interface `FiscalProvider` desenhada
- [ ] `PlugNotasProvider` implementado + testado em sandbox
- [ ] `FocusNFeProvider` implementado + smoke trimestral
- [ ] Storage adapter B2 pra XMLs assinados
- [ ] Cláusula contratual SLA + portabilidade com PlugNotas

---

## Aprovação
- [ ] Roldão — pendente
- [ ] Auditor 5 (compliance) — pendente
