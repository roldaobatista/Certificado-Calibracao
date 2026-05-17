# Anti-corrosion layer — 9 portas/adapters

> **Origem:** Parecer 9 da 2ª auditoria de 10 agentes (17/05/2026) — "agentes IA nunca importam direto dependências jovens/bus-factor-1; sempre via porta/adapter, pra trocar implementação em 1 sprint em vez de 6 meses".
> **Status:** v1 (17/05/2026, noite final). Documento vivo — toda nova integração externa precisa virar porta antes de ser usada.
> **Dependência:** ADR-0001 v2 (stack Django + Flutter + PostgreSQL).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Porta/Adapter** | "Tomada universal" — o código do Aferê fala com uma tomada padrão, e por trás da tomada plugamos qualquer fornecedor. Se o fornecedor sair do ar ou ficar caro, trocamos a tomada sem mexer no resto. |
| **Bus factor 1** | Projeto que depende de UMA pessoa só pra continuar mantido. Se essa pessoa abandonar, o projeto morre. |
| **Lock-in** | Dependência tão profunda de um fornecedor que migrar dele custa anos. |

---

## Por que toda dependência crítica precisa de porta

Auditoria identificou 5 dependências de risco médio-alto:

1. **PlugNotas** — empresa única, todo dado fiscal passa por lá
2. **pyhanko** — mantenedor único (bus factor 1), gera PAdES-LTV crítico
3. **Hostinger VPS** — provedor de 2ª linha, sem SLA forte
4. **LiteLLM** — projeto jovem (2023), CVE recente, ritmo de breaking changes alto
5. **AWS KMS sa-east-1** — região única é SPOF criptográfico (já replicado pra us-east-1)

Sem porta/adapter, trocar qualquer um deles vira reescrita de 6-12 meses. Com porta, vira 1 sprint.

---

## As 9 portas

### 1. `FiscalProvider` (porta fiscal — NFS-e, NF-e, CFDI, AFIP)

**Por que existe:** ADR-0008. PlugNotas pode subir preço 10x ou sair do ar; LATAM (Argentina/México) precisa de outros fornecedores.

**Interface (Python):**
```python
from typing import Protocol

class FiscalProvider(Protocol):
    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult: ...
    def cancel_invoice(self, invoice_id: str, reason: str) -> CancelResult: ...
    def query_status(self, invoice_id: str) -> InvoiceStatus: ...
    def store_xml(self, invoice_id: str, xml: bytes) -> StorageRef: ...
```

**Implementações:**
- `PlugNotasProvider` — NFS-e BR (1ª implementação MVP-1)
- `FocusNFeProvider` — fallback BR homologado em sandbox (smoke test trimestral obrigatório)
- `AFIPProvider` — Argentina factura electrónica (V3+)
- `CFDIProvider` — México CFDI SAT (V3+)
- `MockFiscalProvider` — testes pytest

**Regras de uso pelos agentes IA:**
- ❌ NUNCA importar `plugnotas_sdk` ou `requests.post('https://api.plugnotas.com.br/...')` direto em código de domínio
- ✅ SEMPRE injetar `fiscal: FiscalProvider` via DI
- ✅ XMLs assinados salvos em B2 próprio (não só no PlugNotas) — saída garantida

---

### 2. `SignatureProvider` (porta assinatura PDF — PAdES-LTV)

**Por que existe:** Parecer 4 + 8. pyhanko tem bus factor 1; alternativa Lacuna PKI é paga; iText (Java sidecar) é gold-standard mas exige JVM.

**Interface:**
```python
class SignatureProvider(Protocol):
    def sign_pdf_pades_ltv(
        self,
        pdf_bytes: bytes,
        signer_cert: SignerCertificate,
        timestamp_provider: TimestampProvider,
    ) -> SignedPdfResult: ...

    def verify(self, signed_pdf: bytes) -> VerificationResult: ...
```

**Implementações:**
- `PyhankoProvider` — open source, PAdES-LTV nativo, ICP-Brasil (1ª implementação)
- `LacunaWebPkiProvider` — assinatura no cliente (browser) — usado pra A3 (ADR-0009)
- `ITextSidecarProvider` — fallback Java se pyhanko ficar abandonado (chamado via subprocess)
- `MockSignatureProvider` — testes

**Regras:**
- ❌ NUNCA usar `cryptography.hazmat.primitives.serialization` direto pra assinar PDF de produção
- ✅ Audit trail registra qual provider assinou, com qual cert, em qual timestamp ITI
- ✅ Smoke test trimestral verifica que `pyhanko + ITextSidecar + Lacuna` todos geram PAdES-LTV compatível

---

### 3. `LLMGateway` (porta LLM — Anthropic, OpenAI, Google, Maritaca)

**Por que existe:** ADR-0000 regra #1. LiteLLM é jovem (CVE recente); precisa poder trocar pra SDK Anthropic direto OU outro gateway (Portkey, OpenRouter).

**Interface:**
```python
class LLMGateway(Protocol):
    def chat(
        self,
        messages: list[Message],
        model_class: ModelClass,  # "fast" | "deep" | "br-sovereign"
        tenant_id: TenantId,
        max_tokens: int = 4096,
    ) -> ChatResult: ...

    def embed(self, text: UntrustedInput[str], tenant_id: TenantId) -> Vector: ...
```

**Implementações:**
- `LiteLLMProvider` — gateway self-hosted (1ª implementação)
- `AnthropicDirectProvider` — fallback se LiteLLM cair (R-027 mitigação)
- `MaritacaProvider` — modelo BR pra clientes farma que exigem soberania (R-028)
- `MockLLMGateway` — testes (responde determinístico por hash do prompt)

**Regras:**
- ❌ NUNCA importar `anthropic.Anthropic()` direto no código de produto
- ✅ Hard cap de tokens por tenant configurado no gateway (ADR-0000 regra #4)
- ✅ Input externo PRECISA estar tipado como `UntrustedInput[T]` antes de chegar no gateway (INV-AGENT-001)
- ✅ Audit trail registra: tenant_id, modelo usado, tokens in/out, custo

---

### 4. `StorageProvider` (porta storage WORM — PDFs, audit checkpoints)

**Por que existe:** Backblaze B2 EU Central é decisão atual, mas pode mudar pra Wasabi BR, MinIO self-hosted, ou AWS S3 sa-east-1.

**Interface:**
```python
class StorageProvider(Protocol):
    def put_worm(
        self,
        bucket: str,
        key: str,
        body: bytes,
        retention_days: int,
        tenant_id: TenantId,
    ) -> StorageRef: ...

    def get(self, ref: StorageRef) -> bytes: ...
    def list_by_tenant(self, tenant_id: TenantId, prefix: str) -> list[StorageRef]: ...
```

**Implementações:**
- `BackblazeB2Provider` — EU Central, Object Lock (1ª implementação)
- `WasabiBrProvider` — fallback BR pra cliente farma soberania (R-028)
- `MinIOSelfHostedProvider` — futuro se Hostinger oferecer Object Storage
- `MockStorageProvider` — testes

**Regras:**
- ❌ NUNCA usar `boto3.client('s3')` direto em código de produto
- ✅ Toda chave WORM contém `tenant_id` no prefix (auditoria de isolamento)
- ✅ Retention mínimo 5 anos pra audit checkpoints (LGPD + ISO 17025)

---

### 5. `HostingTarget` (porta de hospedagem — Hostinger, Hetzner, AWS)

**Por que existe:** Hostinger não tem SLA com crédito; mudar pra Hetzner/OVH em 2 anos é cenário plausível.

**Interface (mais conceitual que código — é configuração + Ansible playbook):**
```yaml
hosting:
  provider: hostinger | hetzner | ovh | digitalocean | aws-ec2
  region: br-sp | eu-west | sa-east-1
  resources:
    vcpu: int
    ram_gb: int
    nvme_gb: int
  network:
    public_ipv4: bool
    dns_provider: cloudflare | hostinger | route53
```

**Implementações (Ansible roles):**
- `roles/hosting/hostinger.yml` — KVM 4 (1ª implementação)
- `roles/hosting/hetzner.yml` — fallback testado a cada 6 meses
- `roles/hosting/aws-ec2.yml` — pra cliente enterprise que exige hyperscaler

**Regras:**
- ✅ Provider-agnostic: Docker Compose + Postgres + Redis + Traefik rodam idêntico em qualquer alvo
- ✅ Drill semestral: subir tudo do zero em Hetzner em < 4h, validar restore + funcionamento
- ❌ NUNCA usar API proprietária do provedor em código de produto

---

### 6. `AuthProvider` (porta autenticação — Lucia, Auth0, Clerk, próprio)

**Por que existe:** Auth próprio (django-allauth + django-otp) é decisão atual; mas pra cliente enterprise pode precisar SSO SAML / OIDC, ou eventual migração pra Auth0/WorkOS.

**Interface:**
```python
class AuthProvider(Protocol):
    def authenticate(self, credentials: Credentials) -> AuthResult: ...
    def issue_token(self, user_id: UserId, tenant_id: TenantId, device_id: DeviceId | None) -> Token: ...
    def revoke_token(self, token: Token) -> None: ...
    def verify_mfa(self, user_id: UserId, code: str) -> bool: ...
```

**Implementações:**
- `DjangoAllAuthProvider` — django-allauth + django-otp (1ª implementação)
- `Auth0Provider` — pra cliente enterprise que exige SSO SAML
- `MockAuthProvider` — testes

**Regras:**
- ❌ NUNCA `from django.contrib.auth import authenticate` direto em código de domínio
- ✅ Tokens mobile binded a `device_id` (Auditor 6 critical)
- ✅ MFA TOTP obrigatório pra perfis A e B (admin do tenant)

---

### 7. `QueueProvider` (porta de fila — Celery+Redis, pg-boss, Temporal)

**Por que existe:** Parecer 9. Celery+Redis é decisão atual; pg-boss seria alternativa (1 container a menos); Temporal/Inngest viram opção quando produto crescer.

**Interface:**
```python
class QueueProvider(Protocol):
    def enqueue(
        self,
        task_name: str,
        payload: dict,
        tenant_id: TenantId,
        run_at: datetime | None = None,
        priority: int = 0,
    ) -> JobId: ...

    def run_in_tenant_context(
        self,
        tenant_id: TenantId,
        fn: Callable,
    ) -> Any: ...  # wrapper obrigatório pra tasks com RLS
```

**Implementações:**
- `CeleryRedisProvider` — Celery + Redis (1ª implementação)
- `PgBossProvider` — fallback sem Redis se VPS apertar
- `MockQueueProvider` — testes

**Regras:**
- ❌ NUNCA `@celery.task` ou `@shared_task` direto em código de domínio sem `run_in_tenant_context`
- ✅ `tenant_id` propagado em TODO job — sem isso o job FALHA, não vaza (INV-TENANT-004)
- ✅ Hard timeout por categoria de task (PDF, NFS-e, email, sync mobile)

---

### 8. `SyncProvider` (porta sync mobile — drift, custom REST, WatermelonDB)

**Por que existe:** ADR-0005 (sync strategy) ainda não escrita; drift é decisão atual mas pode mudar pra Realm ou PowerSync.

**Interface (Dart, no app Flutter):**
```dart
abstract class SyncProvider {
  Future<SyncResult> push(LocalChanges changes, TenantId tenant);
  Future<RemoteChanges> pull(LastSyncCursor cursor, TenantId tenant);
  Future<ConflictResolution> resolveConflict(LocalChange l, RemoteChange r);
  Stream<SyncEvent> watchEvents();
}
```

**Implementações:**
- `DriftRestSyncProvider` — drift SQLite local + REST API DRF (1ª implementação)
- `PowerSyncProvider` — fallback se offline robusto provar inviável (ADR-0001 critério de reversão)
- `MockSyncProvider` — testes Flutter

**Regras:**
- ❌ NUNCA escrever conflict resolution ad-hoc no widget — sempre via `SyncProvider.resolveConflict`
- ✅ Regra por entidade: OS = last-write-wins + fila humana; foto = append-only; estoque = transação atômica (definir em ADR-0005)
- ✅ Compressão obrigatória de fotos (max 1200px, JPEG 0.8) antes de upload

---

### 9. `MultiTenantDiscriminator` (porta de tenancy — schema-shared, schema-per-tenant, DB-per-tenant)

**Por que existe:** ADR-0002 escolhe schema-shared + RLS pra 100-5000 tenants; mas a partir de 5k tenants OU cliente farma grande pode precisar schema-per-tenant ou DB-per-tenant.

**Interface (Python):**
```python
class MultiTenantDiscriminator(Protocol):
    def resolve_connection(self, tenant_id: TenantId) -> Connection: ...
    def apply_tenant_filter(self, query: Query, tenant_id: TenantId) -> Query: ...
    def isolate_storage(self, tenant_id: TenantId, key: str) -> str: ...
    def migrate_tenant(self, tenant_id: TenantId, from_strategy: Strategy, to_strategy: Strategy) -> None: ...
```

**Implementações:**
- `SharedSchemaRlsDiscriminator` — schema único + RLS por `tenant_id` (1ª implementação)
- `PerTenantSchemaDiscriminator` — schema por tenant (pra cliente farma grande no futuro)
- `PerTenantDatabaseDiscriminator` — DB inteiro por tenant (cenário enterprise)
- `MockDiscriminator` — testes

**Regras:**
- ❌ NUNCA query Django ORM sem middleware tenant_id ativo (INV-TENANT-001 + INV-TENANT-004)
- ✅ Migração entre strategies via `migrate_tenant()` — sem reescrever queries do domínio
- ✅ Cada Strategy implementa o mesmo contrato — domain code é agnóstico

---

## Estrutura no código

```
src/
├── domain/                    # Regras de negócio puras (sem dependência externa)
│   ├── certificado/
│   ├── instrumento/
│   └── tenant/
│
├── infrastructure/            # Implementações concretas das portas
│   ├── fiscal/
│   │   ├── provider.py        # FiscalProvider Protocol
│   │   ├── plugnotas.py       # PlugNotasProvider
│   │   ├── focus_nfe.py       # FocusNFeProvider
│   │   └── mock.py
│   ├── signature/
│   ├── llm/
│   ├── storage/
│   ├── auth/
│   ├── queue/
│   └── multitenant/
│
└── application/               # Casos de uso — recebem portas via DI
    ├── emitir_certificado.py
    └── enviar_nfse.py
```

---

## Regras gerais pros agentes IA

1. **Toda nova integração externa começa por porta.** Antes de codar com SDK X, escrever `XProvider Protocol` + `MockXProvider` + 1 teste.

2. **Imports proibidos em `domain/` e `application/`:**
   ```python
   # ❌ NUNCA
   from anthropic import Anthropic
   from plugnotas_sdk import PlugNotas
   from pyhanko import sign
   from boto3 import client
   from celery import shared_task

   # ✅ SEMPRE
   from infrastructure.fiscal.provider import FiscalProvider
   from infrastructure.signature.provider import SignatureProvider
   from infrastructure.llm.provider import LLMGateway
   ```

3. **Lint custom (`ruff` rule customizada) bloqueia merge** se import direto de SDK acontecer fora de `infrastructure/`.

4. **Smoke test trimestral obrigatório:**
   - Fiscal: `PlugNotasProvider` + `FocusNFeProvider` ambos passam no teste E2E sandbox
   - Signature: `PyhankoProvider` + `ITextSidecarProvider` ambos geram PAdES-LTV compatível
   - LLM: `LiteLLMProvider` + `AnthropicDirectProvider` ambos respondem ao mesmo prompt-baseline

5. **Custo de troca declarado por porta:** cada porta documenta no docstring "se trocar provider, tempo estimado de migração". Roldão pode planejar evolução.

---

## Riscos mitigados por esta camada

| Risco | Sem ACL | Com ACL |
|---|---|---|
| PlugNotas sobe 10× preço | Reescrita 6-10 semanas | Spike de 1 sprint pra plugar Focus |
| pyhanko vira abandonware + CVE | Reescrita 8-12 semanas | Swap pra iText sidecar em 2 semanas |
| Hostinger sai do ar | 8-24h (manual) | 4h (Ansible playbook Hetzner) |
| LiteLLM tem CVE crítico | Indisponibilidade dias | Switch pra SDK direto em horas |
| AWS KMS sa-east-1 cai | Sistema para | Replica us-east-1 + drill trimestral |
| Tenant farma exige soberania BR | Migração custosa | Wasabi BR + Maritaca já configurados |
| TAM > 5k tenants força sharding | Reescrita inteira | Migrar `Discriminator` strategy sem mudar domain |

---

## Itens a fazer

- [ ] Implementar 9 portas como Protocols Python em `infrastructure/`
- [ ] Implementar `Mock*Provider` pra todas as 9 antes do spike F-1
- [ ] Lint custom semgrep bloqueando imports diretos
- [ ] Smoke test trimestral configurado em GitHub Actions
- [ ] Documentar custo de troca por porta no docstring

---

## Revisão

Revisão obrigatória se:
- Nova integração externa for adicionada (vira porta nova)
- Algum critério de reversão da ADR-0001 disparar (porta correspondente muda)
- Lib base virar abandonware (porta correspondente ganha fallback)

Caso contrário, revisão anual junto com `painel-do-dono.md`.
