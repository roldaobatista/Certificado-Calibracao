---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 06/17
proximo: docs/descoberta/concorrentes.md
idioma: pt-BR
limite-linhas: 220
proposito: estratégia de go-to-market e pricing do add-on de IA vendido aos assinantes do Aferê.
---

<!--
template: gtm-pricing.md
destino: docs/descoberta/gtm-pricing.md
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
-->

# GTM e Pricing — Aferê Prumo (add-on de IA do Aferê)

> **Escopo (D-PROD-001 revisada + D-PROD-011, 2026-05-28):** a camada de IA é um **produto SaaS
> multi-tenant vendido por assinatura** como **add-on do Aferê** (ERP de calibração). A **Balanças
> Solution é o 1º cliente (dogfooding)**; o alvo é vender para os demais assinantes do Aferê.
> Valores em R$ **aprovados pelo dono em 2026-05-29 como ponto de partida** (tabela §2.2); refinam no piloto com o custo real de IA por tenant.

## 1. Posicionamento

- **Para quem**: empresas de assistência técnica/calibração que **já assinam o Aferê**, de portes variados (perfis A/B/C/D).
- **Que problema resolve**: a operação trava na pessoa-chave; atendimento/orçamento manual; prazos de calibração perdidos. A IA destrava, atende com aprovação humana e nunca deixa prazo vencer sem aviso.
- **Diferencial defensável**: conhece o **domínio metrológico-legal** + responde sobre o **equipamento vivo** do Aferê + opera **com o dono (aprovação)** — o que CRM/atendimento genérico não faz (ver `concorrentes.md §4`).
- **Promessa central**: "sua empresa atende mais e melhor sem contratar mais gente — e nunca mais perde prazo de calibração".

## 2. Estratégia de pricing (D-PROD-011)

### 2.1. Modelo
- **Tipo**: assinatura recorrente (SaaS), **add-on do Aferê**.
- **Unidade de cobrança**: **faixa por porte/perfil da empresa** (espelha os perfis **A/B/C/D do Aferê**), com **franquia de uso de IA inclusa** em cada faixa; **excedente** cobrado se o uso estourar muito a franquia.
- **Cobrança**: **na mesma fatura do Aferê** (add-on que o cliente liga). Uma cobrança só.
- **Moeda**: BRL.
- **Princípio de margem**: o preço da faixa tem de cobrir o **custo de IA por tenant** (LLM + WhatsApp + hospedagem) com folga — guardrail G-005. Por isso a franquia de uso + excedente, para o tenant pesado não corroer a margem.

### 2.2. Planos por perfil (espelham o Aferê)

| Perfil (= Aferê) | Quem é | Mensalidade do add-on de IA | Franquia de uso inclusa |
|---|---|---|---|
| **A** | Laboratório acreditado RBC/CGCRE | **R$ 1.000–1.400/mês** | maior |
| **B** ⭐ | Lab rastreável (não-acreditado) — **perfil da Balanças Solution / 1º cliente** | **R$ 550–750/mês** (1º cliente BS = grátis no piloto) | média |
| **C** | Lab em preparação para acreditar | **R$ 300–450/mês** | média-baixa |
| **D** | Calibração comercial pura | **R$ 180–280/mês** | baixa |

- **Excedente de uso**: acima da franquia, cobra-se por faixa de uso adicional `(A DEFINIR)`.
- **Configurável por empresa** (D-PROD-011): quais agentes ligar, parâmetros (limites/avisos/níveis), papéis/permissões por setor, canais e identidade — definidos no onboarding do tenant.

### 2.3. Add-ons / opcionais (futuro)
- Agentes premium (ex.: marketing, jurídico) como módulos adicionais — avaliar depois.

### 2.4. Descontos & promoções
- **Dogfooding/founder**: a **Balanças Solution usa a IA de GRAÇA durante o piloto** (decisão do dono 2026-05-29); entra em faixa (possivelmente especial) só depois de validar.
- **Early adopters do Aferê**: condição especial para os primeiros assinantes que ligarem a IA — `(A DEFINIR)`.

> ⚠️ **Pré-requisito de qualquer preço (gap crítico da auditoria — H-018):** calcular o **custo de IA por
> cliente por perfil** (LLM + WhatsApp + transcrição de áudio + infra) ANTES de fechar valores, e o **ponto de
> equilíbrio**. Sem esse número não dá para garantir margem (R-012, R-019, G-005).
> ✅ **Estimativa inicial (ordem de grandeza) já feita** em [`estimativa-custo-viabilidade.md`](./estimativa-custo-viabilidade.md):
> custo ~R$ 0,80–1,00 por atendimento (com transcrição local); custo/mês por perfil (B ≈ R$ 210–250); piso de preço
> por margem. **Refinar** com preços reais (ADR) e volume real (piloto). O preço de venda final é decisão do dono (vale mais que o custo).

## 3. Estratégia de aquisição

> Vantagem-chave: **a base de aquisição já existe — são os assinantes do Aferê**. É cross-sell, não conquista do zero.

### 3.1. Canais
| Canal | Como | Status |
|---|---|---|
| **Cross-sell na base do Aferê** | oferecer o add-on de IA a quem já assina o ERP | principal |
| **Dogfooding como prova** | mostrar o resultado real na Balanças Solution (case) | principal |
| Indicação entre clientes do Aferê | cliente satisfeito indica | secundário |
| Conteúdo/demonstração | vídeos do ciclo "do oi ao certificado" | apoio |

- **CAC**: baixo (já são clientes do Aferê) — `(A VALIDAR)`.

### 3.2. Funil
- **Assinante do Aferê** → **liga o add-on de IA** (trial/condição inicial) → **onboarding** (configura agentes/parâmetros) → **ativo pagante** → **defensor** (indica).
- **Taxas de conversão alvo**: `(A VALIDAR no piloto)`.

### 3.3. Ciclo de venda
- Curto: o cliente já confia no Aferê; o add-on é uma ativação, não uma venda nova longa.

## 4. Onboarding (configuração por empresa)

- **Tempo até primeiro valor (TTFV)** alvo: `(A VALIDAR)` — primeiro atendimento assistido com aprovação.
- **Fluxo**: ativar add-on → escolher **quais agentes** ligar → ajustar **parâmetros** (limites/avisos/níveis) → definir **papéis/permissões** por setor → conectar **canais** (WhatsApp/e-mail) e identidade → IA começa em **modo assistido** (tudo pela Inbox).
- **Suporte no onboarding**: assistido (a equipe do produto ajuda a configurar) — objeção nº 1 dos clientes é "complicado".

## 5. Retenção

- **Churn alvo**: `(A VALIDAR)`.
- **Sinais de risco**: fila da Inbox parada (não adotou), uso de IA caindo, custo de IA acima do valor percebido.
- **Playbook**: acompanhar adoção (métricas de saúde do agente em `metricas-chave.md`), mostrar valor (horas economizadas + prazos preservados) no Resumo Matinal/painel.

## 6. Dependência estrutural

- A IA é **add-on do Aferê** → só vendável a quem assina o Aferê. A saúde comercial da IA depende da base do Aferê crescer (ver `riscos.md`).

## Critério para promover de `draft` para `stable`

- [x] Modelo de cobrança definido (faixa por perfil + uso incluso — D-PROD-011).
- [x] Relação com o Aferê definida (add-on na mesma fatura).
- [x] Canal de aquisição principal definido (cross-sell na base do Aferê).
- [ ] Valores em R$ por perfil definidos (dependem de medir custo de IA por tenant).
- [ ] Taxas de conversão e churn alvo (validar no piloto).
