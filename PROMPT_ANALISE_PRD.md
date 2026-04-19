# Prompt — Análise crítica do PRD Kalibrium

> Cole o conteúdo abaixo em uma nova sessão do Claude (Claude Code, Claude.ai, ou outra). Se estiver no Claude Code com acesso ao arquivo, ele lerá `PRD.md` direto. Se estiver no Claude.ai, anexe ou cole o PRD completo após o prompt.

---

## Prompt

Você é um painel de revisão multidisciplinar avaliando um PRD (Product Requirements Document) de uma plataforma SaaS de **emissão de certificados de calibração** para laboratórios e empresas, com foco em conformidade ABNT NBR ISO/IEC 17025:2017 e regulação Inmetro/Cgcre.

O PRD está em [`PRD.md`](./PRD.md) (3.800+ linhas, 18 seções). Leia o arquivo completo antes de responder. Se não tiver acesso ao filesystem, peça ao usuário para colar o conteúdo.

### Como você deve atuar

Você simulará **6 papéis sequencialmente**, cada um com sua lente própria, e produzirá uma análise consolidada ao final:

1. **Auditor Cgcre / metrologista sênior** — verifica se o produto realmente sustenta ISO/IEC 17025:2017, Portaria 157/2022, DOQ-CGCRE, ILAC P10/P14/G8.
2. **CTO de SaaS B2B** — avalia arquitetura, multitenancy, escalabilidade, segurança, custo operacional.
3. **Product Manager sênior** — avalia clareza de escopo, MVP defensável, riscos de produto, dependências.
4. **Designer UX/UI sênior** — avalia fluxos, wizard, friction points, acessibilidade, viabilidade dos wireframes.
5. **Advogado especialista em LGPD e contratos SaaS** — avalia compliance LGPD, DPA, retenção, transferência de dados, base legal.
6. **Comercial / Founder** — avalia proposta de valor, pricing, posicionamento, go-to-market, viabilidade comercial.

### O que entregar

Para cada papel, produza:

- **3 a 7 achados** (não menos, não mais).
- Cada achado deve ter:
  - **Título** curto (≤ 80 chars)
  - **Severidade**: 🔴 Crítico / 🟠 Alto / 🟡 Médio / 🟢 Baixo
  - **Onde no PRD** (seção §X.Y e linha aproximada)
  - **Evidência** — citação literal ou paráfrase fiel
  - **Por que é problema** — consequência concreta se não tratado
  - **Recomendação** — ação específica e acionável (não vago)

### Ao final, consolide

- **Top 10 achados** (mix de papéis, ordenados por severidade × esforço).
- **5 perguntas que o autor do PRD precisa responder antes do MVP** — coisas que o documento deixou implícito ou ambíguo.
- **3 riscos existenciais** que o produto deveria tratar prioritariamente.
- **Veredito em 1 linha**: o PRD está pronto para começar implementação? Justifique.

### Tom

- **Crítico mas construtivo.** Não amenize achados reais. Não invente problemas para parecer rigoroso.
- **Evidência > opinião.** Se algo não está no PRD, diga "não está documentado" — não assuma.
- **Quando elogiar, elogie.** O documento tem partes fortes — reconheça-as no início (1 parágrafo).

### Restrições

- Não reescreva o PRD. Sua entrega é análise, não nova versão.
- Não invente cláusulas da ISO/IEC 17025 — cite apenas o que conhece.
- Se você acha que o PRD está bom em algo, diga "OK" e siga — não preencha espaço.
- Trate o PRD como produto real que vai implementar — não como exercício acadêmico.

### Formato de saída

```
# Análise crítica do PRD Kalibrium

## Pontos fortes (1 parágrafo)
[...]

## Achados por papel

### 1. Auditor Cgcre / metrologista
- 🔴 [Título]  — §X.Y L###
  Evidência: [...]
  Por quê: [...]
  Recomendação: [...]
- 🟠 [...]
- ...

### 2. CTO SaaS
- ...

### 3. PM sênior
- ...

### 4. UX/UI
- ...

### 5. LGPD / contratos
- ...

### 6. Comercial / Founder
- ...

## Top 10 achados consolidados
1. 🔴 [...]
2. 🔴 [...]
...

## 5 perguntas para o autor responder
1. ...
2. ...
...

## 3 riscos existenciais
1. ...
2. ...
3. ...

## Veredito
[1 linha]
```

Comece agora. Leia o PRD inteiro antes de produzir a análise.
