---
owner: roldao
revisado-em: 2026-05-29
status: stable
idioma: pt-BR
limite-linhas: 150
proposito: índice único (fonte de verdade) de todas as decisões de produto, não-fazer, guardrails, riscos, hipóteses, jornadas e integrações — com 1 linha cada e link para o documento que detalha.
---

# Índice de decisões — Aferê Prumo

> Criado a partir da auditoria de gaps (2026-05-29): as decisões estavam espelhadas em vários documentos
> sem um lugar central. Aqui cada código tem **1 linha** e aponta para o documento que o define em detalhe.
> Em caso de divergência, **o documento-fonte vence** (este índice é só mapa).

## D-PROD — Decisões de produto (fonte: [`sintese-final.md §9`](./sintese-final.md))

| ID | Resumo |
|---|---|
| D-PROD-001 | Produto **SaaS multi-tenant** vendido por assinatura (add-on do Aferê); Balanças Solution = 1º cliente (dogfooding); configurável por empresa |
| D-PROD-002 | Toda saída ao cliente passa por **revisão humana** na Fase 1 |
| D-PROD-003 | Construir por **fases**, não tudo de uma vez |
| D-PROD-004 | Começar pela frente de **atendimento/orçamento** |
| D-PROD-005 | As ideias do dono são **piso, não teto** — propor além |
| D-PROD-006 | Princípio-mãe: IA **com você, não no lugar de você** (tudo ao cliente passa pela Inbox) |
| D-PROD-007 | Sem RT habilitado → "Responsável pela Emissão" + Disclaimer A + 2 conferências no certificado |
| D-PROD-008 | Ritmo de **1 agente por trimestre** (vale para a **evolução/maturação** pós-piloto; **revisto por D-PROD-018 no piloto** — lá todos ligam juntos, em Nível 1) |
| D-PROD-009 | ERP-núcleo a integrar é o **Aferê** (não Kalibrium/Auvo) |
| D-PROD-010 | Parâmetros: orçamento >R$10k escala pro dono (revisto por D-PROD-019: a IA monta o rascunho e o dono revisa); aviso de prazo 30+7 dias; anti-spam 1/assunto/semana; nada auto-envia por ora |
| D-PROD-011 | Modelo comercial: cobrança por faixa A/B/C/D + franquia de uso; add-on na fatura do Aferê; configurável |
| D-PROD-012 | Aferê = preços/valores; IA = regras de comportamento (desconto ≤3%, prazo ≤3 dias, pagamento à vista, deslocamento auto) |
| D-PROD-013 | **Áudio é capacidade CENTRAL** — IA transcreve áudio do WhatsApp (STT) e age; tom de voz vem das falas reais |
| D-PROD-014 | Cérebro com **busca por significado** (RAG), citação de fonte obrigatória, isolamento multi-tenant, hierarquia de confiança |
| D-PROD-015 | Banco operacional do Auvo pronto p/ migrar (341 clientes, 389 produtos, 424 itens) — base da Onda −1 |
| D-PROD-016 | **Níveis de acesso ao conhecimento por audiência**: cliente externo só vê uso/operação + seus dados; técnico/funcionário vê todo o cérebro |
| D-PROD-017 | **Espelha o Aferê no DADO** (estrutura, oferta, R$/km, parâmetros, locação) — nada em paralelo, se o Aferê não tem a IA não inventa; **MAS a camada de IA faz muito mais** que o Aferê (cérebro, agentes, STT, automação — D-PROD-005) e **o Aferê inteiro também é base de conhecimento** (D-PROD-014/016) |
| D-PROD-018 | **Piloto liga TODOS os agentes de uma vez** (dono, ciente do risco R-001) — revê o "1 agente/trimestre" (D-PROD-008) no piloto; freios: todos em Nível 1 (ligar ≠ autonomia), Inbox priorizada, dogfooding interno, métrica por agente, rollback individual |
| D-PROD-019 | **Valor alto (>R$10k): a IA MONTA o rascunho e escala pro dono revisar** (não "nem rascunha") — revisa D-PROD-010; freio = revisão humana; cliente novo+valor alto = confere dados antes |
| D-PROD-020 | **Cliente pede humano / reclama da IA → handoff IMEDIATO** pro atendente, sem insistir nem fila (reforça D-PROD-006 + CDC); prioridade alta na Inbox |
| D-PROD-021 | **Integração 100% ao Aferê via MÓDULO PRÓPRIO** dedicado (anti-corrosion layer; só ele fala com o Aferê) — sem base paralela (reforça D-PROD-009/017); o desenho técnico fica para o ADR-0001 (etapa certa, hoje congelado) |
| D-PROD-022 | **A IA OPERA o Aferê por completo** (read+write): abrir/editar orçamento, mexer agenda, abrir OS, cadastro, etc. — tudo que o usuário precisar; freios intactos (aprovação humana no que vai ao cliente, campo validado, domínio do agente, 2 conferências no certificado) |
| D-PROD-023 | **Nome do produto = "Aferê Prumo"** (tagline "a IA que mantém sua operação no prumo") — escolhido por auditoria de 5 agentes (4/5). Produto=Aferê Prumo · ERP=Aferê · 1º cliente=Balanças Solution. Substitui "Balanças Solution IA" |

## NF — Não-fazer (fonte: [`nao-fazer.md`](./nao-fazer.md))

| ID | Resumo |
|---|---|
| NF-001 | IA não emite/assina certificado sozinha (2 conferências) |
| NF-002 | IA não envia resposta/orçamento/cobrança/oferta sem aprovação humana |
| NF-003 | IA nunca afirma acreditação RBC/ISO 17025 nem usa "RT" |
| NF-004 | Nenhum agente inventa dado **nem diagnóstico/procedimento técnico** (só Aferê/cérebro curado; senão marca lacuna) |
| NF-005 | Nenhum agente sai do próprio domínio |
| NF-006 | Não enviar PII desnecessária ao LLM (minimização) |
| NF-007 | Não substituir instrumento de medição nem fazer pesagem fiscal |
| NF-008 | IA não responde sobre marca/modelo fora do acervo do cérebro → fila "acervo incompleto" |
| NF-009 | IA não passa conhecimento técnico restrito a cliente externo (só uso/operação + dados do próprio cliente) |
| NF-010 | IA nunca orienta o cliente a abrir a balança ou romper lacre/selo metrológico (Inmetro/IPEM — Lei 9.933/99); vira oferta de visita técnica |
| NF-V1-001..004 | Fora da V1: ~~revenda~~(revogado), NF-e, relatórios avançados, app mobile nativo |
| NF-OUT-001..003 | Integrar em vez de construir: canal WhatsApp, LLM, emissão NF-e |

## G — Guardrails/métricas (fonte: [`metricas-chave.md`](./metricas-chave.md))

| ID | Resumo |
|---|---|
| G-001 | Orçamento errado enviado sem revisão = 0 |
| G-002 | Satisfação do cliente no atendimento por IA |
| G-003 | Prazos de calibração avisados antes de vencer (base 0%) |
| G-004 | Adoção da equipe ≥80% |
| G-005 | Custo de IA/atendimento (LLM + WhatsApp + **STT** em linhas separadas) |
| G-006 | Anti-spam: máx. 1 msg/assunto/cliente/semana |
| G-007 | **Saúde e cobertura do cérebro** (% respondido, citação, lacuna, cobertura por marca) |

## J — Jornadas (fonte: [`jornadas.md`](./jornadas.md))

| ID | Resumo | Status |
|---|---|---|
| J-001 | Atendimento + orçamento pelo WhatsApp (principal) — P-001/P-003 | definida |
| J-002 | Agendamento e aviso de prazo de calibração — P-002/P-003 | definida |
| J-003 | Ordem de serviço de manutenção com histórico — P-002 | definida |
| J-004 | Locação de balança (ciclo de aluguel) | esboço — **Onda V2** (espelha o Aferê, D-PROD-017) |
| J-005 | Ciclo completo "do oi ao certificado" | definida |
| J-006 | Rotina do dono (Inbox, 15–30 min/dia) | definida |
| J-007 | Onboarding de empresa-cliente assinante (B2B) — perfis A/B/C/D | esboço (detalhar com o dono) |
| J-008 | Motorista: entrega/retirada (locação/equipamentos) — P-004 | esboço (pendente: dono da agenda — OS/Campo × Logística) |
| J-009 | Emissão de certificado de calibração (2 conferências) — Responsável pela Emissão | definida |

## Ver também
- Riscos **R-001..R-022** → [`riscos.md`](./riscos.md)
- Hipóteses **H-001..H-018** → [`hipoteses-a-validar.md`](./hipoteses-a-validar.md)
- Integrações **INT-000..INT-010** → [`integracoes-externas.md`](./integracoes-externas.md)
- Auditoria de gaps → [`ACHADOS-AUDITORIA.md`](./dados-reais/_auditoria/ACHADOS-AUDITORIA.md) (V1) + [`ACHADOS-AUDITORIA-V2.md`](./dados-reais/_auditoria/ACHADOS-AUDITORIA-V2.md) (sem viés)
