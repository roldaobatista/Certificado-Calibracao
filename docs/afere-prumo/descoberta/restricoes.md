---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 10/17
proximo: docs/descoberta/hipoteses-a-validar.md
idioma: pt-BR
limite-linhas: 120
proposito: restrições do projeto — orçamento, prazo, equipe, geografia, dependências.
---

<!--
template: restricoes.md
destino: docs/descoberta/restricoes.md
uso: limites duros que moldam decisões. Recomendado (🟡).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤120 linhas.
-->

# Restrições — Aferê Prumo

> Não é "lista de desejos" — é o que limita decisões. Tudo aqui afeta arquitetura, escopo e cronograma.

## 1. Orçamento

- **Total disponível**: caixa próprio, **sem teto duro** (não há investidor); o limite operacional relevante é o **mensal** (abaixo).
- **Mensal recorrente máximo (infra + IA + WhatsApp)**: **~R$ 5 mil/mês** (número-base do dono, 2026-05-29; pode subir até ~R$ 15 mil/mês conforme a operação escala) — guardado por G-005 (custo por atendimento). Com esse patamar, o ponto de equilíbrio é **~13 clientes pagantes** (ver `estimativa-custo-viabilidade.md §5`).
- **Fonte**: caixa próprio da empresa (não há investidor).
- **Princípio**: o preço da assinatura (faixa por perfil) tem de cobrir o custo de IA por tenant com margem (G-005); e, no dogfooding, o custo tem de ser menor que o valor economizado/preservado na Balanças Solution.

## 2. Prazo

- **Primeira entrega visível (Fase 1)**: **sem data fixa de calendário** — decisão do dono (2026-05-29): a entrega acontece **"quando ficar pronto"** (quando o mínimo viável estiver funcionando bem), priorizando qualidade sobre data. O cronograma real nasce junto com a stack (ADR-0001).
- **Sem limite duro externo**: não há compromisso com investidor/regulação que imponha data; ritmo é definido pelo dono (entrega por **prontidão**, não por prazo).

## 3. Equipe

- **Tamanho atual**: **9 pessoas** — Roldão (proprietário/decisor), **2 no escritório** (atendimento/comercial/administrativo), **5 técnicos em campo** (manutenção/calibração), **1 motorista** (logística).
- **Usuários da IA**: escritório (atendimento/orçamento), técnicos (histórico + OS em campo), motorista (rotas/entregas-retiradas de locação), Roldão (gestão).
- **Capacidade de construir software**: não há time de desenvolvimento interno → será necessário apoio técnico (a definir no ADR de stack).
- **Disponibilidade**: equipe ocupada com a operação (escritório de 2 pessoas absorve os ~50 atendimentos/semana); a ferramenta precisa ser simples para não pesar — reforça R-002 (adoção).

## 4. Geografia e mercado

- **Idioma**: pt-BR.
- **Hospedagem**: dado de cliente brasileiro → preferir hospedagem no Brasil (LGPD). `(A CONFIRMAR no ADR)`
- **Mercado-alvo (revisado 2026-05-28)**: a **base de assinantes do Aferê** (empresas de calibração no Brasil) — a IA é add-on do Aferê. A Balanças Solution é o 1º cliente (dogfooding). O teto de mercado é o tamanho da base do Aferê (R-013).
- **Escala/multi-tenant**: a infra deve suportar **empresas de portes muito diferentes** (1 pessoa a vários técnicos/filiais), **configurável por empresa** — não pode ser dimensionada só para o tamanho da Balanças Solution (R-015).

## 5. Dependências externas

| Dependência | Função | Risco se cair | Plano B |
|---|---|---|---|
| **Aferê (ERP-núcleo)** | **Fonte única da verdade** (clientes, OS, certificados, preços) | 🔴 máxima — sem ele a IA não tem sobre o que agir | É a mesma casa (em construção junto); resiliência desenhada no módulo de integração |
| WhatsApp Business API | Canal com o cliente | Indisponibilidade/mudança de regra | Atendimento humano direto |
| Provedor de LLM | "Cérebro" da IA | Preço/disponibilidade | Trocar provedor via camada de adaptação |
| Hospedagem (a definir) | Rodar o sistema | Indisponibilidade | Definir no ADR |

> **🔗 Restrição arquitetural dura (D-PROD-021, dono 2026-05-29):** a camada de IA é **100% integrada ao Aferê**
> (fonte única — **sem base de dados paralela**) e essa integração é **encapsulada num MÓDULO PRÓPRIO dedicado**
> (anti-corrosion layer; só ele fala com o Aferê). O **desenho técnico** desse módulo é discutido na **etapa certa**
> (ADR-0001, hoje congelado até a descoberta fechar) — agora fica firme só o **princípio**.

## 6. Stack pré-decidida

- **Nenhuma stack pré-decidida** → **ADR-0001 livre**.
- Única inclinação registrada: usar um LLM de boa qualidade (ex.: Anthropic Claude) como cérebro — a decidir no ADR-0000 (uso de IA).

## 7. Restrições de processo

- **Compliance**: LGPD aplica (PII de cliente) — ver [`mercado-regulatorio.md`](./mercado-regulatorio.md); materializado na fase-2 (C6).
- **Sem investidor / sem cliente-piloto externo com NDA**: é operação própria.
- **Matriz de permissão por setor** (operacionaliza NF-005): definir quem-vê-o-quê e quem-pode-agir-em-quê (quem enxerga financeiro, quem enxerga PII, quem emite/assina). Como tratamos PII e multi-setor, a matriz é **pré-requisito** da auditoria imutável que a descoberta promete.
- **Toda a governança operável por NÃO-TÉCNICO** (o Roldão): aprovar, ver auditoria, ligar/desligar regra, ver custo, kill-switch — sem depender de TI. É diferencial vs. todos os enterprise.

## 8. Não-restrições (o que NÃO limita)

- Sem restrição de licença de software — livre escolher.
- Sem restrição de fornecedor de IA — pode usar Anthropic/OpenAI/OSS (decidir por qualidade/custo no ADR).
- Sem imposição de cloud específica.

## Critério para promover de `draft` para `stable`

- [ ] Orçamento total + mensal preenchidos.
- [ ] Prazo de MVP definido (data, não "alguns meses").
- [ ] Equipe atual nomeada (cargos, não nomes em projeto solo).
- [ ] ≥2 dependências externas mapeadas com plano B.
