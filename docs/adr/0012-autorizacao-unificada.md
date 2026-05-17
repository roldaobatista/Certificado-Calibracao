# ADR-0012 — Autorização unificada (porta AuthorizationProvider cobrindo RBAC + escopo + cross-tenant + validade)

> **Status:** **PROPOSTA** (17/05/2026, madrugada). Resolve achado da auditoria de 10 agentes (Auditor 8 — RBAC pra 48 módulos × 16 perfis) que apontou que `django-allauth` + permissões nativas do Django **não cobrem** regras como "RT só assina dentro do escopo acreditado vigente", "auditor RBC visitante com acesso time-boxed", "parceiro marketplace vendo dados de N tenants". Decisão é **unificar todas as decisões de autorização em uma porta única `AuthorizationProvider`**, implementada inicialmente em Django + RLS PostgreSQL (sem Casbin/OPA por enquanto), mas com fronteira limpa pra trocar implementação depois sem reescrever domínio.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria 10 agentes 17/05/2026 — Auditor 8 (RBAC) crítico + Auditor I (Segurança da auditoria às cegas) confirmando "Django built-in + RLS é suficiente, defesa em profundidade".
> **Depende de:** ADR-0001 (Django escolhido), ADR-0002 (RLS PostgreSQL), ADR-0006 (feature flags).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Autorização** | Decisão "esse usuário pode fazer essa ação?". Diferente de **autenticação** (que é "esse usuário é mesmo quem ele diz?"). |
| **RBAC** | "Role-Based Access Control" — controle por **papel**. Ex: "Financeiro pode estornar fatura, Comercial não pode". |
| **ABAC** | "Attribute-Based Access Control" — controle por **atributo contextual**. Ex: "RT só assina certificado se o tipo de instrumento estiver dentro do escopo acreditado dele E a acreditação não estiver vencida E o RT está apto pra esse tipo de calibração". |
| **Escopo** | Conjunto de "coisas que aquela pessoa pode ver/fazer". Ex: técnico vê só as OS da filial onde trabalha; RT só assina certificado dentro do escopo acreditado dele. |
| **Time-boxed** | "Tempo limitado". Auditor RBC entra hoje no sistema, mas o acesso dele expira em 72h automaticamente. |
| **Cross-tenant** | Usuário com acesso a vários clientes ao mesmo tempo. Ex: parceiro marketplace que vende plugin pra 10 tenants — ele é "um usuário em 10 contas". |
| **Porta / Adapter** | "Tomada de extensão" — a parte do código que define **o que** o sistema precisa ("preciso saber se esse usuário pode fazer X"). A implementação ("como" essa decisão é tomada) fica numa peça separada que pode ser trocada. |
| **Casbin / OPA / Oso** | Bibliotecas/ferramentas que fazem autorização "fora do Django" — você escreve regras numa linguagem própria, a ferramenta decide. Boas em escala muito grande, mas adicionam complexidade. |
| **RLS** | "Row-Level Security" — trava no banco de dados que impede um cliente de ver dados de outro cliente, mesmo que o código da aplicação erre o filtro. |
| **RAT** | "Registro de Atividades de Tratamento" — exigência da LGPD: o sistema precisa saber QUAL finalidade justifica cada acesso a dado pessoal. |

---

## Contexto

Quando a ADR-0001 foi escrita, o sistema previa **4 perfis principais** (dono, técnico, financeiro, comercial) e o controle de permissões nativo do Django (`django.contrib.auth` + `django-allauth` + `django-otp`) era suficiente.

Hoje o sistema cresceu pra **16 perfis previstos**, com regras de autorização que o Django nativo **não cobre limpo**:

| Perfil | Regra complexa que o Django nativo NÃO cobre limpo |
|---|---|
| **RT (Responsável Técnico acreditado RBC)** | "Só assina certificado se o tipo de instrumento estiver dentro do escopo acreditado dele E a acreditação não estiver vencida E o RT está marcado como apto pra esse tipo de calibração na matriz de competência (ISO 17025 6.2)" |
| **Auditor RBC visitante** | "Tem acesso read-only, scoped aos módulos `metrologia/*` + `rh-frota-qualidade/treinamentos`, time-boxed (expira em N horas)" |
| **Cliente externo (portal-cliente)** | "Vê só os dados do seu próprio CNPJ dentro daquele tenant — mas pode pertencer a matriz + filiais (1 cliente em N CNPJs sob o mesmo grupo)" |
| **Parceiro marketplace (Wave B/V2)** | "É um usuário pertencente a N tenants ao mesmo tempo — vê dados de pedidos dele em cada um. RLS atual assume `1 usuário = 1 tenant` e quebra aqui." |
| **Fornecedor** | "Acesso só ao módulo `suporte-plataforma/fornecedores` + `estoque` (entradas dele), nada mais" |
| **Técnico de campo** | "Vê só OS atribuídas a ele OU OS da equipe dele (definido pela hierarquia em `colaboradores`)" |
| **Financeiro** | "Vê tudo de financeiro, mas só pode estornar fatura se valor < R$ X (definido por tenant) OU se gerente aprovar (workflow BPM)" |
| **Dono do tenant** | "Vê tudo do tenant dele — mas não vê dados pessoais de funcionários demitidos (LGPD crypto-shredding aplicado)" |
| **Roldão (dono Aferê)** | "Vê dados agregados de TODOS os tenants (cross-tenant), mas não vê dados pessoais sem audit trail registrado (LGPD)" |

**Problema concreto:** se cada um desses 16 perfis vive como `if user.groups.filter(name='X').exists() and ...` espalhado em views, serializers, signals, querysets, **vai virar caos em 6 meses**:

1. **Inconsistência:** o mesmo perfil decide diferente em endpoints diferentes (esquece de checar escopo num lugar, checa duas vezes em outro)
2. **Bug regulatório garantido:** "RT assinou certificado fora do escopo" porque alguém esqueceu de validar acreditação naquele endpoint
3. **Auditoria LGPD impossível:** ANPD pergunta "quem viu dados de CPF do cliente X em 2027-03-15?" — sem ponto único de decisão, não consegue responder
4. **Refatoração paralisante:** quando vier um perfil novo (parceiro marketplace), tem que tocar em 200 lugares

**Cenário que disparou a decisão:** auditor 8 calculou que **48 módulos × 16 perfis × 5 ações (CRUD + executar) = 3.840 células** de matriz de permissão. Sem ponto único, isso é ingerenciável.

---

## Decisão

Adotar **porta única `AuthorizationProvider`** que centraliza toda decisão de "esse usuário pode fazer essa ação?". Implementação inicial em Django + RLS PostgreSQL (sem Casbin/OPA), mas a fronteira é limpa o suficiente pra trocar a implementação depois sem reescrever domínio.

### A porta — interface única que TODO código de aplicação chama

```python
# domain/authz/authorization_provider.py
from typing import Protocol
from datetime import datetime

class AuthorizationProvider(Protocol):
    """
    Toda decisão de autorização passa por aqui. Nenhum view, serializer,
    queryset, signal, handler ou task pode decidir "pode/não pode" sem
    chamar este método.
    """
    
    def can(
        self,
        user_id: UUID,
        action: str,          # ex: "certificado.emitir", "fatura.estornar"
        resource: dict,       # ex: {"tipo_instrumento": "balanca", "valor": 5000}
        tenant_id: UUID,      # tenant onde a ação acontece (pode ser N pra cross-tenant)
        purpose: str,         # finalidade LGPD: "execucao_contrato", "cumprimento_obrigacao_legal"
        at_time: datetime,    # quando a decisão é avaliada (default: agora)
    ) -> Decision:
        """
        Retorna Decision(allowed: bool, reason: str, audit_trail_id: UUID).
        SEMPRE grava em audit trail antes de retornar, independente do resultado.
        """
        ...
```

**Toda decisão gera uma linha em `audit_trail.authz_decisions`** — RAT da LGPD fica automático.

---

### As 4 camadas de defesa em profundidade

A porta é a primeira camada, mas não a única. Mantém-se defesa em profundidade:

| Camada | Onde mora | O que faz |
|---|---|---|
| **1. Hook pré-commit** | `.claude/hooks/` | Bloqueia merge se algum endpoint Django novo não chamar `AuthorizationProvider.can()` antes de retornar resposta |
| **2. Middleware Django** | `infrastructure/authz/middleware.py` | Antes de processar request, valida que JWT/sessão tem `user_id` + `tenant_id` válidos; injeta no contexto |
| **3. `AuthorizationProvider.can()`** | `domain/authz/` | Decisão central — RBAC + ABAC + escopo + validade + cross-tenant + audit |
| **4. RLS PostgreSQL** | banco | Mesmo que tudo acima falhe, banco filtra por `tenant_id` na role `app_user` (NOBYPASSRLS) |

**Sem violar qualquer camada, é impossível um RT assinar fora do escopo, um parceiro ver tenant errado, ou um auditor RBC visitante acessar fora do tempo permitido.**

---

### Implementação inicial — Django + tabelas no PG

A implementação concreta da porta vive em `infrastructure/authz/django_authorization_provider.py` e consulta 5 tabelas:

#### 1. `auth_perfil` — RBAC clássico (matriz papel × ação)

| campo | descrição |
|---|---|
| `id` | UUID |
| `nome` | "RT acreditado", "Financeiro", "Cliente externo" |
| `descricao` | texto |
| `tenant_id` | NULL se perfil global (admin Aferê); UUID se perfil de tenant específico |

```
auth_perfil_acao:
  perfil_id × acao (string "modulo.acao") × pode_executar (bool)
```

Ex: `("RT acreditado", "certificado.emitir", true)`.

#### 2. `auth_usuario_perfil` — vínculo usuário → perfil (M:M, time-boxed, cross-tenant)

| campo | descrição |
|---|---|
| `usuario_id` | UUID |
| `perfil_id` | UUID |
| `tenant_id` | UUID (o tenant onde esse perfil está ativo) |
| `valido_de` | datetime |
| `valido_ate` | datetime (NULL = indefinido; auditor RBC = data fim auditoria) |
| `escopo` | JSONB — atributos ABAC (ex: `{"escopo_acreditado": ["balanca", "termometro"], "filial_id": "..."}`) |

**Esta tabela resolve cross-tenant automaticamente.** Um parceiro marketplace tem N linhas (uma por tenant). Um auditor RBC visitante tem 1 linha com `valido_ate = agora + 72h`. Um RT tem `escopo` populado com a acreditação atual vigente.

#### 3. `auth_atributo_dinamico` — ABAC contextual

Atributos derivados em runtime que entram na decisão. Ex:
- "Acreditação do RT está vigente?" → consulta `metrologia/licencas-acreditacoes`
- "Matriz de competência marca esse RT apto pra esse tipo de calibração?" → consulta `rh-frota-qualidade/treinamentos`
- "Valor da fatura está abaixo do limite de estorno desse perfil?" → consulta `financeiro/contas-receber`

Esses atributos são funções Python registradas como `@authz_attribute("acreditacao_vigente")` — `AuthorizationProvider.can()` chama as funções necessárias conforme a ação solicitada.

#### 4. `audit_trail.authz_decisions` — RAT LGPD automático

Toda decisão (autorizada OU bloqueada) grava:

| campo | conteúdo |
|---|---|
| `timestamp` | quando |
| `user_id` | quem pediu |
| `tenant_id` | em qual tenant |
| `action` | string `modulo.acao` |
| `resource_summary` | JSON resumido do recurso (sem PII cru) |
| `purpose` | finalidade LGPD |
| `decision` | `allowed` / `denied` |
| `reason` | string explicando |
| `perfis_aplicados` | array de IDs de perfis que pesaram na decisão |
| `escopo_avaliado` | JSON com atributos ABAC consultados |
| `ip_hash` | SHA-256 do IP |

Append-only (trigger PG bloqueia UPDATE/DELETE). Cópia pra B2 WORM a cada hora (ver ADR-0011).

#### 5. Cache Redis (`auth:user:{user_id}:tenant:{tenant_id}`)

Decisão de autorização é cacheada por 5 minutos pra reduzir N+1. Invalidação automática em:
- Mudança em `auth_usuario_perfil` (perfil concedido/revogado)
- Mudança em `auth_perfil_acao` (matriz)
- Evento `acreditacao.vencida`, `treinamento.expirado`, `licenca.suspensa` (publicados pelos módulos metrologia/RH)

---

### Integração com feature flags (ADR-0006)

**Ponto único de "pode/não pode" combina permissão E feature flag.**

```python
# pseudo-código
def can(user_id, action, ...):
    # 1. Feature flag — esse tenant tem essa funcionalidade ativada?
    if not feature_flag.is_enabled(action_to_feature(action), tenant_id):
        return Decision(allowed=False, reason="feature_disabled")
    
    # 2. RBAC clássico — perfil tem essa ação?
    if not rbac.permits(user_id, action, tenant_id):
        return Decision(allowed=False, reason="rbac_denied")
    
    # 3. ABAC — atributos contextuais batem?
    if not abac.permits(user_id, action, resource, at_time):
        return Decision(allowed=False, reason="abac_denied", detail=...)
    
    # 4. Time-boxed — vínculo ainda válido?
    if not vinculo_vigente(user_id, perfil_id, at_time):
        return Decision(allowed=False, reason="vinculo_expirado")
    
    return Decision(allowed=True, reason="ok", audit_trail_id=...)
```

Sem esse ponto único, feature flag e RBAC podem divergir (feature desabilitada mas usuário tem permissão → confusão UX; admin tira permissão mas feature continua ativa → falsa segurança).

---

## Como funciona na prática — exemplo do RT emitindo certificado

**Cenário:** RT João Silva (CPF 123.456.789-00, acreditado RBC pra "balança industrial" e "termômetro") tenta emitir certificado de calibração de uma **balança hospitalar** (escopo que ele NÃO tem) num tenant onde ele é vinculado.

1. Frontend chama `POST /api/certificados/` com payload `{instrumento_id: "X", tipo: "balanca_hospitalar"}`
2. Middleware Django valida JWT → `user_id=João, tenant_id=Y`
3. View chama `auth_provider.can(user_id=João, action="certificado.emitir", resource={"tipo": "balanca_hospitalar"}, tenant_id=Y, purpose="execucao_contrato")`
4. `AuthorizationProvider`:
   - **Feature flag:** `metrologia.certificados.emitir` está habilitada pro tenant Y? ✅ sim
   - **RBAC:** perfil "RT acreditado" tem ação `certificado.emitir`? ✅ sim
   - **ABAC — escopo acreditado:** consulta `metrologia/licencas-acreditacoes` → escopo atual do João é `["balanca_industrial", "termometro"]`; `"balanca_hospitalar"` NÃO está → ❌ bloqueia
   - **Audit trail:** grava linha com `decision=denied`, `reason=escopo_fora_de_acreditacao`, `escopo_avaliado={"acreditado": [...], "solicitado": "balanca_hospitalar"}`
5. Retorna `403 Forbidden` com mensagem "Tipo de instrumento fora do escopo da sua acreditação RBC vigente"
6. Log do auditor de Segurança fica visível em `audit_trail.authz_decisions`

**Se a acreditação do João vencer amanhã:** evento `acreditacao.vencida` invalida o cache Redis; próximo `can()` consulta tabela atualizada; passa a bloquear até `certificado.emitir` em todos os tipos (não só hospitalar).

**Se um auditor RBC visitante tentar acessar dados às 23h após o prazo de auditoria que terminou às 18h:** vínculo `valido_ate` já passou → bloqueia silenciosamente.

**Se o parceiro marketplace tentar acessar dados de um tenant que não está na lista dele:** `auth_usuario_perfil` não tem linha pra esse tenant → bloqueia.

---

## Cross-tenant — como o RLS aguenta usuário em N tenants

Hoje o middleware ADR-0002 faz `SET LOCAL app.tenant_id = '<um único uuid>'`. Quebra pra parceiro marketplace que precisa ver N tenants.

**Mudança proposta:** middleware passa a setar **lista** de tenants permitidos:

```sql
SET LOCAL app.tenant_ids = '<uuid1>,<uuid2>,<uuid3>';
```

E as policies RLS passam de:

```sql
USING (tenant_id = current_setting('app.tenant_id')::uuid)
```

Pra:

```sql
USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
```

**Impacto:** ~50 policies RLS precisam ser regeradas (script SQL). Comportamento existente (1 tenant) continua funcionando — só passa a aceitar N tenants.

**Defesa em profundidade mantida:** mesmo com a lista, role `app_user` continua `NOBYPASSRLS`. Não há brecha.

**Auditor 2 da auditoria de 10 agentes alertou:** esta mudança é **bloqueante** pra qualquer feature cross-tenant (marketplace, portal cliente matriz+filiais). Wave A não usa, mas Wave B sim.

---

## Por que NÃO Casbin/OPA/Oso/Keycloak/Auth0 — pelo menos por enquanto

A auditoria às cegas (Auditor I — Segurança) foi explícita:

> "Não usar Casbin/OPA/Oso pra V1. Django já faz RBAC em 3 linhas. OPA adiciona outra linguagem (Rego) + overhead deploy. Oso é mais elegante mas perde acompanhamento automático do Django. Defesa em profundidade Django + RLS já elimina >99% dos riscos; Casbin seria defesa #3 desnecessária."

Detalhamento:

| Ferramenta | Por que NÃO agora | Quando reconsiderar |
|---|---|---|
| **Casbin** | Linguagem própria de policy (Rego-like); pool agente IA menor; ferramenta a mais pra manter | Quando matriz superar 50.000 células ou houver requisito de policy-as-code formal pra auditoria externa |
| **OPA (Open Policy Agent)** | Daemon separado (overhead deploy); Rego é linguagem nova pros agentes; latência adicional ~5-20ms por decisão | Quando precisar de policy unificada cross-stack (Django + microsserviços + Kafka + S3) |
| **Oso** | Boa elegância, mas perde integração automática com Django ORM; comunidade menor | Se algum dia migrar pra microsserviços (Wave C) |
| **Keycloak** | Servidor pesado (PostgreSQL dedicado + JVM); over-engineering pra 1-50 tenants; LGPD/ICP-Brasil exige tuning extra | Quando 1.000+ tenants com SSO corporativo (SAML/OIDC) virar requisito |
| **Auth0 / Clerk / WorkOS** | Pago por usuário (~R$ 0,99-2,99/usuário/mês) → inviável em 5k usuários; soberania de dados (LGPD) fica fora do BR | Reconsiderar nunca pra Aferê — modelo de negócio não comporta |

**Reabrir esta ADR** se: matriz > 50k células, requisito de policy externa, microsserviços, SAML/OIDC pra cliente farma TOP, ou se latência média de `can()` ultrapassar 30ms p95 com cache Redis ativo.

---

## Alternativas consideradas

### 1. Manter `django.contrib.auth` espalhado (status quo) — REJEITADA
**Atrativo:** zero novo código de infra.
**Rejeitada porque:** auditor 8 mostrou que 16 perfis × 48 módulos × 5 ações = 3.840 células, ingerenciável sem ponto único. Bug regulatório garantido em < 6 meses.

### 2. Subir Casbin desde o dia 1 — REJEITADA
**Atrativo:** policy-as-code formal, escalável.
**Rejeitada porque:** linguagem extra (CASBIN expression), pool agente IA menor, complexidade desnecessária em 1-50 tenants. Auditor I (segurança) vetou explicitamente.

### 3. OPA com daemon separado — REJEITADA
**Atrativo:** padrão moderno cloud-native.
**Rejeitada porque:** overhead operacional (mais 1 container), latência por chamada externa, Rego é linguagem nova. Wave A não precisa.

### 4. Keycloak self-hosted — REJEITADA
**Atrativo:** SSO, MFA, federação out-of-the-box.
**Rejeitada porque:** JVM + PostgreSQL dedicado pesa no VPS KVM 4 ano 1; complexidade alta de configuração. `django-allauth + django-otp` cobre os requisitos atuais (MFA TOTP, social opcional).

### 5. Espalhar regra em decorators (`@require_perfil("RT")`) — REJEITADA
**Atrativo:** sintaxe leve, fica no view.
**Rejeitada porque:** agentes IA não rastreiam direito decorators encadeados (auditor J — DDD/spec — explicitamente vetou "decorator stack"); regras viajam pra serializer, queryset, signal sem coordenação. Ponto único na porta resolve.

### 6. Construir RBAC + ABAC mas SEM porta (direto na lógica de view) — REJEITADA
**Atrativo:** menos abstração.
**Rejeitada porque:** mata anti-corrosion. Quando precisar trocar pra Casbin (Wave C), reescreve 200 lugares. Porta + adapter custa 200 linhas a mais agora, economiza meses depois.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Ponto único vs decorators espalhados | Ponto único (porta) | Auditoria, troca de implementação, ABAC contextual |
| Casbin/OPA agora vs Django built-in | Django built-in | Auditor I/8 convergiram; complexidade injustificada |
| Cache Redis vs decisão a cada request | Cache 5min com invalidação por evento | Latência <10ms p95 com cache; 50-200ms sem |
| RLS com 1 tenant vs lista de tenants | Lista de tenants (mudança em ADR-0002) | Cross-tenant marketplace/portal exige; defesa em profundidade mantida |
| Audit trail síncrono vs assíncrono | Síncrono (mesma transação que a decisão) | LGPD + 21 CFR Part 11 exigem garantia forte |
| ABAC com atributos plug-in vs tudo hardcoded | Plug-in via `@authz_attribute` registry | Cada módulo registra atributo dele sem mexer no core |

---

## Consequências

### Positivas
- **Toda decisão de autorização cai num único ponto auditável** — fiscalização LGPD/ANPD/Cgcre vira "exporte `audit_trail.authz_decisions` filtrado"
- **Refatorar não desestabiliza** — perfil novo entra como linha em `auth_perfil`, ação nova entra como linha em `auth_perfil_acao`; código de domínio não muda
- **Cross-tenant resolvido** sem furar RLS (parceiro marketplace, portal cliente matriz+filiais)
- **Time-boxed nativo** — auditor RBC visitante, contratos temporários, trial de novo tenant
- **ABAC contextual extensível** — cada módulo registra atributos próprios (`@authz_attribute("acreditacao_vigente")`) sem mexer no core
- **Feature flags unificadas** — uma única decisão pra "esse usuário, nesse tenant, com essa feature ativa, pode fazer essa ação?"
- **Anti-corrosion preservado** — quando precisar trocar pra Casbin/OPA (Wave C+), troca implementação atrás da porta, domínio fica intacto

### Negativas
- **Latência adicional ~5-10ms por request** (com cache Redis) — aceitável pra ERP; mensurável em Grafana
- **Audit trail cresce ~1-2 KB por request** — em 5k tenants × 100 req/min cada = 500 GB/ano. Mitigação: retenção 1 ano quente em PG + frio em B2 WORM
- **Mudança em RLS (lista de tenants)** exige regenerar ~50 policies — script SQL automatizável mas requer cuidado
- **Cache invalidation é complexa** — eventos `acreditacao.vencida`, `treinamento.expirado`, etc precisam ser confiavelmente publicados pelos módulos; outbox pattern (ADR-0011) mitiga
- **ABAC plug-in adiciona uma forma sutil de dependência cruzada** — atributo registrado por módulo A pode ser usado por módulo B; risco de "atributo sumiu, autorização quebra"; mitigação: contrato versionado em `domain/authz/atributos.yaml`

---

## Itens a fazer (consequência operacional desta ADR)

### Bloqueantes antes de Foundation F-B (auth + RBAC)
- [ ] **`docs/arquitetura/autorizacao-convencoes.md`** — convenções pra criar perfil novo, ação nova, atributo ABAC novo; padrão de chamada de `AuthorizationProvider.can()` em views/serializers/tasks
- [ ] **Atualizar `docs/arquitetura/anti-corrosion-layer.md`** — adicionar porta `AuthorizationProvider` formal
- [ ] **Atualizar `REGRAS-INEGOCIAVEIS.md`** — adicionar `INV-AUTHZ-001` (toda decisão passa pela porta), `INV-AUTHZ-002` (audit trail síncrono obrigatório), `INV-AUTHZ-003` (RLS lista de tenants obrigatório)
- [ ] **Hook pre-commit em `.claude/hooks/`** — `authz-check.sh` que rejeita merge se algum endpoint Django novo não chamar `AuthorizationProvider.can()`
- [ ] **Schema das 4 tabelas** (`auth_perfil`, `auth_perfil_acao`, `auth_usuario_perfil`, `audit_trail.authz_decisions`) + migration
- [ ] **Migration RLS** — regerar ~50 policies pra suportar lista de tenants

### Bloqueantes antes de Wave A começar
- [ ] **Implementação inicial da porta** (`infrastructure/authz/django_authorization_provider.py`) com os 16 perfis previstos
- [ ] **Cache Redis com invalidação por evento** — outbox pattern (ADR-0011) consome
- [ ] **Atributos ABAC iniciais:** `acreditacao_vigente`, `treinamento_matriz_competencia`, `limite_estorno_perfil`, `filial_hierarquia_usuario`, `escopo_documento_cliente`
- [ ] **Testes E2E** — cada um dos 16 perfis com cenário positivo + cenário negativo (escopo fora, vínculo expirado, feature desabilitada)
- [ ] **Dashboard Grafana** — taxa de decisões `denied`, top reasons, latência p95 do `can()`

### Bloqueantes antes de Wave B (marketplace + portal cliente cross-tenant)
- [ ] **Validação cross-tenant em produção** — fuzzing automático: usuário com acesso a 3 tenants tenta ver dados de tenant 4 → bloqueia
- [ ] **UI de "trocar tenant ativo"** — pra parceiro marketplace, portal cliente matriz+filiais
- [ ] **Drill de incidente** — simular vazamento cross-tenant; medir tempo de detecção via audit trail

---

## Critérios de reversão (quando esta ADR é revisitada)

| Sinal | Resposta |
|---|---|
| Latência p95 do `can()` ultrapassar 30ms (com cache Redis) | Investigar índices em `auth_*`; se persistir, considerar migrar pra Casbin/OPA com cache em processo |
| Matriz `auth_perfil_acao` ultrapassar 50.000 células | Considerar policy-as-code formal (Casbin/OPA); reabrir ADR |
| Cliente farma TOP exigir SAML/OIDC enterprise | Adicionar Keycloak como adapter de AuthN (não AuthZ — AuthZ continua na porta) |
| ABAC plug-in virar pesadelo de coordenação | Centralizar atributos num registry versionado + revisão obrigatória de PR pra adicionar atributo novo |
| Audit trail crescer mais que 1 TB/ano | Migrar trail antigo pra B2 WORM mais agressivamente (retenção quente cai de 1 ano pra 90 dias) |
| Cross-tenant abrir brecha (vazamento detectado) | Investigar imediato; se RLS lista de tenants for a causa, considerar voltar pra "1 tenant por sessão + UI de troca" com perda de UX mas ganho de segurança |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita porta única `AuthorizationProvider` + Django/RLS como implementação inicial
- [ ] **Auditor de Segurança:** confirma defesa em profundidade (hook → middleware → porta → RLS); valida que cross-tenant não cria brecha
- [ ] **Auditor de Qualidade:** confirma cobertura E2E dos 16 perfis (positivo + negativo por perfil)
- [ ] **Tech-lead substituto:** confirma viabilidade de cache Redis com invalidação por evento; latência <10ms p95 alcançável

---

## Referências

- ADR-0001 — Stack (Django + `django-allauth` + `django-otp` escolhidos)
- ADR-0002 — Multi-tenancy (RLS + middleware tenant_id) — esta ADR estende
- ADR-0006 — Feature flags (esta ADR unifica decisão com flags)
- ADR-0007 — Camada domínio + gerador spec→código (porta `AuthorizationProvider` é padrão hexagonal)
- ADR-0010 — Estratégia de tela (UI de troca de tenant ativo pra cross-tenant)
- ADR-0011 — Banco analítico/BI (audit trail consumido por BI; role admin separada)
- Auditoria 10 agentes 17/05/2026 — Auditor 8 (RBAC pra 48 módulos × 16 perfis) — CRÍTICO
- Auditoria às cegas 17/05/2026 — Auditor I (Segurança) confirmou Django + RLS como suficientes, sem Casbin/OPA
- `docs/dominios/suporte-plataforma/modulos/acesso-seguranca/` (módulo que implementa esta ADR)
- `REGRAS-INEGOCIAVEIS.md` — INV-TENANT-001..004, INV-AGENT-001, INV-AUTHZ-001..003 (a criar)
