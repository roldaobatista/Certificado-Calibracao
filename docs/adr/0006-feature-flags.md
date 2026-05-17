# ADR-0006 — Feature flags

> **Status:** proposta (2026-05-17 noite final). Substitui o stub anterior "0006-reservado".
> **Bloqueia:** habilitação seletiva de feature por tenant; release contínuo seguro.
> **Depende de:** ADR-0001 (stack — Django), ADR-0002 (multi-tenancy).

---

## Contexto

Aferê precisa:
- **Habilitar feature por tenant** (alguns tenants veem módulo X, outros não — sem fork de código)
- **Soft-launch** (rolar 10% dos tenants primeiro, depois 100%)
- **Kill switch** (desligar feature problemática sem rollback)
- **A/B test light** (V2 — comparar 2 variantes de UX)
- **Permissão por perfil** (perfil A vê módulo de acreditação; perfil D não)

Sem feature flags: cada feature é deploy + revert; mudança de público vira migration.

---

## Decisão

**`django-waffle` (open source maduro) + tabela própria pra `tenant_features`**, NÃO LaunchDarkly/Featbit externo.

### Stack

- **django-waffle:** flags globais (debug, kill switch, A/B test light) — gerenciamento via Django admin
- **Tabela `tenant_features` própria:** habilitação por tenant (modelo + RLS) — gerenciamento via UI admin Aferê
- **Decorator + middleware:** `@feature_required("modulo_calibracao")` em view; redireciona ou 404 se tenant não tem
- **Frontend (HTMX + Flutter):** consulta `/api/me/features` no login; cacheia 5 min

### Tipos de flag

| Tipo | Propósito | Onde fica |
|---|---|---|
| **Kill switch global** | "Desligar tudo de NFS-e" em emergência | django-waffle |
| **Feature por tenant** | "Tenant T_42 tem módulo X" | `tenant_features` (próprio) |
| **Feature por perfil** | "Perfil A vê acreditação; perfil D não" | derivado de `tenant.perfil` + catálogo de features |
| **A/B test** (V2) | "Variante A vs B em UX nova" | django-waffle samples |
| **Rollout gradual** | "Soft-launch em 10% dos tenants" | django-waffle percent |

### Catálogo de features

Lista versionada em `docs/comum/feature-flags-catalogo.md` (a criar quando Wave A começar):
- `nfse_emit` — emissão NFS-e (depende de plano)
- `mobile_app` — app técnico
- `certificado_rbc` — emissão com selo RBC (perfil A only)
- `painel_dono` — Wave B
- `crm_kanban` — Wave B (depende plano)
- ...

### Por que não LaunchDarkly / Featbit

| Critério | django-waffle + caseiro | LaunchDarkly / Featbit |
|---|---|---|
| Custo | $0 | R$ 500-3k/mês |
| LGPD | Tudo no Aferê | Decisões de feature vão pra terceiro |
| Tempo de setup | 1 dia | 1 semana + integração |
| Suficiente pra MVP-1 + Wave B | Sim | Over-engineering |
| Custo de troca futura | Anti-corrosion: porta `FeatureFlagProvider` | Médio |

---

## Alternativas consideradas

| Alternativa | Rejeitada porquê |
|---|---|
| **LaunchDarkly** | SaaS pago + LGPD compromete |
| **Featbit (self-host)** | Setup extra (Redis + Node.js + MongoDB) — fora da stack |
| **Hardcoded `if tenant.id == 42:`** | Quebra ANTI-11 (customização por código) |
| **Toggle global em settings.py** | Sem granularidade por tenant |
| **Unleash (self-host)** | OK mas Java/Node — fora da stack Python |

---

## Limites legítimos

- **Não cria customização infinita por tenant.** Feature ou está no catálogo Aferê ou não existe. ANTI-11 preservado.
- **Catálogo é versionado.** Adição/remoção de feature exige PR + revisão Auditor Produto.
- **Auditor de Segurança valida em pre-commit** que feature crítica (financeiro/kms/migrations) requer aprovação humana explícita pra habilitar.
- **Audit log de cada flag toggle** (quem ligou/desligou pra quem, quando, por quê).

---

## Consequências

### Positivas
- Habilitação granular sem fork
- Kill switch rápido
- Rollout seguro (10% → 100%)
- Diferenciação por perfil A/B/C/D explícita
- LGPD em casa

### Negativas
- Complexidade adicional (toda view crítica precisa pensar em flag)
- Catálogo cresce → governança
- Risco de "flag fica ligada eternamente" virar débito técnico → limpeza trimestral

### Riscos
- Flag mal-configurada exibe feature errada → mitigação: auditor produto valida em pre-merge
- Performance: cache invalido a cada mudança → mitigação: TTL 5 min + invalidação por evento

---

## Critério de mortalidade

- Catálogo > 100 features → considerar Featbit self-host
- Performance: latência de check de flag > 50ms p99 → revisar cache
- Tenants > 1000 com features divergentes → considerar LaunchDarkly se LGPD permitir (cláusula DPA)

---

## Implementação (esqueleto, quando Foundation F-G começar)

```
apps/features/
├── models.py                  # FeatureFlag, TenantFeature
├── catalog.py                 # lista versionada
├── decorators.py              # @feature_required("nome")
├── middleware.py              # injeta features na request
├── admin.py                   # Django admin pra gerenciar
└── views/api.py               # GET /me/features

infrastructure/feature_flags/
├── waffle_provider.py         # implementa porta FeatureFlagProvider
└── (futuro) launchdarkly_provider.py  # se um dia migrar
```

---

## Referências

- ADR-0001 (stack — Django), ADR-0002 (multi-tenancy)
- django-waffle: https://waffle.readthedocs.io/
- `prd.md` §5 (non-goals — ANTI-11 customização por tenant)
- `REGRAS-INEGOCIAVEIS.md` INV-AGENT-001
- `docs/arquitetura/anti-corrosion-layer.md` (proposta de 10ª porta: FeatureFlagProvider)
