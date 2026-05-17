# ADR-0008 — Camada fiscal pluggable (multi-país e multi-fornecedor)

> **Status:** proposta (17/05/2026 noite final) — aguardando aprovação do Roldão. Bloqueante do Portão 2 da ADR-0001 candidata.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Parecer 7 (crescimento futuro) + Parecer 4 (supply chain) + Parecer 8 (incidente PlugNotas) da 2ª auditoria de 10 agentes (17/05/2026). ADR-0001 v2 cita PlugNotas como SDK Python mas sem porta/adapter agnóstica — em 2-3 anos sair pra LATAM vira reescrita de 6-12 meses.
> **Depende de:** ADR-0001 v2 (stack Django + DRF), `docs/arquitetura/anti-corrosion-layer.md`
> **Crítico:** R-016 score 20 — cutover NFS-e Padrão Nacional **01/09/2026** é deadline duro

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **NFS-e** | Nota Fiscal de Serviços eletrônica — emitida por cada prefeitura (com regras diferentes), substituiu o talão de papel. |
| **Padrão Nacional NFS-e** | Padrão único que vai unificar (parte) das ~5.500 prefeituras a partir de 01/09/2026. |
| **BaaS fiscal** | "Banco como serviço" mas pra fiscal — empresa que cuida de toda a complicação de emitir nota e te entrega uma API simples. PlugNotas, Focus NFe, TecnoSpeed são exemplos. |
| **AFIP / CFDI** | AFIP = Argentina (fisco). CFDI = México (fisco). Cada país tem suas próprias regras de nota fiscal eletrônica. |
| **WORM** | "Write Once, Read Many" — armazenamento que NÃO permite apagar nem alterar (exigido pra retenção fiscal e ISO 17025). |

---

## Contexto

NFS-e tem deadline duro **01/09/2026** (Resolução CGSN 189/2026 — confirmado em Bucket D regulatório). PlugNotas é a 1ª implementação proposta porque:
- SDK Python oficial
- Cobertura nacional ampla (~2.000 prefeituras ativadas, mais Padrão Nacional)
- Cliente paga só por NFS-e emitida (sem mensalidade fixa pesada)

Mas há 3 riscos do PlugNotas (Parecer 4 + 8):

1. **Empresa única (bus factor empresarial)** — se subir preço 10x ou sair do ar, contrato fiscal trava
2. **LATAM:** Argentina (AFIP factura electrónica), México (CFDI SAT), Chile (DTE) — PlugNotas só cobre BR. Internacionalização (sinalizada como tese pelo Parecer 7) vira reescrita 6-12 meses se acoplar Django direto ao SDK PlugNotas
3. **Vendor lock-in regulatório** — acoplar `from plugnotas_sdk import ...` no código de domínio obriga reescrita inteira pra mudar fornecedor

---

## Decisão

Adotar **interface `FiscalProvider` agnóstica de país e fornecedor**, com PlugNotas como 1ª implementação obrigatória + Focus NFe como fallback homologado obrigatório + estrutura preparada pra AFIP/CFDI no futuro.

### 1. Interface `FiscalProvider` (Protocol Python)

```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

@dataclass(frozen=True)
class InvoicePayload:
    """Payload agnóstico de país. Adapter traduz pra formato do fornecedor."""
    tenant_id: UUID
    issuer_taxid: str           # CNPJ/CUIT/RFC
    customer_taxid: str
    customer_name: str
    customer_address: Address
    service_description: str
    service_code: str           # CNAE BR / código municipal / CFDI uso
    amount: Decimal
    issue_date: datetime
    metadata: dict              # campos específicos do país (vai pra adapter)

@dataclass(frozen=True)
class InvoiceResult:
    invoice_id: str             # ID interno do fornecedor
    status: InvoiceStatus       # PENDING | AUTHORIZED | REJECTED | CANCELED
    authorization_code: str | None
    pdf_url: str | None
    xml_bytes: bytes | None     # XML assinado (BR) ou JSON equivalente (outros países)
    raw_response: dict          # response completo do fornecedor (debug)
    rejection_reason: str | None

class FiscalProvider(Protocol):
    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult:
        """Emite nota fiscal de serviço. Síncrono — adapter cuida de retry interno."""
        ...

    def cancel_invoice(self, invoice_id: str, reason: str) -> CancelResult:
        """Cancela nota emitida. Janela depende da legislação local."""
        ...

    def query_status(self, invoice_id: str) -> InvoiceStatus:
        """Consulta status (pra notas que ficaram PENDING)."""
        ...

    def store_xml(self, invoice_id: str, xml: bytes) -> StorageRef:
        """Garante cópia do XML assinado no nosso storage WORM (B2 EU)."""
        ...

    def supported_countries(self) -> list[CountryCode]:
        """Quais países este provider cobre. PlugNotas = ['BR']."""
        ...

    def health_check(self) -> HealthStatus:
        """Pra circuit breaker e smoke test trimestral."""
        ...
```

### 2. Implementações

**`PlugNotasProvider`** — NFS-e BR (1ª implementação MVP-1)
- Usa `plugnotas-sdk` (Python) — isolado em `infrastructure/fiscal/plugnotas.py`
- Cobertura: ~2.000 municípios + Padrão Nacional CGSN 189/2026
- Cliente paga por NFS-e emitida (sem mensalidade fixa pesada)
- Configurado em `.env`: `PLUGNOTAS_API_KEY`, `PLUGNOTAS_ENVIRONMENT` (sandbox/production)

**`FocusNFeProvider`** — fallback BR homologado (OBRIGATÓRIO)
- Usa SDK REST direto (focusnfe não tem SDK Python oficial robusto)
- Cobertura semelhante a PlugNotas
- **Smoke test trimestral obrigatório:** CI roda emissão sandbox + cancelamento sandbox → garante que swap em emergência funciona
- Sem ele, R-006 + R-016 não são mitigados (Parecer 8)

**`AFIPProvider`** — Argentina factura electrónica (V3+, ~2028)
- Endpoint WSAA + WSFE da AFIP
- Preparar estrutura agora; implementação só quando 1º cliente AR aparecer

**`CFDIProvider`** — México CFDI SAT (V3+, ~2028)
- Integração via PAC (Proveedor Autorizado de Certificación) — equivalente mexicano de BaaS fiscal
- Preparar estrutura agora; implementação só quando 1º cliente MX aparecer

**`MockFiscalProvider`** — testes pytest
- Resposta determinística por hash do payload
- Modos: `always_authorize`, `always_reject`, `pending_then_authorize`, `network_timeout`

**`OnPremiseFiscalProvider`** — cenário "sem internet" (futuro distante)
- Cliente com restrição extrema de soberania (farma TOP-3) que recusa BaaS terceiro
- Geração local de XML + assinatura ICP-Brasil + envio direto pra webservice da prefeitura
- Complexo, custo alto — só se mercado demandar

### 3. Armazenamento de XMLs assinados (defesa em profundidade)

XMLs ficam em **2 lugares** simultaneamente:

1. **Servidor do fornecedor** (PlugNotas/Focus NFe) — primary
2. **Backblaze B2 EU Central com Object Lock** (nosso storage WORM) — backup soberano

**Razão:** se fornecedor sair do ar ou cancelar contrato, ainda temos os XMLs pra:
- Recuperar emissão (resubmeter via fallback)
- Atender LGPD art. 18 (portabilidade)
- Atender auditoria CGCRE/Receita Federal (retenção 5 anos legal + 10 anos prudencial)

Implementação em `FiscalProvider.store_xml()` — adapter PlugNotas faz cópia automática após `emit_invoice` ser autorizada.

### 4. Smoke test trimestral obrigatório

GitHub Action agendada a cada 90 dias (cron `0 0 1 */3 *`):

```yaml
name: Fiscal Provider Smoke Test
on:
  schedule:
    - cron: '0 0 1 */3 *'  # 1º dia de jan/abr/jul/out
jobs:
  test-providers:
    steps:
      - name: Test PlugNotas sandbox
        run: pytest tests/fiscal/test_plugnotas_e2e.py --env=sandbox
      - name: Test Focus NFe sandbox
        run: pytest tests/fiscal/test_focus_nfe_e2e.py --env=sandbox
      - name: Compare outputs
        run: python tools/fiscal/compare_providers.py
      - name: Alert if either fails
        if: failure()
        run: # send WhatsApp + email pro Roldão
```

**Sem smoke verde, ADR-0008 desclassificado** — Parecer 4 exige.

### 5. Cláusula contratual SLA com fornecedor

Antes do 1º tenant pago, contratar PlugNotas + Focus NFe **com cláusulas obrigatórias:**
- SLA 99.5% mensal escrito
- DPA assinada (LGPD)
- Aviso prévio de 90 dias pra reajuste > IPCA
- Aviso prévio de 180 dias pra descontinuação
- Direito de retirar TODOS os XMLs em qualquer momento (formato XSD padronizado)
- Sub-processadores transparentes

### 6. Circuit breaker no `FiscalProvider`

Implementação no wrapper:
```python
class CircuitBreakerFiscalProvider:
    def __init__(self, primary: FiscalProvider, fallback: FiscalProvider):
        self.primary = primary
        self.fallback = fallback
        self.breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult:
        try:
            with self.breaker:
                return self.primary.emit_invoice(payload)
        except CircuitBreakerError:
            # Primary indisponível há > 60s — usa fallback
            logger.warning("primary fiscal provider down, using fallback")
            return self.fallback.emit_invoice(payload)
```

---

## Itens a fazer

### Bloqueantes pra F-A começar
- [ ] **`FiscalProvider` Protocol** implementado em `infrastructure/fiscal/provider.py`
- [ ] **`PlugNotasProvider`** implementado + teste E2E em sandbox
- [ ] **`FocusNFeProvider`** implementado + teste E2E em sandbox (smoke trimestral)
- [ ] **`MockFiscalProvider`** implementado pra testes
- [ ] **`store_xml()` em B2 EU Central** com Object Lock configurado
- [ ] **Lint custom semgrep** bloqueando `import plugnotas_sdk` fora de `infrastructure/fiscal/`
- [ ] **Circuit breaker** com fallback automático configurado

### Pré-MVP-1 (contratos)
- [ ] **Cláusula contratual PlugNotas** revisada por advogado SaaS regulado (R-042 pacote E-4)
- [ ] **Cláusula contratual Focus NFe** sandbox firmado (mesmo sem usar — pra ativar em emergência)
- [ ] **Cotação real** PlugNotas vs Focus NFe (custo por NFS-e + setup) registrado

### Pós-MVP-1 (LATAM)
- [ ] **`AFIPProvider`** se 1º cliente AR aparecer
- [ ] **`CFDIProvider`** se 1º cliente MX aparecer

---

## Consequências

### Positivas
- **Deadline NFS-e 01/09/2026 atendido** com fornecedor maduro (PlugNotas).
- **Plano B real testado trimestralmente** — Focus NFe não é promessa, é smoke test verde.
- **LATAM viável sem reescrita** — AFIP/CFDI plugam na mesma interface.
- **Saída garantida** — XMLs em B2 próprio, contrato com direito de retirada.
- **R-016 (cutover) + R-006 (município padrão próprio) + R-019 (concorrente) mitigados** estruturalmente.

### Negativas
- **Custo de PlugNotas + Focus NFe sandbox simultâneo** — ~R$ 200-500/mês (estimativa) só pra manter fallback. Vale.
- **Smoke test trimestral consome tempo** — 1 dia de revisão a cada 3 meses se passar; ≥3 dias se algum provider quebrar.
- **Complexidade adicional** — adapter pattern + circuit breaker exige convenção rígida pros agentes IA.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| BaaS único (PlugNotas) vs múltiplos (PlugNotas + Focus) | Múltiplos (smoke trimestral) | Deadline regulatório + bus factor — Parecer 8 |
| Adapter pattern vs SDK direto | Adapter | R-016 + R-019 + Internacionalização — Parecer 7 |
| XML só no fornecedor vs cópia em B2 próprio | Cópia em B2 | Soberania + LGPD portabilidade + auditoria CGCRE |
| Build próprio fiscal vs SaaS | SaaS BaaS | Deadline 01/09/2026 não permite construir |
| Circuit breaker manual vs library | `pybreaker` library | Padrão indústria, menos código próprio |

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| PlugNotas sobe preço 10x | Switch pra Focus NFe via flag (smoke test garantia que funciona) |
| PlugNotas sai do mercado | Mesmo — Focus NFe vira primary |
| Cliente farma TOP-3 exige on-premise fiscal | Implementar `OnPremiseFiscalProvider` (caro, mas estrutura preparada) |
| 1º cliente Argentina/México | Implementar `AFIPProvider` / `CFDIProvider` (interface já agnóstica) |
| Padrão Nacional NFS-e estabilizar 100% em 2027 | Avaliar reduzir BaaS pra emissão direta — economia mas vale o esforço? |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita PlugNotas + Focus NFe (smoke trimestral) + B2 próprio? — pendente
- [ ] **Auditor 5 (compliance):** confirma cobertura regulatória (CGSN 189/2026, NIT-DICLA-030, retenção)? — pendente
- [ ] **Auditor 4 (supply chain — 1ª auditoria):** confirma bus factor mitigado? — pendente
- [ ] **Advogado SaaS regulado:** revisou cláusulas contratuais? — pendente
