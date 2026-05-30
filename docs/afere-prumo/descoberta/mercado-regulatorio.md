---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 13/17
proximo: docs/descoberta/dados-existentes.md
idioma: pt-BR
limite-linhas: 200
proposito: leis, normas, órgãos e prazos aplicáveis ao domínio.
---

<!--
template: mercado-regulatorio.md
destino: docs/descoberta/mercado-regulatorio.md
uso: só projetos regulados (financeiro, saúde, educação, telecom, energia, governo, dados pessoais sensíveis).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3 (condicional, 🔵)
limite: ≤200 linhas.
-->

# Mercado regulatório — Aferê Prumo

> Se o produto NÃO é regulado, marcar este arquivo como N/A em `docs/nao-aplica.md` com gatilho de reavaliação.

## 1. Domínio regulado

- **Setor**: dados pessoais (LGPD) + metrologia legal (domínio do serviço da empresa).
- **Atividade**: infraestrutura de IA que atende clientes (WhatsApp) e organiza dados de uma empresa de balanças que faz venda, manutenção, **calibração/aferição com selo (Inmetro/IPEM/RBC)** e locação.
- **Nota**: o software **não** é o instrumento de medição regulado; quem é regulado pela metrologia legal é a balança e o serviço de calibração. Mas se a IA gerar/gerenciar **certificados e prazos de calibração**, ela toca o domínio regulado — o conteúdo do certificado deve seguir as normas, não pode ser "inventado" pela IA.

## 2. Leis e normas aplicáveis

| ID | Norma | Órgão | Aplica a | Prazo de conformidade |
|---|---|---|---|---|
| REG-001 | LGPD (Lei 13.709/2018) | ANPD | Todo tratamento de dado de cliente (nome, telefone, CNPJ, endereço, histórico) | vigente |
| REG-002 | Marco Civil da Internet (Lei 12.965/2014) | — | Guarda de registros de acesso/aplicação | vigente |
| REG-003 | Metrologia legal — Portarias/RBC do Inmetro e IPEM estaduais | Inmetro / IPEM | Conteúdo e validade de certificados de calibração/aferição (domínio do serviço) | vigente |
| REG-004 | Código de Defesa do Consumidor (Lei 8.078/1990) | Procon/Senacon | Atendimento e oferta ao cliente final (inclusive se feita por IA) | vigente |
| REG-005 | Diretrizes de IA (PL 2338/2023 em tramitação; boas práticas ANPD) | ANPD/futuro | Uso de IA que interage com pessoas — acompanhar evolução | em evolução |

## 3. Órgãos fiscalizadores

| Órgão | O que fiscaliza | Penalidade típica |
|---|---|---|
| ANPD | LGPD | Advertência → multa até 2% do faturamento (limitado a R$ 50 milhões/infração) |
| Bacen | sistema financeiro | Multa, suspensão, descredenciamento |
| <Receita Federal> | <obrigações fiscais> | <multa por NF-e atrasada, etc.> |
| <Anvisa> | <saúde, dispositivo médico> | <suspensão de certificação> |

## 4. Certificações que o produto precisa / pretende obter

| Certificação | Quando | Custo estimado | Status |
|---|---|---|---|
| <ISO 27001> | <antes de F-3> | <R$ X> | <não iniciado> |
| <SOC 2 Type II> | <antes de cliente enterprise> | <R$ Y> | <não iniciado> |
| <PCI DSS> | <quando armazenar PAN> | <R$ Z> | <não aplicável V1> |
| <Certificação Bacen> | <quando virar IF> | <R$ W> | <não aplicável V1> |

## 5. Obrigações recorrentes

| Obrigação | Frequência | Responsável | Próxima entrega |
|---|---|---|---|
| RIPD revisão | <anual> | <DPO> | 2026-05-28 |
| ROPA atualização | <toda mudança de tratamento> | <DPO> | <contínuo> |
| Auditoria externa | <anual> | <CFO> | 2026-05-28 |
| Relatório de incidentes | <a cada incidente, ≤72h> | <DPO> | <quando ocorrer> |

## 6. Pontos críticos identificados

- **🔴 RT não habilitado (decisão maio/2026)**: a Balanças Solution **não possui Responsável Técnico habilitado (CREA/CRQ)** no momento. Regras inegociáveis daí decorrentes:
  - Documentos externos (certificado, proposta) usam o papel **"Responsável pela Emissão"** (**Roldão** — designado pelo dono em 2026-05-29) — **NUNCA "RT"**.
  - A IA é **proibida de afirmar acreditação RBC ou ISO/IEC 17025** que a empresa não tem.
  - **Disclaimer A (não-acreditação RBC)** entra em **todo** certificado; **Disclaimer B** (verificação metrológica legal pelo Ipem) entra quando o equipamento é classe III/IIII de uso comercial.
- **Certificado = 2 conferências**: agente Metrologia confere 30+ campos obrigatórios (ISO 17025) e bloqueia se houver erro (ex.: peso padrão vencido, incerteza não informada); só então o Responsável pela Emissão revisa, preenche incerteza e assina. PDF leva assinatura + QR de validação.
- **PII de cliente via WhatsApp/LLM**: nome, telefone, CNPJ, histórico → LGPD; base legal, ROPA, direitos do titular (fase-2/C6); pseudonimização antes do LLM.
- **Atendimento por IA ao consumidor**: a IA opera "com" o humano (Inbox aprova tudo que vai ao cliente); permitir falar com humano (CDC).
- **"Camada de Confiança da IA" como capacidade de PRODUTO obrigatória da V1** (não só detalhe técnico), com responsável: (a) **pseudonimização pré-LLM**; (b) **score de toxicidade/ofensa na SAÍDA** antes de mostrar ao cliente; (c) **defesa contra instrução vinda do conteúdo do cliente** (prompt injection — R-007); (d) **trilha imutável** de todo prompt/resposta. Lição da análise de concorrentes (todos os enterprise embalam isso como produto).

### 6.1 Penalidades de metrologia legal (fonte: portarias no cérebro técnico)

As **Portarias Inmetro 157/2022 (balanças)** e **289/2021 (pesos padrão)** remetem expressamente às penalidades do
**Art. 8º da Lei nº 9.933/1999** (que dispõe sobre as competências do Inmetro). Tipos de penalidade previstos
(em ordem de gravidade): **advertência → multa → interdição → apreensão → inutilização** do instrumento.
A própria 157/2022 prevê marcações como **"INTERDITADO PARA VENDA DIRETA AO PÚBLICO"** e que o **Inmetro pode
interditar a utilização** de instrumento defeituoso.

- **Implicação para a IA (reforça D-PROD-007 / NF-003)**: se a IA emitir certificado afirmando acreditação/RT
  que a empresa não tem, ou liberar instrumento fora de conformidade, **a empresa (e o Responsável pela Emissão)**
  responde — daí as **2 conferências** serem **obrigação legal**, não boa prática (ver J-009).
- **Quem responde**: o **Responsável pela Emissão** (pessoa física designada: **Roldão**, decisão do dono 2026-05-29) e a empresa (Controlador).
- ⚠️ **Validar com advogado de conformidade**: os **valores** de multa e a aplicação exata por tipo de infração
  (a Lei 9.933/99 gradua a multa por gravidade) — não fixar valores sem confirmação jurídica. Fonte legal completa
  no cérebro: `dados-reais/_banco/cerebro/remesp/portaria-inmetro-157-2022-balancas.txt` (linha ~71) e `...-289-2021-...txt`.

## 7. Riscos regulatórios (cruzar com riscos.md)

- Vazamento/uso indevido de PII de cliente → R em `riscos.md`; mitigação via C6 LGPD na fase-2.
- IA dar resposta errada que vira oferta vinculante ao consumidor → revisão humana antes de fechar; ver H-005.
- Mudança na regulação de IA (PL 2338/2023) → acompanhar; baixo impacto na V1.

## 8. Pessoas envolvidas

- **DPO / Encarregado**: **Roldão (dono) acumula o papel inicialmente** (decisão 2026-05-29; permitido no porte atual). Registrar nome/contato no ROPA quando a fase-2 (LGPD) descongelar; **reavaliar encarregado dedicado ao abrir comercialmente para outros clientes** (vira gatilho).
- **Responsável pela Emissão de certificados** (pessoa física exigida pela norma): **Roldão** (designado pelo dono em 2026-05-29). ⚠️ **Formalizar**: registrar a **qualificação técnica** + **termo de designação** e onde fica arquivado — o nome já está cravado; falta só o ato formal (pendência do dono). Substitui o antigo "a nomear".
- **Controlador**: **Solution Automação e Pesagem LTDA**, CNPJ **50.412.190/0001-22**, Rondonópolis-MT (**ratificado pelo dono em 2026-05-29**). A empresa trocou de CNPJ ~set/2025 — antes **Balanças Solution LTDA**, Campo Grande-MS, mantida como **histórico** para dados anteriores.
- **Advogado de compliance**: a contratar/consultar pontualmente — em especial para as **penalidades do Inmetro/IPEM** (emissão sem RT habilitado) e a responsabilidade legal do certificado (ver §6; as portarias 157/2022 e 289/2021 estão no cérebro técnico para consulta).
- **Auditor externo**: não contratado (não exigido na escala atual).

## 9. Preparação para conformidade LGPD (insumos prontos para a fase-2)

> ⚠️ Os arquivos formais (`conformidade/lgpd/ropa.md`, `aipd.md`, `retencao-dados.md`) estão na **fase-2 congelada**.
> Esta seção **prepara todo o conteúdo** deles aqui na descoberta (2026-05-29) — quando a fase-2 descongelar, é só transferir.

### 9.1 Operações de tratamento (insumo do ROPA)

| Operação | Dados pessoais | Base legal (LGPD) | Retenção sugerida |
|---|---|---|---|
| Cadastro de cliente (Aferê) | nome, CNPJ/CPF, telefone, e-mail, endereço | execução de contrato (Art. 7º V) | enquanto cliente + 5 anos (fiscal) |
| Atendimento WhatsApp (texto) | telefone, conteúdo da conversa | execução de contrato | 2 anos |
| **Áudio do WhatsApp (bruto)** | voz (dado que pode revelar sensível) | execução de contrato + legítimo interesse | **reter o áudio bruto por 3 meses** (decisão do dono 2026-05-29); depois descartar com registro de auditoria — guarda-se a transcrição (texto) por 2 anos |
| **Transcrição do áudio** | conteúdo transcrito | execução de contrato | 2 anos (liga a OS/orçamento) |
| Orçamento / OS / certificado | dados do cliente + equipamento | execução de contrato + obrigação legal (metrologia) | 5 anos |
| Logs / auditoria da IA | identificador + ação | legítimo interesse + obrigação | 6 meses (app) / 5 anos (fiscal) |
| Pagamento / cobrança | dados de cobrança | obrigação legal/fiscal | 5 anos |
| **Dados de terceiros** (clientes finais nos áudios; parceiros do grupo) | nome, voz | legítimo interesse (conhecimento agregado) | **só agregado/anonimizado** — não individualizar a outro tenant (R-020) |

- **Controlador**: **Solution Automação e Pesagem LTDA**, CNPJ **50.412.190/0001-22**, Rondonópolis-MT (ratificado 2026-05-29 — ver §8). **Encarregado**: Roldão (decisão 2026-05-29).

### 9.2 Avaliação de impacto (insumo da AIPD) — "transcrição de áudio + resposta automatizada"

- **O que trata**: áudio bruto + transcrição + conteúdo da conversa.
- **Quem é afetado**: cliente final + equipe.
- **Decisão automatizada**: a IA sugere, mas **toda saída ao cliente passa por revisão humana** (D-PROD-006) — não há decisão automatizada sem humano (atende Art. 20).
- **Riscos** (já mapeados): desconto/ação errada (R-016), invenção de diagnóstico (R-017), vazamento de áudio/terceiro (R-020), vazamento de conhecimento restrito a cliente (R-022).
- **Supervisão humana (Art. 20)**: canal = **a fila de aprovação (Inbox)**; quem revisa = dono/equipe do escritório (2 pessoas); regra de bloqueio = desconto acima do teto, valor > R$ 10k, assunto regulado → trava até revisão; transparência = cliente sempre pode "falar com humano".

### 9.3 Transferência internacional (insumo do ROPA §4)

- **Pendente da decisão de hospedagem** (adiada para o ADR — dono 2026-05-29): se Brasil, sem transferência; se LLM/STT em provedor fora, exige base legal + cláusulas-padrão + pseudonimização pré-LLM (NF-006). STT **local** evita transferência do áudio.

## Critério para promover de `draft` para `stable`

- [x] ≥3 normas aplicáveis identificadas com fonte.
- [ ] Cada certificação tem status declarado.
- [x] DPO/encarregado nomeado (Roldão, inicial — §8).
- [x] Pontos críticos têm referência cruzada (riscos R-016..R-022, decisões D-PROD, §9 insumos LGPD).
