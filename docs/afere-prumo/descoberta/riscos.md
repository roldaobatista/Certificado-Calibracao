---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 09/17
proximo: docs/descoberta/restricoes.md
idioma: pt-BR
limite-linhas: 200
proposito: registro de riscos do projeto (R-NNN) com probabilidade, impacto e mitigação.
---

<!--
template: riscos.md
destino: docs/descoberta/riscos.md
uso: cada risco com ID R-NNN, probabilidade (A/M/B), impacto (A/M/B), responsável, mitigação.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤200 linhas.
-->

# Riscos — Aferê Prumo

> Distintos das ameaças de segurança (`docs/seguranca/threat-model.md`). Aqui é risco de **produto/negócio/operação/projeto**.

## Como ler

- **Probabilidade**: A (alta — ≥50%), M (média — 20-50%), B (baixa — <20%) em horizonte de 12 meses.
- **Impacto**: A (alto — bloqueia projeto / dano financeiro >R$X), M (médio — atraso de meses), B (baixo — contornável).
- **Severidade** (derivada): A×A = 🔴 crítico, A×M ou M×A = 🟠 alto, demais = 🟡 médio/baixo.

## Riscos ativos

| ID | Descrição | Categoria | Prob | Imp | Sev | Responsável | Mitigação | Status |
|---|---|---|---|---|---|---|---|---|
| R-001 | Escopo "tudo de uma vez" trava o projeto e nada é entregue | projeto | A | A | 🔴 | Roldão | ⚠️ **Dono optou por ligar TODOS os agentes no piloto** (D-PROD-018, 2026-05-29, risco aceito). Mitigação revisada: **CONSTRUÇÃO ainda faseada** tecnicamente; no piloto **todos em Nível 1** (nada ao cliente sem aprovação — ligar≠autonomia); **dogfooding interno** (cobaia = própria empresa); **Inbox priorizada**; **métrica por agente** desde o dia 1; **rollback individual** de agente | ativo — **risco aceito, monitorar de perto** |
| R-002 | Equipe interna não adota e volta pra planilha/papel | gente | M | A | 🟠 | Roldão | Piloto 30d, simplicidade, envolver equipe cedo (H-004) | ativo |
| R-003 | IA dá resposta/orçamento errado ao cliente | produto | M | A | 🟠 | equipe atend. | Modo rascunho + revisão humana antes de enviar (NF-002, H-005) | ativo |
| R-004 | Vazamento/uso indevido de PII de cliente | segurança/regulatório | B | A | 🟠 | DPO (a designar) | C6 LGPD na fase-2; dado mínimo ao LLM; controle de acesso | ativo |
| R-005 | Custo de LLM/WhatsApp cresce sem controle | financeiro | M | M | 🟡 | Roldão | Guardrail de custo por atendimento; limites; medir desde o piloto | ativo |
| R-006 | Provedor (WhatsApp/LLM) muda regra, preço ou disponibilidade | técnico | M | M | 🟡 | tech-lead (a definir) | Camada de adaptação (não acoplar core); plano B por integração | ativo |
| R-007 | Cliente tenta enganar a IA por mensagem (prompt injection) para extrair dado ou forçar ação | segurança | M | A | 🟠 | tech-lead (a definir) | IA só age sobre o Aferê com permissão; ação externa exige aprovação humana; pseudonimização; nunca executar instrução vinda do conteúdo do cliente | ativo |
| R-008 | IA inventar dado operacional (cliente, preço, nº de série, prazo) | produto | M | A | 🟠 | equipe | Consultar sempre o Aferê (fonte real); se não achar, pedir confirmação; citar a fonte; nunca chutar | ativo |
| R-009 | **Buy-vs-build**: helpdesk/CRM pronto (Zendesk/Zoho/HubSpot...) atende a pergunta-resposta "bom o suficiente", barato e rápido → questiona-se por que construir | mercado | A | M | 🟠 | Roldão | Ancorar valor nos ~20% insubstituíveis (Aferê, certificado, prazo por equipamento, campo offline, RT); aceitar que os ~80% genéricos são comoditizáveis | ativo |
| R-010 | Dependência da qualidade/disponibilidade do Aferê — "consulta a fonte real" fica frágil se o Aferê atrasar ou não expor dados confiáveis | técnico | M | A | 🟠 | Roldão | Tratar disponibilidade/qualidade dos dados do Aferê como pré-requisito de CADA onda, não detalhe de integração | ativo |
| R-011 | Inveja de funcionalidade: pressão para acelerar além do Nível 1 antes dos dados justificarem (fere D-PROD-006, expõe a CDC/certificado) | produto | M | A | 🟠 | Roldão | Graduar automação só por métrica de saúde do agente (aprovação-sem-edição), nunca por comparação com concorrente | ativo |
| R-012 | **Margem por tenant negativa**: cliente de uso pesado consome mais LLM/WhatsApp do que a mensalidade da faixa cobre | financeiro | M | A | 🟠 | Roldão | Franquia de uso + cobrança de excedente (D-PROD-011); kill-switch e monitor de custo por tenant (G-005, métrica de margem por tenant) | ativo |
| R-013 | **Dependência da base do Aferê**: a IA só é vendável a quem assina o Aferê → o teto de mercado da IA é o tamanho da base do Aferê | mercado | M | M | 🟡 | Roldão | Crescer junto com o Aferê; usar a IA como motivo a mais para assinar o ERP (cross-sell nos dois sentidos) | ativo |
| R-014 | **Complexidade de configuração/onboarding por empresa**: cada cliente é diferente (agentes, parâmetros, permissões) → suporte cresce e risco de configuração errada | operação | M | M | 🟡 | Roldão | Defaults bons por perfil A/B/C/D; onboarding assistido; configuração simples (operável por não-técnico) | ativo |
| R-015 | **Atender portes muito diferentes** (de 1 pessoa a empresa com vários técnicos/filiais) com a mesma ferramenta sem ficar nem pobre pro grande nem complexo pro pequeno | produto | M | M | 🟡 | Roldão | Perfis A/B/C/D + configurabilidade; validar com ≥1 cliente de cada porte antes de abrir comercial | ativo |
| R-016 | **Erro de transcrição de áudio** leva a ação/orçamento incorreto (ex.: "3 ton" vira "30 ton") — a entrada já chega corrompida (≠ alucinação); atendimento é majoritariamente por áudio (D-PROD-013) | produto | M | A | 🟠 | equipe atend. | Usar o score de confiança da transcrição (abaixo do limiar → escala); repetir ao cliente em texto antes de agir ("recebi: calibrar 3 ton, certo?"); auditar casos de baixa confiança; medir taxa de correção no piloto | ativo |
| R-017 | **IA inventa diagnóstico/procedimento técnico** quando o cérebro não tem a resposta (ex.: significado de código de erro de indicador) — em metrologia legal, diagnosticar errado um equipamento fiscal pode levar a operação ilegal | produto | M | A | 🟠 | equipe | Agente marca "lacuna de conhecimento" em vez de inventar (NF-004); resposta de baixa confiança vai pra fila de aprovação; carga do cérebro (Onda 0) é pré-requisito de cada onda; citação de fonte obrigatória (D-PROD-014) | ativo |
| R-018 | **Cérebro técnico desatualiza ou tem fontes conflitantes** (ex.: Toledo × Inmetro), OCR falho, itens duplicados ou busca lenta — compromete a confiabilidade de toda resposta da IA | produto/técnico | M | A | 🟠 | tech-lead (a definir) | Versão e data por fonte; hierarquia de confiança das fontes (D-PROD-014: manual oficial > Aferê > grupo > conversa); teste de coerência; ciclo de atualização semestral; dedupe + revisão dos itens escaneados | ativo |
| R-019 | **Custo de transcrição (STT) consome a margem do tenant**: áudio é 50%+ do atendimento; se a transcrição for serviço pago, cada minuto vira R$ que sai da margem (refina R-005/R-012) | financeiro | M | A | 🟠 | Roldão | Decidir local × pago no ADR de stack; G-005 mede STT em linha própria (R$/min); franquia por perfil mede "minutos de áudio", não só nº de conversas; kill-switch por custo/atendimento; medir minutos reais no piloto | ativo |
| R-020 | **Vazamento de dado pessoal de terceiro** (clientes finais e, sobretudo, parceiros do grupo nacional) dentro do cérebro, sem segregação por empresa | segurança/regulatório | M | A | 🟠 | DPO (a designar) | Isolamento multi-tenant do cérebro (D-PROD-014); só conhecimento técnico AGREGADO vira produto — dado pessoal de terceiro nunca exposto a outro tenant; anonimização antes de compartilhar; cobre AIPD/ROPA na fase-2 | ativo |
| R-021 | **Desconto: IA limita a ~3% mas a prática real chega a 26%** (dados Auvo) — se o escalonamento ao dono for lento, perde-se negócio ou frustra o cliente que pediu desconto | produto/comercial | M | M | 🟡 | Roldão | Escalonamento rápido (fila priorizada para pedido de desconto); medir tempo de resposta do desconto escalado; política de desconto configurável por empresa (D-PROD-012); a IA nunca fecha desconto grande sozinha | ativo |
| R-022 | **IA vaza conhecimento técnico restrito a cliente externo** (procedimento de calibração/ajuste, código de erro interno, parâmetro metrológico) — quebra D-PROD-016/NF-009; risco competitivo e de uso indevido de equipamento fiscal | produto/segurança | M | A | 🟠 | Roldão | Classificação de acesso por fonte do cérebro (público-cliente × restrito-interno); identidade do interlocutor obrigatória; resposta cliente-facing filtra pelo nível "uso"; pergunta técnica restrita de cliente → oferta de serviço, nunca o procedimento | ativo |

## Riscos por categoria

### Projeto / produto
- R-001 (escopo), R-003 (resposta errada), R-011 (inveja de funcionalidade), R-015 (portes diferentes), R-016 (erro de transcrição), R-017 (inventa diagnóstico técnico), R-021 (desconto IA×prática)

### Técnico
- R-006 (dependência de provedor), R-010 (dependência do Aferê), R-018 (qualidade/manutenção do cérebro)

### Regulatório / segurança
- R-004 (PII), R-007 (prompt injection), R-020 (vazamento de dado de terceiro no cérebro), R-022 (vazamento de conhecimento técnico restrito a cliente)

### Gente / time
- R-002 (adoção)

### Financeiro
- R-005 (custo de uso de IA/mensageria), R-012 (margem por tenant negativa), R-019 (custo de transcrição STT)

### Mercado
- R-009 (buy-vs-build), R-013 (dependência da base do Aferê)

### Operação / infra
- R-014 (complexidade de configuração/onboarding); indisponibilidade do canal WhatsApp ou do LLM → fallback para atendimento humano (parte de R-006).

## Riscos vigiados (não-ativos, mas reabrir se gatilho)

| ID | Descrição | Gatilho para reativar |
|---|---|---|
| R-V-001 | <ex.: pedido de feature internacional> | <quando ≥3 clientes pedirem em pesquisa> |

## Riscos resolvidos (mover para histórico)

| ID | Descrição | Como foi resolvido | Quando |
|---|---|---|---|
| R-X | <...> | <...> | 2026-05-28 |

## Revisão

- Frequência: a cada marco (fechamento de fase) e mensal durante a Fase 1.
- Próxima revisão: ao fim do preenchimento da descoberta.
- Revisores: Roldão + responsável técnico (a definir no ADR de stack).

## Critério para promover de `draft` para `stable`

- [ ] ≥5 riscos identificados (3 categorias diferentes no mínimo).
- [ ] Cada risco tem responsável nomeado.
- [ ] Cada risco tem mitigação concreta (não "monitorar").
- [ ] Frequência de revisão definida.
