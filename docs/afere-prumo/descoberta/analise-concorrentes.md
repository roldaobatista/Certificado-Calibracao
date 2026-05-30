---
owner: roldao
revisado-em: 2026-05-29
status: stable
idioma: pt-BR
limite-linhas: 320
proposito: registro da análise de 10 concorrentes (workflow multi-agente) e as melhorias que ela gerou para a descoberta
---

# Análise de concorrentes → melhorias para a descoberta

> Gerado por workflow multi-agente em 2026-05-28: **10 agentes** (1 por concorrente da lista do dono)
> + 1 síntese. Concorrentes: Salesforce/Agentforce, Microsoft Dynamics/Copilot, ServiceNow, Zendesk,
> Intercom/Fin, Freshdesk/Freddy, HubSpot/Breeze, Zoho/Zia, UiPath, Automation Anywhere.
> Foco: melhorar a DESCOBERTA (produto/diferencial/risco/hipótese/governança) — **sem decidir stack**.

## Resumo executivo

Os 10 convergem para lições dentro do nosso princípio-mãe ("opera COM o dono"): (1) cada agente
precisa virar **contrato explícito** (Tópicos/Ações/nunca-faz/escalonamento), não só nome de setor;
(2) **gatilhos de escalonamento nomeados** mesmo com tudo passando pela Inbox, para priorizar a fila;
(3) níveis de automação **graduáveis por tipo de ação** com critério numérico; (4) faltam métricas de
**saúde do agente** (aprovado-sem-edição, escalonamento+motivo, CSAT), distintas do volume; (5) o
**cérebro** deve ser base **versionada com citação de fonte** e **detecção de lacunas**. O contraste
competitivo mais forte é **filosofia** (eles otimizam deflexão autônoma; nós, aprovação humana em
domínio regulado) e **dado** (eles raciocinam sobre FAQ/contato; nós sobre o **equipamento vivo** no
Aferê). Risco recorrente: **buy-vs-build** — o atendimento genérico é comoditizável; o valor mora no
insubstituível (Aferê, certificado, prazo por equipamento, campo offline, restrição legal de RT).

## Rastreabilidade da propagação (auditoria 2026-05-29)

As 40 melhorias foram aplicadas nos documentos da descoberta (alta/média/baixa abaixo). A **fonte única**
de onde cada decisão/risco/hipótese gerada vive agora é o **[`indice-decisoes.md`](./indice-decisoes.md)**
(D-PROD/NF/G/J/R/H/INT). Cruzar lá quando precisar achar onde uma melhoria foi parar.

> **Teste disfarçado de concorrente (decisão 2026-05-29, atualizada na retomada):** a análise documental foi sobre
> **funções públicas**. **Decisão do dono: ✅ FAZER o teste disfarçado** (mystery shopping). **Roteiro simples:**
> alguém de confiança se passa por cliente e pede, em ≥1 concorrente, (1) um **orçamento** de calibração/manutenção e
> (2) um **atendimento** com dúvida técnica — anotando **tempo de 1ª resposta, tom, se atende por áudio/WhatsApp, o que
> pergunta, prazo e preço**. Comparar com o nosso padrão (tom em `regras-negocio.md §6.1`; exemplos em `exemplos-saida-ia.md`)
> para **copiar o que é bom e superar o que é ruim**. **Quem**: dono/pessoa de confiança. **Quando**: ≥1 teste antes de
> usar o eixo "aviso proativo"/atendimento como argumento de venda. **Cuidado legal**: registrar só o atendimento comercial
> recebido (não gravar pessoa sem ciência onde a lei exigir, não coletar dado pessoal de terceiros — LGPD).

## Diferenciais reforçados (a análise confirma)

1. **Filosofia assistido-primeiro como propósito** (não limitação) — vs. deflexão autônoma dos 10.
2. **Equipamento como entidade central + dado operacional vivo (Aferê)** — vs. FAQ/contato estático.
3. **Domínio metrológico-legal embutido** (certificado, 2 conferências, peso padrão, Disclaimer A, "Responsável pela Emissão").
4. **Aviso proativo por equipamento+norma** (antes de qualquer contato) — vs. renovação de contrato por data.
5. **Custo e simplicidade para PME de 9 pessoas, operável por não-programador**.
6. **Dois checkpoints humanos**: editorial (revisar texto) + bloqueio técnico — orquestradores só têm o bloqueio.
7. **Integração nativa com o Aferê** (mesma casa) — vs. RPA frágil por cima de sistema fechado.

> ⚠️ **Cautela de venda (A-13 da auditoria):** os diferenciais 2 e 7 (responder sobre o "equipamento vivo"
> consultando o Aferê em tempo real) dependem de uma integração que **ainda está em construção** (INT-000, sem
> contrato/SLA). **Não usar esse argumento em venda real até estar operando com dado real na Onda 1**; testar
> latência/consistência no dogfooding primeiro (liga a R-010).

## Melhorias APLICADAS nesta descoberta (alta prioridade) ✅

1. ✅ `concorrentes.md §4` — diferenciação reposicionada em 4 eixos duros (filosofia, dado, domínio, aviso proativo).
2. ✅ `concorrentes.md §5` + `riscos.md R-009` — risco buy-vs-build + Zoho/Microsoft + comoditização + fragmentação da verdade.
3. ✅ `riscos.md R-010/R-011` — dependência do Aferê; inveja de funcionalidade.
4. ✅ `nao-fazer.md` — gatilhos de escalonamento nomeados + níveis graduáveis por tipo de ação.
5. ✅ `metricas-chave.md §3.1` — métricas de saúde do agente; deflexão como guardrail observado (nunca meta).
6. ✅ `sintese-final.md §4.2` — ficha-contrato por agente + cérebro versionado com citação de fonte + detecção de lacunas.
7. ✅ `value-proposition-canvas.md §7` — equipamento como entidade central.
8. ✅ `hipoteses-a-validar.md` — H-006 a H-012 (critério de graduação; Inbox-não-vira-gargalo; banco de testes; offline; volume repetível; citar fonte; extração de documento).

## Melhorias de média prioridade — ✅ TODAS APLICADAS (2026-05-28, a pedido do dono)

- ✅ `riscos.md`/`mercado-regulatorio.md` — "Camada de Confiança da IA" como capacidade de produto (pseudonimização, toxicidade na saída, anti-injection, trilha imutável).
- ✅ `integracoes-externas.md` — risco de lock-in da **orquestração de processo** (lógica de processo em ativo nosso, não na ferramenta).
- ✅ `jornadas.md J-005` — formalizar como **máquina de estados** (tipo de passo, dono, gatilho, exceção); processo que "trava sozinho" na etapa obrigatória.
- ✅ `jornadas.md`/`nao-fazer.md` — nomear os 2 checkpoints (editorial vs bloqueio) no fluxo.
- ✅ `nao-fazer.md NF-004` — separar DECISÃO (IA) de GRAVAÇÃO no Aferê/certificado (campo estruturado validado, nunca texto livre de LLM).
- ✅ `jornadas.md J-006` — Inbox com resumo do caso, indicador de confiança para ordenar fila, aprovação em lote, reatribuição/delegação.
- ✅ `jornadas.md J-006` — "Cockpit de Governança de IA" (uma tela: agentes ativos, permissões, nível de automação, custo, kill-switch).
- ✅ `sintese-final.md Onda 0` — cérebro com detecção de lacunas (pergunta não respondida vira backlog de cadastro).
- ✅ `jornadas.md`/`vpc` — governança por regras em linguagem natural ("Minhas Regras" no caminho proativo).
- ✅ `personas.md P-002` — recursos de campo como teto do app offline (checklist, assinatura, foto antes/durante/depois, **ler QR para puxar histórico**, fila de sync com resolução de conflito).
- ✅ `personas.md P-C-001` — dono como "orquestrador/governador" + objeção "por que não usar HubSpot/Zoho pronto?" com resposta.
- ✅ `restricoes.md` — matriz de permissão por setor (quem vê/age em quê); toda governança operável por não-técnico.
- ✅ `metricas-chave.md §4` — barrar "taxa de deflexão" como anti-métrica.
- ✅ `nao-fazer.md §3/§4` — non-goals anti-suite (não adotar plataforma horizontal como núcleo; não virar helpdesk/CRM/RPA genérico; não responder por "achismo do LLM").

## Melhorias de baixa prioridade — ✅ TODAS APLICADAS (2026-05-28)

- ✅ `jornadas.md J-002/J-004` — motor genérico "prazo + alarme + escalonamento" reutilizável (calibração, devolução de locação, 1ª resposta, item antigo na Inbox).
- ✅ `jornadas.md`/`metricas` — política de SLA de atendimento por tempo (máx. 1ª resposta, máx. resolução, o que acontece ao estourar).
- ✅ `metricas-chave.md`/`jornadas.md J-002` — guardrail de **frequência de aviso** ao cliente (máx. mensagens/período, opt-out) — anti-spam.
- ✅ `sintese-final.md §4.1` — nomear 3 modos de uso: agente↔cliente (sempre Nível 1), copiloto↔atendente/dono (mais solto), análise↔gestão.
- ✅ `vpc` — ganho emocional de governança ("não tenho medo de esquecer nem de emitir errado").
- ✅ `integracoes-externas.md` — verbalizar risco de Dataverse/CRM horizontal duplicar a verdade do Aferê.
- ✅ `concorrentes.md §1` — separar plataformas de atendimento/CRM de orquestração/RPA; coluna "vem pronto vs segue sendo nosso".

## Riscos competitivos consolidados

Buy-vs-build (nº1) · comoditização rápida (12-18 meses) · inveja de funcionalidade/pressão por
automação total · âncora de expectativa de UX (Inbox precisa nascer polida) · fragmentação da verdade
(2º dono do dado) · régua de governança/auditoria elevada · vertical pronto por integrador ·
dependência da qualidade do Aferê. **Risco inverso (a favor):** o concorrente real continua sendo o
**não-uso** (planilha + WhatsApp) — não desviar o foco do piloto enxuto da Onda 1.

## Novas hipóteses geradas

H-006 a H-012 — registradas em [`hipoteses-a-validar.md`](./hipoteses-a-validar.md).
