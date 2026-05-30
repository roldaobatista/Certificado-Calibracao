---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 04/17
proximo: docs/descoberta/value-proposition-canvas.md
idioma: pt-BR
limite-linhas: 180
proposito: Business Model Canvas — 9 blocos do modelo de negócio.
---

<!--
template: business-model-canvas.md
destino: docs/descoberta/business-model-canvas.md
uso: Canvas clássico de Osterwalder. Curto, factual, sem prosa filosófica.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤180 linhas. Se passar, blocos estão verbosos — encurtar.
-->

# Business Model Canvas — Aferê Prumo

> **Nota (revisada 2026-05-28 — virada de escopo):** isto **é um produto SaaS vendido por
> assinatura** (add-on de IA do Aferê) a empresas de calibração de **vários tipos e tamanhos**,
> **configurável por empresa**. A **Balanças Solution é o 1º cliente (dogfooding)**. Portanto há
> **receita real** (assinatura), não só ROI interno. O bloco de receita/pricing abaixo depende das
> faixas de preço **aprovadas pelo dono em 2026-05-29** (ponto de partida; refinam no piloto — ver `gtm-pricing.md` §2.2).
> O ROI interno segue valendo como prova de valor no 1º cliente.

## 1. Proposta de valor (centro do canvas)

- Para **empresas de calibração que assinam o Aferê**, uma IA central (cérebro + agentes por setor) que **atende, orça, abre OS, confere certificado e avisa prazos** — **configurável por empresa**, eliminando trabalho manual e prazos perdidos.
- Atendimento ao cliente respondido em segundos pelo WhatsApp, a qualquer hora — **sempre com aprovação humana**.
- Orçamento em rascunho automático (a equipe só revisa); prazo de calibração avisado antes de vencer (receita recorrente preservada).
- Responde sobre o **equipamento vivo** (histórico, nº de série, próximo prazo) consultando o Aferê — não inventa.
- **Escala sem inchar a equipe**: o mesmo time atende mais clientes.

## 2. Segmentos de cliente

> **Clientes pagantes** = empresas de assistência técnica/calibração que assinam o Aferê, por perfil:

- **Perfil A** — laboratório acreditado RBC/CGCRE.
- **Perfil B** ⭐ — lab rastreável não-acreditado (**Balanças Solution = 1º cliente / dogfooding**).
- **Perfil C** — lab em preparação para acreditar.
- **Perfil D** — calibração comercial pura.
- **Usuários dentro de cada empresa-cliente**: equipe de escritório (atendimento/comercial), técnicos de campo, motorista/logística, dono/gestor; e o **cliente final** de cada empresa (atendido via WhatsApp).
- **Anti-segmentos**: quem não assina o Aferê (a IA é add-on do Aferê); consumidor varejo PF; lab sem clientes externos (calibração interna pura).

## 3. Canais

- **Aquisição**: **cross-sell na base de assinantes do Aferê** + dogfooding (case Balanças Solution). Ver `gtm-pricing.md`.
- **Acesso (usuário da empresa-cliente)**: web (e celular para o técnico em campo, offline-first).
- **Entrega ao cliente final**: WhatsApp/e-mail.
- **Pós-venda**: suporte assistido no onboarding (configuração por empresa); IA com fallback humano sempre.

## 4. Relacionamento com cliente/usuário

- **Onboarding da equipe**: assistido, simples (objeção nº 1 é "complicado" — P-C-001).
- **Com o cliente**: IA com opção de falar com humano sempre disponível.

## 5. Fontes de receita (D-PROD-011)

**Receita = assinatura recorrente** do add-on de IA, **faixa por perfil A/B/C/D do Aferê** + franquia de uso inclusa + excedente; cobrada **na fatura do Aferê**.

| Linha | Modelo | Faixa (R$/mês) | Volume estimado |
|---|---|---|---|
| Assinatura IA — Perfil A | recorrente por tenant | **R$ 1.000–1.400/mês** | nº de assinantes A `(A VALIDAR)` |
| Assinatura IA — Perfil B ⭐ | recorrente por tenant | **R$ 550–750/mês** | inclui a Balanças Solution (1º, grátis no piloto) |
| Assinatura IA — Perfil C | recorrente por tenant | **R$ 300–450/mês** | `(A VALIDAR)` |
| Assinatura IA — Perfil D | recorrente por tenant | **R$ 180–280/mês** | `(A VALIDAR)` |
| Excedente de uso | variável | por faixa de uso `(A DEFINIR)` | tenants pesados |

- **Prova de valor (dogfooding na Balanças Solution)**: horas de atendimento economizadas + receita recorrente de calibração preservada (antes 100% perdida) — é o **case** que sustenta a venda aos demais.
- **Margem**: preço da faixa > custo de IA por tenant (LLM + WhatsApp + hospedagem) — guardrail G-005.

## 6. Recursos-chave

- **Equipe**: Roldão (dono/decisor) + equipe de atendimento e técnicos (usuários) + apoio técnico para construir (a definir).
- **Tecnologia**: provedor de LLM, WhatsApp Business API, base de dados de clientes/equipamentos/preços.
- **Dados**: cadastro de clientes, equipamentos, histórico de serviços, tabela de preços/serviços — ativo proprietário central.

## 7. Atividades-chave

- Atender e orçar (com IA, revisão humana).
- Calibrar/manter e registrar histórico + agendar próximo prazo.
- Avisar prazos proativamente.

## 8. Parcerias-chave

- Provedor de LLM (ex.: Anthropic) — "cérebro"; plano B: trocar via adapter.
- WhatsApp Business (Meta/BSP) — canal; plano B: atendimento humano.
- (Futuro) provedor fiscal para NF-e, se necessário.

## 9. Estrutura de custos

| Linha | Tipo | Observação |
|---|---|---|
| LLM (uso por tokens) | variável **por tenant** | escala com o uso de cada empresa; coberto pela franquia + excedente |
| WhatsApp Business (por conversa) | variável **por tenant** | idem |
| Hospedagem/infra | fixo + variável | compartilhada (multi-tenant) + parte por tenant |
| Construção/manutenção do produto | investimento (fixo) | rateado entre os assinantes conforme a base cresce |
| Suporte/onboarding | semi-variável | configuração por empresa; cresce com nº de clientes |

- **Critério de viabilidade por tenant**: mensalidade da faixa > custo de IA daquele tenant (margem positiva por cliente).
- **Break-even**: nº de assinantes pagantes que cobre o investimento fixo de construção/manutenção — `(A VALIDAR)` quando os preços por perfil forem definidos.

## Hipóteses-mais-arriscadas-do-canvas

- H-001 (a dor de atendimento justifica a Fase 1).
- H-002 (prazos perdidos custam receita recorrente).
- H-004 (a equipe adota e não volta pra planilha).

## Critério para promover de `draft` para `stable`

- [ ] Todos os 9 blocos preenchidos (mesmo que com "investigar").
- [ ] Pelo menos 2 hipóteses arriscadas identificadas e amarradas a `hipoteses-a-validar.md`.
- [ ] Break-even calculado.
