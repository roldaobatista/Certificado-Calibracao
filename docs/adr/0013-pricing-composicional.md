# ADR-0013 — Modelo de pricing composicional pra billing-saas (planos flexíveis com componentes)

> **Status:** **PROPOSTA** (17/05/2026, madrugada). Cobre exigência explícita do Roldão: "preço por conjunto de módulos, por quantidade de usuários, adicional por usuário, vários tipos de configurações". Substitui o modelo de pricing simples (preço fixo mensal/anual) da v1 do modelo de domínio do `billing-saas`.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Roldão sinalizou diretamente (sessão 17/05/2026 madrugada) que o modelo atual (`Plano.preco_mensal` + `Plano.preco_anual` + `Plano.limite_usuarios` simples) **não cobre** os cenários comerciais que ele quer suportar.
> **Depende de:** ADR-0001 (stack — Django), ADR-0002 (multi-tenancy — assinatura é por tenant), ADR-0006 (feature flags — módulos liberados vinculam ao plano), ADR-0012 (autorização — limite contratado vira regra de autorização).
> **Bloqueia:** US-BIL-009 (operador cria/edita plano com componentes), US-BIL-010 (cálculo composicional de fatura), implementação do módulo `billing-saas`.

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Plano** | "Pacote comercial" que você vende. Ex: "Starter", "Pro", "Enterprise". Cada um tem suas regras de preço. |
| **Componente de preço** | "Peça" que monta o preço total do plano. Igual ingredientes de uma receita. Plano = soma dos componentes. |
| **Base fixa** | Valor que sempre é cobrado todo mês, independente de quantos usuários ou de quanto usa. Ex: R$ 200/mês de "mensalidade base". |
| **Faixa de usuários** | "Degraus" de preço por quantidade. Ex: 1-5 usuários = R$ 100, 6-15 = R$ 250, 16+ = R$ 500. |
| **Adicional por usuário (overage)** | "Vai além do incluso, paga extra". Ex: plano inclui 5 usuários, cada usuário a mais = R$ 40/mês. |
| **Bundle de módulos** | "Quais módulos vêm dentro do plano". Plano Starter = só OS + Calibração. Plano Pro = adiciona Fiscal + Financeiro. |
| **Add-on** | "Módulo extra avulso". Cliente do plano Starter quer Fiscal? Paga R$ 150/mês a mais e ativa o módulo. |
| **Cobrança por uso (metered)** | "Paga conforme usa". Ex: incluso 100 NFS-e/mês, cada uma a mais = R$ 0,80. Cliente que emite 130 NFS-e paga 30 × R$ 0,80 = R$ 24 extras. |
| **Desconto por volume** | "Quanto mais usa, mais desconto". Ex: acima de 50 usuários, 10% de desconto no total. |
| **Snapshot do plano** | "Foto" do plano no momento que o cliente contratou. Se você mudar o preço do plano amanhã, **o cliente continua pagando o preço da foto** (preço não retroage — INV-026). |
| **Trial** | Período grátis pra cliente testar antes de pagar. Já existia no modelo antigo, continua. |

---

## Contexto

A v1 do modelo de domínio do `billing-saas` (cravada em 17/05/2026 noite) modelou `Plano` como:

```
Plano:
  - codigo (A/B/C/D)
  - preco_mensal: Money
  - preco_anual: Money
  - limite_usuarios: int
  - limite_volume: int (ex: nº OS/mês)
  - modulos_liberados: list[str]
  - duracao_trial_dias: int
```

Esse modelo **funciona** se você vende 4 planos fechados (A/B/C/D) com preço único e limite fixo de usuários. Mas Roldão pediu cenários que esse modelo **não comporta**:

1. **"Preço por conjunto de módulos"** — Plano Starter (OS + Calibração), Plano Pro (Starter + Fiscal + Financeiro), Plano Enterprise (Pro + BI + Marketplace). Bundles diferentes.
2. **"Preço por quantidade de usuários"** — 1-5 usuários = R$ X, 6-15 = R$ Y, 16+ = R$ Z. Faixas (tiers), não preço único.
3. **"Adicional por usuário"** — Plano inclui 5 usuários, cada usuário a mais cobra valor extra (overage per-seat).
4. **"Vários tipos de configurações"** — pode incluir add-ons avulsos (cliente do Starter compra módulo Fiscal isolado), cobrança por uso (R$ 0,80 por NFS-e acima de 100/mês), descontos por volume (acima de 50 usuários, 10% off).

Cenários reais de SaaS B2B brasileiro que isso cobre:
- **Bling:** plano por porte (MEI / PME / Empresa) com módulos diferentes
- **Conta Azul:** plano base + módulos opcionais (Folha, Loja Virtual)
- **PipeRun / RD Station:** preço por usuário com faixas + add-ons
- **Asaas / SuperLógica:** mensalidade base + cobrança por uso (R$ por boleto emitido)

A v1 não comporta nenhum desses cenários sem hack.

---

## Decisão

Adotar **modelo de pricing composicional**: cada `Plano` é composto por **uma lista de `ComponentesPrecificacao`**, cada componente tem um tipo (base, faixa, overage, bundle, addon, uso, desconto). Fatura mensal é calculada agregando todos os componentes aplicáveis ao tenant naquele ciclo.

### Os 7 tipos de componente

| # | Tipo | Pra que serve | Exemplo |
|---|---|---|---|
| 1 | **`ComponenteBase`** | Mensalidade fixa do plano | R$ 200/mês fixo |
| 2 | **`ComponenteFaixaUsuarios`** | Preço escalonado por quantidade de usuários | 1-5 = R$ 100, 6-15 = R$ 250, 16+ = R$ 500 |
| 3 | **`ComponenteAdicionalUsuario`** | Overage per-seat após N inclusos | Inclui 5, cada extra = R$ 40 |
| 4 | **`ComponenteBundleModulos`** | Quais módulos vêm inclusos | Calibração + Certificados + OS + Fiscal |
| 5 | **`ComponenteAddon`** | Módulo opcional avulso | Marketplace = R$ 150/mês extra |
| 6 | **`ComponenteUsoVariavel`** | Cobrança por uso acima do incluso | 100 NFS-e inclusas, extra = R$ 0,80/un |
| 7 | **`ComponenteDesconto`** | Desconto automático por volume/ciclo | Acima de 50 usuários, -10% no total. Anual = -15% no total. |
| 8 | **`ComponenteExtensaoMarketplace`** (V2/V3 — ADR-0055) | Cobrança de extensão de parceiro + revenue share | Extensão "Balança Rodoviária" = R$ 50/mês; Aferê fica com 30%, desenvolvedor 70% |

**Combinação típica de um Plano "Pro" no Aferê (exemplo concreto):**

```yaml
plano: pro
componentes:
  - tipo: ComponenteBase
    preco_mensal: 350
    preco_anual: 3570    # 15% off no anual
  
  - tipo: ComponenteBundleModulos
    modulos: [os, calibracao, certificados, fiscal, contas-receber, caixa-tecnico]
  
  - tipo: ComponenteFaixaUsuarios
    faixas:
      - { de: 1, ate: 5, preco_por_usuario: 0 }      # 5 usuários inclusos na base
      - { de: 6, ate: 15, preco_por_usuario: 35 }
      - { de: 16, ate: null, preco_por_usuario: 25 } # ≥16 = preço cai (desconto progressivo)
  
  - tipo: ComponenteUsoVariavel
    recurso: nfse_emitidas
    unidade_inclusa: 100
    preco_por_unidade_extra: 0.80
  
  - tipo: ComponenteUsoVariavel
    recurso: whatsapp_enviados
    unidade_inclusa: 500
    preco_por_unidade_extra: 0.10
  
  - tipo: ComponenteAddon
    modulo: marketplace
    preco_mensal: 150
    opcional_no_checkout: true
  
  - tipo: ComponenteDesconto
    aplicavel_se: ciclo_anual
    desconto_percentual: 15

limites_duros:
  storage_gb: 50          # não cobra extra, bloqueia upload acima
  api_calls_dia: 100000
```

Fatura mensal de um cliente que tem esse Plano "Pro" + 8 usuários + 120 NFS-e + 300 WhatsApp + marketplace ativado:

```
ComponenteBase                     R$ 350,00
ComponenteFaixaUsuarios (8 user)   R$ 105,00  (3 usuários na faixa 6-15 × R$ 35)
ComponenteUsoVariavel (NFS-e)      R$  16,00  (20 extras × R$ 0,80)
ComponenteUsoVariavel (WhatsApp)   R$   0,00  (300 ≤ 500 inclusos)
ComponenteAddon (marketplace)      R$ 150,00
                                   ─────────
Subtotal                           R$ 621,00
ComponenteDesconto (anual?)        R$   0,00  (cliente em mensal)
                                   ─────────
TOTAL FATURA MENSAL                R$ 621,00
```

### Versionamento — preço não retroage (INV-026)

**Toda mudança em qualquer componente cria nova versão do plano.** Assinaturas existentes mantêm a versão contratada (snapshot). Novas assinaturas (a partir da data da mudança) usam a versão atual.

Exemplo:
- 2026-09-01: você publica Plano "Pro" v1 com ComponenteBase R$ 350.
- 2026-12-15: cliente A contrata Plano "Pro" v1 → assinatura A guarda `plano_versao = "pro@v1"`.
- 2027-03-10: você ajusta ComponenteBase pra R$ 400 → sistema cria automaticamente `pro@v2`.
- Cliente A continua pagando R$ 350 (sua assinatura tem snapshot v1).
- Cliente B (novo, contrata em 2027-04-01) paga R$ 400 (assinatura tem snapshot v2).

**Migração explícita:** se Roldão quiser que cliente A passe pra v2, gera comando `migrar_assinatura_pra_versao(cliente_a, "pro@v2", efetivo_em=proximo_ciclo)` — entra em histórico, cliente notificado, evento auditável.

### Limites duros vs cobrança extra

Há 2 tipos de limite:
- **Limite cobrado (overage):** estourou, sistema cobra extra. Exemplo: usuários adicionais, NFS-e adicionais. Cliente continua usando.
- **Limite duro (hard cap):** estourou, sistema bloqueia. Exemplo: storage acima de 50 GB → upload de novo PDF bloqueia. API calls acima de 100k/dia → rate limit.

Modelo permite ambos. Roldão escolhe qual recurso é qual no momento de montar o plano.

### Estrutura no modelo de domínio

```
Plano (raiz do agregado)
├── id, codigo, nome, descricao, ativo, ordem_exibicao
├── versao (semver: "pro@v3")
├── moeda
├── duracao_trial_dias (0 = sem trial)
├── ciclos_aceitos: [mensal, anual]
├── deprecado_em: datetime | null   # plano não some, apenas para de aparecer no checkout
└── componentes: ComponentePrecificacao [N]

ComponentePrecificacao (interface — 7 implementações)
├── id, plano_id, ordem
└── (campos específicos do tipo)

ComponenteBase
├── preco_mensal: Money
├── preco_anual: Money | null

ComponenteFaixaUsuarios
├── faixas: list[FaixaPreco { de, ate, preco_por_usuario }]
└── tipo_contagem: usuarios_ativos | usuarios_cadastrados | usuarios_logados_30d

ComponenteAdicionalUsuario
├── quantidade_inclusa: int
├── preco_por_usuario_extra: Money

ComponenteBundleModulos
├── modulos: list[str]   # ex: ["os", "calibracao", "fiscal"]

ComponenteAddon
├── modulo: str
├── preco_mensal: Money
├── preco_anual: Money | null
├── opcional_no_checkout: bool   # tenant pode adicionar sozinho?

ComponenteUsoVariavel
├── recurso: str   # "nfse_emitidas", "whatsapp_enviados", "ocr_processados"
├── unidade_inclusa: int
├── preco_por_unidade_extra: Money

ComponenteDesconto
├── aplicavel_se: enum (ciclo_anual, volume_acima_de_N_usuarios, cupom_X, periodo_promocional)
├── desconto_percentual: Decimal | null
├── desconto_valor_fixo: Money | null
├── parametro: dict   # ex: {volume_acima_de: 50}

ComponenteExtensaoMarketplace (V2/V3 — ADR-0055, achado G-MKT-3)
├── extension_id: str                   # FK MarketplaceExtension publicada
├── preco_mensal: Money                 # cobrado do tenant
├── percentual_afere: Decimal = 30      # Aferê retém
├── percentual_desenvolvedor: Decimal = 70  # repassado mensal via payout PIX D+30
├── opcional_no_checkout: bool = true

LimiteDuro
├── plano_id
├── recurso: str   # "storage_gb", "api_calls_dia"
├── valor_maximo: int
└── acao_ao_estourar: bloquear_imediato | bloquear_proximo_ciclo
```

### Fatura ganha breakdown

A entidade `FaturaSaaS` v1 tinha só `valor`, `desconto_total`, `valor_liquido`. Pra cliente entender de onde sai cada R$, v2 adiciona:

```
FaturaSaaS:
  - id, tenant_id, assinatura_id, numero, ciclo, data_emissao, data_vencimento
  - valor_bruto, descontos_total, valor_liquido
  - status (aberta/paga/falhou/estornada)
  - linhas: list[LinhaFatura]
  
LinhaFatura:
  - componente_origem: str    # "ComponenteBase", "ComponenteFaixaUsuarios", etc
  - descricao: str            # "Mensalidade base", "8 usuários na faixa 6-15", "20 NFS-e além das 100 inclusas"
  - quantidade: Decimal
  - preco_unitario: Money
  - subtotal: Money
```

Renderizada no PDF da fatura como tabela com linhas — cliente vê quanto está pagando por quê.

### Eventos de domínio adicionados

| Evento novo | Quando dispara | Pra que serve |
|---|---|---|
| `BillingSaas.PlanoCriado` | operador comercial Aferê publica plano novo | Auditor de Segurança valida; Notificações pra cadastrar no catálogo público |
| `BillingSaas.PlanoVersionado` | operador comercial Aferê edita plano existente → cria nova versão | Histórico imutável + notificação interna |
| `BillingSaas.ComponentePrecoMudou` | componente específico foi editado | Telemetria pricing; auditor produto verifica regras |
| `BillingSaas.AddonContratado` | tenant ativou addon | Auth provisiona; módulo liberado |
| `BillingSaas.AddonCancelado` | tenant desativou addon | Auth revoga; efeito no próximo ciclo |
| `BillingSaas.LimiteDuroAtingido` | tenant chegou no hard cap | Notifica tenant; bloqueia conforme `acao_ao_estourar` |
| `BillingSaas.UsoMedido` | uso medido pra cobrança variável | Agregado em fatura no fim do ciclo; alerta tenant em 80% do incluso |

---

## Onde isso liga com as ADRs existentes

| ADR | Conexão |
|---|---|
| **ADR-0006 (feature flags)** | `ComponenteBundleModulos` e `ComponenteAddon` ativam features. Sistema sincroniza: assinatura mudou → tabela `tenant_features` atualiza. INV-030 mantido (admin tenant não liga feature fora do plano). |
| **ADR-0012 (autorização)** | `AuthorizationProvider.can()` consulta plano contratado pra negar ação fora do bundle. Ex: tenant tenta emitir certificado sem módulo Certificados → bloqueia com `reason=modulo_nao_contratado`. |
| **ADR-0011 (BI 3 fases)** | MRR, ARR, churn por componente — métricas por tipo de componente entram nos dashboards. Painel-do-dono Roldão vê: receita base × receita variável × receita addon. |
| **ADR-0008 (fiscal pluggable)** | NFS-e da assinatura SaaS reflete o valor agregado da fatura (com breakdown nos serviços tributados). |
| **ADR-0005 (engine automações)** | `ComponenteDesconto` versionado usa o `RuleEngineProvider` (porta #14 na ACL) — regra "se ciclo=anual então -15%" é expressada como regra versionada. |
| **`anti-corrosion-layer.md` (porta #14 `RuleEngineProvider`)** | Cálculo de fatura usa essa porta pra avaliar componentes (cada componente é uma "regra"). |

---

## Como funciona na prática — 3 cenários

### Cenário 1 — Plano "Starter" (simples, pra ME/MEI)
```yaml
plano: starter
componentes:
  - ComponenteBase: { preco_mensal: 89 }
  - ComponenteBundleModulos: { modulos: [os, calibracao, certificados] }
  - ComponenteAdicionalUsuario: { quantidade_inclusa: 3, preco_por_usuario_extra: 25 }
limites_duros:
  - { recurso: storage_gb, valor_maximo: 10, acao_ao_estourar: bloquear_imediato }
```
Cliente paga R$ 89 fixo + R$ 25 por usuário acima de 3. Tem só 3 módulos. Storage limitado.

### Cenário 2 — Plano "Pro" (com faixas + uso variável + addon — exemplo completo acima)
Já mostrado acima.

### Cenário 3 — Plano "Enterprise" (faixa + desconto volume + tudo incluso)
```yaml
plano: enterprise
componentes:
  - ComponenteBase: { preco_mensal: 1500, preco_anual: 15300 }   # -15% no anual
  - ComponenteBundleModulos: { modulos: [TODOS_OS_48_MODULOS] }
  - ComponenteFaixaUsuarios:
      faixas:
        - { de: 1, ate: 25, preco_por_usuario: 0 }     # 25 usuários inclusos
        - { de: 26, ate: 100, preco_por_usuario: 50 }
        - { de: 101, ate: null, preco_por_usuario: 35 }
  - ComponenteDesconto: { aplicavel_se: ciclo_anual, desconto_percentual: 15 }
  - ComponenteDesconto: { aplicavel_se: volume_acima_de_N_usuarios, parametro: {volume_acima_de: 100}, desconto_percentual: 10 }
```
Cliente grande paga mensalidade alta mas tem todos os módulos e ganha desconto progressivo.

---

## Alternativas consideradas

### 1. Manter o modelo simples v1 (preço fixo + limites simples) — REJEITADA
**Atrativo:** menos código, mais fácil de implementar.
**Rejeitada porque:** não cobre os 4 cenários que Roldão pediu explicitamente. Forçaria 4 hacks no código (`if codigo == "enterprise": cobrar_diferente()` espalhado).

### 2. Usar Stripe Billing como fonte de verdade — REJEITADA
**Atrativo:** Stripe Billing tem tudo isso pronto (Products, Prices, Subscriptions, Usage Records, Tiers).
**Rejeitada porque:** lock-in forte; LGPD compromete (dado contratual sai do BR sem DPA aprovado); migração futura pra outro gateway (PagSeguro/MP) ficaria amarrada. Aferê precisa **dominar o modelo de pricing internamente** — Stripe vira só executor de cobrança, não fonte da verdade.

### 3. DSL declarativa em YAML versionada (sem entidades em PG) — REJEITADA
**Atrativo:** "plano é arquivo YAML"; sem migrations, sem ORM, sem complexidade.
**Rejeitada porque:** plano precisa ser versionado por tenant (snapshot na contratação), referenciado em fatura, auditável via WORM. YAML solto perde tudo isso. Modelo em PG + serialização YAML para input/export é o equilíbrio.

### 4. Pricing externo via Lago / Metronome / Orb — REJEITADA (re-avaliar V3)
**Atrativo:** ferramentas modernas focadas só em pricing (usage-based, tiered, hybrid).
**Rejeitada porque:** todas SaaS pagas (R$ 800-3000/mês fixo); LGPD compromete; over-engineering pra 1-50 tenants ano 1. **Reabrir se TAM superar 1.000 tenants OU pricing virar pesadelo manual.** Porta `PaymentGatewayProvider` (#11 na ACL) já abstrai cobrança; mover pricing pra Lago seria nova porta `PricingEngine` (não cabe agora).

### 5. Construir engine genérico de regras de pricing em vez de 7 tipos fixos — REJEITADA
**Atrativo:** "qualquer regra de preço futura cabe".
**Rejeitada porque:** abre brecha ANTI-11 (customização infinita); auditor de Segurança não consegue validar; agentes IA tropeçam em engine genérico. 7 tipos fixos cobrem 95% dos cenários SaaS B2B + se aparecer tipo 8 vira ADR.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Modelo simples (v1) vs composicional (v2) | Composicional | Roldão pediu explicitamente |
| Stripe Billing vs internal pricing | Internal | LGPD + lock-in + soberania |
| 7 tipos fixos vs engine genérico | 7 tipos | ANTI-11 + auditabilidade + previsibilidade pros agentes IA |
| Snapshot na contratação vs preço dinâmico | Snapshot | INV-026 (preço não retroage); Receita Federal exige rastreabilidade |
| Limite duro vs cobrança extra | Ambos (decisão por recurso) | Storage faz sentido bloquear; NFS-e faz sentido cobrar |
| Versionamento automático vs manual | Automático (toda mudança vira nova versão) | Sem versionamento agente erra; com versionamento histórico fica auditável |
| Breakdown na fatura vs valor único | Breakdown | Cliente B2B reclama de "fatura cega"; transparência reduz suporte |

---

## Consequências

### Positivas
- **Cobre 100% dos cenários comerciais** que Roldão listou + cenários de SaaS B2B típicos (Bling, Conta Azul, Pipedrive, Asaas)
- **Receita variável modelada** desde dia 1 — NFS-e, WhatsApp, OCR podem virar margem extra sem reescrever billing
- **Add-ons abrem upsell** — cliente Starter compra módulo Fiscal isolado sem upgrade total
- **Versionamento automático** — preço nunca retroage; Receita Federal fica feliz
- **Breakdown na fatura reduz suporte** — cliente vê de onde vem cada R$
- **ANTI-11 preservado** — 7 tipos fixos, sem código customizado por tenant

### Negativas
- **Modelo de domínio cresce ~3x** — 1 entidade `Plano` vira 9 (Plano + 7 ComponenteX + LimiteDuro + LinhaFatura)
- **Cálculo de fatura fica complexo** — não é `valor = plano.preco_mensal` mais; é função de N componentes
- **UI de "criar plano" exige tela dedicada** — Django Admin puro fica ruim com 7 tipos de componente; precisa wizard
- **Testes de cobrança multiplicam** — cada componente exige caso positivo + edge case (overage = exatamente 0, faixa de 1 usuário, addon ativado meio do ciclo)
- **Migração da v1 (se já tiver assinaturas em produção)** — não é o caso no MVP-1 (zero tenants pagos), mas ficar atento se cravar v1 antes da v2 entrar

### Negativas mitigadas
- "Cálculo complexo": isolado num único módulo `domain/billing_saas/calculadora.py` com testes exaustivos; resto do sistema não vê complexidade.
- "UI de criar plano": módulo `acesso-seguranca` + Django Admin cobre Wave A (Roldão monta no admin); tela dedicada vira US-BIL-009 explícita pra Wave B.

---

## Itens a fazer (consequência operacional desta ADR)

### Bloqueantes antes do MVP-1 começar
- [ ] **Atualizar modelo de domínio do billing-saas** com 7 componentes + LimiteDuro + LinhaFatura (esta sessão)
- [ ] **US-BIL-009** (operador comercial cria/edita catálogo de planos com componentes) — adicionada no PRD (esta sessão)
- [ ] **US-BIL-010** (sistema calcula fatura pelo agregado de componentes) — adicionada no PRD (esta sessão)
- [ ] **Atualizar entidade `Assinatura`** pra carregar snapshot do plano contratado (não só `plano_id` + `plano_versao`)
- [ ] **Atualizar entidade `FaturaSaaS`** pra ter lista de `LinhaFatura`
- [ ] **Atualizar US-BIL-002** (cobrança recorrente) pra usar nova lógica de cálculo

### Bloqueantes antes de Wave B (módulo billing-saas começar a ser construído)
- [ ] **`docs/dominios/financeiro/modulos/billing-saas/calculadora-fatura.md`** — algoritmo passo-a-passo de cálculo composicional, com exemplos e edge cases
- [ ] **Tela operador comercial Aferê** (Django + HTMX) — wizard com 7 passos (1 por tipo de componente), com simulação ao vivo de fatura exemplo
- [ ] **Hook `pricing-versioning`** — qualquer alteração em Plano dispara criação de versão nova automaticamente
- [ ] **Testes de cobrança** — pytest fixtures cobrindo 20+ cenários (incluindo edges: 0 usuários, exatamente no limite, addon ativado meio do ciclo, cupom + desconto volume + ciclo anual juntos)
- [ ] **Medição de uso variável** — instrumentar pontos de medição (`MeterUsoEvent` publicado em outbox quando NFS-e emite, WhatsApp envia, etc) — consumido pela `CalculadoraFatura`

### Atualizações em docs existentes
- [ ] **`docs/dominios/financeiro/modulos/billing-saas/modelo-de-dominio.md`** — refazer v2 (esta sessão)
- [ ] **`docs/dominios/financeiro/modulos/billing-saas/prd.md`** — adicionar US-BIL-009 + US-BIL-010 (esta sessão)
- [ ] **`AGENTS.md`** — adicionar ADR-0013 no índice (esta sessão)
- [ ] **`REGRAS-INEGOCIAVEIS.md`** — revisar INV-026 (preço não retroage) e INV-030 (feature flag não burla plano) pra incluir referência a componente

---

## Critérios de reversão (quando esta ADR é revisitada)

| Sinal | Resposta |
|---|---|
| 7 tipos não cobrem cenário comercial real que Roldão quer | Reabrir ADR e adicionar tipo 8 (com cuidado — cada tipo novo é manutenção crônica) |
| Roldão pedir customização de fórmula POR TENANT (ANTI-11) | NEGAR — usar o catálogo composicional. Se persistir, escalar pra revisão de ANTI-11 |
| Cálculo composicional ultrapassar 200ms p95 | Otimizar (memoização do snapshot; evitar consulta em runtime) — não é caso pra Lago/Metronome |
| TAM > 1.000 tenants com pricing virando pesadelo manual | Considerar Lago/Metronome via porta `PricingEngine` nova; modelo interno continua sendo fonte da verdade |
| Roldão precisar "preço sob medida" pra cliente farma TOP | Criar plano específico (não cabe customizar; cria entrada nova com componentes ajustados) |
| Fatura com breakdown gerar reclamação ("muito detalhado") | Esconder linhas com valor zero; agregar variáveis se cliente preferir |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita pricing composicional com 7 tipos de componente
- [ ] **Auditor de Produto:** confirma que 7 tipos cobrem cenários comerciais reais
- [ ] **Auditor de Segurança:** confirma que ANTI-11 preservado (sem customização por tenant)
- [ ] **Auditor de Qualidade:** confirma cobertura de testes pros 20+ cenários de cálculo

---

## Referências

- ADR-0001 — Stack (Django + PG)
- ADR-0002 — Multi-tenant (assinatura por tenant)
- ADR-0006 — Feature flags (módulos liberados sincronizados com plano)
- ADR-0008 — Fiscal pluggable (NFS-e da assinatura usa valor agregado)
- ADR-0011 — BI 3 fases (MRR/ARR/churn por componente)
- ADR-0012 — Autorização unificada (limite contratado vira regra de autorização)
- `docs/arquitetura/anti-corrosion-layer.md` (porta `RuleEngineProvider` #14 usada pelo cálculo de fatura)
- `docs/dominios/financeiro/modulos/billing-saas/prd.md` (US-BIL-001..010)
- `docs/dominios/financeiro/modulos/billing-saas/modelo-de-dominio.md` (v2 pós esta ADR)
- `REGRAS-INEGOCIAVEIS.md` — INV-026 (preço não retroage), INV-030 (feature flag não burla plano), INV-038 (plano em uso não deletável)
- Estudo de pricing B2B BR: Bling, Conta Azul, Asaas, SuperLógica, RD Station, PipeRun
