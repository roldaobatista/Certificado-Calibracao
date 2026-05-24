---
adr: 0057
titulo: Acessibilidade WCAG 2.1 nível AA — checklist binária obrigatória por tela
status: aceito
data-decisao: 2026-05-23
decisor: roldao
contexto-marco: Onda 2 plano-v2 (saneamento pré-Marco 3 Fase 5)
relacionados:
  - docs/adr/0010-estrategia-tela.md
  - docs/adr/0018-scanner-qr-pwa.md
  - docs/CONVENCOES-DOC.md
  - REGRAS-INEGOCIAVEIS.md
---

# ADR-0057 — Acessibilidade WCAG 2.1 nível AA

## Status

**ACEITO** em 2026-05-23. Originalmente reservada pelo plano-v2 da Onda 0 (auditor PROD apontou ⛔ CRÍTICO: "a11y na Onda 5 é tarde demais — Wave A inteira nasce sem contrato, retrofit custa 5-10x mais"). Antecipada para Onda 2 e aceita antes do Marco 3 Fase 5 implementar telas.

## Contexto

Auditor de produto da auditoria projeto-inteiro (Onda 0 plano-v2) detectou que **acessibilidade não tem contrato mecânico** no projeto:

- Única menção a WCAG: 1 linha solta no PRD `equipamentos` §9 NFR.
- ADR-0010 (estratégia de tela HTMX + 5 SPAs isoladas) **não menciona a11y**.
- ADR-0018 (scanner QR em PWA) **não menciona a11y**.
- Nenhum hook valida a11y em PRD nem em código.
- Nenhum invariante `INV-A11Y-*` em REGRAS-INEGOCIÁVEIS.md.

Risco real:

1. **Tenant farma / órgão público:** Lei Brasileira de Inclusão (Lei 13.146/2015 — LBI art. 63) + Decreto 9.094/2017 + Decreto Federal sobre Acessibilidade em Sítios da União exigem WCAG AA para sistemas que atendem público interno de órgão público. Tenant farma com cliente final acessando portal cliente também cai na LBI.
2. **Calibração ISO 17025 cl. 6.2.3:** "pessoal deve ter competência para usar os recursos" — inclui RT/técnico com deficiência. Sistema inacessível = pessoal sem condição operacional = NC potencial em auditoria CGCRE.
3. **Custo de retrofit:** experiência conhecida do mercado mostra retrofit de a11y em sistema pronto custa 5-10x do que nascer certo. Wave A vai gerar ~20 telas; retrofit estimado em 4-8 sprints só pra a11y se entrar como dívida.

## Decisão

**Adotar WCAG 2.1 nível AA como contrato binário obrigatório por tela, com checklist em PRD + hook validador + invariantes em REGRAS.**

### Cláusulas obrigatórias

#### INV-A11Y-001 — Todo input tem label acessível

Todo `<input>`, `<textarea>`, `<select>` em template HTMX ou componente SPA tem:

- `<label for="id">` associado, OU
- `aria-label="…"` explícito, OU
- `aria-labelledby="…id"` apontando para elemento com texto.

Hook `a11y-checklist-spec.sh` valida que PRD novo declara explicitamente esta cláusula como AC. Validação em runtime (axe-core no E2E) fica em F-C3 da Foundation F-C quando suite E2E entrar.

#### INV-A11Y-002 — Navegação por teclado funcional

Toda ação acionável por mouse é acionável por teclado:

- `Tab` percorre todos os controles em ordem lógica.
- `Enter`/`Space` ativa botão e link.
- `Esc` fecha modal/dropdown.
- Modal tem **trap de foco** (Tab cicla dentro do modal; foco não sai pra background até fechar).
- Botões não-`<button>` (ex: `<div onclick>`) são proibidos — usar `<button type="button">` ou `<a>` com `role="button"`.

#### INV-A11Y-003 — Contraste mínimo 4.5:1 (texto normal) / 3:1 (texto grande)

Texto normal (até 18pt regular ou 14pt bold) tem contraste mínimo 4.5:1 contra fundo. Texto grande tem 3:1. Componentes de UI (borda de input, ícone clicável) têm 3:1 mínimo.

Tokens de design no `tailwind.config.js` (ou equivalente Wave A) declaram explicitamente quais combinações foreground/background estão validadas. Hook `tailwind-a11y-tokens.sh` fica como GATE-A11Y-2 (entra quando Tailwind ou design system aparecer em Wave A).

#### INV-A11Y-004 — Foco visual sempre visível

`*:focus-visible` declarado globalmente. **Proibido** `outline: none` sem substituto explícito. Foco em link/botão/input tem outline ou border com contraste ≥3:1.

#### INV-A11Y-005 — Erro de formulário anunciado a leitor de tela

Quando validação de formulário falha (HTMX swap inline ou re-render):

- Container de erro tem `role="alert"` ou `aria-live="assertive"`.
- Input com erro tem `aria-invalid="true"` + `aria-describedby="id-erro"` apontando para mensagem.
- Mensagem de erro tem texto humano descrevendo o problema (não só ícone vermelho).

#### INV-A11Y-006 — Texto alternativo para imagem informativa

Toda `<img>` tem `alt="…"`:

- Imagem informativa (logo cliente, foto técnico) → `alt="descrição funcional"`.
- Imagem decorativa → `alt=""` (vazio, não ausente) + `role="presentation"`.
- Imagem com texto embutido → texto repetido em `alt`.

Equivalentes: `<svg>` tem `<title>` ou `aria-label`; ícone fonte (`<i class="icon-…">`) tem `aria-hidden="true"` + texto adjacente OU `aria-label`.

#### INV-A11Y-007 — Heading hierárquico

Template tem hierarquia de `<h1>` → `<h2>` → `<h3>` sem pular nível. Cada página/tela tem exatamente 1 `<h1>`. Hook `a11y-checklist-spec.sh` valida que PRD declara hierarquia esperada.

#### INV-A11Y-008 — Mensagem de erro sem oracle de enumeração (toca SEC-LOG-001)

Em fluxo de autenticação/recuperação, mensagem de erro **NÃO** revela se conta existe. Aliás, é a mesma regra do `SEC-LOG-001` (sem oracle de enumeração) — repetida aqui porque tem componente de UX (texto da mensagem) que o auditor de produto valida, não o auditor de segurança.

### Checklist obrigatória em PRD

Todo PRD novo (e retrofit de PRD existente em Wave A) tem seção "Acessibilidade" com:

```markdown
## N. Acessibilidade (WCAG 2.1 AA — ADR-0057)

| Critério | Tela 1 | Tela 2 | ... |
|---|---|---|---|
| INV-A11Y-001 (label em input) | ✅ AC-XYZ | ✅ | |
| INV-A11Y-002 (teclado funcional) | ✅ AC-XYZ | ✅ | |
| INV-A11Y-003 (contraste 4.5:1) | ✅ tokens validados | ✅ | |
| INV-A11Y-004 (foco visível) | ✅ global CSS | ✅ | |
| INV-A11Y-005 (erro anunciado) | ✅ AC-XYZ | n/a (sem form) | |
| INV-A11Y-006 (alt em imagem) | n/a (sem imagem) | ✅ AC-XYZ | |
| INV-A11Y-007 (heading hierárquico) | ✅ AC-XYZ | ✅ | |
| INV-A11Y-008 (sem oracle enumeração) | n/a | ✅ AC-XYZ (login) | |
```

Cada `✅` aponta para um AC binário no PRD. `n/a` é aceito desde que justificado (tela sem form, sem imagem, etc).

Hook `a11y-checklist-spec.sh` valida presença desta seção em PRD novo.

### Validação em runtime

- **F-C2:** `axe-core` injetado em testes E2E (quando E2E entrar — gate da Foundation F-C2 ou Wave A, o que vier antes).
- **F-C3:** dashboard Grafana com métrica "telas com axe-core score < 95%" (vai pra zero em Wave A).
- **Wave A:** pre-merge runs `axe-core` em PR que toca template/SPA; falha se score < 95% sem justificativa em ADR.

## Consequências

### Positivas

- Tenant farma/órgão público fica viável sem retrofit de meses.
- ISO 17025 cl. 6.2.3 (competência pessoal) preservada.
- Cada PRD novo já nasce com contrato a11y → reduz dívida.
- Decisão alinhada com Decreto 9.094/2017 + LBI art. 63.

### Negativas

- ~30% a mais de esforço por tela na Wave A (estimativa baseada em mercado SaaS BR).
- Designer/UI agent precisa conhecer WCAG (até hoje não exigido).
- Tokens de design precisam ser declarados com contraste validado (não pode "pegar a cor que parece bonita").

### Aceitas conscientemente

- Validação em runtime (axe-core) entra só em F-C2 — janela atual usa só checklist em PRD.
- Hook `a11y-checklist-spec.sh` valida só ESTRUTURA do PRD (seção presente), não conteúdo semântico — agente IA ainda pode preencher mentindo (auditor de produto pega na review).

## GATEs

- **GATE-A11Y-1:** criar hook `a11y-checklist-spec.sh` (parte da Onda 2; depende desta ADR).
- **GATE-A11Y-2:** declarar tokens de design com contraste validado quando Tailwind/design system aparecer em Wave A.
- **GATE-A11Y-3:** integrar `axe-core` em testes E2E na Foundation F-C2.
- **GATE-A11Y-4:** Marco 3 Fase 5 (use cases OS) DEVE preencher seção "Acessibilidade" no PRD M3 antes de gerar 1ª tela. Bloqueia início da Fase 5 se não estiver lá.

## Não-objetivos desta ADR

- **NÃO** exige WCAG 2.1 nível AAA (mais rigoroso; deixa pra Wave C/V2 se mercado farma TOP exigir).
- **NÃO** exige a11y em e-mail transacional (cobertura LGPD/UX, não WCAG estrito — fica ADR-0060 EmailTemplateProvider).
- **NÃO** define stack específica (Tailwind / Bootstrap / custom CSS — decisão fica em ADR-0010 quando UI Wave A começar).
- **NÃO** cobre acessibilidade física do hardware do técnico (smartphone com botão grande, etc — fica V2).

## Histórico

- 2026-05-23: reservada como ADR-0056 pela Onda 0 plano-v2.
- 2026-05-23: renumerada para ADR-0057 após detectar conflito com ADR-0056 já aceita (numeração OS Marco 3).
- 2026-05-23: aceita pela Onda 2 plano-v2.
