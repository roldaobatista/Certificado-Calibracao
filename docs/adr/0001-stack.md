# ADR-0001 — Stack técnica do produto (candidata, revisão 2)

> **Status:** **CANDIDATA — não final** (17/05/2026, noite). Direção provisória: Django + Flutter + PostgreSQL. Cravada como definitiva só após passar nos **3 portões de validação** descritos abaixo.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Histórico:**
> - **v1 (17/05 tarde):** recomendava TypeScript fullstack — **reprovada** pela 1ª auditoria de 10 agentes (Auditor 10 identificou viés grave: otimização pela conveniência do agente IA, não pelo valor pro negócio).
> - **v2 (17/05 noite):** pivotou pra Django + Flutter aplicando o critério "negócio vence" ([[feedback_negocio_sobre_agente]]).
> - **2ª auditoria de 10 agentes (17/05 noite):** confirmou Django + Flutter como tecnicamente correto MAS apontou 8 ressalvas novas — principal: **aceitar stack antes de fechar discovery (sintese-final.md vazia) é "founder is customer" virando real**. Daí o status mudar pra CANDIDATA.
> **Origem:** Aud-22 da auditoria 12 agentes — "ADR-0001 stack técnica bloqueia spike F-1". Bloqueia também Foundation F-A..F-H.
> **Depende de:** ADR-0000 (uso de IA) — todas as decisões aqui respeitam as 5 regras de lá.

---

## Validação progressiva — 3 portões obrigatórios

Esta ADR não é aceita como "final" enquanto os 3 portões abaixo não passarem. Se qualquer um falhar, a ADR reabre — isso é feature, não bug.

### Portão 1 — Discovery fechada (bloqueia F-A)
Antes de qualquer linha de código de produto:
- [ ] `docs/discovery/sintese-final.md` fechada com ICP + MVP-1 + 3 cartas de intenção de clientes externos (não-Roldão)
- [ ] Onda 1 de 5 entrevistas anti-Roldão concluída
- [ ] 20 telefones quentes listados (Aud-18)
- [ ] R-001 (founder is customer) score caiu de 20 pra ≤9 com evidência

### Portão 2 — Decisões técnicas derivadas (bloqueia F-A)
4 ADRs novas + 1 doc arquitetural escritas e aprovadas:
- [x] **ADR-0002 multi-tenancy** — schema-shared + middleware tenant_id + RLS + roles NOBYPASSRLS + wrapper Celery ✅ proposta (17/05/2026)
- [x] **ADR-0007 camada de domínio + gerador spec→código** — pipeline spec PT → YAML → Django+Pydantic+OpenAPI+Dart ✅ proposta (17/05/2026)
- [x] **ADR-0008 fiscal pluggable** — interface `FiscalProvider` agnóstica de país (BR/AR/MX); PlugNotas 1ª impl + Focus NFe smoke trimestral ✅ proposta (17/05/2026)
- [x] **ADR-0009 onde A3 assina** — A3 sempre cliente-side via Web PKI Lacuna; A1 server-side com KMS ✅ proposta (17/05/2026)
- [x] `docs/arquitetura/anti-corrosion-layer.md` — 9 portas (Fiscal, Signature, LLM, Storage, Hosting, Auth, Queue, Sync, MultiTenant) ✅ criado (17/05/2026)
- [x] `REGRAS-INEGOCIAVEIS.md` — INV-TENANT-004 + INV-AGENT-001 adicionadas ✅ (17/05/2026)
- [ ] Aprovação do Roldão nas 4 ADRs + ACL — pendente

### Portão 3 — Spike F-1 cravado + drills cronometrados (bloqueia MVP-1)
- [ ] **Spike F-1 com escopo recortado** (não Foundation completa) — só Django + DRF + PG + RLS + pytest. Mobile, fiscal, LLM em spikes irmãos. 4-6 semanas máx.
- [ ] **Critério de mortalidade falsificável:** ≤2 intervenções de código/semana do Roldão, ≤3 bugs SEV-1 em prod, token cap R$ 1.500/spike. Se falhar, dispara plano B (tech-lead consultivo R$ 8-15k/mês) — NÃO reverte pra TS.
- [ ] **Taxonomia de bug obrigatória por commit** (`lang | spec-drift | hipotese-produto | infra | seguranca`) — sem isso, falha de F-1 vira discussão religiosa (Parecer 3).
- [ ] **1 drill obrigatório mensal antes do 1º tenant pago** (auditoria 17/05/2026 reduziu de 4 → 1):
  - Restore pgBackRest em provedor B testado
- [ ] **Outros 3 drills disparam quando 5 tenants pagos ativos:**
  - Failover KMS sa-east-1 → us-east-1
  - Swap fiscal PlugNotas → Focus (smoke test)
  - Cross-tenant canary com fuzz concorrente
- [ ] **5 ativos contratuais/operacionais** (Parecer 8): DPO designado, playbook ANPD 3 dias úteis, seguro cyber + RC profissional, on-call não-solo (sucessor digital), hash-chain audit com `tenant_id` em cada linha + WORM

**Se passar nos 3 portões:** ADR-0001 vira definitiva. Se falhar em qualquer um: reabre com aprendizados documentados.

---

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Stack** | Conjunto de ferramentas/linguagens com que o sistema é feito (igual "linha de produção") |
| **Backend** | Parte que roda no servidor (processa regras; não aparece pro usuário) |
| **Frontend** | Parte que aparece na tela do usuário |
| **Banco de dados** | Onde ficam guardados todos os dados |
| **Framework** | "Esqueleto" pronto de programação |
| **ORM** | Tradutor entre código e banco |
| **Admin** | Telas de "gerenciar tabela" automáticas (Django gera de graça — você usa direto pra cadastrar tenant, criar usuário, ajustar configuração sem esperar tela bonita) |
| **RLS** | Trava no banco que impede tenant A enxergar dados de tenant B |
| **Offline-first** | App de celular que funciona sem internet e sincroniza depois |
| **Celery** | Robô que executa tarefas pesadas em segundo plano (enviar e-mail, gerar PDF, etc) |
| **HTMX** | Jeito moderno de fazer site interativo sem precisar de muito JavaScript |
| **PAdES-LTV** | Padrão de assinatura PDF que continua válido por anos (ISO 17025 exige) |

---

## Por que a v1 (TypeScript fullstack) foi reprovada

Auditoria de 10 agentes em 17/05/2026 identificou que a v1 escolheu stack pelo critério "agentes IA erram menos nessa stack" — mas isso é conveniência do agente, não valor pro Aferê. Roldão corrigiu: *"o que adianta tecnologia que o agente é melhor, mas é ruim pro negócio?"*

Aplicando "negócio vence":

| Critério de negócio | TS fullstack (v1) | Django + Flutter (v2) |
|---|---|---|
| NFS-e até 01/09/2026 (deadline duro) | Libs Node rasas; risco vermelho | Libs Python maduras (`nfelib`, `pynfe`, `erpbrasil.edoc`); via SaaS BR também |
| Certificado A3 ICP-Brasil | Sem lib Node madura pra PKCS#11; bloqueador real | `python-pkcs11` + `pyhanko` resolvem |
| PAdES-LTV (ISO 17025) | `node-signpdf` não cobre LTV | `pyhanko` gera PAdES-LTV nativo, open source |
| Admin pra Roldão mexer dia 1 | Construir do zero (6-12 meses) | Django Admin grátis na hora |
| Offline mobile robusto | React Native + WatermelonDB (médio) | Flutter + drift (objetivamente superior) |
| Ecossistema fiscal BR | Raso | Maduro (10+ anos de ERP brasileiro em Python) |
| Custo de tokens LLM | Mais código escrito = mais token | Django "bateria incluída" = menos código = menos token |
| Agentes IA erram menos | TS vence | Django perde (mitigável via plano B) |

7 critérios de negócio em 8 vão pra Django+Flutter. O único critério em que TS ganhava era de conveniência do agente — não vale o trade-off regulatório.

---

## Contexto (4 decisões fundadoras do Roldão 17/05/2026)

1. **Onde o usuário abre:** navegador (Chrome/Edge) no PC + aplicativo no celular.
2. **Offline robusto obrigatório:** técnico fecha OS, fotografa lacre/selo INMETRO, coleta assinatura, registra leitura de balança sem sinal.
3. **Quem programa:** agentes IA (Claude Code + Codex CLI) supervisionados pelo Roldão. Modelo 100% agentes. Plano B (tech-lead consultivo R$ 8-15k/mês) dispara se LEAP F-1 falhar.
4. **Orçamento ano 1:** Hostinger VPS KVM 4 já contratado + Backblaze + KMS + free tiers. Auditor 8 alertou estouro previsto no Mês 12 (R$ 9k em vez de R$ 1.5k) — exige cota agregada de tokens LLM (corrigida nesta v2).

Restrições herdadas do Discovery:
- Multi-tenant SaaS com isolamento duro (INV-TENANT-001/002/003 + R-001 score 20).
- Spec-as-source (D2): spec PT → código gerado.
- Foundation F-A..F-H precisa de: multi-tenant + RLS, RBAC, mobile shell, WhatsApp BSP, hooks CI, devcontainer.
- ADR-0000 regra #1: todo chamado LLM passa por LiteLLM (abstração).

---

## Decisão

Adotar **Python (Django) + Dart (Flutter) + PostgreSQL** rodando em Docker Compose no VPS Hostinger.

### Componentes escolhidos

| Camada | Escolha | Por quê em 1 linha |
|---|---|---|
| **Backend** | Django 5.x LTS + Django REST Framework | Admin grátis (Roldão mexe dia 1); ORM maduro pra ERP; ecossistema fiscal BR robusto |
| **API spec** | drf-spectacular (OpenAPI 3) | Spec-as-source (D2) gera schema OpenAPI auto a partir dos serializers; Flutter consome via gerador |
| **Banco** | PostgreSQL 16+ com RLS | RLS nativo (INV-TENANT-003 + SEC-TENANT-001); JSONB pra configurações de tenant |
| **Multi-tenant** | Schema compartilhado + middleware `tenant_id` + RLS PG | Auditor 2 vetou schema-per-tenant pra 100-5000 tenants; ADR-0002 detalha |
| **Filas/jobs** | Celery + Redis | Padrão indústria; PDF/email/sync em background; Redis volta (vale o container) |
| **Cache** | Redis (mesmo container do Celery) | Sessions Django + cache de queries pesadas |
| **Auth** | django-allauth + django-otp (MFA TOTP) + SimpleJWT pro mobile | Admin pronto, MFA nativo, session management testado em milhões de instalações; elimina auth caseiro (Auditor 6 crítico) |
| **Frontend admin/operacional** | Django Admin + Jazzmin (skin moderno) + HTMX + Alpine.js | Você mexe direto desde dia 1; telas operacionais ganham interatividade sem SPA pesada |
| **Frontend portal cliente** | Django templates + HTMX + Tailwind | Cliente final baixa certificado, abre chamado, vê histórico — não precisa SPA |
| **Mobile** | Flutter 3.x + drift (SQLite ORM) + Riverpod | Offline mais maduro que RN; foto/câmera/GPS robustos; UI consistente Android+iOS |
| **Sync mobile** | API REST DRF + drift + estratégia per-entidade | Conflict resolution definido em ADR-0005 (regra por entidade: OS = last-write-wins com fila humana; foto = append-only; estoque = transação atômica) |
| **Validação** | DRF serializers + Pydantic v2 nos boundaries críticos | Tipos derivados da spec PT (D2); brand type `UntrustedInput[T]` pro pipeline LLM |
| **Fiscal NFS-e** | PlugNotas (SDK Python oficial) | Auditor 5 crítico: cobertura nacional + ADN + variações municipais; deadline 01/09/2026 viável |
| **Assinatura PDF** | pyhanko (PAdES-LTV nativo, ICP-Brasil) | Open source; atende ISO 17025 + INV-017 carimbo do tempo ITI |
| **Certificado A1/A3** | `python-pkcs11` (A3 token) + `cryptography` (A1) — orquestrado pelo backend; opção Web PKI Lacuna pro perfil A se token específico do cliente não tiver driver | Lib madura Python; A3 viável |
| **LLM gateway** | LiteLLM self-hosted (rede Docker isolada — Auditor 6) | Atende ADR-0000 regra #1; switchover provider em horas |
| **Container** | Docker Compose | Pool de exemplos alto pros agentes; K8s overkill no VPS single |
| **CI/CD** | GitHub Actions → SSH → `docker compose up -d` | Trivial; sem dependência de SaaS pago de pipeline |
| **IaC servidor** | Ansible playbook único | Reprodutibilidade; Auditor 7 exige antes do 1º tenant pago |
| **Observabilidade** | OpenTelemetry → Grafana Cloud + Axiom + B2 (WORM logs longos) | Vendor-neutro; retenção 7 anos via B2 (Auditor 7) |
| **WORM (PDFs + audit)** | Backblaze B2 Object Lock — **região EU Central** (não US) | Cliente farma exige BR-compat; EU + DPA é o mais próximo (Auditor 5) |
| **Crypto crítica** | AWS KMS **Multi-Region Key (MRK)** primária sa-east-1 + replica us-east-1 — não cópia manual, ciphertext portável entre regiões sem recriptografar (correção pós-3ª auditoria 17/05/2026 — Auditor 7 alertou que "replica" sem MRK significa recriptografar tudo em fallback) | SPOF criptográfico mitigado de verdade |
| **Backup PG** | pgBackRest (PITR contínuo) → B2 criptografado com chave em KMS | RPO ≤ 15min, restore mensal testado (Auditor 6 + 7) |
| **Email transacional** | Resend (free 3k/mês → Pro depois) | SPF/DKIM/DMARC ok |
| **WhatsApp BSP** | A definir em ADR-0004 (Z-API ou Meta direto) | Volume MVP cabe em Z-API básico |

### Topologia no VPS Hostinger KVM 4

```
VPS Hostinger SP (4 vCPU / 16GB / 200GB NVMe)
└── Docker Compose
    ├── traefik (proxy reverso + SSL Let's Encrypt + rate limit)
    ├── postgres-16 (banco principal — volume persistente, WAL → pgBackRest)
    ├── redis-7 (cache + Celery broker)
    ├── web (Django + Gunicorn — 3 workers, atrás de Traefik)
    ├── worker-default (Celery workers — fila comum)
    ├── worker-pdf (Celery dedicado — geração PDF + assinatura, CPU-bound isolado)
    ├── beat (Celery beat — cron de lembretes recalibração)
    ├── litellm (gateway LLM — REDE DOCKER ISOLADA, sem credenciais DB)
    └── otel-collector (telemetria → Grafana Cloud + Axiom + B2)

Externos:
├── Backblaze B2 EU Central (PDFs + audit chain + logs longos) — WORM Object Lock
├── AWS KMS sa-east-1 + replica us-east-1 (chaves: assinatura, hash chain, JWT, backup key)
├── PlugNotas (NFS-e — SDK Python via REST)
├── Resend (email transacional)
├── Grafana Cloud + Axiom (observabilidade ativa, 14-30 dias)
└── Anthropic + OpenAI/Google (LLMs via LiteLLM)
```

---

## Por que essa stack vence pelo critério "negócio vence"

1. **Django Admin = você usa dia 1.** Cadastrar tenant, criar usuário, ajustar permissão, ver tabela de OS, exportar CSV — tudo pronto sem esperar agente terminar tela. Economiza 6-12 meses comparado a "admin construído na mão".
2. **Ecossistema fiscal BR maduro.** PlugNotas + pyhanko + python-pkcs11 + comunidade ERP Python brasileira de 10+ anos. Deadline 01/09/2026 NFS-e fica viável.
3. **Flutter ganha em offline robusto.** Persona Bruno (técnico campo) precisa: foto legível de selo INMETRO em condições ruins, sync de 14 fotos/OS via 4G fraco, render PDF, assinatura. Flutter + drift + flutter_vision_camera entrega; RN + WatermelonDB ficou em "talvez".
4. **django-allauth + django-otp** elimina auth caseiro (maior risco de OWASP A07 segundo Auditor 6). Lib testada em milhões de instalações.
5. **Multi-tenant maduro:** `django-multi-tenant` (Citus) + middleware + RLS PG é padrão indústria pra schema compartilhado escalável.
6. **Menos código escrito = menos tokens de LLM.** Django entrega pronto: admin, ORM, signals, migrations, allauth, DRF. Cada feature consome menos token (Auditor 8 — estoque estimado).
7. **Stack roda no VPS KVM 4 confortavelmente.** Memória estimada: PG 4GB + Redis 1GB + Gunicorn 1.5GB + 2 workers Celery 1GB + Traefik 0.2GB + LiteLLM 1GB + OTel 0.3GB = ~9GB com folga.

---

## Alternativas consideradas

### 1. TypeScript fullstack (NestJS + React + RN) — **proposta v1, REPROVADA**
**Atrativo:** linguagem única, agentes IA cometem menos erros nessa stack.
**Rejeitada porque:** otimizar pra conveniência do agente é viés de orquestrador (Auditor 10 grave). NFS-e + A3 + PAdES-LTV em TS = território raso, deadline regulatório em risco. Sem admin grátis = 6-12 meses construindo. **Esse é exatamente o trade-off errado.**

### 2. Rails + Hotwire
**Atrativo:** stack ERP-classic, convenção forte, Hotwire elimina SPA. Pool de devs BR existe.
**Rejeitada porque:** ecossistema fiscal BR Ruby é menor que Python; pyhanko (assinatura PAdES-LTV) não tem equivalente Ruby maduro; agentes IA tem pool muito maior em Django que em Rails (esse argumento é tiebreaker, vale aqui).

### 3. Java/Kotlin + Spring Boot
**Atrativo:** iText (PAdES-LTV gold standard), maduro em compliance, libs fiscais BR robustas.
**Rejeitada porque:** JVM apertada em VPS KVM 4; verbosidade alta = mais tokens; agentes IA produzem código verboso em Spring; ecossistema Python no BR é maior pra ERP (Bling, Tiny e similares).

### 4. PHP + Laravel
**Atrativo:** hospedagem barata, dev BR abundante, Filament Admin compete com Django Admin.
**Rejeitada porque:** ecossistema fiscal BR PHP existe mas é mais fragmentado; pyhanko não tem equivalente PHP maduro; agentes IA produzem mais bug em PHP (typing fraco).

### 5. Stack híbrida (Django backoffice + Node/Go pra microsserviços)
**Atrativo:** Django pra ERP + serviço dedicado pra cálculo de incerteza ou parser SEFAZ.
**Adiada:** começar mono-stack Django; quebrar em microsserviço só quando dor real (premissa YAGNI).

### 6. React Native em vez de Flutter pro mobile
**Atrativo:** linguagem única se backend fosse TS; mas backend é Python.
**Rejeitada porque:** sem o argumento "mesma linguagem do back", Flutter ganha objetivamente em offline + foto + UI consistente (Auditor 3 já marcava Flutter como superior).

---

## Mitigações pro LEAP F-1 (modelo 100% agentes)

Auditor 1 + Auditor 10 alertaram que Django é território onde agentes IA erram um pouco mais que TS. **Mitigações concretas:**

1. **Spike F-1 com critério de mortalidade explícito** — 2 sprints construindo módulo Estoque + módulo OS simples em Django. Gate: Roldão intervém ≤ 2x/semana, ≤ 3 bugs em produção. Se falhar, dispara plano B (tech-lead consultivo R$ 8-15k/mês).
2. **Pin Django 5.0 LTS** (não 5.1 ou 5.2) — pool de exemplos no treinamento dos agentes maior na LTS estável.
3. **Convenções rígidas documentadas em `docs/arquitetura/django-convencoes.md`** — estrutura de apps, naming, layered architecture, signals proibidos por default (override explícito), uso de `select_related`/`prefetch_related` obrigatório em querysets de lista.
4. **Lint Python pesado:** ruff (formatter + linter) + mypy strict + bandit (segurança) + django-upgrade. CI bloqueia merge.
5. **Test pyramid:** pytest-django + factory-boy (factories padronizados) + pytest-cov ≥ 80% por app. Playwright pra E2E.
6. **Spec → código gerado:** `cookiecutter-django` modificado + scaffold próprio que gera app Django a partir da spec PT (D2). Agentes complementam, não criam do zero.
7. **Code review obrigatório por agente auditor 2** (Família 5 qualidade) — todo PR passa.

---

## Correções dos 10 auditores incorporadas

| # | Auditor | Correção aplicada |
|---|---|---|
| 1 | Stack-fit | Pin Django 5.0 LTS; convenções rígidas; scaffold; lint pesado |
| 2 | Multi-tenant | Middleware obrigatório `tenant_id` thread-local + RLS + role `app_user` NOBYPASSRLS + role `app_migrator` separada |
| 2 | Multi-tenant | Wrapper obrigatório `run_in_tenant(tenant_id, fn)` pra Celery tasks; teste de fuzzing concorrente |
| 2 | Multi-tenant | INV-TENANT-004 nova: role do app criada com NOBYPASSRLS; hook valida |
| 3 | Mobile offline | Flutter dev-build desde dia 1 (não managed); `flutter_camera` com perfil de captura calibrado; compressão client-side ≤1MB; upload chunked com retry |
| 3 | Mobile offline | ADR-0005 sync strategy escrita antes de F-D; regra de conflict resolution por entidade |
| 3 | Mobile offline | Render PDF certificado no backend (Celery worker dedicado), não mobile |
| 4 | Performance | Spike F-1 inclui benchmark carga sintética 50 tenants antes de cravar VPS |
| 4 | Performance | Worker Celery dedicado pra PDF (CPU-bound isolado); índices compostos `(tenant_id, ...)` em todas FKs |
| 4 | Performance | Cloudflare na frente (free tier) — ganho TTI cliente em 4G fraco |
| 5 | Compliance | PlugNotas como BaaS fiscal (SDK Python); ADR-0008 fiscal só formaliza |
| 5 | Compliance | pyhanko pra PAdES-LTV (open source, ICP-Brasil); ITI carimbo do tempo via REST |
| 5 | Compliance | Backblaze B2 EU Central pra WORM (cliente farma BR-compat) |
| 6 | Segurança | django-allauth + django-otp em vez de auth caseiro |
| 6 | Segurança | LiteLLM em rede Docker isolada, sem credencial DB, allowlist egress |
| 6 | Segurança | `UntrustedInput[T]` brand type Pydantic pro pipeline LLM (segregação ADR-0000 regra #5) |
| 6 | Segurança | RBAC global deny-by-default + decorator `@public` explícito; teste E2E enumera rotas |
| 6 | Segurança | Backup PG criptografado com chave KMS (não texto plano em B2) |
| 6 | Segurança | Trivy + Semgrep + OSV + gitleaks no CI, bloqueia High/Critical |
| 6 | Segurança | Rate limiting (`django-ratelimit`) em login/reset; CSRF default Django; cookies `__Host-` SameSite=Lax |
| 6 | Segurança | SSL pinning Flutter (técnico em rede WiFi cliente) |
| 7 | Operação/DR | pgBackRest PITR contínuo → B2; restore mensal cronometrado; RTO ≤ 4h / RPO ≤ 15min |
| 7 | Operação/DR | Matriz de alertas definida (PG down / fila travada / cert SSL <7d / B2 backup falhou); dispara WhatsApp + e-mail |
| 7 | Operação/DR | On-call: Roldão + bot escalação (mesmo solo, documentado); sucessor digital + cofre |
| 7 | Operação/DR | KMS replica us-east-1; janela manutenção mensal declarada (migration breaking) |
| 8 | Custo | **Cota agregada LLM teto R$ 800/mês ano 1** com circuit breaker antes da cota por tenant disparar |
| 8 | Custo | Revisão Mês 6 com gatilho: token > R$ 600 → migra tarefas baixa complexidade pra Haiku/Sabiá |
| 8 | Custo | IRRF 15% + IOF 3,5% sobre remessas exterior orçados (Anthropic, AWS, Grafana, Axiom) |
| 8 | Custo | Certificado A1 ICP-Brasil orçado (~R$ 300/ano) |
| 9 | Débito futuro | Anti-corrosion layer obrigatório: porta/adapter pra auth, queue, LLM gateway, sync mobile, multi-tenant — agentes nunca importam direto |
| 9 | Débito futuro | ADR-0002 multi-tenancy escrita antes de F-A (não promessa) |
| 10 | Viés | Esta v2 aplica o critério "negócio vence" — [[feedback_negocio_sobre_agente]] |
| 10 | Viés | LEAP F-1 com critério de mortalidade falsificável; spike F-1 mede também custo do "admin Roldão se fosse construído na mão" como contraprova |

**Total: 33 correções incorporadas.**

---

## Consequências

### Positivas
- **Roldão usa Django Admin desde a primeira semana** — não depende de tela pronta pra cadastrar/configurar/auditar.
- **Risco regulatório dramaticamente menor** — NFS-e, A3, PAdES-LTV têm caminho conhecido.
- **Custo de tokens LLM menor** — Django escreve menos código próprio (admin, allauth, signals, ORM, migrations entregam pronto).
- **Comunidade ERP BR robusta** — quando precisar contratar tech-lead consultivo (plano B), pool de devs Python brasileiros é gigante.
- **Stack envelhece bem** — Django existe há 20 anos, Postgres tem 30, Flutter é forte (Google) — todas com horizonte 10+ anos (Auditor 9).

### Negativas
- **Agentes IA produzem mais bug em Django+Flutter que em TS-fullstack** — não dramático, mas mensurável. Mitigação: convenções rígidas + scaffold + plano B armado.
- **2 linguagens (Python + Dart)** — contexto cognitivo pros agentes dobra parcialmente vs TS único. Aceitável trade-off pelo ganho de negócio.
- **Web admin/operacional não é SPA moderna** — HTMX + Alpine não é o futuro brilhante. Mas atende. Migrar pra SPA depois é trabalho linear.
- **Celery + Redis** = 2 containers a mais que procrastinate (Python; pg-boss é Node, correção pós-3ª auditoria 17/05/2026). Vale: ecossistema maduro.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Agente erra menos (TS) vs negócio entregue (Django) | Django | "Negócio vence" — [[feedback_negocio_sobre_agente]] |
| Linguagem única vs admin grátis | Admin grátis (Django) | 6-12 meses economizados; trade-off invertido vs v1 |
| Flutter vs RN | Flutter | Sem "mesma linguagem do back", offline robusto vence |
| Auth caseiro vs django-allauth | django-allauth | OWASP A07 #1; agentes IA não deveriam fazer crypto-auth |
| procrastinate (Python; pg-boss é Node, correção pós-3ª auditoria 17/05/2026) (1 container) vs Celery+Redis (2) | Celery+Redis | Maturidade vale 1 container |
| SPA moderna vs HTMX | HTMX | Menos JS = menos coisa pra agente errar; migrar depois |
| BaaS fiscal (PlugNotas) vs construir | PlugNotas | Deadline 01/09/2026 não permite construir |
| Build próprio assinatura vs SaaS | pyhanko (open source) | Vence porque é open source — sem custo recorrente |

---

## Critérios de reversão (quando esta ADR é revisitada)

| Sinal | Resposta |
|---|---|
| LEAP F-1 falhar (Roldão intervém >2x/semana ou >3 bugs prod em sprint) | Disparar plano B: tech-lead Python consultivo R$ 8-15k/mês. **NÃO** reverter pra TS. |
| TAM real > 5.000 tenants em 2028 | Migrar `schema-shared + RLS` pra `schema-per-tenant` ou DB-per-tenant. Anti-corrosion layer já protege. |
| Offline Flutter provar inviável no F-D | Revisitar Flutter version + drift; **não** voltar pra RN (foi rejeitado por mérito). |
| Custo operacional > R$ 3.000/mês no MVP | Reavaliar fornecedores e plano Hostinger. |
| Anthropic abrir região BR | Remover sanitização agressiva da regra #2 ADR-0000 — opcional. |
| Lei BR de IA (PL 2338/2023) virar lei | Reavaliar regra #2 e fluxo dados. |
| Django LTS sair (5.0 → 5.2 em 2027) | Upgrade controlado em janela de manutenção; sem reescrita. |

---

## Itens a fazer (consequência operacional desta ADR)

### Bloqueantes ANTES de F-A (Foundation começar)
- [ ] **ADR-0002 multi-tenancy** — schema-shared + middleware tenant_id + RLS + roles + wrapper Celery
- [ ] **ADR-0003 mobile técnico campo** — Flutter dev-build + offline + auth biométrica
- [ ] **ADR-0004 hospedagem e DR** — RTO/RPO + pgBackRest + replica KMS + on-call
- [ ] **ADR-0005 sync mobile** — conflict resolution per-entidade
- [ ] **ADR-0006 auth e RBAC** — django-allauth + django-otp + MFA + 4 perfis + permissões módulo
- [ ] **ADR-0008 fiscal** — formalizar PlugNotas + assinatura + ITI
- [ ] **`docs/arquitetura/django-convencoes.md`** — convenções rígidas pros agentes
- [ ] **`docs/arquitetura/anti-corrosion-layer.md`** — porta/adapter pra auth, queue, LLM, sync, multi-tenant
- [ ] **`docs/arquitetura/overview.md`** — code map + entry points
- [ ] **`.devcontainer/`** — D4
- [ ] **F-G hooks+CI** — ruff + mypy + bandit + django-upgrade + Trivy + Semgrep + OSV + gitleaks + pytest

### Atualizações em docs existentes
- [ ] **REGRAS-INEGOCIAVEIS.md** — adicionar INV-TENANT-004 (NOBYPASSRLS) + INV-AGENT-001 (UntrustedInput type)
- [ ] **ARQUITETURA.md** — preencher status com link pra esta ADR
- [ ] **memory `project_hosting.md`** — atualizar de Fastify pra Django + Celery (memory antigo está desatualizado)

### Spike F-1
- [ ] **Spike F-1 com critério de mortalidade explícito** — 2 sprints; módulo Estoque + módulo OS simples; gate Roldão ≤ 2x/sem intervenção + ≤ 3 bugs prod

---

## Revisão

Revisão obrigatória se:
- Qualquer critério de reversão acima disparar.
- Nova decisão fundadora do Roldão mudar premissa.
- ADR-0000 (uso de IA) for revisada.
- Auditoria de 10 agentes (a repetir antes do MVP-1 fechar) identificar novo viés ou risco crítico.

Caso contrário, revisão anual junto com `painel-do-dono.md`.

---

## Aprovação

- [x] **Roldão (decisor):** aceita Django + Flutter + PostgreSQL como **direção CANDIDATA**, sujeita aos 3 portões — aprovado 17/05/2026
- [ ] **Portão 1 (discovery fechada):** ICP + MVP-1 + 3 cartas de intenção — pendente
- [ ] **Portão 2 (4 ADRs filhas + ACL expandido):** ADR-0002, 0007, 0008, 0009 + anti-corrosion layer — pendente
- [ ] **Portão 3 (spike F-1 + drills):** F-1 verde + 4 drills cronometrados verdes + 5 ativos contratuais — pendente
- [ ] **Auditor 4 (governança):** confirma ADR-0000 respeitada — pendente
- [ ] **Auditor 5 (qualidade):** confirma TST-001..004 compatíveis — pendente
- [ ] **Auditor 10 (anti-viés 2ª rodada):** confirma que esta v2 + 3 portões corrigiu os 8 achados novos — pendente
