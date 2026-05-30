---
owner: roldao
revisado-em: 2026-05-29
status: stable
idioma: pt-BR
limite-linhas: 160
proposito: estimativa de ORDEM DE GRANDEZA do custo de IA por cliente (por perfil) e do ponto de equilíbrio, para destravar a conversa de preço. NÃO é preço final — refina com preços reais (ADR) e volume real (piloto).
---

# Estimativa de custo de IA e viabilidade — Aferê Prumo

> Pedido do dono (2026-05-29): "estima agora com premissas". Resolve o gap crítico da auditoria
> (custo de IA por cliente / ponto de equilíbrio nunca calculados — itens 4, 5, 6; H-018).
> **⚠️ TUDO AQUI É ESTIMATIVA de ordem de grandeza.** Os preços de provedor são aproximados e dependem do
> ADR de stack; o volume e os tokens reais só o piloto mede. Serve para ter um **número de partida**, não preço final.

## 1. Premissas (explícitas — trocar quando tiver dado real)

| Premissa | Valor usado | Observação |
|---|---|---|
| Câmbio | US$ 1 = R$ 5,50 | premissa; ajustar |
| LLM por atendimento | ~15 mil tokens entrada + ~2 mil saída | conversa + contexto do cérebro/RAG; mix Haiku (barato) + Sonnet (raciocínio) |
| Preço LLM (ordem) | entrada ~R$ 0,02/mil · saída ~R$ 0,08/mil (média do mix) | aproximação; varia por modelo escolhido (ADR-0000) |
| WhatsApp Business | ~R$ 0,50 por conversa (janela 24h) | varia por BSP; algumas conversas de serviço já são gratuitas |
| Transcrição (STT) | **local ≈ R$ 0** (só CPU/tempo) | já provado nesta descoberta (whisper.cpp). Se API paga: ~R$ 0,03/min |
| Áudio por atendimento | ~3–5 min (vários PTT) | base: 1.120 áudios em 5 conversas |
| Infra/hospedagem | rateio ~R$ 30–80/tenant/mês | servidor + banco + cérebro; decisão no ADR |
| Margem-alvo mínima | ≥ 40% | guardrail (metricas-chave G-005/margem por tenant) — **o dono define o final** |

## 2. Custo estimado por ATENDIMENTO

| Item | Com STT local (recomendado) | Com STT pago |
|---|---|---|
| LLM (cérebro + agentes) | ~R$ 0,30–0,46 | ~R$ 0,30–0,46 |
| WhatsApp | ~R$ 0,50 | ~R$ 0,50 |
| Transcrição | ~R$ 0,00 | ~R$ 0,09–0,15 |
| **Total por atendimento** | **~R$ 0,80–1,00** | **~R$ 0,90–1,15** |

> A escolha **STT local** (já validada) praticamente zera o custo de áudio e mantém o áudio dentro de casa (LGPD) —
> é o que segura a margem, já que o atendimento é majoritariamente por voz.

## 3. Custo mensal estimado por PERFIL (volume × custo/atendimento + infra)

| Perfil | Volume estimado (atend./mês) | Custo IA/mês (STT local) | + infra | **Custo total/mês (ordem)** |
|---|---|---|---|---|
| **A** (lab acreditado, maior) | ~400 | ~R$ 320–400 | ~R$ 80 | **~R$ 400–480** |
| **B** ⭐ (BS / rastreável) | ~200 (50 atend/sem) | ~R$ 160–200 | ~R$ 50 | **~R$ 210–250** |
| **C** (em preparação) | ~120 | ~R$ 100–120 | ~R$ 40 | **~R$ 140–160** |
| **D** (comercial pura) | ~60 | ~R$ 50–60 | ~R$ 30 | **~R$ 80–90** |

> Volume do perfil B vem de dado real (Balanças Solution: ~50 atendimentos/semana). Os demais são proporção estimada.

## 4. Implicação para o preço (margem-alvo ≥ 40%)

Para cobrir o custo com ≥40% de margem, a **mensalidade mínima** do add-on por perfil fica na ordem de:

| Perfil | Custo/mês (ordem) | Preço mínimo p/ 40% margem (ordem) |
|---|---|---|
| A | ~R$ 440 | **~R$ 730+** |
| B | ~R$ 230 | **~R$ 380+** |
| C | ~R$ 150 | **~R$ 250+** |
| D | ~R$ 85 | **~R$ 140+** |

> ⚠️ Isso é **piso de custo**, não recomendação de preço. O **preço de venda é decisão do dono** e considera
> também o **valor entregue** (horas economizadas + prazos preservados), não só o custo. O add-on pode (e deve)
> valer bem mais que o custo se preserva receita de recalibração e destrava o dono-gargalo.

### 4.1 Preço de venda — ✅ APROVADO pelo dono (2026-05-29) como ponto de partida

Precificar pelo **valor** (não só custo): o add-on preserva receita de recalibração que hoje vence (0% controlado)
e libera o dono-gargalo. **O dono aprovou estas faixas** (2026-05-29) como preço de partida:

| Perfil | Piso de custo | **Preço de venda APROVADO** | Margem aprox. |
|---|---|---|---|
| A | ~R$ 730 | **R$ 1.000–1.400/mês** | ~55–65% |
| B ⭐ | ~R$ 380 | **R$ 550–750/mês** | ~55–65% |
| C | ~R$ 250 | **R$ 300–450/mês** | ~50–60% |
| D | ~R$ 140 | **R$ 180–280/mês** | ~50% |

> ✅ **Aprovado pelo dono (2026-05-29)** como ponto de partida. Ainda **refina no piloto** com **disposição
> a pagar** real (H-013: ouvir ≥5 assinantes do Aferê) e com os custos reais. A franquia de uso inclusa por
> faixa segue D-PROD-011; excedente cobrado acima dela.

## 5. Ponto de equilíbrio (estimativa grosseira)

- **Investimento/custo fixo mensal** — ✅ **número-base cravado pelo dono (2026-05-29): ~R$ 5 mil/mês** (começar enxuto; o STT local praticamente zera o custo de áudio). O teto pode subir até ~R$ 5–15 mil/mês conforme a operação cresce (2 pessoas no escritório + infra de IA).
- Regra: `nº de clientes para se pagar = custo fixo mensal ÷ margem média por cliente`.
- **Margem média por cliente** (com o preço de venda aprovado §4.1): ordem de **~R$ 350–450/mês** (média entre perfis).
- Cenários na faixa informada pelo dono (R$ 5–15 mil/mês):

| Custo fixo mensal | Margem média/cliente | Clientes p/ equilíbrio |
|---|---|---|
| R$ 5.000 | R$ 400 | ~13 |
| R$ 8.000 | R$ 400 | ~20 |
| R$ 12.000 | R$ 400 | ~30 |
| R$ 15.000 | R$ 400 | ~38 |

> ✅ **Ponto de equilíbrio (com o número-base do dono, R$ 5 mil/mês): ~13 clientes pagantes** (sobe pra ~20–38 se o custo fixo crescer até R$ 15 mil/mês conforme a operação escala).
> Como a aquisição é **cross-sell na base do Aferê** (CAC baixo) e a BS é dogfooding grátis, o equilíbrio depende
> sobretudo de **quantos assinantes do Aferê ligam o add-on**. Refina com o custo real + volume real do piloto.

## 6. O que falta para virar número firme (refino)

1. **Preço real dos provedores** (LLM, WhatsApp BSP, hospedagem) → ADR de stack.
2. **Tokens e volume reais** por atendimento → medir no piloto (G-005).
3. **Custo fixo mensal** → ✅ **número-base cravado pelo dono: ~R$ 5 mil/mês → equilíbrio ~13 clientes** (2026-05-29); refina o valor real na fase de stack.
4. **Decisão STT local × pago** → ADR (recomendação: local, pelo custo e LGPD).
5. Revisar a margem-alvo e o preço de venda com o dono (liga a H-013, H-018, R-012, R-019).
