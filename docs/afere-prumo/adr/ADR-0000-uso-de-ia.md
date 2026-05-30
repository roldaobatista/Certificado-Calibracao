---
id: ADR-0000
titulo: Usar LLM como cérebro dos agentes, em modo assistido com aprovação humana
status: aceita
data-proposta: 2026-05-28
data-aceite: 2026-05-29
depende-de: []
bloqueia-fase: F-A
superseded-by:
owner: roldao
revisado-em: 2026-05-29
idioma: pt-BR
limite-linhas: 250
proposito: registrar a decisão de usar IA generativa (LLM) em produção, com escopo, riscos e controle de custo
---

# ADR-0000: Usar LLM como cérebro dos agentes, em modo assistido com aprovação humana

> ✅ **FASE DE ARQUITETURA FECHADA — o dono declarou "arquitetura fechada" em 2026-05-29.** Este ADR está **ACEITO** no
> princípio (multi-LLM sem lock-in via `LLMGateway` do Aferê + Maritaca). **Modelos default** ficam provisórios até o
> piloto medir qualidade real em pt-BR no domínio (sub-decisão), sem reabrir o ADR.

## Contexto

A infraestrutura de IA da Balanças Solution depende de um "cérebro" que entende mensagens
em linguagem natural (WhatsApp/e-mail), classifica intenção, compõe respostas e monta rascunhos
(orçamento, OS). A descoberta (`sintese-final.md`) definiu o princípio **"a IA opera com você,
não no lugar de você"**: 100% das ações visíveis ao cliente passam por aprovação humana (Inbox),
e nada irreversível sai sem humano. Trata dados pessoais de cliente (LGPD) num domínio regulado
(metrologia). Esta ADR registra **se e como** usar LLM — obrigatória para qualquer projeto que
usa IA em produção.

## Opções consideradas

### Opção 1: LLM de provedor gerenciado (ex.: Anthropic Claude) — Haiku para tarefas baratas + Sonnet para composição
- **Prós:** qualidade alta em pt-BR; rápido de integrar; modelo barato (Haiku) para classificar/rotear e modelo forte (Sonnet) para compor; o plano do dono já tem essa inclinação.
- **Contras:** custo por uso (tokens); dado trafega para fora → exige pseudonimização e DPA; dependência de fornecedor.
- **Custo:** baixo para começar; variável conforme volume (controlado por kill-switch e guardrail G-005).

### Opção 2: LLM de outro provedor gerenciado (ex.: OpenAI) ou múltiplos
- **Prós:** alternativa/segundo fornecedor; reduz dependência de um só.
- **Contras:** mesma questão de PII/DPA; manter dois fornecedores aumenta complexidade.
- **Custo:** semelhante.

### Opção 3: LLM open-source rodando local/privado
- **Prós:** dado não sai de casa (melhor para LGPD); sem custo por token.
- **Contras:** qualidade em pt-BR e custo de infraestrutura (GPU) hoje desfavoráveis para uma equipe de 9 pessoas; muito esforço operacional.
- **Custo:** alto (infra + manutenção).

## Decisão (revisada 2026-05-29 pelo pedido do dono — ARQUITETURA MULTI-LLM, SEM LOCK-IN)

**Princípio decidido pelo dono (2026-05-29):** *"ter opções, pesquisar custo/qualidade, não ficar
preso a apenas uma LLM."* Logo, a decisão **não é "um fornecedor"** e sim uma **arquitetura agnóstica
de provedor**:

- **Camada de adaptação multi-provedor** (porta única para qualquer LLM): o núcleo dos agentes nunca
  chama um fornecedor direto. Um **roteador de modelos** escolhe por **tarefa, custo e qualidade** —
  modelo barato para classificar/rotear, modelo forte para compor/raciocinar — e **permite trocar ou
  combinar fornecedores** (Anthropic, OpenAI, Google, modelos abertos, LLM nacional) sem reescrever os
  agentes. Mitiga lock-in (R-006) e vira alavanca de custo (R-005).
- **Seleção dos modelos = orientada por benchmark de custo×qualidade** (pesquisa pedida pelo dono;
  1ª versão entregue em 2026-05-29 — ver `docs/adr/ADR-0000-benchmark-llms.md`). Candidatos fortes hoje:
  **Claude** (Haiku/Sonnet — referência em pt-BR), **Gemini** (Flash — custo baixíssimo), **GPT** (mini),
  e **LLM nacional** (Maritaca/Sabiá — processa em PT e casa com "dados no Brasil"). Modelos default ficam
  para a sub-decisão após o dono ver o benchmark.
- **Sempre em modo assistido (Nível 1):** a IA sugere, o humano aprova; subir automação só com dados (≥80% de aceite).
- **Pseudonimização pré-LLM obrigatória + DPA** com cada provedor ativado (independe de qual modelo).
- **Modelos default escolhidos pelo dono (2026-05-29, provisórios — refina no piloto com dados reais):** falar com o
  cliente → **Maritaca/Sabiá na frente** (pt-BR, cobra em reais, dado no Brasil) + **Claude de reserva** nos casos
  difíceis (orçamento alto, diagnóstico); **transcrição de áudio → whisper.cpp local** (grátis, fica no Brasil);
  classificar/rotear → modelo barato. A escolha final sai do piloto.

> Status segue `proposta` porque a **fase de arquitetura está ABERTA** (só o dono fecha) e os modelos default são
> **provisórios até o piloto medir qualidade real em pt-BR no domínio de balanças**. O **princípio** (multi-LLM
> agnóstico + camada de adaptação + modo assistido) e a **1ª escolha de modelos** já estão definidos.

### Refinamentos da auditoria cega (2026-05-29 — incorporados; ver `AUDITORIA-CEGA-ARQUITETURA-2026-05-29.md`)
- **Testar Sabiá × Claude Haiku ANTES de cravar o default** (auditoria: 0/10 citaram Sabiá; consenso ancora em Claude por **tool-calling** e raciocínio normativo). Teste cego em 2 dimensões: **tool-calling estruturado** (acionar a API do Aferê sem alucinar parâmetro) + **raciocínio metrológico**. Rotear o **difícil/tool-use crítico para o Claude**; Sabiá no volume barato pt-BR.
- **Camada de adaptação = LiteLLM — JÁ EXISTE no Aferê** (porta `LLMGateway` #3: LiteLLM + Anthropic/OpenAI/Google + **`MaritacaProvider`** + `model_class fast|deep|br-sovereign` + `embed()`; verificado 2026-05-29). A camada de IA **reusa essa porta**, não monta a sua. Confirma a estratégia multi-modelo **E a aposta em Maritaca/Sabiá** — o Aferê já a previu para "soberania BR".
- **Cache de prompt** (system prompt longo + contexto RAG repetido) — alavanca grande de margem; ligar desde cedo.
- **Transcrição:** cravar **whisper large-v3** (faster-whisper/CTranslate2 — roda em CPU no volume atual); (a) **interface plugável com fallback gerenciado** para picos/indisponibilidade; (b) **glossário de domínio** no STT (OIML, Inmetro, "célula de carga", "classe III", nº de série) — STT genérico erra jargão, e nº de série errado vira orçamento/calibração errada.
- **Citação de fonte obrigatória no RAG** (documento + trecho) para o humano que aprova auditar a origem — em metrologia legal, resposta sem origem vira não-conformidade.

## Consequências

### Positivas
- Qualidade alta em pt-BR com baixo esforço de integração.
- Custo controlável: Haiku barato no volume (classificação/roteamento), Sonnet só onde precisa.
- Troca de fornecedor possível pela camada de adaptação.

### Negativas
- Custo recorrente por uso → exige **kill-switch** e monitor de custo (G-005).
- PII trafega para fornecedor externo → **pseudonimização pré-LLM** obrigatória + DPA.

### Reversibilidade
Alta (se houver camada de adaptação): trocar de modelo/provedor sem reescrever os agentes.

## Non-goals
- Não decide o provedor de WhatsApp (ADR futura) nem a stack do sistema (ADR-0001).
- Não decide treinar modelo próprio (fora de escopo).

## Como validar (gates)
- [ ] Camada de adaptação isola o provedor de LLM do resto do sistema (trocar de modelo sem mexer nos agentes).
- [ ] Roteador de modelos escolhe por tarefa/custo/qualidade; suporta ≥2 provedores.
- [ ] Benchmark de custo×qualidade documentado e revisado com o dono antes de cravar os modelos default.
- [ ] Pseudonimização aplicada antes de qualquer envio ao LLM (nenhum CPF/telefone cru sai).
- [ ] Kill-switch de custo + alerta de gasto mensal funcionando.
- [ ] DPA com cada provedor ativado avaliado/assinado antes de produção com dado real.

## Referências
- `docs/descoberta/sintese-final.md` (D-PROD-006 princípio assistido)
- `docs/descoberta/integracoes-externas.md` (INT-002)
- `docs/descoberta/riscos.md` (R-005 custo, R-006 fornecedor, R-007 prompt injection)
