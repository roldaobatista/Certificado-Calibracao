# Anti-corrosion layer — 18 portas/adapters

> **Origem:** Parecer 9 da 2ª auditoria de 10 agentes (17/05/2026) — "agentes IA nunca importam direto dependências jovens/bus-factor-1; sempre via porta/adapter, pra trocar implementação em 1 sprint em vez de 6 meses".
> **Status:** v3 (17/05/2026, madrugada — auditoria 10 agentes pós-48-módulos aplicada: +AuthorizationProvider, +BpmEngineProvider, +RuleEngineProvider, +AnalyticsBackend, +DocumentSearchProvider, +MarketplaceExtensionProvider, +EmailTemplateProvider). Documento vivo — toda nova integração externa precisa virar porta antes de ser usada.
> **Dependência:** ADR-0001 v2 (stack Django + Flutter + PostgreSQL), ADR-0010 (estratégia tela), ADR-0011 (BI 3 fases), ADR-0012 (autorização unificada).

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

## As 18 portas

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
- `ProcrastinateProvider` — fallback sem Redis (Postgres-based, Python puro — substitui o equivocado pg-boss que é Node/JavaScript, identificado por Auditor 7 da 3ª auditoria de 10 agentes em 17/05/2026)
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

### 10. `OmniChannelProvider` (porta omnichannel — WhatsApp, Email, SMS, Web Chat)

**Por que existe:** Auditoria 12 agentes achado C6 (17/05/2026). Módulo `comunicacao-omnichannel` integra com WhatsApp BSP (Meta/Twilio), SMTP, SMS gateway. Sem porta, trocar de BSP (Twilio → 360dialog, ou perder Cloud API oficial Meta) vira reescrita do módulo inteiro. Custo $/mensagem por canal muda com volume — precisa poder rotear.

**Interface (Python):**
```python
class OmniChannelProvider(Protocol):
    def enviar_mensagem(
        self,
        canal: ChannelType,              # whatsapp_business | email_smtp | sms | web_chat
        destinatario: ContactAddress,    # phone E.164 | email | handle
        template: TemplateId,            # template aprovado quando canal exige (WhatsApp)
        variaveis: dict[str, str],
        tenant_id: TenantId,
        idempotency_key: str,
    ) -> SendResult: ...

    def receber_webhook(
        self,
        canal: ChannelType,
        payload: UntrustedInput[dict],   # assinado/HMAC validado antes
        tenant_id: TenantId,
    ) -> InboundMessage: ...

    def consultar_status(self, message_id: ExternalMessageId, canal: ChannelType) -> MessageStatus: ...

    def validar_template(self, canal: ChannelType, template: TemplateDraft) -> TemplateValidation: ...
```

**Canais suportados:**
- `whatsapp_business` — exige template aprovado pela Meta pra mensagens fora da janela 24h
- `email_smtp` — SMTP genérico (SES, SendGrid, Postmark, SMTP próprio)
- `sms` — gateway SMS (Twilio, AWS SNS, Zenvia BR)
- `web_chat` — chat embedded no portal do tenant (websocket interno, mas mesma interface)

**Implementações:**
- `WhatsAppCloudApiProvider` — Meta Cloud API direto (1ª implementação MVP, custo Meta direto, sem BSP markup)
- `TwilioWhatsAppProvider` — fallback BSP (Twilio) se Meta limitar acesso direto
- `SmtpGenericProvider` — SMTP padrão (AWS SES 1ª escolha BR)
- `TwilioSmsProvider` / `AwsSnsSmsProvider` — SMS (escolha por país; AWS SNS mais barato BR)
- `WebChatInternalProvider` — chat interno, websocket Django Channels
- `MockOmniChannelProvider` — testes (responde determinístico por hash)

**Eventos emitidos (consumidos por `Comunicacao.*`):**
- `Mensagem.Enviada` — mensagem aceita pelo provider
- `Mensagem.Entregue` — provider confirmou entrega (delivery receipt)
- `Mensagem.Lida` — leitura confirmada (WhatsApp blue ticks, email pixel se habilitado)
- `Mensagem.Recebida` — inbound (webhook do canal)
- `Mensagem.Falhou` — erro de entrega (número inválido, opt-out provider-side, bounce, etc.)

**Compliance / DPA (LGPD):**
- ❗ Cada implementação exige **DPA assinado** com provider antes de ir pra produção (Meta/WhatsApp, Twilio, AWS SES, etc.). Sem DPA → vazamento de dado pessoal sem base legal de transferência. Lista versionada em `docs/conformidade/comum/subprocessadores.md` (a criar).
- Opt-out global por canal respeitado: provider NÃO recebe número/email se cliente tem opt-out registrado no Aferê (validação ANTES do call).
- Webhook inbound: HMAC validado **antes** de qualquer parsing; payload entra tipado como `UntrustedInput[dict]`.

**Custo monitorado:**
- Painel Grafana mostra **$/mensagem por canal por tenant** (WhatsApp template ~R$ 0,08, SMS ~R$ 0,05, email ~R$ 0,0001).
- Alerta se custo de tenant subir > 50% mês a mês (sinal de abuse / loop).
- Hard cap configurável por tenant (proteção budget).

**Regras de uso pelos agentes IA:**
- ❌ NUNCA importar `twilio.rest.Client`, `requests.post('https://graph.facebook.com/...')`, `boto3.client('sns')`, `smtplib.SMTP` direto em código de domínio
- ✅ SEMPRE injetar `channel: OmniChannelProvider` via DI
- ✅ Templates WhatsApp validados via `validar_template()` antes de submeter à Meta (rejeição comum por copy promocional)
- ✅ `idempotency_key` obrigatório (regra automação pode reentregar evento → mensagem dup é grave)

---

### 11. `PaymentGatewayProvider` (porta pagamento — Stripe, PagSeguro, Mercado Pago)

**Por que existe:** Auditoria 12 agentes achado C6 (17/05/2026). Módulo `billing-saas` cobra assinaturas via gateway externo. Sem porta, trocar gateway (Stripe sair do BR, PagSeguro mudar fee, exigir Mercado Pago pra clientes que só pagam por lá) vira reescrita do billing. PCI-DSS exige que dados de cartão **nunca passem pelo backend Aferê** — porta força tokenização correta.

**Interface (Python):**
```python
class PaymentGatewayProvider(Protocol):
    def criar_cobranca(
        self,
        valor: Money,
        metodo: PaymentMethod,            # cartao_token | boleto | pix
        cliente: CustomerRef,
        tenant_id: TenantId,
        idempotency_key: str,
        descricao: str,
    ) -> ChargeResult: ...

    def tokenizar_cartao(
        self,
        dados_cartao_client_side: TokenizationRequest,  # client-side SDK retornou token; backend só repassa
        tenant_id: TenantId,
    ) -> CardToken: ...

    def receber_webhook(
        self,
        payload: UntrustedInput[dict],    # assinatura HMAC validada antes
        tenant_id: TenantId,
    ) -> WebhookEvent: ...

    def consultar_status(self, payment_id: ExternalPaymentId) -> PaymentStatus: ...

    def reembolsar(
        self,
        payment_id: ExternalPaymentId,
        valor: Money | None,              # None = reembolso total
        motivo: str,
    ) -> RefundResult: ...
```

**Implementações:**
- `StripeProvider` — Stripe (1ª implementação MVP-1; cartão internacional + boleto BR via Stripe BR)
- `PagSeguroProvider` / `PagBankProvider` — 2ª onda (BR, taxas competitivas pra débito BR, integração PIX nativa)
- `MercadoPagoProvider` — 3ª onda (alta penetração BR, exigência de clientes que só pagam via MP)
- `MockPaymentGatewayProvider` — testes (simula sucesso/falha/3DS deterministicamente)

**Compliance PCI-DSS:**
- ❗ **Dados completos de cartão (PAN, CVV) NUNCA passam pelo backend Aferê.** Tokenização é **client-side** via SDK do gateway (Stripe Elements, PagSeguro Checkout Transparente client JS) — backend recebe apenas o token opaco.
- ❗ `MetodoPagamento` no banco guarda APENAS: `gateway`, `gateway_token`, `ultimos_4`, `bandeira`, `vencimento_mes/ano`. Nunca PAN, nunca CVV. Reforça `SEC-NNN` do `billing-saas/modelo-de-dominio.md`.
- ❗ Reduz escopo PCI-DSS pra **SAQ-A** (e-commerce com terceirização total) em vez de SAQ-D (mais exigente).

**Eventos emitidos (consumidos por `BillingSaas.*`):**
- `Pagamento.Confirmado` — webhook confirmou pagamento
- `Pagamento.Falhou` — recusa do emissor / saldo insuficiente / fraude detectada
- `Pagamento.Reembolsado` — estorno total ou parcial processado
- `Cartao.Tokenizado` — novo método de pagamento adicionado pelo tenant (auditoria)

**Custo monitorado:**
- MDR por método (cartão ~3,5%, boleto ~R$ 3,50, PIX ~0,4%) painel Grafana.
- Alerta de **chargeback rate > 0,5%** (gatilho regulatório das bandeiras).

**Regras de uso pelos agentes IA:**
- ❌ NUNCA importar `stripe.Charge.create()` ou `pagseguro_sdk` direto em código de domínio
- ❌ NUNCA construir form de cartão no Django template — sempre client-side SDK do gateway
- ✅ SEMPRE injetar `payment: PaymentGatewayProvider` via DI
- ✅ Webhook HMAC validado **antes** do parsing; `tenant_id` resolvido pelo `external_customer_id` mapeado em tabela própria
- ✅ `idempotency_key` obrigatório (gateway pode retentar; cobrança duplicada é grave)
- ✅ Audit trail registra: tenant, gateway usado, valor, método, status, tentativa N

---

### 12. `AuthorizationProvider` (porta autorização — ADR-0012)

**Por que existe:** ADR-0012. Com 16 perfis × 48 módulos × escopo dinâmico + cross-tenant + time-boxed, decidir "pode/não pode" espalhado em views/serializers/querysets vira bug regulatório garantido. Implementação atual em Django + RLS PostgreSQL, mas precisa fronteira limpa pra trocar pra Casbin/OPA/Oso depois (Wave C+) sem reescrever domínio.

**Interface (Python):**
```python
class AuthorizationProvider(Protocol):
    def can(
        self,
        user_id: UUID,
        action: str,              # "certificado.emitir", "fatura.estornar"
        resource: dict,           # {"tipo_instrumento": "balanca", "valor": 5000}
        tenant_id: UUID,
        purpose: str,             # finalidade LGPD
        at_time: datetime,
    ) -> Decision: ...

    def attributes_for(self, user_id: UUID, tenant_id: UUID) -> dict: ...
    def register_dynamic_attribute(self, name: str, resolver: Callable) -> None: ...
```

**Implementações:**
- `DjangoRlsAuthorizationProvider` — Django built-in + RLS PostgreSQL + cache Redis (1ª implementação MVP-1)
- `CasbinAuthorizationProvider` — fallback se matriz superar 50k células (Wave C+)
- `OPAAuthorizationProvider` — fallback se microsserviços virarem realidade
- `MockAuthorizationProvider` — testes

**Regras:**
- ❌ NUNCA decidir autorização fora desta porta (`if user.groups.filter(...)` proibido em views/serializers)
- ✅ Audit trail síncrono obrigatório (INV-AUTHZ-002) — `audit_trail.authz_decisions` recebe linha antes do retorno
- ✅ Cache Redis com invalidação por evento (`acreditacao.vencida`, `treinamento.expirado`, `licenca.suspensa`)
- ✅ ABAC plug-in via `@authz_attribute("acreditacao_vigente")` — cada módulo registra atributo dele

---

### 13. `BpmEngineProvider` (porta workflow engine — Camunda, Temporal, django-fsm, custom)

**Por que existe:** Auditor 10 da auditoria pós-48-módulos. Módulo `suporte-plataforma/automacoes-bpm` executa workflow visual com etapas, branches, paralelo, eventos, sub-processos, esperar humano. ADR-0005 cravou engine caseiro sobre procrastinate + DSL YAML pra MVP-1, mas Wave B+ pode demandar trocar pra Temporal ou Camunda. Sem porta, troca = reescrita.

**Interface:**
```python
class BpmEngineProvider(Protocol):
    def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict,
        tenant_id: TenantId,
    ) -> WorkflowExecution: ...

    def evaluate_condition(self, condition: dict, context: dict) -> bool: ...
    def schedule_timer(self, workflow_run_id: UUID, at_time: datetime) -> None: ...
    def wait_for_event(self, workflow_run_id: UUID, event_type: str, timeout: timedelta) -> Any: ...
    def cancel_workflow(self, workflow_run_id: UUID, reason: str) -> None: ...
```

**Implementações:**
- `ProcrastinateBpmEngine` — engine caseiro sobre procrastinate + Django state machine + outbox (1ª implementação Wave B MVP — ver ADR-0005 revisada)
- `TemporalProvider` — fallback se workflows >10 etapas com esperas >24h virarem comuns (Wave C+)
- `CamundaProvider` — fallback se cliente farma exigir engine certificada
- `MockBpmEngine` — testes

**Regras:**
- ❌ NUNCA orquestrar workflow longo com Celery puro (`time.sleep` + retries) em código de domínio
- ✅ Estado persistente sempre fora do job (Django model + state machine)
- ✅ Idempotency key obrigatório por step
- ✅ Audit trail por transição (INV-027 OS, INV-040 onboarding, INV-045 despesa, etc)

---

### 14. `RuleEngineProvider` (porta motor de regras — comissões, precificação, garantia, alçadas)

**Por que existe:** Auditor 10. Comissões hoje têm 1 fórmula no MVP-1, mas Wave B/V2 listam 7 fórmulas adicionais + escalonadas por meta. Precificação tem régua. Garantia tem cobertura por regra. Alçadas de aprovação em BPM. Sem porta, lógica vira if-else espalhado em `domain/comissoes/`, `domain/precificacao/`, `domain/garantia/`.

**Interface:**
```python
class RuleEngineProvider(Protocol):
    def evaluate(
        self,
        rule_id: str,                # "comissao.vendedor_meta_mensal_v2"
        context: dict,               # {"valor_venda": 5000, "meta_mes": 100000, ...}
        tenant_id: TenantId,
    ) -> RuleResult: ...

    def register_rule(self, rule_id: str, definition: RuleDefinition) -> None: ...
    def list_rules(self, tenant_id: TenantId, scope: str) -> list[RuleSummary]: ...
    def explain(self, rule_id: str, context: dict, result: RuleResult) -> str: ...
```

**Implementações:**
- `AstSimpleRuleEngine` — AST Python eval com allowlist de operadores + sandbox (1ª implementação MVP)
- `DroolsRuleEngine` / `EasyRulesEngine` — fallback se Wave B exigir motor formal
- `MockRuleEngine` — testes

**Regras:**
- ❌ NUNCA usar `eval(rule_str)` direto — sempre via porta com allowlist
- ✅ Toda regra versionada (auditoria fiscal exige reproduzir cálculo histórico — INV-026)
- ✅ `explain()` obrigatório (comissão calculada precisa ser justificada pro vendedor)
- ✅ Decisão cacheada por contexto+versão da regra (Redis, TTL 5min)

---

### 15. `AnalyticsBackend` (porta camada analítica/BI — ADR-0011)

**Por que existe:** ADR-0011. Sistema começa com PostgreSQL único + vistas materializadas (Fase 0), depois read-replica PG (Fase 1), depois DuckDB embedded ou ClickHouse (Fase 2). Cada fase muda **onde** as queries de BI rodam — sem porta, código de aplicação saberia "qual fase está ativa".

**Interface:**
```python
class AnalyticsBackend(Protocol):
    def query_aggregate(
        self,
        dataset: str,                # "dre_mensal", "fluxo_caixa", "os_abertas_kpi"
        filters: dict,
        tenant_id: TenantId,
        time_range: TimeRange,
    ) -> DataFrame: ...

    def materialize(self, view_id: str) -> RefreshResult: ...
    def stream_changes(self, dataset: str, since: datetime) -> Iterator[Change]: ...
    def export(self, dataset: str, filters: dict, format: str, tenant_id: TenantId) -> StorageRef: ...
```

**Implementações:**
- `PgMaterializedViewBackend` — Fase 0 (PG único + REFRESH MATERIALIZED VIEW CONCURRENTLY)
- `PgReadReplicaBackend` — Fase 1 (mesma interface, conexão direcionada à réplica)
- `DuckDbAnalyticsBackend` — Fase 2a (DuckDB embarcado em ETL noturno)
- `ClickHouseAnalyticsBackend` — Fase 2b (ClickHouse self-hosted ou cloud)
- `MockAnalyticsBackend` — testes

**Regras:**
- ❌ NUNCA query OLTP direto pra dashboard (ex: `Certificado.objects.aggregate(...)` em view de painel) — sempre via `AnalyticsBackend`
- ✅ Painel do dono cross-tenant usa role separada + vistas dedicadas (ADR-0011) — não BYPASSRLS
- ✅ Audit trail BI em `audit_trail.bi_events` (21 CFR Part 11)
- ✅ Link público respeita "n ≥ 3 agregação mínima" (LGPD)

---

### 16. `DocumentSearchProvider` (porta busca + OCR documental)

**Por que existe:** Auditor 10. Módulo `suporte-plataforma/gestao-documental` exige busca full-text em PDFs escaneados + OCR assíncrono + versionamento. Hoje viável com PostgreSQL FTS + Tesseract. Se cliente farma TOP exigir busca semântica vetorial (em V3), troca pra Elasticsearch ou Typesense sem reescrever módulo.

**Interface:**
```python
class DocumentSearchProvider(Protocol):
    def index_document(
        self,
        document_id: UUID,
        content: bytes,
        metadata: dict,
        tenant_id: TenantId,
    ) -> IndexResult: ...

    def search(
        self,
        query: str,
        filters: dict,
        tenant_id: TenantId,
        limit: int = 50,
    ) -> list[SearchHit]: ...

    def ocr_async(self, document_id: UUID, tenant_id: TenantId) -> JobId: ...
    def reindex(self, tenant_id: TenantId, since: datetime | None) -> RefreshResult: ...
```

**Implementações:**
- `PgFtsTesseractProvider` — Postgres FTS (GIN index + websearch_to_tsquery) + Tesseract em Celery worker dedicado (1ª implementação MVP)
- `ElasticsearchProvider` — Wave B+ se Wave A saturar (>100k docs/tenant ou busca >2s p95)
- `TypesenseProvider` — alternativa leve a Elasticsearch
- `ClaudeVisionOcrProvider` — implementação OCR premium (custo por tenant) pra docs onde Tesseract falha
- `MockDocumentSearchProvider` — testes

**Regras:**
- ❌ NUNCA `cursor.execute("SELECT ... WHERE conteudo @@ ...")` direto fora desta porta
- ✅ OCR sempre assíncrono (SLA 5min na ingestão — US-DOC-008)
- ✅ Texto extraído tipado como `UntrustedInput[str]` (LLM safety — INV-AGENT-001)
- ✅ Audit trail registra: quem buscou o quê, quem viu qual documento

---

### 17. `MarketplaceExtensionProvider` (porta SDK de extensões marketplace — V2/V3)

**Por que existe:** Auditor 10. Módulo `comercial/marketplace` (V2/V3) introduz padrão "plugin/extension" — parceiros instalam extensões em N tenants. Sem porta + governança, vira pesadelo (cada extensão acessa de jeito diferente, ANTI-11 customização infinita). Decisão é diferida pra V2, mas a porta entra desde já pra evitar refactor brutal.

**Interface (rascunho — vai virar ADR-0005-B quando V2 começar):**
```python
class MarketplaceExtensionProvider(Protocol):
    def install_extension(
        self,
        extension_id: str,
        tenant_id: TenantId,
        config: dict,
    ) -> InstallResult: ...

    def invoke_hook(
        self,
        extension_id: str,
        hook_name: str,         # "before_emit_certificate", "after_create_os"
        payload: UntrustedInput[dict],
        tenant_id: TenantId,
    ) -> HookResult: ...

    def list_installed(self, tenant_id: TenantId) -> list[InstalledExtension]: ...
    def uninstall(self, extension_id: str, tenant_id: TenantId) -> None: ...
```

**Implementações:**
- `NoopMarketplaceProvider` — Wave A/MVP-1 (marketplace ainda não existe; porta retorna vazio)
- `SandboxedPythonExtensionProvider` — V2 (extensões em Python rodando em sandbox isolado, allowlist de APIs)
- `WebhookExtensionProvider` — V2 (extensões rodam fora do Aferê, comunicação via webhook assinado)
- `MockMarketplaceExtensionProvider` — testes

**Regras:**
- ❌ Extensão NUNCA acessa Django ORM direto — sempre via API Aferê
- ❌ Extensão NUNCA executa código não-sandboxado dentro do processo Aferê
- ✅ Hook recebe `UntrustedInput[dict]` — payload tipado como não-confiável
- ✅ Audit trail registra: extensão X executou hook Y no tenant Z (LGPD subprocessador)
- ✅ DPA por extensão obrigatório (LGPD — extensão recebe dados pessoais)

---

### 18. `EmailTemplateProvider` (porta templates de email com versionamento)

**Por que existe:** Auditor 10. Email transacional é enviado via porta `OmniChannelProvider` (#10), mas **renderização do template** vive separada — Wave A já tem 20+ templates (boas-vindas, recuperação senha, confirmação OS, recalibração 30d, fatura emitida, comissão calculada, etc). Wave B (omnichannel) e Wave B (CRM) adicionam dezenas mais. Sem porta de template + versionamento, agente IA replica HTML.

**Interface:**
```python
class EmailTemplateProvider(Protocol):
    def render(
        self,
        template_id: str,           # "welcome_tenant_admin_v3"
        variables: dict,
        tenant_id: TenantId,
        locale: str = "pt-BR",
    ) -> RenderedEmail: ...           # subject + html + text fallback

    def list_templates(self, tenant_id: TenantId) -> list[TemplateSummary]: ...
    def preview(self, template_id: str, variables: dict) -> RenderedEmail: ...
    def validate(self, template: TemplateDraft) -> ValidationResult: ...
```

**Implementações:**
- `JinjaTemplateProvider` — Jinja2 + storage em Django model `EmailTemplate` (1ª implementação MVP)
- `MJMLTemplateProvider` — MJML pra responsividade avançada (Wave B/V2 se UX exigir)
- `MockEmailTemplateProvider` — testes

**Regras:**
- ❌ NUNCA inline HTML em código Python (`f"<h1>Olá {nome}</h1>"`)
- ✅ Toda variável escapada por default (XSS — defesa)
- ✅ Versionamento semver no template_id (`welcome_tenant_admin_v3`)
- ✅ Preview obrigatório antes de tenant ativar template customizado

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
│   ├── multitenant/
│   ├── omnichannel/           # OmniChannelProvider (WhatsApp/Email/SMS/Chat)
│   ├── payment/               # PaymentGatewayProvider (Stripe/PagSeguro/MP)
│   ├── authz/                 # AuthorizationProvider (ADR-0012)
│   ├── bpm/                   # BpmEngineProvider (workflow engine)
│   ├── rules/                 # RuleEngineProvider (comissões/precificação/garantia)
│   ├── analytics/             # AnalyticsBackend (ADR-0011, BI 3 fases)
│   ├── docsearch/             # DocumentSearchProvider (FTS + OCR)
│   ├── marketplace/           # MarketplaceExtensionProvider (V2/V3)
│   └── email_template/        # EmailTemplateProvider (Jinja2 + versionamento)
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
   from twilio.rest import Client
   import stripe
   import smtplib
   from django.contrib.auth.decorators import permission_required  # decisão de authz fora da porta
   from jinja2 import Template  # template de email fora da porta

   # ✅ SEMPRE
   from infrastructure.fiscal.provider import FiscalProvider
   from infrastructure.signature.provider import SignatureProvider
   from infrastructure.llm.provider import LLMGateway
   from infrastructure.omnichannel.provider import OmniChannelProvider
   from infrastructure.payment.provider import PaymentGatewayProvider
   from infrastructure.authz.provider import AuthorizationProvider
   from infrastructure.bpm.provider import BpmEngineProvider
   from infrastructure.rules.provider import RuleEngineProvider
   from infrastructure.analytics.provider import AnalyticsBackend
   from infrastructure.docsearch.provider import DocumentSearchProvider
   from infrastructure.marketplace.provider import MarketplaceExtensionProvider
   from infrastructure.email_template.provider import EmailTemplateProvider
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
| WhatsApp BSP sobe fee 5×, Meta corta Cloud API direto | Reescrita módulo comunicação | Swap implementação `OmniChannelProvider` em 1 sprint |
| Stripe deixar BR / PagSeguro mudar regras | Reescrita billing | Plugar `PagBankProvider`/`MercadoPagoProvider` em 1 sprint |
| Matriz RBAC superar 50k células ou cliente farma exigir SSO | Reescrita autorização espalhada | Swap `DjangoRlsAuthorizationProvider` → `CasbinAuthorizationProvider`/`OPAAuthorizationProvider` em 2 sprints |
| Engine de automações precisar workflows >10 etapas com esperas dias | Reescrita BPM | Swap `ProcrastinateBpmEngine` → `TemporalProvider`/`CamundaProvider` em 3 sprints |
| BI saturar PG único (Fase 0) | Migração complexa | Trocar `PgMaterializedViewBackend` → `PgReadReplicaBackend` → `DuckDb`/`ClickHouse` em ordem |
| Busca FTS PG saturar (>100k docs/tenant) | Reescrita busca | Plugar `ElasticsearchProvider` em 1 sprint |

---

## Itens a fazer

- [ ] Implementar 18 portas como Protocols Python em `infrastructure/`
- [ ] Implementar `Mock*Provider` pra todas as 18 antes da Foundation F-A começar
- [ ] Lint custom semgrep bloqueando imports diretos (incluindo `permission_required` decorator e `jinja2.Template` fora da porta)
- [ ] Smoke test trimestral configurado em GitHub Actions
- [ ] Documentar custo de troca por porta no docstring

---

## Revisão

Revisão obrigatória se:
- Nova integração externa for adicionada (vira porta nova)
- Algum critério de reversão da ADR-0001 disparar (porta correspondente muda)
- Lib base virar abandonware (porta correspondente ganha fallback)

Caso contrário, revisão anual junto com `painel-do-dono.md`.
