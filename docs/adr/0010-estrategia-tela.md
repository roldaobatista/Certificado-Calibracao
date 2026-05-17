# ADR-0010 — Estratégia de tela (UI): HTMX para o operacional, SPA isolada para 5 módulos visuais

> **Status:** **PROPOSTA** (17/05/2026, noite). Resolve achado da auditoria de 10 agentes (Auditor 3 — Frontend HTMX vs SPA) que apontou que HTMX puro **não cobre** Editor BPM, Portal Cliente, Marketplace, BI e Omnichannel. Decisão é "manter HTMX no núcleo, abrir 5 exceções controladas", não "trocar tudo por SPA".
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria 10 agentes da ADR-0001 v3 (17/05/2026 noite). Consenso 3 auditores (Frontend, Backend, Anti-corrosion) que ADR-0001 v2 deixou estratégia de tela ambígua entre HTMX (escolhido) e "outros casos" (não definidos).
> **Depende de:** ADR-0001 (stack) — não revoga, complementa.

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Tela** | Cada página/janela que o usuário enxerga |
| **HTMX** | Jeito moderno de fazer site interativo SEM precisar de muito JavaScript. O servidor (Django) manda pedaços de HTML prontos pro navegador, que troca só a parte que mudou. Funciona como "página tradicional ligeiramente mais esperta". |
| **Alpine.js** | Tempero de JavaScript leve em cima do HTMX — pra coisas que precisam responder na hora (abrir/fechar menu, mostrar/esconder campo, validar antes de enviar) |
| **SPA** | "Single-Page Application" — página que comporta como aplicativo (igual Gmail, Trello, Figma). O navegador baixa um app inteiro e roda quase tudo do lado do cliente. Visualmente mais moderno, mas mais pesado e mais complexo de fazer. |
| **Vue / React / Next.js** | Tecnologias pra construir SPA. Vue é o mais leve, Next.js é Vue/React com SEO embutido (importante pra Marketplace ser achado no Google) |
| **ECharts** | Biblioteca de gráficos que roda no navegador. Não é SPA — é "tempero gráfico" que cabe em HTMX |
| **Bundle** | "Pacote" de JavaScript que o navegador baixa. Quanto menor, mais rápido carrega. SPA tem bundle grande (centenas de KB), HTMX puro tem bundle pequeno (dezenas de KB) |
| **PWA** | Site que vira app no celular sem precisar de loja (App Store / Play Store). Cliente abre no navegador, clica "instalar" e fica como ícone na tela |

---

## Contexto

A ADR-0001 v2 escolheu **Django Admin + Jazzmin + HTMX + Alpine.js** pro frontend operacional, **Django templates + HTMX + Tailwind** pro portal cliente, **Flutter** pro mobile. Decisão foi tomada com **19 módulos previstos**.

A auditoria de 10 agentes (17/05/2026) auditou contra os **48 módulos atuais** e identificou que HTMX puro **não cobre adequadamente 5 módulos com UI rica**:

| Módulo | Tipo de UI exigida | Por que HTMX não dá conta |
|---|---|---|
| `suporte-plataforma/automacoes-bpm` | Editor visual drag-and-drop de workflow (canvas, mini-mapa, undo/redo) | Reatividade DOM pesada; estado client-side rico; HTMX é round-trip servidor |
| `comercial/portal-cliente` | Dashboard mobile-first, PWA, 60%+ tráfego mobile, expectativa de UX moderna do cliente externo (farma/RBC) | Cliente farma espera "Trello/Notion"; HTMX entrega "site dos anos 2010" — fricção real de percepção |
| `comercial/marketplace` | Vitrine pública (SEO obrigatório), carrinho, grid drag-drop de curadoria, paginação lazy de 100+ items, preview de plugin | Marketplace precisa de TTI rápido em 4G + SEO + experiência de e-commerce; HTMX é fraco em SEO de SPA-likes |
| `dados/bi` | Dashboards com gráficos interativos, drill-down, builder de relatórios | Render de gráficos não roda em HTMX puro (precisa JS) |
| `comercial/comunicacao-omnichannel` | Central de atendimento multi-canal em tempo real (chat ao vivo, distribuição por skill, reprocessamento com diff) | Real-time + estado complexo de atendimento ativo |

**Os outros 43 módulos** (OS, Calibração, Certificado, Fiscal, Estoque, CRM, Treinamentos, SST, Licenças, Caixa Técnico, Contas a Receber, Equipamentos, Acesso/Segurança, Chamados, Agenda, etc.) **continuam excelentes em HTMX** — são CRUDs operacionais, formulários, fluxos curtos com transições servidor-driven. É exatamente o caso de uso onde HTMX brilha.

---

## Decisão

Adotar **estratégia híbrida com 3 camadas claras**, no mesmo deploy Django (sem servidor separado, sem container extra):

### Camada 1 — Núcleo operacional (43 módulos) → HTMX + Alpine.js + Django templates

Inclui (lista não-exaustiva):
- Toda a Wave A operacional: `os`, `chamados`, `agenda`, `app-tecnico` (web complementar — o mobile é Flutter), `base-conhecimento`, `calibracao`, `certificados`, `licencas-acreditacoes`, `treinamentos`, `seguranca-trabalho`, `estoque`, `equipamentos`, `acesso-seguranca`, `clientes`, `orcamentos`, `fiscal`, `contas-receber`, `caixa-tecnico`.
- Toda a Wave B operacional: `garantia`, `projetos`, `crm`, `contratos`, `precificacao`, `sla-contratual`, `contas-pagar`, `comissoes`, `custeio-real`, `despesas`, `relatorios-financeiros` (a parte tabular; gráficos vêm da camada 2 via ECharts), `produtos-pecas-servicos`, `fornecedores`, `onboarding`, `configuracoes-sistema`, `engenharia-tecnica`, `gestao-documental`, `suporte-saas`, `release-management`, `colaboradores`, `qualidade`, `auditoria-externa`, `capacity-planning-operacional`.

**Stack:** Django templates + HTMX 1.x + Alpine.js 3.x + Tailwind CSS. Bundle alvo: ≤ 60 KB de JS gzipped por página.

### Camada 2 — Tempero gráfico em HTMX (sem virar SPA) → `dados/bi` e relatórios

`dados/bi` e qualquer painel com gráficos (incluindo `painel-do-dono`, `relatorios-financeiros`, `capacity-planning-operacional`, `comissoes` com simulação) usam **HTMX como casca + ECharts como lib de gráfico carregada por página**. Drill-down acontece via HTMX (request para `/bi/cubo/X?filtro=Y` → backend retorna fragmento HTML com gráfico atualizado).

**Stack:** Django templates + HTMX + ECharts 5.x. Sem framework SPA. Bundle de gráfico: ~150 KB gzipped (carregado só nas páginas que usam).

**Critério de saída pra Camada 3:** se BI exigir builder visual drag-drop de relatórios customizáveis (US-BI-016 em diante), reavalia migração pra SPA Vue 3 (decisão diferida pra Wave B; ADR nova).

### Camada 3 — SPA isolada (5 módulos) → Vue 3 / Next.js leve dentro do mesmo deploy

Cada módulo da lista abaixo tem **uma SPA própria**, construída como pasta `static/spa-<modulo>/` no projeto Django, servida pela mesma instância Gunicorn (não há container/servidor extra). API consumida é a mesma DRF do backend.

| Módulo | Tecnologia | Por quê | Bundle alvo (gzipped) |
|---|---|---|---|
| `suporte-plataforma/automacoes-bpm` | **Vue 3 + Vue Flow** | Editor visual de workflow — Vue Flow é a biblioteca de canvas drag-drop mais madura; Vue 3 é leve e tem pool grande de agentes IA | ≤ 200 KB |
| `comercial/marketplace` | **Next.js 14 (modo estático / SSG)** | Marketplace precisa SEO (Google indexar plugins/parceiros) + TTI rápido em 4G. Modo SSG gera HTML estático no build → roda em qualquer servidor estático, deploy no mesmo Gunicorn via proxy | ≤ 180 KB por rota |
| `comercial/portal-cliente` | **Next.js 14 (SSG + ilhas dinâmicas)** | Cliente externo, mobile-first PWA, expectativa UX moderna. SSG por padrão; partes dinâmicas (chat, status de OS) viram "ilha" React. Funciona offline mínimo via service worker | ≤ 180 KB por rota |
| `comercial/comunicacao-omnichannel` | **Vue 3 (admin SPA puro)** | Central de atendimento — admin operacional, sem necessidade de SEO. Vue 3 puro é mais leve que Next.js e tem ecossistema de UI components maduro (PrimeVue, Vuetify) | ≤ 160 KB |
| `dados/bi` (builder visual, diferido pra Wave B) | **Decisão diferida — provavelmente Vue 3** | Só ativa se demanda real de builder customizável aparecer. Wave A do BI fica em Camada 2 (HTMX + ECharts) | TBD |

**Restrição importante:** **nenhuma SPA é deploy separado**. Tudo roda no mesmo Gunicorn Django via:
- Pasta `static/spa-<modulo>/` com build production gerado por CI (`npm run build` → arquivos estáticos)
- Rota Django renderiza o `index.html` da SPA + Django serve estáticos via WhiteNoise (ou Traefik na produção)
- API consumida é a mesma `/api/v1/...` DRF

Não há container Next.js separado, não há Node em produção. Só durante o build (CI).

---

## Por que essa decisão vence pelo critério "negócio vence"

1. **Não bota Roldão pra aprender duas stacks novas.** 43 módulos seguem HTMX simples; 5 módulos têm SPA mas Roldão não opera essas telas (Marketplace é cliente externo + parceiros, Portal Cliente é cliente externo, BPM editor é admin operacional, Omnichannel é atendente, BI builder é Wave B). Roldão usa BI consumidor (Camada 2 — HTMX + ECharts), que é simples.

2. **Mantém Django como fonte de verdade.** Toda regra de negócio, autorização, multi-tenancy fica no Django. SPA só consome API. Nada de lógica de negócio em JavaScript.

3. **Custo agente IA controlado.** 90% do código que os agentes escrevem é Django + HTMX (território seguro, pool grande de exemplos). Vue 3 e Next.js têm pool grande também — não é tecnologia esotérica. SPA é minoria do esforço.

4. **Cliente externo vê UX moderna onde precisa.** Portal Cliente e Marketplace são as duas telas que clientes externos vão julgar primeiro. Não dá pra entregar "site dos anos 2010" pra cliente farma.

5. **NFS-e, A3, OS, Calibração, Certificado seguem em HTMX simples.** O núcleo regulatório do MVP-1 não muda de stack — risco de regressão zero.

---

## Como funciona na prática

### Estrutura de pastas (proposta)

```
projeto/
├── django/                           # backend único
│   ├── apps/                          # 48 apps Django
│   │   ├── os/                        # HTMX (templates + views)
│   │   ├── calibracao/                # HTMX
│   │   ├── automacoes_bpm/            # API DRF + serve index.html da SPA
│   │   ├── marketplace/               # API DRF + serve build Next
│   │   ├── portal_cliente/            # API DRF + serve build Next
│   │   ├── comunicacao_omnichannel/   # API DRF + serve index.html da SPA Vue
│   │   ├── bi/                        # HTMX + ECharts (Camada 2)
│   │   └── ...
│   ├── templates/                     # templates Django pra Camadas 1 e 2
│   └── static/                        # build das SPAs vai parar aqui
│       ├── spa-bpm/                   # build Vue produção
│       ├── spa-marketplace/           # build Next estático
│       ├── spa-portal-cliente/        # build Next estático
│       └── spa-omnichannel/           # build Vue produção
└── spas/                              # source-code das 4 SPAs (dev only)
    ├── bpm/                           # projeto Vue
    ├── marketplace/                   # projeto Next
    ├── portal-cliente/                # projeto Next
    └── omnichannel/                   # projeto Vue
```

### Pipeline de deploy

1. CI roda `npm run build` em cada `spas/<modulo>/` → gera `dist/` ou `out/`
2. CI copia output pra `django/static/spa-<modulo>/`
3. CI roda `python manage.py collectstatic`
4. `docker compose up -d` sobe Gunicorn que serve tudo
5. Traefik na frente faz cache de estáticos

**Nada de Node em produção. Nada de container Next/Vue separado.**

### Compartilhamento de autenticação

Todas as 5 SPAs herdam a sessão Django:
- Camada 1 (HTMX) usa cookie de sessão Django padrão (SameSite=Lax, `__Host-`)
- Camada 3 (SPA) também usa o mesmo cookie → SPA chama `/api/v1/...` com `credentials: include` → DRF autentica via SessionAuthentication
- Mobile (Flutter, fora desta ADR) usa SimpleJWT separado

Isso elimina lógica duplicada de login. Não há "login da SPA" diferente do "login do operacional".

---

## Alternativas consideradas

### 1. HTMX puro pra tudo (manter ADR-0001 v2 inalterada) — REJEITADA
**Atrativo:** stack única, agente IA escreve só Django + HTMX.
**Rejeitada porque:** Editor BPM drag-drop, Marketplace SEO, Portal Cliente PWA não cabem em HTMX sem hacks gigantes (custom JS solto, perde a vantagem de "menos JS"). Auditor 3 mostrou 3 casos concretos.

### 2. SPA pra tudo (React/Next.js fullstack, Django só API) — REJEITADA
**Atrativo:** UI consistente, framework único de frontend.
**Rejeitada porque:** custo de reescrever 43 módulos operacionais em SPA é enorme (3-6x mais código). Perde o ganho do Django Admin. Agente IA escreve mais JavaScript que Python → mais bug. Não há ganho de UX em OS/Calibração/Certificado/Fiscal — esses fluxos são tabulares, HTMX é melhor. Esta é a versão "TS fullstack" que a 1ª auditoria já reprovou.

### 3. SPA pra Marketplace + Portal Cliente; HTMX + Alpine pesado pros outros 3 (BPM, BI, Omnichannel) — REJEITADA
**Atrativo:** menos SPAs, menos coisa pra manter.
**Rejeitada porque:** editor BPM com Alpine é território onde "Alpine vira Vue mal feito" — vira mais código JS solto que Vue real. Omnichannel real-time precisa de WebSocket + estado complexo → Alpine também fica forçado. Melhor admitir 4-5 SPAs do que ter 3 SPAs "disfarçadas" de Alpine.

### 4. Flutter web pra todas as 5 telas — REJEITADA
**Atrativo:** reaproveita know-how de Flutter mobile.
**Rejeitada porque:** Flutter web adiciona ~30 MB de Chromium + dart2js → bundles obesos; Tailwind não roda nativo; SEO fraco (problema crítico pro Marketplace). Auditor 6 marcou explicitamente "NÃO fazer Flutter web".

### 5. Astro em vez de Next.js pro Portal Cliente / Marketplace — DIFERIDA
**Atrativo:** Astro é mais leve que Next.js, SEO nativo melhor.
**Diferida:** vale revisitar em Mês 4 quando começar a construir Portal Cliente. Pool de agente IA pra Next.js é maior que Astro hoje; decisão final na hora de codar.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Stack única (só HTMX) vs UI moderna onde precisa | Híbrida (HTMX + 4 SPAs) | 5 módulos não cabem em HTMX sem desfigurar |
| Vue vs React/Next em todas as SPAs | Misto (Vue 3 + Next.js) | Next.js só onde SEO importa (Marketplace, Portal Cliente); Vue 3 puro onde é admin SPA (BPM, Omnichannel) |
| Deploy separado (container Next) vs build estático servido pelo Django | Build estático servido pelo Django | Zero container extra, zero Node em produção, custo VPS não muda |
| SPA com router próprio vs SPA por módulo | SPA por módulo (4 builds independentes) | Cada módulo evolui sozinho; sem mono-build gigante; agentes IA tocam código por módulo |
| Roldão aprende SPA vs Roldão fica só no admin | Roldão fica só no admin/HTMX | Roldão não opera Marketplace/Portal/BPM/Omnichannel — quem opera são clientes externos, atendentes, e o próprio sistema |
| Tailwind em SPA e em HTMX vs CSS diferente | Tailwind em ambos | Mesmo design system; agentes IA conhecem; bundle Tailwind purged é pequeno |

---

## Consequências

### Positivas
- **Cliente externo (Portal + Marketplace) vê UX moderna** — sem fricção de "site velho" comprometer venda.
- **Editor BPM dá pra construir de verdade** — sem hack de Alpine virando Vue mal feito.
- **Núcleo operacional (43 módulos) segue simples** — HTMX é território seguro pra agentes IA.
- **Custo VPS não muda** — nada de container extra; só build estático.
- **Login único** — sessão Django serve todas as camadas.
- **SEO Marketplace funciona** — Next.js SSG indexa.

### Negativas
- **4 stacks de frontend (HTMX, Alpine, Vue 3, Next.js) em vez de 2.** Manutenção dispersa. Mitigação: cada SPA é isolada por módulo; agentes IA tocam uma de cada vez; convenções documentadas.
- **CI precisa rodar `npm install` + `npm run build`** pra 4 SPAs. Adiciona 3-5 min ao pipeline. Mitigação: cache de `node_modules` por SPA no GitHub Actions.
- **Agente IA precisa saber Vue 3 + Next.js além de Django.** Mitigação: pool de exemplos Vue/Next é grande; convenções rígidas (`docs/arquitetura/spa-convencoes.md` a criar).
- **Versionamento de SPA vs backend.** Quando API DRF muda, SPA precisa atualizar junto. Mitigação: contrato OpenAPI gerado a partir do DRF (ADR-0007) + tipos TypeScript gerados → quebra em compile time, não runtime.

---

## Itens a fazer (consequência operacional desta ADR)

### Bloqueantes antes de começar Wave A
- [ ] **`docs/arquitetura/spa-convencoes.md`** — convenções rígidas pras 4 SPAs (estrutura de pasta, padrão de chamada de API, gerenciamento de estado, autenticação, error boundary, tipos compartilhados).
- [ ] **`docs/arquitetura/htmx-convencoes.md`** — convenções pra Camada 1 e Camada 2 (quando usar HTMX puro, quando temperar com Alpine, quando carregar ECharts).
- [ ] **`docs/arquitetura/anti-corrosion-layer.md`** — adicionar porta `UIShell` (abstração mínima da fronteira HTML/SPA pra geração de spec).
- [ ] **`scripts/setup-spa.sh`** — comando único que cria nova SPA seguindo template (Vue ou Next.js) com tudo configurado.

### Bloqueantes antes de começar cada SPA
- [ ] **BPM (Wave B):** decidir entre Vue Flow e Drawflow.js; spike de 1 dia validando drag-drop com 50 nós + undo/redo.
- [ ] **Marketplace (Wave B/V2):** confirmar Next.js SSG ou avaliar Astro; decidir gateway de pagamento dele (split fee).
- [ ] **Portal Cliente (Wave B):** decidir nível de PWA (só "instalável" ou com offline real); confirmar Next.js ou Astro.
- [ ] **Omnichannel (Wave B):** decidir biblioteca de UI (PrimeVue vs Vuetify vs custom Tailwind).

### Atualizações em docs existentes
- [ ] **ADR-0001 v3:** adicionar referência cruzada pra esta ADR-0010. Reescrever parágrafo "Django Admin = você usa dia 1" pra "Django Admin = debug/config a partir da semana 2; UI operacional é HTMX/Alpine; 5 módulos visuais ricos têm SPA isolada — ver ADR-0010".
- [ ] **`docs/arquitetura/overview.md` (a criar):** code map mostrando onde mora cada camada.
- [ ] **`docs/faseamento-modulos.md`:** marcar quais módulos da Wave B vão precisar de SPA isolada (4 já listados aqui).

---

## Critérios de reversão (quando esta ADR é revisitada)

| Sinal | Resposta |
|---|---|
| Build Next.js/Vue estourar CI tempo > 10 min | Cache mais agressivo; se persistir, avaliar Astro (mais leve) |
| Bundle de SPA > 250 KB gzipped | Auditar dependências; trocar lib pesada; considerar code-split por rota |
| Cliente externo reclamar "Portal está lento" no 4G | Auditar lighthouse; otimizar imagens; considerar Astro |
| BPM editor exigir colaboração real-time (2 usuários editando juntos) | Reavaliar — pode precisar de Yjs/CRDT no canvas |
| BI builder customizável virar requisito real (não só consumidor) | Migrar BI da Camada 2 (HTMX + ECharts) pra Camada 3 (Vue 3 + ECharts) — ADR nova |
| Agentes IA produzirem mais bug em Vue/Next do que esperado | Reforçar convenções; spike-revisão; em último caso, simplificar SPA pra Alpine + ECharts |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita estratégia híbrida (HTMX núcleo + 4 SPAs isoladas)
- [ ] **Auditor de Qualidade:** confirma cobertura de testes para 4 stacks em CI
- [ ] **Auditor de Segurança:** confirma sessão Django compartilhada não cria brecha entre camadas
- [ ] **Tech-lead substituto:** confirma viabilidade de Vue 3 + Next.js convivendo no mesmo deploy

---

## Referências

- ADR-0001 — Stack técnica (esta ADR complementa)
- Auditoria 10 agentes 17/05/2026 noite — Auditor 3 (Frontend), Auditor 1 (Backend), Auditor 10 (Anti-corrosion layer)
- `docs/dominios/comercial/modulos/portal-cliente/prd.md`
- `docs/dominios/comercial/modulos/marketplace/prd.md`
- `docs/dominios/comercial/modulos/comunicacao-omnichannel/prd.md`
- `docs/dominios/suporte-plataforma/modulos/automacoes-bpm/prd.md`
- `docs/dominios/dados/modulos/bi/prd.md`
