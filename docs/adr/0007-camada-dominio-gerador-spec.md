# ADR-0007 — Camada de domínio + gerador spec→código

> **Status:** **aceito** (17/05/2026 — aprovada pelo Roldão como parte da autorização pra arrancar Foundation F-A). Estado anterior: proposta (noite do mesmo dia). Bloqueante do Portão 2 da ADR-0001 candidata, agora destravado.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Nota de implementação:** o **pipeline spec→código completo** (parser markdown→YAML + templates Jinja2 + `make spec-sync`) é entregável de **Wave A**, não de F-A. F-A entrega apenas a **estrutura de pastas** (`domain/`, `infrastructure/`, `application/`) e o **boilerplate mínimo** (EventBus Protocol, value objects, DomainEvent base) — ver `docs/faseamento-foundation-waves.md` §2 entregável 7 (convenções django). Codegen completo entra quando a 1ª spec real (Wave A — `calibracao`) precisar dele.
> **Origem:** Parecer 6 da 2ª auditoria de 10 agentes — *"Django ORM + DRF serializer + Pydantic + Dart = 4 representações do mesmo conceito que divergem em 2 sprints sem gerador. Spec-as-source (D2) precisa de pipeline real, não de promessa."*
> **Depende de:** ADR-0001 v2 (stack Django + Flutter), decisão fundadora D2 (spec-as-source)
> **Relacionado:** `docs/arquitetura/anti-corrosion-layer.md`, `REGRAS-INEGOCIAVEIS.md` (INV-NNN como invariantes)

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Spec PT** | Documento em português com IDs (INV-NNN, BIG-NN, JTBD-NN) que descreve uma regra de negócio. Decisão fundadora D2 diz "spec PT é a verdade; código segue a spec". |
| **Spec-as-source** | Princípio: quando spec muda, código é regenerado. Não o contrário. |
| **ORM** | "Tradutor" entre código Python e tabelas do banco (Django ORM). |
| **Serializer** | "Tradutor" entre objeto Python e JSON da API. |
| **Pydantic** | "Validador" que confere se um dado obedece um formato antes de processar. |
| **Gerador / codegen** | Programa que escreve outro programa. Aqui: lê markdown da spec → produz código Django + Dart automaticamente. |
| **Agregado (DDD)** | "Caixa" de regras de negócio que pertencem juntas (ex: agregado "Certificado" tem regras de emissão, cancelamento, assinatura). |
| **Anemic model** | Anti-padrão: classes que são só "saco de dados", sem regras. Toda lógica vira `if` espalhado em controllers. |

---

## Contexto

Decisão fundadora **D2 (spec-as-source)** diz: spec PT é a verdade; código segue a spec. Sem ferramenta concreta, o que acontece na prática:

- Agente IA escreve as 4 representações do conceito MANUALMENTE:
  1. Django ORM Model (`models.py`)
  2. DRF Serializer (`serializers.py`)
  3. Pydantic boundary (`schemas.py`)
  4. Dart class no Flutter (`models/foo.dart`)

- Em 2 sprints, divergem. Campo `valor: Decimal` no model vira `valor: float` no serializer, vira `valor: str` no Pydantic, vira `valor: double` no Dart. Bug silencioso entra em produção.

- Invariantes (INV-001, INV-007, INV-015, etc.) viram `if` espalhado em `save()` ao invés de método de agregado testável. Validação em 4 lugares (sem 1 fonte).

- **Django seduz o agente a colocar regra de negócio no `Serializer.validate()` ou no `Model.save()`** — anti-padrão clássico que o Parecer 6 alertou.

Spec-as-source sem pipeline real vira **documentação morta**.

---

## Decisão

Adotar **pipeline de geração spec→código** + **camada de domínio separada do Django ORM** + **invariantes em 3 camadas obrigatórias** + **message bus explícito (não Django signals)**.

### 1. Pipeline spec → código

```
┌──────────────────┐
│  Spec PT         │   IDs estáveis: INV-NNN, BIG-NN, JTBD-NN
│  (markdown)      │
└────────┬─────────┘
         │ (1) parser tools/spec-extract/
         ▼
┌──────────────────┐
│  YAML/JSON       │   estrutura: agregados, campos, invariantes, transições
│  intermediário   │
└────────┬─────────┘
         │ (2) make spec-sync (templates Jinja2)
         ▼
┌──────────────────────────────────────────────────────┐
│  Código gerado (cascateado):                         │
│                                                       │
│  ├── Migration Django (draft, revisão humana)        │
│  ├── Dataclass domínio (domain/{entidade}/agregado.py)│
│  ├── Django Model (infrastructure/models/)           │
│  ├── DRF Serializer (infrastructure/serializers/)    │
│  ├── Pydantic Schema (infrastructure/schemas/)       │
│  ├── factory-boy fixture (tests/factories/)          │
│  ├── pytest test stub citando INV (tests/test_inv_*) │
│  └── OpenAPI 3 (drf-spectacular regenera)            │
└────────┬─────────────────────────────────────────────┘
         │ (3) openapi-generator + drift_dev
         ▼
┌──────────────────┐
│  Dart client +   │   Flutter consome via codegen
│  drift schema    │
└──────────────────┘
```

**Comando único:**
```bash
make spec-sync
```

**Hook CI bloqueia merge** se:
- Spec mudou e gerados não regeneraram
- Drift entre YAML intermediário e código gerado

### 2. Estrutura de pastas

```
src/
├── domain/                          # camada de domínio PURA (sem Django)
│   ├── certificado/
│   │   ├── agregado.py              # Certificado, métodos puros
│   │   ├── invariantes.py           # assert_inv_001(), assert_inv_007() etc
│   │   ├── eventos.py               # CertificadoEmitido, CertificadoCancelado
│   │   └── repository.py            # Protocol (sem implementação)
│   ├── instrumento/
│   ├── tenant/
│   └── shared/
│       ├── value_objects.py         # CPF, CNPJ, Email, Money
│       └── events.py                # EventBus Protocol
│
├── infrastructure/                  # adapters concretos
│   ├── models/                      # Django Models (gerados)
│   ├── serializers/                 # DRF Serializers (gerados)
│   ├── schemas/                     # Pydantic (gerados)
│   ├── repositories/                # implementação Django dos Protocols
│   │   └── certificado_django.py
│   └── eventbus/
│       └── celery_bus.py            # implementação concreta do EventBus
│
├── application/                     # casos de uso
│   ├── emitir_certificado.py        # recebe repos + eventbus via DI
│   └── cancelar_certificado.py
│
└── tools/
    └── spec-extract/                # parser spec PT → YAML
        ├── parser.py
        └── templates/               # Jinja2 templates por tipo de output
            ├── django_model.py.j2
            ├── pydantic_schema.py.j2
            ├── dart_class.dart.j2
            └── ...
```

### 3. Invariantes em 3 camadas obrigatórias

Toda invariante crítica (INV-NNN) é expressa em **3 lugares simultaneamente**:

**(a) Banco — pra dado-dependente:**
- `CHECK` constraint, `EXCLUSION` constraint, ou RLS policy
- Exemplo INV-011 (padrão usado com calibração vencida): `CHECK (validade_calibracao >= data_uso)`
- Exemplo INV-TENANT-003: RLS policy
- Exemplo INV-015 (perfil A exige acreditação real): `CHECK (perfil != 'A' OR cnpj_cgcre IS NOT NULL)`

**(b) Domínio — pra regra-de-comportamento:**
- Método `assert_invariant_NNN()` no agregado, puro (sem Django)
- Exemplo INV-007 (certificado emitido é imutável):
  ```python
  class Certificado:
      def aprovar_edicao(self) -> None:
          if self.status == Status.EMITIDO:
              raise InvariantViolation(
                  inv_id="INV-007",
                  message="Certificado emitido não pode ser editado"
              )
  ```

**(c) Teste — pra prova:**
- pytest cujo nome cita o ID
- TST-004 (REGRAS-INEGOCIAVEIS.md) exige
- Exemplo: `test_inv_007_certificado_emitido_nao_pode_ser_editado()`

**Pydantic NÃO é lar de invariante.** Pydantic só valida formato/tipo de I/O (boundary HTTP, LLM, IPC). Invariante de negócio sempre nas 3 camadas acima.

### 4. Message bus explícito (NÃO Django signals)

**Por quê?** Django signals são:
- Invisíveis (acoplados ao ORM, executam em cascata sem rastro)
- Difíceis de testar
- Ordem não-determinística
- Quebram atomicidade transacional quando combinam com Celery

**Em vez de signals:**

```python
# domain/shared/events.py
class EventBus(Protocol):
    def emit(self, event: DomainEvent) -> None: ...
    def subscribe(self, event_type: type, handler: Callable) -> None: ...

# domain/certificado/eventos.py
@dataclass(frozen=True)
class CertificadoEmitido(DomainEvent):
    certificado_id: UUID
    tenant_id: UUID
    timestamp: datetime
    signatario_cpf: str

# application/emitir_certificado.py
class EmitirCertificadoUseCase:
    def __init__(self, repo: CertificadoRepository, bus: EventBus):
        self.repo = repo
        self.bus = bus

    def execute(self, cmd: EmitirCertificadoCommand) -> Result:
        cert = Certificado.criar(cmd)
        cert.assert_invariant_002()  # cadeia rastreabilidade
        cert.assert_invariant_007()  # imutabilidade após emissão
        self.repo.save(cert)
        self.bus.emit(CertificadoEmitido(...))  # explícito, auditável
        return Result.ok(cert)
```

**Subscribers:**
- `enviar_pdf_pra_cliente` (handler de email)
- `agendar_recalibracao_proxima_data` (Celery task)
- `notificar_signatario_via_whatsapp`

Cada handler é **explícito**, **testável isoladamente**, e **roda em transação separada** (não bloqueia o use case).

### 5. Convenção `Django signals = proibido por default`

Lint custom semgrep:
```yaml
- id: no-django-signals
  pattern: |
    @receiver($SIGNAL)
    def $FN(...): ...
  message: "Django signals proibidos. Use EventBus explícito em application/. Override exige decorator @signal_allowed + revisão de Auditor 2."
  severity: ERROR
```

Override permitido apenas com:
- Decorator `@signal_allowed(reason="...", reviewer="Auditor 2")`
- Justificativa por escrito
- Revisão humana documentada

### 6. Conexão com anti-corrosion layer

Repository Protocols do domínio são implementados em `infrastructure/repositories/`:

```python
# domain/certificado/repository.py (Protocol — PURO)
class CertificadoRepository(Protocol):
    def save(self, cert: Certificado) -> None: ...
    def get(self, id: UUID, tenant_id: UUID) -> Certificado: ...
    def list_by_tenant(self, tenant_id: UUID) -> list[Certificado]: ...

# infrastructure/repositories/certificado_django.py (concreto — Django)
class DjangoCertificadoRepository:
    def save(self, cert: Certificado) -> None:
        model = CertificadoModel.from_domain(cert)
        model.save()  # Django ORM aqui é OK; domain não vê
    # ...
```

Domain code **NUNCA** importa `from django.db import models`. Sempre via Protocol.

---

## Itens a fazer

### Bloqueantes pra F-A começar
- [ ] **`tools/spec-extract/` parser markdown → YAML** (regex extraindo blocos INV/BIG/JTBD)
- [ ] **Templates Jinja2** pra cada tipo de output (django_model, pydantic_schema, dart_class, factory, test_stub)
- [ ] **`make spec-sync`** target no Makefile
- [ ] **Hook CI** bloqueando merge se spec muda e gerados não regeneram
- [ ] **`domain/shared/` boilerplate** (EventBus Protocol, value objects, DomainEvent base)
- [ ] **Lint custom semgrep** `no-django-signals` ativo

### Documentação obrigatória
- [ ] **`docs/arquitetura/spec-as-source-pipeline.md`** — pipeline detalhado com exemplos
- [ ] **`docs/arquitetura/django-convencoes.md`** — convenções pros agentes (já citado em ADR-0001 v2)

### Pós-MVP-1
- [ ] Avaliar adoção de `Pydantic v2 + DRF Spectacular` versus alternativas (`apispec`, `ninja`)
- [ ] Mover boilerplate gerado pra biblioteca interna se padrão estabilizar

---

## Consequências

### Positivas
- **Spec PT vira fonte real** — não documentação morta.
- **Domain code testável sem subir Django** — testes ultra-rápidos (10x mais rápidos que test client DRF).
- **Mudança de spec cascateia automaticamente** — agente IA não precisa lembrar das 4 representações.
- **Invariantes em 3 camadas = defesa em profundidade** (banco + domínio + teste).
- **Refactor de stack futura mais fácil** — domain agnóstico de Django, troca por FastAPI / Litestar é refactor mecânico em `infrastructure/`.
- **EventBus explícito é auditável** — todo evento de domínio passa por log estruturado.

### Negativas
- **Boilerplate inicial é grande** — 4 layers (domain/infrastructure/application + tools/spec-extract). Justificável só se projeto crescer; em MVP super-enxuto seria over-engineering.
- **Curva de aprendizado pros agentes** — Django convida ao "model fat" anti-pattern. Convenção exige disciplina + lint.
- **Tempo de implementação do pipeline** — ~2 semanas pra deixar parser + templates + scaffolding rodando. Atrasa F-A.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Domain layer separada vs "fat models" Django | Separada | Parecer 6 alertou; D2 spec-as-source exige código derivado |
| Pipeline de geração vs escrita manual das 4 reps | Pipeline | Em 2 sprints, manual diverge (Parecer 6) |
| EventBus explícito vs Django signals | EventBus | Auditabilidade + atomicidade + testabilidade |
| Pydantic como invariante vs Pydantic só I/O | Só I/O | Invariante vive nas 3 camadas (banco + domínio + teste) |
| Markdown spec → YAML → código vs spec direto em YAML | Markdown → YAML | Markdown é legível pro Roldão; YAML é estruturado pro codegen |

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| Pipeline de codegen virar gargalo (mais lento que escrever manual) | Avaliar simplificar templates ou cair pra geração híbrida |
| Roldão deixar de conseguir validar spec PT no Django Admin | Refatorar Admin pra refletir mudança de spec |
| Pydantic v2 quebrar compatibilidade major | Avaliar alternativa (msgspec, attrs) |
| Spec PT crescer demais (>50 specs ativas) | Particionar por bounded context |

---

## Aprovação

- [x] **Roldão (decisor):** aceita pipeline spec→código + camada de domínio separada — ✅ aprovado em 2026-05-17 como parte da autorização pra arrancar Foundation F-A (com nota: pipeline completo é entregável de Wave A; F-A entrega só a estrutura de pastas + boilerplate)
- [ ] **Auditor 6 (spec-as-source — 2ª auditoria):** confirma que 4-representações-divergem foi resolvido? — valida durante Wave A (quando codegen real roda)
- [ ] **Auditor de qualidade (Família 5):** confirma TST-004 compatível com test stubs gerados? — valida durante Wave A
