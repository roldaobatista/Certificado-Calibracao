---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 15/17
proximo: docs/glossario.md
idioma: pt-BR
limite-linhas: 200
proposito: APIs e sistemas terceiros que o produto depende.
---

<!--
template: integracoes-externas.md
destino: docs/descoberta/integracoes-externas.md
uso: condicional — só se depende de terceiros. Marque N/A em nao-aplica.md se autocontido.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3 (condicional, 🔵)
limite: ≤200 linhas.
-->

# Integrações externas — Aferê Prumo

> Cada integração é dependência. Mapear ANTES de codar para evitar surpresa de SLA, custo ou contrato.

> **O que é `ordem-descoberta 15/17`?** Os documentos da Descoberta seguem uma sequência fixa de 17 etapas. Este é o 15º. O campo `proximo` (no topo do arquivo) indica qual documento preencher logo em seguida — aqui, o glossário do produto. É só um roteiro de leitura/preenchimento, não tem nada a ver com prioridade técnica.

## Formato canônico

Cada integração tem:
- **Provedor**
- **Finalidade no produto**
- **Endpoint / método de integração** (REST, webhook, OAuth, SFTP, e-mail, etc.)
- **SLA contratado** (uptime, tempo de resposta)
- **Custo** (faixa mensal estimada V1 e V2)
- **Plano B** se cair
- **Conformidade**: LGPD (DPA assinado?), região (Brasil?), retenção
- **Status**: <contratado | em negociação | apenas avaliado | descartado>

> Provedores específicos serão decididos via ADR na fase de arquitetura (tecnologia só na hora certa).
> Aqui registramos as dependências que a visão (plano do dono = piso) já implica.

## INT-000 — Aferê / "Certificado de calibração" (ERP operacional — NÚCLEO)

- **Finalidade**: é a **fonte oficial dos dados do negócio** — clientes, equipamentos, ordens de serviço, certificados de calibração, histórico. A IA **consulta e age** sobre esse sistema; nunca inventa dado operacional.
- **O que é**: ERP SaaS multi-tenant em Python/Django + PostgreSQL (`C:/projetos/Certificado de calibracao/`), em construção, com a Balanças Solution como primeiro usuário (dogfooding).
- **🔗 INTEGRAÇÃO 100% AO AFERÊ, VIA MÓDULO PRÓPRIO (D-PROD-021 — decisão do dono 2026-05-29):** a camada de IA é **100% integrada ao Aferê** — fonte única da verdade, **sem nenhuma base de dados paralela** (reforça D-PROD-009/017). Toda a conversa com o Aferê é **encapsulada em um MÓDULO PRÓPRIO de integração** (camada dedicada/isolada — *anti-corrosion layer*, ports & adapters), **não espalhada** pelos agentes: os agentes falam com esse módulo, e só ele fala com o Aferê. **O DESENHO técnico do módulo** (contratos, API/DRF × banco × eventos, sincronização, autenticação) **é discutido na ETAPA CERTA do planejamento** — o **ADR-0001** (`docs/adr/ADR-0001-stack-e-integracao-afere.md`), hoje **congelado** até a descoberta fechar. Aqui fica firme **o princípio** (100% + módulo próprio); o **como** vem depois, na hora certa.
- **⚙️ A IA OPERA o Aferê por completo (D-PROD-022 — dono 2026-05-29):** a integração é **read + write completo** —
  a IA pode **executar tudo que o usuário precisar** no Aferê: **abrir/editar orçamento, mexer na agenda, abrir/atualizar
  OS, cadastro, disparar fluxo de certificado, financeiro** etc. (não é só consulta). **Freios intactos:** o que vai ao
  cliente ou é irreversível passa pela **aprovação humana** (Nível 1); grava **campo estruturado validado** (nunca texto
  livre em doc oficial); cada agente só no seu domínio (NF-005); 2 conferências no certificado (NF-001).
- **Método de integração**: a definir no ADR-0001 — provavelmente API interna (DRF) e/ou banco/eventos, **sempre atrás do módulo próprio**. Vantagem: **mesma casa, em construção** → dá pra desenhar a integração junto (não é sistema fechado de terceiro).
- **Criticidade**: 🔴 máxima — sem o Aferê, a IA não tem sobre o que agir.
- **Duplo papel (D-PROD-017, dono 2026-05-29)**: além de fonte de **dado exato** (consulta pontual), o **Aferê inteiro é também base de conhecimento** — todo o seu conteúdo é indexado no cérebro (INT-010) para busca por significado.
- **Conformidade**: o Aferê já é multi-tenant + RLS + auditoria WORM; a IA herda esses limites de isolamento e acesso (importante: o Aferê como conhecimento mantém o isolamento por empresa e o acesso por audiência — D-PROD-016).
- **Status**: em construção (integração nasce junto).

## INT-001 — WhatsApp Business (canal principal com o cliente)

- **Finalidade**: receber e responder clientes (atendimento, orçamento, aviso de prazo).
- **⚠️ Áudio domina (D-PROD-013)**: nos dados reais, a **maioria das mensagens dos clientes é de VOZ** (PTT). Este canal exige **transcrição de áudio (STT)** como etapa obrigatória de entrada — ver **INT-009**. Sem STT, a IA não entende o que o cliente pediu.
- **Endpoint**: WhatsApp Business Platform (API oficial Meta/Cloud API) ou BSP homologado. Usar **API oficial** (regra do plano).
- **Criticidade**: 🔴 alta. **Plano B**: atendimento humano no WhatsApp comum.
- **Conformidade**: trata PII (telefone, nome, conteúdo) → ROPA + DPA; verificação Meta pendente.
- **Status**: apenas avaliado.

## INT-002 — Provedor de IA / LLM (o "cérebro")

- **Finalidade**: entender mensagens, classificar, compor resposta, montar rascunho de orçamento, organizar conhecimento.
- **Endpoint**: API de LLM — inclinação do plano é **Anthropic Claude (Haiku + Sonnet)**; decidir no ADR-0000 (uso de IA).
- **Criticidade**: 🔴 alta. **Plano B**: trocar provedor via camada de adaptação. Guardrail de custo (G-005) + kill-switch.
- **Conformidade**: **pseudonimização antes de enviar ao LLM** (não mandar PII desnecessária); DPA do provedor.
- **Status**: apenas avaliado.

## INT-009 — Transcrição de áudio (STT — voz → texto)

- **Finalidade**: converter as **mensagens de voz** (a maioria no WhatsApp — D-PROD-013) em texto antes de o cérebro/agentes entenderem. Também serve para áudios em e-mail/Teams e para transcrever o **acervo histórico** (memória da IA).
- **Método**: a definir via ADR. **Já provado nesta descoberta que dá para rodar LOCAL e de graça** (whisper.cpp + modelo open-source `large-v3-turbo`, sem serviço pago, sem mandar áudio para fora — ver skill `transcrever-audio-whatsapp`), o que **zera o custo por minuto** e **mantém o áudio dentro de casa (LGPD)**. Alternativa: API de STT paga (custo por minuto + envia áudio do cliente a terceiro — pior para LGPD).
- **Criticidade**: 🔴 alta (sem isso o canal principal fica "surdo"). **Plano B**: pedir ao cliente que escreva (péssima UX) ou transcrição manual.
- **Custo**: local ≈ 0 (só CPU/tempo); API paga = por minuto de áudio (entra na conta da assinatura — G-005).
- **Conformidade**: se local, o áudio **não sai da infraestrutura** (ótimo p/ LGPD). Se API, exige DPA + pseudonimização + avaliação de transferência internacional (TIA).
- **Status**: apenas avaliado (prova de conceito local feita em 2026-05-28: 4,7 h de áudio a ~0,95× tempo real, qualidade ótima).

## INT-010 — Cérebro técnico (base de conhecimento com busca por significado)

- **Finalidade**: a base de conhecimento **não-estruturado** que dá autoridade técnica à IA (D-PROD-014) — manuais, procedimentos de calibração, códigos de erro, normas. Distinto do Aferê (dado estruturado/exato). É a Onda 0.
- **Estado atual (já coletado nesta descoberta)**: **1.099 fontes (~84 MB de texto)** em `dados-reais/_banco/cerebro/` — 876 manuais, 143 procedimentos de calibração, 7 tabelas de código de erro, 24 normas OIML (R76/R111/R60/R134), 11 documentos Inmetro/IPEM (VIM, GUM, Portarias 157/2022 e 289/2021), + guias Mettler Toledo. Índice: `dados-reais/_banco/cerebro/INDICE-CEREBRO.md`.
- **+ Conhecimento dos parceiros (fonte agregada do ramo)**: o **conhecimento extraído do grupo nacional de balanceiros** (250 técnicos · 946 áudios transcritos + 20.240 mensagens) — vocabulário do ramo, marcas/modelos/peças, problemas→soluções e preços de mercado — está consolidado em `dados-reais/grupos/_transcricao/conhecimento-parceiros.md`. É **agregado e anonimizado** (sem nome de terceiro, PII mascarada — R-020), classificado **restrito-interno** (D-PROD-016) e tem **autoridade baixa** na hierarquia abaixo (apoio, nunca fonte oficial ao cliente). O subproduto `vocabulario-tecnico.txt` alimenta o **prompt do STT** (INT-009), melhorando a transcrição de termos técnicos (célula, IND780, excentricidade...).
- **Ingestão**: via INT-005 (Drive/OneDrive) + extração de PDF/doc → texto, **+ o Aferê INTEIRO como base de conhecimento** (D-PROD-014/017 refinado pelo dono 2026-05-29): histórico de OS, certificados, orçamentos, conversas e configurações do Aferê são indexados para busca por significado (além da consulta pontual do INT-000). **Armazenamento e busca semântica** (qual banco vetorial / embeddings) = decisão de ADR na fase de arquitetura (não antecipar stack).
- **Criticidade**: 🔴 alta (sem cérebro, a IA não diagnostica nem cita fonte). **Requisitos**: citação de fonte obrigatória, isolamento multi-tenant, hierarquia de confiança das fontes, detecção de lacuna (D-PROD-014).
- **Mecanismo de isolamento entre empresas (requisito de segurança, não só promessa — C-6 da auditoria):** a busca por significado deve **filtrar por empresa ANTES de retornar** qualquer resultado (o filtro de tenant é aplicado na consulta, nunca depois); o **Roteador** (que vê mensagens de todas as empresas) nunca cruza dado entre tenants. **Teste obrigatório de vazamento**: um funcionário da empresa A tentando achar dado/tom da empresa B deve retornar **zero** — entra na suíte de segurança e roda a cada release. (Conhecimento técnico genérico — manual Toledo, norma — é compartilhável; dado de cliente/empresa **não**.)
- **Mecanismo de acesso por audiência (D-PROD-016 — A-5/A-6 da auditoria):** a classificação **público-cliente × restrito-interno** é **propriedade de cada fonte** (etiquetada na ingestão, ver INDICE-CEREBRO), não decidida na hora pela pergunta. Ao responder, a IA filtra pela **identidade do interlocutor** (cliente externo × funcionário autenticado) **+** a etiqueta da fonte; um **guardrail rejeita** resposta que contenha trecho "restrito-interno" para cliente externo (teste de vazamento de conhecimento — R-022).
- **Riscos associados**: R-017 (inventar diagnóstico), R-018 (desatualizar/conflito de fontes), R-020 (vazamento de dado de terceiro).
- **Status**: matéria-prima coletada; tecnologia do índice a definir no ADR.

### Hierarquia de precedência das fontes (regra de desempate — gaps da auditoria V2)

> Fecha dois gaps da auditoria: (1) **conflito entre versões de norma técnica** não modelado e (2) **Aferê com duplo papel** (dado exato + conhecimento) sem regra de desempate. O cérebro tem 1.099+ fontes que **se contradizem** (revisões diferentes do mesmo manual, norma nova × revogada, palpite de parceiro × manual oficial). Sem regra de desempate, a IA pode citar fonte errada ou revogada. Esta hierarquia é **obrigatória** e aplicada **na recuperação, antes de responder** (o detalhe técnico de como vai para o ADR do cérebro).

**(A) Fato do negócio (preço, cliente, agenda, prazo, status de OS) → o Aferê SEMPRE vence.** O **dado estruturado do Aferê (INT-000)** tem precedência absoluta sobre qualquer interpretação por busca semântica do mesmo assunto no cérebro. A IA **nunca** contradiz um valor exato do Aferê com algo "lembrado" do conhecimento (reforça D-PROD-009/012/017). Se a busca semântica devolver um dado que diverge do Aferê, vence o Aferê e a IA **sinaliza a divergência ao revisor**.

**(B) Conhecimento técnico-legal (como calibrar, o que é obrigatório, como diagnosticar) → ordem de autoridade decrescente:**
1. **Norma legal brasileira vigente** — Portaria Inmetro vigente (ex.: 157/2022 p/ balanças, 289/2021 p/ pesos padrão), Lei 9.933/99, RTM. É lei: vence tudo.
2. **Recomendação OIML recepcionada** pela norma BR (R76, R111, R60, R134...) — base técnica das portarias.
3. **Guia/vocabulário Inmetro** (VIM, GUM, VIML) — para método e cálculo de incerteza.
4. **Manual oficial do fabricante na versão vigente**, para o modelo específico (Toledo etc.) — procedimento, peça e código de erro daquele equipamento.
5. **Procedimento de calibração interno** alinhado às fontes acima.
6. **Conhecimento de parceiros/mercado** (grupo de balanceiros) — **apoio interno apenas** (restrito-interno): **nunca** citável como fonte oficial ao cliente nem como base de decisão metrológica (é informal/não-validado). Serve para vocabulário, pistas de diagnóstico e referência de preço de mercado.

**(C) Conflito de versão da MESMA fonte (rev.15 × rev.16; norma nova × antiga) → vence a vigente/mais recente.** Cada fonte carrega metadado de vigência: `revisao`, `data`, `status` (`vigente | revogada | substituída-por`). **Exceção (caso histórico):** quando o caso exige a regra da época — recalibração/laudo de equipamento antigo, certificado já emitido, contrato que fixou a norma da assinatura — usa-se a **versão da época** e a IA **sinaliza** ("conforme norma X vigente em <data>"). Fonte **revogada** nunca é apresentada como vigente; só aparece com aviso de revogação.

**(D) Conflito não resolvível pelas regras acima → não escolher em silêncio.** A IA **marca o conflito**, responde com a fonte de maior autoridade **e alerta a curadoria/revisor** — não decide sozinha entre duas fontes oficiais que divergem (liga em R-018).

> Os metadados de vigência e a etiqueta público-cliente×restrito-interno são **propriedade de cada fonte**, atribuídos na **ingestão** pela curadoria do cérebro (papel humano — ver `agentes.md` e `INDICE-CEREBRO.md`). A deduplicação de fonte repetida (pastas Toledo duplicadas no Drive) usa **hash + revisão**, com revisão humana — ver `dados-existentes.md` e `_drive/ACHADOS-DRIVE.md`.

## Fluxo ponta-a-ponta do áudio do cliente (a desenhar em ADR dedicado)

Sequência que liga INT-001 → INT-009 → INT-010/INT-002 → INT-001, ainda sem detalhe de implementação (vai para ADR):

1. Cliente envia **áudio** no WhatsApp (INT-001).
2. Áudio entra na **fila de transcrição** (INT-009) → vira texto + **score de confiança**.
3. **Armazenamento**: onde mora o áudio bruto e por quanto tempo (retenção — ver `conformidade/lgpd/retencao-dados.md`, hoje em branco); a transcrição fica ligada a cliente/ordem/data/origem.
4. Texto entra no **cérebro/agentes** (INT-010 + INT-002) — busca semântica + consulta ao Aferê (INT-000).
5. IA monta resposta/rascunho → **fila de aprovação** (Inbox) → volta ao cliente pelo WhatsApp.
6. **Registro de auditoria** de toda a cadeia (quem aprovou, qual fonte citada).

> ⚠️ **Pendências deste fluxo (gaps da auditoria, a resolver na arquitetura):** onde mora o áudio bruto e prazo de retenção (R-020, LGPD); como o texto se liga ao cliente/ordem; tratamento de baixa confiança (R-016, devolver ao cliente em texto antes de agir).

## Resumo das integrações (do plano = piso)

| ID | Fonte/Provedor | Finalidade | Criticidade | Prioridade |
|---|---|---|---|---|
| INT-000 | Aferê (ERP Django/Postgres) | Dados oficiais do negócio | 🔴 máxima | núcleo |
| INT-001 | WhatsApp Business API | Canal com o cliente | 🔴 alta | onda 1 |
| INT-002 | LLM (Claude Haiku+Sonnet) | "Cérebro" da IA | 🔴 alta | núcleo |
| INT-003 | E-mail (Outlook 365 / MS Graph) | Canal/entrada de demanda | 🟠 alta | onda 1 |
| INT-004 | Conta Azul → **Aferê** | **Financeiro é do próprio Aferê (INT-000)** — NFS-e (PlugNotas), boleto/PIX (Asaas), contas a receber, conciliação; **a IA opera o Aferê** pra isso (D-PROD-022). **Conta Azul = legado fora do escopo da IA** (como o Auvo). | — | fora de escopo |
| INT-005 | Google Drive / OneDrive | Base documental (PDFs, contratos) | 🟠 média | cérebro documental |
| INT-006 | Microsoft Teams | Conversas/decisões internas | 🟡 baixa | onda 2 |
| INT-007 | ClickUp | Tarefas/projetos | 🟡 baixa | onda 2 |
| INT-008 | Agenda (Outlook/Google) | Visitas/compromissos | 🟡 baixa | onda 2 |
| INT-009 | Transcrição de áudio (STT) | Voz do cliente → texto (pode ser local/grátis) | 🔴 alta | onda 1 |
| INT-010 | Cérebro técnico (1.099 fontes; busca semântica) | Conhecimento técnico não-estruturado | 🔴 alta | Onda 0 |

- **Orquestração de automações**: o plano sugere **n8n** como ferramenta de ingestão/automação — decidir no ADR.
- **Custos mensais**: `(A VALIDAR)` quando provedores forem escolhidos.

## Vendor lock-in

- **Crítico** (substituição custaria meses): INT-000 (Aferê — é o núcleo, por design).
- **Médio** (substituição custaria semanas): INT-001 (WhatsApp), INT-002 (LLM).
- **Baixo** (intercambiável): INT-005..008. *(INT-004 Conta Azul saiu do escopo — o financeiro é do Aferê, INT-000.)*

> Para integrações críticas, considerar **anti-corrosion layer** (ports & adapters) para que troca futura não exija reescrita do core. Detalhar em `docs/dominios/<dom>/anti-corrosion-layer.md` (C3).

> **Lock-in da ORQUESTRAÇÃO de processo (distinto do lock-in de LLM/WhatsApp):** a lógica de
> processo (máquina de estados, quem aprova o quê, regras de metrologia) precisa morar em **ativo
> nosso**, não presa na ferramenta de orquestração (ex.: n8n) — para trocar a ferramenta sem
> reescrever a operação.
>
> **Fonte única da verdade = Aferê (risco a evitar):** a IA **não replica** o modelo de dados em
> sistema paralelo. Risco a vigiar: a tentação de adotar um Dataverse/CRM horizontal que **duplique
> a verdade do Aferê**, criando dois donos do mesmo dado (esvazia o Aferê). Decidido em D-PROD-009.

## Conformidade global

> ⚠️ **Nenhuma integração foi contratada ainda** — todas estão "apenas avaliado". DPAs, TIA e mapa de
> PII serão preenchidos na fase-2 (conformidade) / ADR, antes de operar com cliente real. Esqueleto a preencher:

| Integração | PII/campos que trafega | Controlador | Sub-operador | DPA assinado? | Transfer. internacional? | Anonimização |
|---|---|---|---|---|---|---|
| INT-001 WhatsApp | telefone, nome, conteúdo, **áudio** | Balanças Solution | Meta/BSP | ⛔ pendente | a definir (hospedagem) | pré-LLM |
| INT-002 LLM | texto pseudonimizado | Balanças Solution | provedor de IA | ⛔ pendente | provável (EUA) → TIA | sim (NF-006) |
| INT-009 STT | **áudio bruto** | Balanças Solution | local OU API | n/a se local | n/a se local | — |
| INT-010 Cérebro | conhecimento técnico agregado | Balanças Solution | — | — | — | dado de terceiro não exposto (R-020) |

- **Decisão pendente que destrava a tabela**: transcrição **local × paga** e **hospedagem Brasil × fora** (afeta TIA). Registrar no ADR.

## Histórico de mudanças

| Data | Mudança | Motivo |
|---|---|---|
| 2026-05-28 | Integrações mapeadas (INT-000..009); todas "apenas avaliado" | Descoberta — nenhuma contratada ainda |
| 2026-05-29 | +INT-010 (cérebro técnico) e fluxo ponta-a-ponta do áudio | Auditoria de gaps (propagação das decisões de áudio/cérebro) |
| 2026-05-29 | INT-010: +conhecimento dos parceiros como fonte; +**hierarquia de precedência das fontes** (regra de desempate A/B/C/D) | Fecha gaps da auditoria V2 (conflito de versão de norma + duplo papel do Aferê) |
| 2026-05-29 | **INT-004 Conta Azul reclassificado como LEGADO fora do escopo da IA** — financeiro (NFS-e/boleto/cobrança) é do **Aferê**, operado pela IA (D-PROD-022) | Correção do dono na fase de arquitetura: premissa antiga "Conta Azul gera boleto" estava errada — quem faz é o Aferê |

## Critério para promover de `draft` para `stable`

- [ ] ≥1 integração crítica mapeada com plano B.
- [ ] Custo total mensal calculado.
- [ ] DPAs identificados para todas que tocam PII.
- [ ] Vendor lock-in classificado.
