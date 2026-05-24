---
adr: 0058
titulo: Porta ProductAnalyticsProvider — eventos de produto separados de eventos de domínio
status: aceito
data-decisao: 2026-05-23
decisor: roldao
contexto-marco: Onda 2 plano-v2 (saneamento pré-Marco 3 Fase 5)
relacionados:
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/arquitetura/anti-corrosion-layer.md
  - docs/conformidade/comum/retencao-matriz.md
---

# ADR-0058 — Porta ProductAnalyticsProvider

## Status

**ACEITO** em 2026-05-23. Originalmente reservada na Onda 0 plano-v2 (auditor PROD apontou ⛔ CRÍTICO: "Wave A inteira sai cega sem instrumentação"; auditor LGPD apontou ⛔ ALTO: "analytics produto sem matriz de consentimento"). Antecipada da Onda 5 para Onda 2 antes do Marco 3 Fase 5 gerar 1ª tela.

## Contexto

O auditor de produto da auditoria projeto-inteiro (Onda 0 plano-v2) detectou:

1. **Eventos do bus são de DOMÍNIO** (`Cliente.Criado`, `OS.Aberta`, `Certificado.Emitido`) — descrevem mudança de estado de negócio. **Não são de PRODUTO** (não medem se feature está sendo USADA, qual funil quebra, em que tela técnico abandona).
2. Sem instrumentação de produto, **dogfooding vira anedota, não dado**: Roldão olha o app, sente que "tá lento", mas não tem evidência objetiva de onde lenta nem quantas vezes.
3. Sem matriz de consentimento, eventos com PII (mesmo pseudonimizada) podem violar LGPD art. 7º IX (legítimo interesse) vs art. 11 (consentimento explícito).

Auditor LGPD reforçou na auditoria do plano-v2: "métrica `OS aberta/dia por usuário` não é interesse legítimo automático — perfil comportamental por usuário identificado exige opt-in (art. 7º IX + art. 10)".

## Decisão

**Criar porta `ProductAnalyticsProvider` (19ª porta na anti-corrosion layer) separada do bus de eventos de domínio + matriz canônica de consentimento + hook anti-PII em payload.**

### 1. Porta ProductAnalyticsProvider

Em `src/domain/shared/ports/product_analytics.py`:

```python
class ProductAnalyticsProvider(Protocol):
    def registrar_evento(
        self,
        evento: NomeEventoProduto,  # enum canônico abaixo
        tenant_id: UUID,
        usuario_id: UUID | None,    # None se evento anônimo (visitante)
        propriedades: dict[str, Any],
        base_legal: BaseLegalLGPD,  # enum: INTERESSE_LEGITIMO | CONSENTIMENTO_EXPLICITO
    ) -> None: ...

    def registrar_consentimento(
        self,
        tenant_id: UUID,
        usuario_id: UUID,
        opt_in: bool,
        timestamp: datetime,
    ) -> None: ...

    def revogar_consentimento(
        self,
        tenant_id: UUID,
        usuario_id: UUID,
        timestamp: datetime,
    ) -> None: ...
```

Adapters esperados:

- **Adapter `local`** (dev/test): grava em tabela `eventos_analytics_produto` com TTL configurável.
- **Adapter `posthog`** (Wave A se decidido): integração com PostHog self-hosted (open-source, hospedável próprio — alinhado com BUSL-1.1).
- **Adapter `null`**: descarta tudo (fallback emergencial se LGPD pedir desligamento).

Implementação concreta fica para Wave A; spec da Wave A escolhe adapter.

### 2. Distinção evento de domínio × evento de produto

| Aspecto | Evento de domínio (bus existente) | Evento de produto (esta ADR) |
|---|---|---|
| Persistência | `outbox_events` + `dead_letter_events` | tabela própria `eventos_analytics_produto` (ou backend externo) |
| Imutável | Sim (append-only, hash chain) | Sim (append-only sem hash chain) |
| Sequência | Schema versionado (ADR-0036 quando aceita) | Schema versionado por `evento_nome` + `evento_versao` |
| Quem consome | Outros módulos (saga, consumer) | Time de produto, dashboards, BI |
| LGPD | Base legal: execução contrato (art. 7º V) | Base legal: depende (ver §3 abaixo) |
| Retenção | Conforme matriz por entidade | 365 dias por padrão; 90 dias se PII pseudonimizada presente |
| Cross-tenant | NUNCA (RLS força) | NUNCA (provider sempre passa tenant_id) |

### 3. Matriz canônica de consentimento LGPD

| Tipo de evento | Base legal | Exige opt-in? | Exemplo |
|---|---|---|---|
| **Telemetria operacional anônima** | Legítimo interesse (art. 7º IX) | Não | `App.HealthCheck.Ok`, `Servidor.LatenciaP95`, `Bus.MensagensProcessadas` |
| **Telemetria operacional com tenant_id (sem usuário)** | Legítimo interesse | Não | `Tenant.OS.AbertasNoMes`, `Tenant.UsoStorageMB` |
| **Funil de feature sem perfil de usuário (agregado anônimo)** | Legítimo interesse | Não | `Funil.NovaOS.Step1Concluido` (sem `usuario_id`) |
| **Perfil comportamental por usuário identificado** | Consentimento explícito (art. 7º I + art. 11) | **SIM** | `Funil.NovaOS.Step1Concluido` com `usuario_id` |
| **A/B test por usuário identificado** | Consentimento explícito | **SIM** | `Experimento.NovaTela.Variante=A` |
| **Tracking cross-tela com cookie/fingerprint** | Consentimento explícito | **SIM** | `Sessao.RetornoEm` (em SaaS web) |
| **Evento com PII em propriedades (CPF/email/telefone)** | **PROIBIDO independente de base legal** | n/a | bloqueado pelo hook |

Decisão por evento entra no PRD do módulo que cria o evento + revisão `auditor-conformidade-lgpd` + spec do `ProductAnalyticsProvider` adapter mantém matriz canônica.

### 4. INV-PROD-ANALYTICS-001 — sem PII em payload

**Proibido** em `propriedades` de evento: CPF, CNPJ, e-mail, telefone, RG, CEP, nome completo, endereço, data de nascimento, qualquer hash não-versionado de PII.

Permitido: `usuario_id` (UUID interno), `tenant_id`, valores enum, IDs de entidade, contadores, timestamps, identificadores de feature.

Hook `analytics-anti-pii-payload.sh` valida payload em código que chama `ProductAnalyticsProvider.registrar_evento(...)`:

- Regex de CPF/CNPJ/e-mail/telefone/CEP/RG (reutiliza regex do `seed-anti-pii-real.sh`).
- Detecção de chamada a `.format()`, f-string, `%` com variável de nome suspeito (`cpf`, `email`, `nome`, `endereco`).
- Allowlist via comentário: `# analytics-pii: skip -- <razão>` exige aprovação `auditor-conformidade-lgpd`.

### 5. INV-PROD-ANALYTICS-002 — sem cross-tenant

Provider sempre exige `tenant_id` no método. Adapter local grava com FK `tenant_id` + RLS policy `tenant_id_eq_session`. Adapter externo (PostHog) usa workspace separado por tenant OU tag `tenant_id` no evento que filtra dashboard.

### 6. INV-PROD-ANALYTICS-003 — opt-in real, não dark pattern

Quando consentimento explícito é exigido (matriz §3):

- Checkbox de opt-in **NÃO** vem marcado por padrão (LGPD ANPD Guia Cookies 2022 §4.3).
- Texto da pergunta é claro, sem jargão. Exemplo aceito: "Permito que o Aferê meça como uso o sistema para melhorar funcionalidades. Não compartilhamos com terceiros."
- Opção "Não permitir" tem mesma proeminência visual que "Permitir".
- Revogação acessível em 2 cliques desde qualquer tela (link no footer "Privacidade").

### 7. Catálogo canônico de eventos de produto

Vai viver em `docs/conformidade/comum/catalogo-eventos-analytics.md` (a criar). Estrutura por módulo: nome do evento + base legal + propriedades obrigatórias + retenção.

Marco 3 Fase 5 PRD declara quais eventos de OS são gerados + base legal de cada. Hook `a11y-checklist-spec.sh` extensão valida que PRD novo tem seção "Analytics de Produto" preenchida.

## Consequências

### Positivas

- Wave A nasce instrumentada — dogfooding vira dado objetivo.
- Matriz LGPD evita armadilha "métrica simples virou perfilamento sem opt-in".
- Separação evento domínio/produto evita poluir bus (`outbox_events` cresceria absurdo com analytics).
- Hook anti-PII pega o erro no commit, não em auditoria ANPD.

### Negativas

- Cada PRD novo precisa preencher matriz consentimento.
- Adapter externo (PostHog) exige hospedagem própria → custo operacional (~R$ 30-100/mês quando entrar; aceitável vs SaaS analytics fechado tipo Mixpanel/Amplitude).
- Dois fluxos de evento (domínio + produto) = duas tabelas, dois consumers — complexidade.

### Aceitas conscientemente

- Decisão de adapter (local / PostHog / null) fica pra Wave A spec.
- Tracking de visitante anônimo (sem `usuario_id`) é permitido por legítimo interesse — Roldão prefere medir sem opt-in do anônimo, com opt-in só pro identificado.

## GATEs

- **GATE-PRODANALYTICS-1:** criar tabela `eventos_analytics_produto` no F-C2 (junto com structlog + métricas — observabilidade infra).
- **GATE-PRODANALYTICS-2:** criar `catalogo-eventos-analytics.md` na Onda 2 (parte do checklist do M3 PRD).
- **GATE-PRODANALYTICS-3:** hook `analytics-anti-pii-payload.sh` criado e registrado em `_test-runner.sh` na Onda 2 (parte desta sub-onda).
- **GATE-PRODANALYTICS-4:** Marco 3 Fase 5 PRD declara eventos OS + base legal antes de gerar 1ª tela.
- **GATE-PRODANALYTICS-5:** Wave A escolhe adapter concreto (PostHog self-hosted vs alternativa).
- **GATE-PRODANALYTICS-6:** revogação de consentimento integrada com ADR-0061 (canal do titular + DPO) — interface única `/privacidade`.

## Não-objetivos desta ADR

- **NÃO** exige A/B test em Wave A (decisão futura por feature flag — ADR-0006).
- **NÃO** define design do banner de consentimento (UX — fica PRD Wave A).
- **NÃO** cobre logs técnicos do servidor (esses são observabilidade — F-C2; LGPD trata diferente).
- **NÃO** cobre tracking de marketing (site institucional Aferê — fora do escopo SaaS).

## Histórico

- 2026-05-23: reservada como ADR-0057 pela Onda 0 plano-v2.
- 2026-05-23: renumerada para ADR-0058 após conflito ADR-0056.
- 2026-05-23: aceita pela Onda 2 plano-v2.
