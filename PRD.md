# PRD — Plataforma Aferê de Certificação de Calibração

> **Documento:** Product Requirements Document (PRD)
> **Versão:** 1.8
> **Data:** 2026-04-19
> **Status:** Especificação em revisão — correções cirúrgicas aplicadas a partir da consolidação de duas análises críticas multidisciplinares (ver [ANALISE_CONSOLIDADA_PRD.md](./ANALISE_CONSOLIDADA_PRD.md))
> **Autor consolidador:** Equipe Aferê
> **Base documental:** [`ideia.md`](./ideia.md), [`iso 17025/`](./iso%2017025), [`normas e portarias inmetro/`](./normas%20e%20portarias%20inmetro)

---

## Sumário executivo

A **Plataforma Aferê de Certificação de Calibração** é uma solução metrológica composta por **aplicativo web** (gestão, revisão, emissão, portal do cliente) e **aplicativo Android** (execução em campo/laboratório, offline-first), conectados por um backend único que centraliza regras de negócio, cálculos, trilha de auditoria e a fonte oficial dos certificados.

Diferente de um simples gerador de PDF, o produto opera simultaneamente como **sistema metrológico**, **sistema da qualidade** e **sistema documental**, sustentando a **ABNT NBR ISO/IEC 17025:2017** e o ecossistema regulatório brasileiro (Inmetro / Cgcre / DOQ-CGCRE / NIT-DICLA / Portaria 157/2022 — IPNA, Portaria 289/2021 — pesos padrão, RTAC, RTM, ILAC P10/P14/G8).

A premissa de produto é: **nenhuma emissão viola as regras automatizadas declaradas em §9**. Toda emissão é precedida por validações duras que bloqueiam o fluxo (padrão vencido, ambiente fora da faixa, signatário sem competência, regra de decisão não acordada, etc.) — o sistema só libera assinatura quando todas as condições normativas automatizáveis estão verdes. A conformidade sistêmica ISO/IEC 17025 da organização depende, além disso, dos fatores humanos descritos em §16.2.

---

## 1. Visão e proposta de valor

### 1.1 Visão
Tornar a emissão de certificados de calibração de balanças (e, em fases seguintes, demais instrumentos) uma operação **tecnicamente defensável, rastreável e auditável de ponta a ponta**, executável tanto na bancada do laboratório quanto na planta do cliente, sem dependência de internet no momento da execução.

### 1.2 Proposta de valor

| Para... | Entregamos... | Que resolve... |
|---------|---------------|----------------|
| **Laboratório de calibração** | Plataforma única que substitui planilhas Excel + PDFs avulsos + WhatsApp | Risco de não conformidade em auditoria Cgcre, retrabalho, certificado emitido com erro |
| **Técnico calibrador** | App Android guiado, offline, com checklist e bloqueios | Esquecer ensaio, usar padrão vencido, anotar resultado errado |
| **Revisor / signatário** | Workflow de revisão e assinatura eletrônica auditável | Assinar serviço com falhas, perder rastreabilidade do "quem aprovou o quê" |
| **Cliente final** | Portal com QR code de verificação de autenticidade | Receber PDF adulterado, não saber quando recalibrar |
| **Gestor da qualidade** | Trilha imutável, indicadores, gestão de NC e auditoria interna | Preparar acreditação Cgcre sem evidência consolidada |
| **Inmetro / auditor Cgcre** | Estrutura preparada para **DCC (Digital Calibration Certificate)** | Falta de padronização e dificuldade de verificação documental |

### 1.3 Diferenciais competitivos
1. **Conformidade por arquitetura**: o sistema impede ações fora da norma; não depende da disciplina do técnico.
2. **Offline-first real**: execução completa sem rede, com sincronização posterior e reconciliação no backend.
3. **Web ↔ Android conectados**: mesma fonte de verdade, mesmo modelo de dados, mesma trilha de auditoria.
4. **Pronto para DCC**: modelo de dados preparado para exportação XML segundo Plano Estratégico Inmetro 2024–2027.
5. **Cobertura regulatória brasileira nativa**: cadastro vivo de DOQ-CGCRE, NIT-DICLA, RTM e portarias aplicáveis.

---

## 2. Objetivos e não-objetivos

### 2.1 Objetivos do produto (O que faremos)
1. Permitir cadastro completo de **clientes** e **equipamentos**, com vínculo obrigatório (1 equipamento → 1 cliente).
2. Permitir cadastro e controle de **padrões metrológicos** com cadeia de rastreabilidade.
3. Executar calibração via **wizard guiado passo a passo** no Android, com bloqueios automáticos.
4. Calcular **resultado bruto + incerteza expandida (k=2)** com balanço documentado.
5. Aplicar **regra de decisão** (ILAC G8) quando o cliente solicitar declaração de conformidade.
6. Emitir **certificado de calibração** assinado eletronicamente, em PDF/A, com QR code de verificação.
7. Manter **trilha de auditoria imutável** de toda alteração, revisão, aprovação e reemissão.
8. Operar **offline-first** no Android, com sincronização eventual.
9. Disponibilizar **portal do cliente** para consulta de certificados e verificação de autenticidade.
10. Sustentar **acreditação ISO/IEC 17025:2017** e regulação Inmetro/Cgcre.

### 2.2 Não-objetivos (O que NÃO faremos no MVP)
- Não emitiremos certificados de **ensaio** (apenas calibração).
- Não atenderemos **calibração clínica** (ISO 15189) nem **inspeção** (ISO/IEC 17020).
- Não substituiremos **ERP financeiro** — exportaremos dados via API.
- Não automatizaremos **agendamento de visitas técnicas** no MVP (entra na Fase 2).
- Não geraremos **certificado digital qualificado ICP-Brasil** no MVP — assinatura eletrônica auditável apenas.
- Não calibraremos balanças automáticas no MVP — foco em **NAWI / IPNA** (Portaria 157/2022).

### 2.3 Princípios de produto (não-negociáveis)
1. **Resultado e incerteza nunca são omitidos** em certificado com declaração de conformidade.
2. **Padrão vencido / sem certificado / fora da faixa BLOQUEIA** a emissão.
3. **Certificado não tem validade automática** — periodicidade é responsabilidade do proprietário do equipamento.
4. **Recomendação de intervalo de recalibração não consta no certificado** (salvo condição contratual específica e identificada).
5. **Laboratório acreditado**: respeitar **escopo, CMC e símbolo de acreditação** segundo DOQ-CGCRE-028.
6. **Nenhuma ferramenta sozinha garante ISO/IEC 17025** — o produto sustenta a conformidade, não a substitui.
7. **O sistema reconhece 3 perfis regulatórios da organização emissora** (ver §6.5) e cada perfil tem modelo de certificado próprio, regras de rastreabilidade próprias e bloqueios próprios. **As regras de arquitetura impedem que um perfil emita certificado fora do que lhe é permitido** (ex.: organização não-acreditada não consegue gerar selo Cgcre/RBC — o campo não existe na UI e validações de backend bloqueiam tentativa semântica).

---

## 3. Métricas de sucesso

| Categoria | Métrica | Meta MVP (12 meses) |
|-----------|---------|---------------------|
| Adoção | Laboratórios ativos | ≥ 20 |
| Adoção | Certificados emitidos / mês | ≥ 1.500 |
| Qualidade | % certificados emitidos sem reemissão por erro | ≥ 98% |
| Qualidade | Não conformidades em auditoria Cgcre por uso do sistema | 0 |
| Operação | Tempo médio de execução de calibração (campo) | ≤ 35 min |
| Operação | % de calibrações concluídas offline e sincronizadas com sucesso | ≥ 99,5% |
| Confiança | % de QR codes do certificado verificados pelos clientes | ≥ 30% |
| Negócio | NPS de técnicos calibradores | ≥ 60 |
| Negócio | Churn anual | ≤ 8% |

---

## 4. Contexto regulatório

### 4.1 Base normativa (vinculante)

| Referência | Aplicação no produto |
|------------|---------------------|
| **ABNT NBR ISO/IEC 17025:2017** | Competência, imparcialidade e operação consistente. Sustenta cláusulas 4 a 8. |
| **Portaria Inmetro nº 157/2022** | RTM de balanças não automáticas (IPNA) — classes I, II, III, IIII (base OIML R 76). |
| **Portaria Inmetro nº 289/2021** | RTM de pesos padrão (1 mg a 50 kg) — classes E1, E2, F1, F2, M1, M2, M3 (base OIML R 111). |
| **Portaria Inmetro nº 248/2008** | Pré-medidos por massa/volume — referência para EMA. |
| **DOQ-CGCRE-008** | Orientação para expressão da incerteza de medição. |
| **DOQ-CGCRE-028** | Uso do símbolo Cgcre em relatórios e certificados. |
| **NIT-DICLA-021 / 030 / 038** | Critérios para calibração, rastreabilidade e materiais de referência. |
| **NIT-DICLA-007** | Critérios gerais para acreditação — processo de acreditação de laboratórios. |
| **NIT-DICLA-026** | Requisitos específicos para laboratórios de calibração. |
| **DOQ-CGCRE-019** | Uso do símbolo ILAC MRA em certificados (Tipo A em reconhecimento internacional). |
| **ILAC P10** | Política de rastreabilidade metrológica. |
| **ILAC P14** | Política de incerteza em calibração. |
| **ILAC G8** | Regra de decisão e declaração de conformidade. |
| **ILAC G24** | Diretrizes para intervalos de calibração. |
| **EURAMET cg-18** | Boa prática para calibração de NAWI (referência técnica). |
| **Plano Estratégico Inmetro 2024–2027** | Preparação para DCC (Digital Calibration Certificate). |

### 4.2 Mapeamento norma → módulo do produto

| Cláusula ISO/IEC 17025 | Módulo Aferê |
|------------------------|------------------|
| 4.1 Imparcialidade | Cadastro de declarações de conflito + matriz de risco no módulo Qualidade |
| 4.2 Confidencialidade | RBAC, criptografia, termos de confidencialidade no Onboarding |
| 5 Estrutura | Cadastro de unidades, organograma, escopo |
| 6.2 Pessoal | Matriz de competências, autorização por atividade |
| 6.3 Instalações | Registro de condições ambientais por OS |
| 6.4 Equipamentos / padrões | Módulo Padrões |
| 6.5 Rastreabilidade | Cadeia documentada de cada padrão até INM |
| 6.6 Serviços externos | Cadastro de fornecedores qualificados |
| 7.1 Análise crítica | Workflow de aceite da OS |
| 7.2 Métodos | Módulo Procedimentos versionados |
| 7.5 Registros técnicos | Captura completa no wizard + anexos com hash |
| 7.6 Incerteza | Engine de cálculo + balanço documentado |
| 7.7 Validade dos resultados | Cartas de controle, intercomparações |
| **7.8 Conteúdo do certificado** | **Wizard + template normativo (seção 8 deste PRD)** |
| 7.9 Reclamações | Módulo Qualidade |
| 7.10 Trabalho não conforme | Módulo Qualidade |
| 7.11 Sistemas (LIMS) | Validação interna do próprio sistema |
| 8.3 / 8.4 | Controle de documentos e registros |
| 8.5 Riscos e oportunidades | Módulo Qualidade |
| 8.7 Ações corretivas | Módulo Qualidade |
| 8.8 Auditoria interna | Módulo Qualidade |
| 8.9 Análise crítica pela direção | Painel gerencial |

---

## 5. Personas e perfis de usuário

### 5.1 Personas primárias

#### Técnico Calibrador (app Android — campo/laboratório)
- Executa calibração in loco, frequentemente sem internet.
- Precisa de fluxo guiado, claro, com pouco campo livre e muito assistente.
- Tolerância zero a sincronização que perca dados.

#### Revisor Técnico (web)
- Profissional sênior que confere coerência metrológica.
- Não pode revisar serviço executado por si próprio.
- Devolve para correção via comentário estruturado.

#### Signatário Autorizado (web e Android)
- Aprova e assina eletronicamente o certificado.
- Só pode assinar tipos de instrumento dentro de sua matriz de competência.
- Bloqueado se o sistema detectar qualquer pendência (padrão vencido, revisão incompleta, regra de decisão não acordada).

#### Gestor da Qualidade (web)
- Administra procedimentos, escopo, CMC, NC, auditorias internas, treinamentos.
- Consome trilha de auditoria, indicadores e relatórios.

#### Administrador (web)
- Configura organização, usuários, integrações, parâmetros.

### 5.2 Personas secundárias

#### Cliente Final (portal web público)
- Consulta seus certificados, verifica autenticidade via QR code, baixa PDF assinado.
- Sem login obrigatório para verificação pública por hash.

#### Auditor (somente leitura — web)
- Auditor interno, externo (Cgcre) ou cliente em auditoria de fornecedor.
- Vê tudo, edita nada.

### 5.3 Matriz de permissões (resumo)

| Ação | Técnico | Revisor | Signatário | Gestor Qualidade | Admin | Auditor |
|------|---------|---------|------------|------------------|-------|---------|
| Criar OS | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Executar calibração (Android) | ✓ | — | — | — | — | — |
| Revisar serviço | — | ✓ | — | — | — | — |
| Assinar certificado | — | — | ✓ | — | — | — |
| Cadastrar procedimento | — | — | — | ✓ | ✓ | — |
| Cadastrar usuário | — | — | — | — | ✓ | — |
| Consultar trilha completa | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reemitir certificado | — | — | ✓ | ✓ | — | — |

---

## 6. Arquitetura do produto

### 6.1 Camadas funcionais (visão de produto)

| Camada | Responsabilidade |
|--------|------------------|
| **Metrológica** | Cálculos, incerteza, CMC, regra de decisão |
| **Regulatória** | RTM/portarias, escopo, símbolo de acreditação, uso legal |
| **Qualidade** | Trilha de auditoria, competência, documentos, bloqueios |
| **Documental** | Certificado robusto, verificável, reemitível, rastreável |

### 6.2 Componentes técnicos (visão de engenharia)

| Componente | Função |
|-----------|--------|
| **App Android (campo)** | Execução, coleta de evidências, operação offline, assinatura local, fila de sincronização |
| **App Web (back-office)** | Cadastros, revisão, assinatura, qualidade, indicadores, configuração |
| **Portal Cliente (web público)** | Consulta de certificados, QR code, autenticidade, download PDF |
| **Backend técnico** | Autenticação, RBAC, regras de negócio, cálculo consolidado, emissão oficial, APIs |
| **Engine de cálculo** | Repetibilidade, excentricidade, linearidade, incerteza expandida (base EURAMET cg-18) |
| **Engine de validação** | Bloqueios normativos antes de cada transição de estado |
| **Storage de evidências** | Anexos imutáveis com hash SHA-256 |
| **Audit log** | Imutável, append-only, exportável |

### 6.3 Estratégia de dados

- **App Android**: SQLite local criptografado (SQLCipher), fila de eventos pendentes.
- **Backend**: PostgreSQL como fonte oficial; serviço de eventos para reconciliação.
- **Anexos**: object storage com hash + retenção configurável.
- **Trilha de auditoria**: tabela append-only + cadeia de hashes.
- **Reconciliação**: ao sincronizar, eventos do app são reaplicados pelo backend; conflitos vão para fila de revisão humana.

### 6.4 Integrações (Fases 2/3)
- ERP financeiro (faturamento por OS).
- E-mail transacional (envio de certificado ao cliente).
- WhatsApp Business API (notificação de vencimento — opt-in).
- Exportação **DCC XML** (Plano Estratégico Inmetro 2024–2027).
- API REST aberta para clientes corporativos consumirem certificados.

### 6.5 Tipos de organização emissora (perfis regulatórios)

> **Conceito estrutural do produto.** O sistema reconhece três perfis distintos de organização emissora. O perfil é definido na configuração da organização (somente Administrador) e impacta: **modelo de certificado impresso**, **regras de rastreabilidade aceitas para padrões**, **uso de símbolos de acreditação**, **declarações de rodapé** e **bloqueios automáticos**. **Mudança de perfil exige justificativa, aprovação e ficará registrada na trilha de auditoria.**

#### Tipo A — Laboratório acreditado RBC / ISO/IEC 17025

- **Quem é:** laboratório com acreditação Cgcre vigente (CAL-XXXX), dentro da Rede Brasileira de Calibração (RBC).
- **Pode emitir:** certificado **com símbolo Cgcre/RBC**, dentro do escopo acreditado, respeitando a CMC declarada.
- **Padrões aceitos:** somente padrões com cadeia de rastreabilidade ao SI via INM ou laboratório acreditado signatário ILAC MRA.
- **Cabeçalho do certificado:** "Acreditação Cgcre nº CAL-XXXX" + símbolo Cgcre/RBC (uso conforme **DOQ-CGCRE-028**).
- **Rodapé/declaração:** "*Os resultados são metrologicamente rastreáveis ao SI por meio do INM (Inmetro). Certificado emitido sob acreditação Cgcre nº CAL-XXXX, signatária dos acordos de reconhecimento mútuo ILAC MRA.*"
- **Regras especiais:**
  - Cálculo de U expandida não pode ser inferior à CMC declarada para o ponto de medição (bloqueia uso do símbolo, mas permite emissão sem símbolo).
  - Item de calibração fora do escopo acreditado → certificado emitido obrigatoriamente **sem símbolo Cgcre/RBC**, com aviso explícito ao signatário.
  - Cadastro de escopo (`scope_items`) e CMC (`cmc_items`) obrigatório.
  - Validade da acreditação monitorada com alertas (90/30/7 dias).

#### Tipo B — Organização sem ISO/IEC 17025, padrões calibrados em RBC

- **Quem é:** empresa que **não possui acreditação** ISO/IEC 17025, mas mantém seus padrões calibrados em laboratórios **RBC acreditados pela Cgcre**.
- **Pode emitir:** certificado de calibração **rastreável ao SI via RBC**, declarando explicitamente a rastreabilidade pelos padrões — **sem usar símbolo Cgcre/RBC** (vedado a não acreditados).
- **Padrões aceitos:** somente padrões com certificado emitido por **laboratório RBC acreditado** (validado automaticamente pelo nº CAL-XXXX do laboratório emissor cadastrado no padrão).
- **Cabeçalho do certificado:** identificação da empresa **sem símbolo Cgcre**.
- **Rodapé/declaração:** "*Os resultados são metrologicamente rastreáveis ao Sistema Internacional de Unidades (SI) por meio dos padrões utilizados, calibrados por laboratórios acreditados pela Cgcre/Inmetro (RBC). Esta organização não é acreditada Cgcre.*"
- **Regras especiais:**
  - Padrão sem certificado RBC → **bloqueia** uso na OS.
  - Tentativa de inserir símbolo Cgcre/RBC → **bloqueio por arquitetura** (não aparece na interface).
  - Declaração de conformidade permitida, com regra de decisão (ILAC G8) acordada e registrada — **sem símbolo de acreditação**.

#### Tipo C — Organização com padrões calibrados pelo Inmetro fora do escopo RBC

- **Quem é:** empresa que utiliza padrões calibrados **pelo Inmetro (ou outro INM)** em serviço **não pertencente ao escopo RBC** (ex.: calibração realizada pela Diretoria de Metrologia Científica, calibração interlaboratorial sem acreditação).
- **Pode emitir:** certificado de calibração **sem qualquer referência à RBC ou Cgcre**, com declaração de rastreabilidade ao Inmetro/INM **através dos padrões**.
- **Padrões aceitos:** padrões com certificado emitido pelo Inmetro/INM (com identificação clara do emissor).
- **Cabeçalho do certificado:** identificação da empresa **sem símbolo Cgcre/RBC**.
- **Rodapé/declaração:** "*Os resultados são metrologicamente rastreáveis ao Sistema Internacional de Unidades (SI) por meio dos padrões utilizados, calibrados pelo Inmetro. Esta organização não é acreditada Cgcre e este certificado não está sob escopo RBC.*"
- **Regras especiais:**
  - Tentativa de inserir símbolo Cgcre/RBC → **bloqueio por arquitetura**.
  - Não permite declarar "conforme RBC" em nenhum campo livre (validador semântico).
  - Declaração de conformidade permitida com regra de decisão acordada — sem qualquer alusão à acreditação.

#### Matriz comparativa dos 3 perfis

| Aspecto | Tipo A — Acreditado RBC | Tipo B — Padrões RBC | Tipo C — Padrões Inmetro |
|---------|-------------------------|----------------------|--------------------------|
| Acreditação Cgcre da organização | ✅ Sim | ❌ Não | ❌ Não |
| Símbolo Cgcre/RBC no certificado | ✅ Permitido (no escopo) | ❌ Bloqueado | ❌ Bloqueado |
| Origem aceita do certificado dos padrões | INM ou lab RBC/ILAC MRA | **Somente lab RBC** | Inmetro/INM (qualquer) |
| Declara rastreabilidade ao SI | ✅ Direta + via acreditação | ✅ Via padrões RBC | ✅ Via padrões Inmetro |
| Cita a RBC no certificado | ✅ Sim | ✅ Como origem dos padrões | ❌ Não |
| Validação contra escopo/CMC | ✅ Obrigatória | ❌ Não aplicável | ❌ Não aplicável |
| Modelo de PDF | Template A | Template B | Template C |
| Numeração de certificados | Pode usar série acreditada | Série interna | Série interna |
| Auditoria Cgcre | ✅ Sujeita | ❌ Não sujeita ao sistema | ❌ Não sujeita ao sistema |

#### Configuração e governança do perfil
- Definido no onboarding da organização pelo Administrador.
- Alteração exige: justificativa textual, anexo de evidência (ex.: certificado Cgcre vigente para mudar para Tipo A; carta de descomissionamento para mudar para Tipo C), aprovação por dois usuários com perfil Administrador.
- Toda mudança fica registrada em `audit_logs` com efeito a partir da data de aprovação — **certificados emitidos antes da mudança permanecem com o perfil vigente na época**.
- Para Tipo A: cadastro obrigatório do nº CAL-XXXX, data de validade da acreditação, escopo (`scope_items`) e CMC (`cmc_items`). Sem esses dados, o perfil A não é ativado.

#### Multi-organização e organizações híbridas
- Cada `organization` no sistema tem **um único perfil** ativo.
- Empresa que possui dois CNPJs (ex.: filial acreditada + filial não acreditada) usa **duas organizações distintas no sistema**, cada uma com seu perfil — para garantir isolamento de selo, escopo e numeração.

### 6.6 Multitenancy e isolamento

- **Modelo:** SaaS multi-tenant com isolamento lógico por `organization_id`. Toda tabela transacional (`clients`, `equipments`, `standards`, `work_orders`, `certificates`, `audit_logs`, `procedures`, etc.) carrega `organization_id` obrigatório e indexado.
- **Isolamento de dados:** consulta sem `organization_id` na cláusula `WHERE` é proibida — enforcement por **Row Level Security (RLS)** no PostgreSQL + middleware de tenant na API + testes automatizados de cross-tenant leak.
- **Isolamento de credenciais:** segredos por organização (chaves de assinatura, integrações ERP, webhooks) armazenados em vault com escopo de tenant.
- **Numeração de certificados:** sequencial **por organização** — nenhum cliente vê numeração de outro.
- **Multi-organização por usuário:** um usuário pode pertencer a N organizações (ex.: consultor de qualidade que atende 3 laboratórios), com seleção explícita de "organização ativa" no login e troca via menu. Trilha de auditoria registra `organization_id` de cada ação.
- **Planos comerciais por organização:** plano (Starter/Pro/Enterprise), limites (usuários, OS/mês, equipamentos), faturamento e ciclo de cobrança vivem em `organization_subscription`.
- **Backup e restauração:** export por organização (certificados, padrões, OS, auditoria) — atende requisito de portabilidade da LGPD.
- **Encerramento:** cancelamento de plano congela a organização (modo somente leitura por 90 dias) antes do offboarding controlado.

### 6.7 Planos comerciais (visão de produto)

> **Modelo:** SaaS por assinatura mensal/anual, cobrança por organização. Trial Pro de 14 dias automático no auto-cadastro. Preços em BRL — **valores indicativos para validação comercial**, não preços finais.

#### 6.7.1 Tabela comparativa

| Recurso | **Starter** | **Pro** | **Enterprise** |
|---------|-------------|---------|----------------|
| **Preço-alvo (mensal, anual à vista)** | R$ 249/mês | R$ 749/mês | Sob consulta (≥ R$ 2.500/mês) |
| **Perfil regulatório suportado** | A, B, C | A, B, C | A, B, C + multi-organização |
| **Usuários ativos** | até 3 | até 15 | ilimitado |
| **Equipamentos cadastrados** | até 200 | ilimitado | ilimitado |
| **Clientes cadastrados** | até 50 | ilimitado | ilimitado |
| **Padrões cadastrados** | até 30 | ilimitado | ilimitado |
| **OS / mês** | até 80 | ilimitado | ilimitado |
| **Certificados emitidos / mês** | até 80 | ilimitado | ilimitado |
| **Armazenamento de evidências** | 5 GB | 50 GB | 500 GB + add-on |
| **Retenção de auditoria** | 5 anos | 10 anos | configurável (≥ 10 anos) |
| **App Android offline** | ✅ | ✅ | ✅ |
| **Wizard de execução completo** | ✅ | ✅ | ✅ |
| **Engine de incerteza GUM/EURAMET** | ✅ | ✅ | ✅ |
| **3 templates de certificado (A/B/C)** | ✅ | ✅ | ✅ + customização |
| **Selo Cgcre/RBC (perfil A)** | ✅ | ✅ | ✅ |
| **QR code de verificação pública** | ✅ | ✅ | ✅ |
| **Portal do cliente final** | básico | completo | completo + white-label |
| **Login Google/Microsoft/Apple** | ✅ | ✅ | ✅ |
| **MFA TOTP** | ✅ | ✅ | ✅ |
| **SSO corporativo SAML 2.0** | ❌ | ❌ | ✅ |
| **Provisionamento SCIM** | ❌ | ❌ | ✅ |
| **Gestão de competências** | básica | completa | completa |
| **Módulo Qualidade (NC, auditoria interna)** | ❌ | ✅ | ✅ |
| **Painel gerencial e indicadores** | básico | completo | completo + BI export |
| **Integração ERP via API** | ❌ | webhook | API REST completa |
| **Importação em massa (CSV)** | ❌ | ✅ | ✅ |
| **Exportação DCC XML** (Fase 3) | ❌ | ❌ | ✅ |
| **Reemissão controlada de certificado** | ✅ | ✅ | ✅ |
| **Histórico de revisões de certificado** | ✅ | ✅ | ✅ |
| **Customização de identidade do certificado** | logo + cor | logo + cor + assinatura | identidade visual completa |
| **Idiomas do certificado** | PT-BR | PT-BR | PT-BR + EN (Fase 2) |
| **Suporte** | e-mail (48h útil) | e-mail prioritário (24h útil) + chat | dedicado + telefone + SLA contratual |
| **SLA de disponibilidade** | best effort | 99,5% | 99,9% (com créditos) |
| **Onboarding assistido** | self-service | sessão de 1h | implantação dedicada (até 16h) |
| **Treinamento** | base de conhecimento | webinars mensais | turmas presenciais opcionais |
| **DPA / contrato customizado (LGPD)** | termo padrão | termo padrão | DPA negociável |
| **Faturamento** | cartão | cartão / boleto | nota fiscal / boleto / contrato anual |

#### 6.7.2 Add-ons (todos os planos, exceto onde marcado)

| Add-on | Preço-alvo | Disponível em |
|--------|-----------|---------------|
| Pacote 50 GB de evidências | R$ 99/mês | Pro, Enterprise |
| Usuário extra | R$ 79/usuário/mês | Pro |
| Marca branca (white-label) do portal cliente | R$ 499/mês | Enterprise |
| Assinatura digital qualificada ICP-Brasil (Fase 2) | R$ 12/certificado | Pro, Enterprise |
| Implantação extra (horas) | R$ 350/h | todos |
| Auditoria pré-Cgcre (consultoria) | sob orçamento | todos |

#### 6.7.3 Regras de cobrança e ciclo

- **Trial automático:** todo auto-cadastro entra em trial Pro de 14 dias, sem cartão.
- **Conversão:** ao final do trial, organização entra em modo somente leitura por 7 dias se não converter; depois, congelamento total (dados preservados por 90 dias).
- **Upgrade/downgrade:**
  - Upgrade é imediato e prorratado.
  - Downgrade entra em vigor no próximo ciclo (não retroativo).
  - Downgrade que viole limites do plano alvo (ex.: 5 usuários para Starter de 3) bloqueia até a operação resolver o excedente.
- **Anual à vista:** desconto de 2 mensalidades.
- **Cancelamento:** a qualquer momento; sem multa; export de dados por 90 dias.
- **Modo "freeze":** organização pode pausar a assinatura por até 6 meses (50% do valor) — mantém dados acessíveis em leitura.
- **Trial estendido (sob aprovação):** ciclos especiais para laboratórios em processo de acreditação.

#### 6.7.4 Métricas comerciais

| Métrica | Meta ano 1 | Meta ano 2 |
|---------|-----------|-----------|
| MRR (Monthly Recurring Revenue) | R$ 30.000 | R$ 120.000 |
| ARPU (Average Revenue per Account) | R$ 600 | R$ 850 |
| CAC (Custo de Aquisição) | ≤ R$ 1.500 | ≤ R$ 1.200 |
| Payback CAC | ≤ 5 meses | ≤ 4 meses |
| Conversão trial → pago (self-service) | ≥ 8% | ≥ 15% |
| Conversão pipeline assistido (Pro/Enterprise) | ≥ 25% | ≥ 35% |
| Churn mensal | ≤ 4% | ≤ 2,5% |
| Net Revenue Retention | ≥ 100% | ≥ 110% |

### 6.8 Funil de aquisição e onboarding (visão de produto)

```
[Site de vendas público]
      │
      ▼
[Auto-cadastro: e-mail+senha OU Google OU Microsoft OU Apple]
      │
      ▼
[Verificação de e-mail]
      │
      ▼
[Wizard de Onboarding da Organização (10 passos)]
      │
      ▼
[Tour guiado no app web + convite a equipe]
      │
      ▼
[Primeira OS executada no Android]
```

Cada etapa tem métrica própria; eventos vão para o painel de produto (drop-off por etapa, time-to-first-certificate).

---

## 7. Módulos do produto

### 7.1 Autenticação, perfis e rastreabilidade humana

#### Métodos de login (web e Android)
- **E-mail + senha** (com regras de força: mín. 12 caracteres, sem reuso das últimas 5).
- **SSO social:** Google, Microsoft (Entra ID), Apple — via OAuth 2.0/OIDC. Vinculação à organização: 1º acesso de e-mail ainda não cadastrado abre fluxo de auto-cadastro (§7.15) ou ingresso por convite (§7.13).
- **SSO corporativo (Enterprise):** SAML 2.0 com IdP do cliente (Azure AD, Okta, Keycloak) — provisionamento via SCIM opcional.
- **MFA:** TOTP (Google/Microsoft Authenticator) — opcional para usuários comuns, **obrigatório para signatários e administradores**.
- **Biometria:** suportada no Android (impressão digital / face) como segundo fator local; nunca substitui credencial em ações sensíveis (assinatura).
- **Login offline (Android):** token derivado de senha + biometria, cache seguro, expiração configurável (default 7 dias).

#### Assinatura eletrônica
- **Re-autenticação obrigatória** a cada assinatura (digita senha ou usa biometria + senha em ação sensível).
- Signature payload contém: `user_id`, `organization_id`, hash do documento, timestamp do servidor (UTC), versão do `normative_package` (§16.5), nonce.
- Trilha imutável armazena o payload + assinatura criptográfica.

#### Segregação de funções (enforcement por arquitetura)
- Técnico **não revisa** o próprio serviço.
- Revisor **não assina** o que revisou.
- Signatário só assina tipo de instrumento dentro da sua matriz de competência (§7.13).
- Mudança de perfil regulatório da organização exige **2 administradores** (§6.5).

### 7.2 Módulo Cliente

#### Campos
- Razão social / nome
- CNPJ / CPF (validados)
- Inscrição estadual (opcional)
- Contatos múltiplos (nome, cargo, e-mail, telefone, WhatsApp)
- Endereços múltiplos (sede, filiais, locais de instalação)
- Setor / segmento
- Responsável pelo acompanhamento técnico
- Condições especiais do local (ex.: câmara fria, área classificada)
- Histórico de serviços
- Anexos contratuais (proposta, contrato, ordem de compra)

#### Regras
- CNPJ/CPF único por organização.
- Cliente inativo não permite criar nova OS, mas seus certificados ficam consultáveis.
- Vínculo obrigatório com **pelo menos 1 endereço** antes de cadastrar equipamentos.

#### Telas
- Lista (busca por razão social, CNPJ, segmento)
- Detalhe (abas: dados, contatos, endereços, equipamentos, certificados, financeiro, anexos)
- Formulário de criação/edição

### 7.3 Módulo Equipamento (instrumento de pesagem)

> **Regra estrutural inviolável: todo equipamento é obrigatoriamente vinculado a 1 cliente.** Não existe equipamento "órfão".

#### Campos
- Código interno (gerado automaticamente, único na organização)
- TAG do cliente (opcional)
- Tipo (NAWI / IPNA, comercial, industrial, analítica, plataforma, semi-analítica)
- Fabricante, modelo, número de série
- **Capacidade máxima** (Max)
- **Divisão** (d) e divisão de verificação (e)
- **Classe de exatidão** (I, II, III, IIII conforme Portaria 157/2022)
- Faixa nominal e faixa efetiva de uso
- Tara
- Aprovação de modelo Inmetro (quando aplicável)
- Status regulatório (em uso, em reparo, descalibrado, descomissionado)
- Localização (cliente + endereço + sala/setor)
- Uso pretendido (comercial, fiscal, industrial, laboratorial)
- Fotos da placa, lacres, célula de carga, indicador
- Histórico de calibrações, reparos, ajustes, troca de célula/indicador, ocorrências
- Próximo vencimento de calibração (informativo, programa do cliente)

#### Regras
- Vínculo a cliente é **obrigatório e imutável** após criação (transferência via fluxo dedicado de "transferência entre clientes" com trilha).
- Cadastro só é considerado completo quando: tipo, capacidade, divisão e classe estão preenchidos.
- Equipamento descomissionado não permite nova OS, mas mantém histórico consultável.

#### Telas
- Lista global (busca por TAG, série, cliente, tipo, próximo vencimento)
- Detalhe (abas: identificação, fotos, histórico, certificados emitidos, anexos técnicos, ocorrências)
- Formulário guiado de criação (com leitor de QR/código de barras opcional)

### 7.4 Módulo Padrões e instrumentos auxiliares

- Pesos padrão (E1/E2/F1/F2/M1/M2/M3 — Portaria 289/2021)
- Massas auxiliares
- Termohigrômetro, barômetro, inclinômetro, acessórios
- Cada padrão: ID, descrição, fabricante/modelo, faixa, valor nominal convencional, **incerteza**, **certificado vinculado** (PDF anexado), **laboratório emissor** (acreditado/INM), data da calibração, vencimento interno, fatores de correção, status.

#### Bloqueios automáticos (não-negociáveis)
- Padrão **vencido** → bloqueia uso em nova OS.
- Padrão **fora da faixa** do ensaio → bloqueia o ensaio específico.
- Padrão **sem cadeia documental válida** (sem certificado anexado/sem rastreabilidade ao SI) → bloqueia aprovação final do certificado.

#### Validação por perfil regulatório da organização (ver §6.5)
Cada padrão registra obrigatoriamente o **tipo da fonte do certificado**:
- `INM` (Inmetro / instituto nacional)
- `RBC` (laboratório acreditado Cgcre, com nº CAL-XXXX)
- `ILAC_MRA` (laboratório acreditado por signatário ILAC MRA fora do Brasil)
- `OUTRO` (não rastreável — uso restrito a fins informativos, **bloqueado em qualquer perfil**)

| Perfil da organização | Fontes aceitas para padrões usados em emissão |
|-----------------------|-----------------------------------------------|
| **Tipo A — Acreditado RBC** | `INM`, `RBC`, `ILAC_MRA` |
| **Tipo B — Padrões RBC** | **Somente `RBC`** (e `INM` quando o INM atua como provedor de calibração ao laboratório) |
| **Tipo C — Padrões Inmetro fora de RBC** | `INM` |

Se o padrão selecionado pelo técnico tiver fonte incompatível com o perfil da organização, o sistema bloqueia a OS na seleção do padrão, com mensagem explícita e link para o módulo Padrões.

### 7.5 Módulo Procedimentos e métodos

- Cadastro versionado (código, revisão, vigência, escopo de aplicação, tipo de instrumento).
- Sequência de ensaios (excentricidade, repetibilidade, linearidade, histerese — base EURAMET cg-18).
- Critérios de aceitação por classe.
- Vínculo com norma de referência (NBR ISO 17025, RTM 157/2022, EURAMET cg-18, etc.).
- **Workflow de aprovação**: elaborador → revisor → aprovador (gerente da qualidade).
- Procedimentos não vigentes não podem ser selecionados em nova OS.

### 7.6 Módulo Ordem de Serviço (OS)

- Solicitação inicial → análise crítica (cláusula 7.1) → aceite → planejamento → execução.
- Campos: cliente, equipamento(s), procedimento aplicável, local de execução, data planejada, técnico designado, padrões reservados, **regra de decisão acordada (se haverá declaração de conformidade)**.
- Estado: rascunho → aceita → em execução → executada → em revisão → aprovada → emitida → entregue.
- Cada transição registra autor, timestamp, dispositivo e geo (quando disponível).

### 7.7 Wizard de execução e emissão do certificado (núcleo do produto)

> **Princípios:**
> 1. **O técnico não escolhe a ordem dos passos.** O wizard impõe a sequência normativa. O fluxo só avança quando o passo atual está válido.
> 2. **Tudo que o sistema já sabe, o sistema preenche.** O técnico só digita o que **só pode** ser capturado no momento da execução (leituras de balança, condições ambientais reais, fotos, observações).
> 3. **Confirmar > Digitar.** Quando o sistema sugere algo, o técnico confirma com um toque; só edita se houver desvio justificado (que vira nota técnica).

#### 7.7.1 Auto-preenchimento ao selecionar equipamento (cascata)

Ao escolher o equipamento na abertura da OS (ou no Passo 1 do wizard), o sistema auto-completa em cascata:

| Campo / decisão | Origem do dado | Editável pelo técnico? |
|-----------------|----------------|------------------------|
| **Cliente** | Vínculo obrigatório do equipamento (§7.3) | ❌ Não (precisa transferir o equipamento) |
| **Endereço de execução** | Endereços do cliente; pré-seleciona o último usado, ou o cadastrado como "local da balança" | ✅ Sim (entre os endereços do cliente) |
| **Identificação completa** (TAG, série, fabricante, modelo, capacidade Max, divisão d/e, classe I/II/III/IIII, faixa nominal, faixa efetiva) | Cadastro do equipamento (§7.3) | ❌ Não no wizard (correção pelo módulo Equipamento, com trilha) |
| **Casas decimais nas leituras** | Resolução `d` do equipamento | ❌ Não (teclado travado nas casas certas) |
| **Procedimento aplicável** | Match automático: `tipo equipamento + classe + faixa` × procedimentos vigentes (§7.5) | ✅ Sim, se houver mais de um aplicável |
| **Sequência de ensaios** (excentricidade, repetibilidade, linearidade, histerese...) | Definida no procedimento selecionado | ❌ Não |
| **Pontos de calibração da curva** | Calculados a partir da faixa do equipamento + critério do procedimento (ex.: 10%, 25%, 50%, 75%, 100% da Max) | ✅ Sim, com justificativa em campo "desvios do método" (vai para o certificado) |
| **Padrões necessários** (e quais cargas combinam para cada ponto) | **Algoritmo de combinação automática** entre `pesos disponíveis` e `pontos da curva`, respeitando faixa, classe e validade | ✅ Substituição entre padrões equivalentes válidos |
| **Validação dos padrões** (vencimento, faixa, fonte conforme §7.4) | Engine de validação | ❌ Bloqueia se inválido |
| **Critérios de aceitação** (EMA por classe) | Portaria Inmetro 157/2022 (IPNA) ou critério interno do procedimento | ❌ Não |
| **Regra de decisão** | Acordo registrado no contrato/OS do cliente (se houver) | ✅ Sim, se cliente solicitar mudança (re-acordo registrado) |
| **Condições ambientais** | Leitura automática do termohigrômetro/barômetro cadastrados como ativos no laboratório (se houver integração) ou pré-preenche última leitura para o técnico confirmar com foto do display | ✅ Sim (leitura sempre confirmada) |
| **Faixa permitida de ambiente** | Definida no procedimento | ❌ Não |
| **Histórico do equipamento** (última calibração, último ajuste, ocorrências, fator de correção anterior) | Registros do próprio equipamento | ❌ Visualização apenas; influencia avisos ao técnico |
| **Estado na recepção** | Pré-marcado como "Conforme"; muda para "Com observações" ao tocar no campo | ✅ Sim |
| **Nº do certificado** | Sequencial automático segundo regra do perfil regulatório (§6.5) — Tipo A pode usar série acreditada, B/C série interna | ❌ Não |
| **Template de PDF** | Definido pelo perfil regulatório da organização (§8.14) | ❌ Não |
| **Cabeçalho institucional** (logo, razão social, CNPJ, nº CAL se Tipo A) | Configuração da organização | ❌ Não |
| **Rodapé / declaração de rastreabilidade** | Definido pelo perfil regulatório | ❌ Não |
| **Data de calibração** | Data/hora do dispositivo no fechamento da execução | ❌ Não |
| **Data de emissão** | Data/hora do servidor no momento da assinatura | ❌ Não |
| **Técnico executor** | Usuário logado | ❌ Não |
| **Revisor sugerido** | Próximo revisor disponível com competência para o tipo de instrumento (round-robin) | ✅ Sim, dentro dos elegíveis |
| **Signatário sugerido** | Signatário autorizado para o tipo de instrumento + dentro do escopo (Tipo A) com menor fila | ✅ Sim, dentro dos elegíveis |
| **Texto de observações padrão** | Bibloteca de notas reutilizáveis da organização (ex.: "Calibração realizada com a balança no local de uso") | ✅ Sim |
| **Anexos automáticos** | Certificados PDF dos padrões usados, ficha técnica do procedimento, balanço de incerteza | ❌ Anexados automaticamente ao PDF final |

#### 7.7.2 Cálculos automáticos durante a execução

- **Erro de indicação por ponto** = leitura − valor convencional do padrão.
- **Repetibilidade** = desvio padrão experimental das N repetições, calculado em tempo real após a última leitura.
- **Excentricidade** = diferença entre maior e menor leitura nas posições, calculada automaticamente assim que todas as posições são preenchidas.
- **Histerese** = diferença entre leituras crescente e decrescente, calculada ao fechar o ensaio.
- **Incerteza expandida U (k=2)** com balanço completo (§7.8) — recalculada a cada nova leitura.
- **Decisão de conformidade** (se aplicável) — atualizada em tempo real, mostrando ao técnico se o ponto passa ou falha pela regra acordada (com banda de guarda visual).

#### 7.7.3 Validações automáticas que bloqueiam o avanço

- Leitura impossível para a resolução do equipamento (ex.: 3 casas decimais quando d = 0,01).
- Repetições fora da janela esperada (alerta amarelo, não bloqueia, mas exige confirmação).
- Ambiente fora da faixa do procedimento.
- Padrão expirou entre o início e o fim da execução (raro, mas possível em execuções longas).
- Tempo de estabilização não respeitado entre cargas (cronômetro do app).

#### 7.7.4 O que o técnico de fato digita

Reduzido ao mínimo: **leituras da balança**, **leitura do termohigrômetro/barômetro** (se não houver integração), **fotos** (placa, lacres, display, ambiente), **observações livres** (apenas quando há desvio).

Tudo o resto é decidido pelo sistema, com confirmação visual antes do avanço.

#### 7.7.5 Pré-visualização do certificado (Passo 13)

Antes do técnico fechar a execução, o app renderiza **prévia integral** do certificado já com todos os campos preenchidos (cabeçalho, cliente, equipamento, padrões, ambiente, resultados, incerteza, decisão, rodapé, template do perfil) — o técnico confere visualmente o que será emitido. Qualquer correção volta o wizard ao passo correspondente; nada de edição livre fora do fluxo.

#### Passo 1 — Identificação da OS
- Selecionar OS planejada (ou criar nova com base em cliente + equipamento).
- Confirmar técnico executor (re-autenticação).

#### Passo 2 — Verificação do equipamento
- Confirmar identificação (TAG, número de série).
- Foto obrigatória da placa.
- Estado na recepção (conforme / com observações + texto).
- Verificar lacres (íntegros / rompidos + foto).

#### Passo 3 — Reserva e validação de padrões
- Selecionar padrões necessários conforme procedimento.
- Sistema valida automaticamente: vigência, faixa, certificado anexado, rastreabilidade.
- **Bloqueio automático** se algum padrão falhar.

#### Passo 4 — Condições ambientais
- Registrar temperatura, umidade, pressão (lidos do termohigrômetro/barômetro cadastrados, com link para leitura manual + foto do display).
- Sistema valida faixa permitida pelo procedimento.
- **Bloqueio** se ambiente fora da faixa (com possibilidade de NC).

#### Passo 5 — Verificação inicial (zero, repetibilidade rápida)
- Roteiro guiado.
- Capturar leituras com teclado numérico travado em casas decimais corretas.

#### Passo 6 — Excentricidade
- Posicionar carga nos pontos cardeais conforme desenho exibido.
- Capturar leituras.
- Sistema calcula desvios automaticamente.

#### Passo 7 — Repetibilidade
- N repetições conforme procedimento.
- Sistema calcula desvio padrão experimental.

#### Passo 8 — Linearidade / pontos da curva
- Sequência crescente e decrescente conforme procedimento.
- Sistema calcula erro de indicação por ponto.

#### Passo 9 — Pesagem mínima (se aplicável)
- Avaliar conforme USP <41> ou critério interno.

#### Passo 10 — Cálculo consolidado e incerteza
- Engine calcula erro, repetibilidade, excentricidade, contribuições de incerteza, incerteza combinada e expandida (k=2, ~95%).
- Balanço de incerteza documentado: fontes, distribuição, divisor, sensibilidade, contribuição.
- **Conformidade com CMC** (se laboratório acreditado): bloqueia se U expandida < CMC declarada.

#### Passo 11 — Regra de decisão (opcional)
- Só aparece se cliente solicitou declaração de conformidade na OS.
- Aplicar regra acordada (ILAC G8): aceitação binária, com banda de guarda, etc.
- Resultado: Aprovado / Aprovado com risco / Reprovado / Indeterminado.

#### Passo 12 — Observações técnicas
- Texto livre estruturado (ajustes realizados, eventos atípicos).

#### Passo 13 — Pré-visualização e fechamento da execução
- Técnico revisa todos os dados.
- Assina como executor (re-autenticação).
- OS passa para "em revisão" (ainda não é certificado oficial).

#### Passo 14 — Revisão técnica (web)
- Revisor confere coerência: padrões adequados, ambiente OK, cálculo coerente, conformidade com método.
- Pode rejeitar (volta para o técnico com comentário) ou aprovar.

#### Passo 15 — Assinatura e emissão (web)
- Signatário autorizado revisa o certificado renderizado.
- Re-autenticação + assinatura eletrônica.
- Sistema gera **PDF/A imutável**, hash SHA-256, número sequencial irrevogável.
- QR code aponta para `https://verifica.afere.com.br/c/{hash}`.
- Distribuição: download na plataforma + envio ao e-mail do cliente.

### 7.8 Engine de cálculo e incerteza

- Implementação seguindo **EURAMET cg-18** + **ISO/IEC Guide 98-3 (GUM)**.
- Fontes típicas de incerteza para NAWI: padrões, repetibilidade, excentricidade, resolução, deriva, temperatura, empuxo do ar.
- Cada cálculo gera **balanço de incerteza estruturado** (auditável e exportável).
- Versionamento da engine: cada certificado registra a versão da engine usada.

### 7.9 Módulo Qualidade

- Não conformidades (cláusula 7.10): abertura, tratamento, ações imediatas, eficácia.
- Reclamações (7.9): registro, análise, resposta ao cliente, fechamento, vínculo opcional com NC e fluxo de reemissão (§7.10).
- Ações corretivas (8.7): causa raiz (5 Por Quês), plano de ação, verificação de eficácia.
- Auditoria interna (8.8): plano anual, programa por área, checklists derivados de [`iso 17025/03-checklists`](./iso%2017025/03-checklists), evidências, NC.
- Análise crítica pela direção (8.9): pauta padrão com **entradas automáticas do sistema** (certificados, NC, reclamações, indicadores), ata, deliberações.
- Imparcialidade (4.1): declarações de conflito anuais, matriz de risco à imparcialidade.
- Gestão de riscos e oportunidades (8.5): registro de riscos com probabilidade × impacto.
- Documentos da qualidade: hierarquia MQ/PG/PT/IT/FR versionada e aprovada (§7.5).
- Indicadores: tempo médio de OS, taxa de NC, % ações no prazo, eficácia, NPS.
- Wireframes completos: §17.9.

### 7.10 Trilha de auditoria e reemissão controlada

#### Trilha de auditoria
- **Append-only**, sem UPDATE/DELETE permitido.
- Cada evento: ator, ação, entidade, antes/depois, timestamp UTC, dispositivo, IP/geo, hash do evento anterior (cadeia tipo Merkle).
- Exportável para auditoria Cgcre.

#### Reemissão controlada (ISO/IEC 17025 §7.8.8)
- **Nunca se edita** um certificado emitido — gera-se uma nova versão (R1, R2, ...) que substitui formalmente a anterior.
- **Dupla aprovação** obrigatória: signatário diferente do original + Gestor da Qualidade.
- **Lista controlada de motivos** (`DADO_CADASTRAL`, `ERRO_TIPOGRAFICO`, `RECALCULO_INCERTEZA`, `MUDANCA_REGRA_DECISAO`, `RETIRADA_DECLARACAO_CONFORMIDADE`, `ANEXO_FALTANTE`, `OUTRO`).
- **Bloqueio crítico:** mudanças em **leituras brutas, padrões usados ou condições ambientais reais** exigem **nova OS** com nova execução em campo — não se reemite.
- PDF anterior preservado com marca-d'água "SUBSTITUÍDA POR R1"; hash original ainda resolve a verificação pública apontando para R1.
- Notificação automática ao cliente.
- Wireframe completo: §17.8.

### 7.11 Portal do Cliente

- Login do cliente (multi-usuário).
- Lista de equipamentos, certificados, próximos vencimentos (informativo).
- Download de PDF.
- Página pública de verificação por QR code (sem login).

### 7.12 Indicadores e relatórios

- Painel gerencial: certificados/mês, NC, taxa de reemissão, tempo médio por OS, ocupação por técnico, vencimento de padrões, vencimento de competências.
- Relatórios: por cliente, por equipamento, por técnico, por procedimento, por período.

### 7.13 Gestão de usuários, equipes e competências

#### Conceitos
- **Usuário** — identidade individual com e-mail único globalmente.
- **Membership** — vínculo `usuário ↔ organização ↔ papéis`. Um usuário pode ter membership em N organizações.
- **Papel (Role)** — Administrador, Gestor da Qualidade, Signatário Autorizado, Revisor Técnico, Técnico Calibrador, Auditor Somente-Leitura, Cliente Externo.
- **Equipe (Team)** — agrupamento opcional de usuários (ex.: "Equipe Campo SP", "Plantão Noturno") usado para distribuição de OS e relatórios.
- **Competência (Competency)** — autorização formal para atuar em determinado tipo de instrumento + faixa, com validade. Ex.: "Signatário — IPNA classe III até 50 kg — válido até 2027-04-19".

#### Telas e funcionalidades
- **Lista de usuários** (filtro por papel, equipe, status, competência expirando).
- **Detalhe do usuário**: dados, papéis, competências, histórico de atividades, último login, dispositivos vinculados.
- **Convite por e-mail** (§7.15 fluxo): admin envia convite com papel pré-atribuído; convidado aceita via link único de 72h e completa o cadastro (e-mail/senha ou SSO).
- **Matriz de competências** (visão da organização): linhas = usuários, colunas = tipos de instrumento; célula com status (autorizado / não autorizado / expirando / expirado) e validade.
- **Plano de treinamento e autorização** — alinhado com cláusula 6.2 da ISO 17025; cada autorização exige evidência (curso, ata, registro de supervisão).
- **Avaliação periódica de desempenho** — campo de registro com ciclo configurável (anual default).
- **Bloqueios automáticos:**
  - Competência expirada → usuário não pode mais executar/assinar serviços do tipo correspondente.
  - Alertas proativos: 90/30/7 dias antes do vencimento da autorização.
  - Suspensão (admin) → revoga sessões ativas em todos os dispositivos.
- **Provisionamento Enterprise (SCIM):** criação/desativação automática de usuários a partir do IdP corporativo.
- **Rastreabilidade humana:** todo evento (login, assinatura, alteração) registra `user_id`, `organization_id`, `device_id`, IP, geo (quando disponível) na trilha de auditoria.

#### Ciclo de vida do usuário
```
Convite → Aceito → Ativo → (Suspenso ↔ Ativo) → Desligado
                              │
                              ▼
                      Acesso revogado;
                      histórico preservado
                      (LGPD: anonimização opcional)
```

### 7.14 Wizard de Onboarding da Organização

> **Objetivo:** reduzir time-to-first-certificate para **menos de 1 hora** desde o auto-cadastro até a primeira OS executável. O wizard é executado uma única vez pelo Administrador inicial; pode ser pausado e retomado.

#### 10 passos sequenciais

| # | Passo | O que coleta / configura |
|---|-------|--------------------------|
| 1 | **Identidade da organização** | Razão social, CNPJ (validado e auto-preenchimento via integração com base pública), nome fantasia, segmento, telefone, e-mail institucional |
| 2 | **Endereço(s) operacionais** | Sede + unidades; CEP com auto-preenchimento (ViaCEP) |
| 3 | **Logo e identidade visual** | Upload de logo (PNG/SVG), cor primária para o cabeçalho do certificado, assinatura institucional (texto) |
| 4 | **Perfil regulatório (§6.5)** | Escolha entre Tipo A / B / C com explicação visual lado a lado; se Tipo A, captura nº CAL-XXXX e validade da acreditação; se Tipo B, ativa validação de fonte RBC para padrões |
| 5 | **Escopo e CMC (somente Tipo A)** | Cadastro inicial de itens de escopo acreditado e CMC declarada por ponto/faixa — pode ser pulado e completado depois (alerta) |
| 6 | **Numeração e identidade do certificado** | Padrão de numeração (sugestão por perfil), prefixo, dígitos, ano. Pré-visualização do template de PDF (A/B/C) com os dados da organização aplicados |
| 7 | **Equipe inicial** | Convite a até 5 usuários iniciais com papel pré-atribuído (Admin, Gestor Qualidade, Signatário, Revisor, Técnico). Envio em lote via e-mail. Pode ser feito depois |
| 8 | **Cadastro do primeiro padrão** | Wizard guiado para cadastrar 1 padrão (peso ou termohigrômetro) com upload obrigatório do certificado PDF do padrão e classificação da fonte (INM/RBC/ILAC/OUTRO) — desbloqueia o sistema para emitir |
| 9 | **Cadastro do primeiro procedimento** | Sugestão de 3 templates pré-prontos (IPNA classe III calibração de campo / IPNA bancada / verificação interna) — usuário escolhe um e ajusta. Dispensável se já houver procedimento |
| 10 | **Plano e ativação** | Confirmação do plano contratado (Starter/Pro/Enterprise), aceite de termos de uso e DPA (LGPD), ativação. Tour guiado opcional pelo app web. |

#### Estado e governança
- Cada passo gera registro em `organization_onboarding_steps` (status, timestamp, usuário).
- Configuração inicial **não trava o uso**: organização entra em modo "trial" funcional após o passo 4; passos 5-10 podem ser concluídos depois com banner persistente "Configuração 60% concluída".
- **Bloqueios duros para emitir o 1º certificado oficial** (por perfil regulatório):
  - **Tipo B e Tipo C:** passos 1, 4, 6, 8 obrigatoriamente concluídos.
  - **Tipo A:** passos 1, 4, **5 (escopo acreditado e CMC cadastrados)**, 6, 8 obrigatoriamente concluídos — sem escopo/CMC a validação §9 (U vs. CMC) não é possível e o perfil A não pode emitir certificado acreditado.
- **Re-execução parcial:** o wizard pode ser reaberto por seção via "Configurações da Organização" — útil para mudança de logo, atualização de CMC, troca de padrão de numeração.

### 7.15 Site de vendas e auto-cadastro

#### Site de vendas público (`afere.com.br`)
- **Objetivo:** captação de leads e auto-cadastro qualificado (PLG — product-led growth).
- **Páginas previstas:**
  - **Home** — proposta de valor por persona (laboratório / técnico / cliente final).
  - **Como funciona** — vídeo + animações do wizard.
  - **Conformidade** — explicação dos 3 perfis regulatórios (§6.5) e como o sistema garante ISO 17025 + portarias (§16).
  - **Preços** — planos (Starter / Pro / Enterprise) com limites e features. Comparativo lado a lado.
  - **Recursos** — biblioteca de blog/posts, modelos de procedimento gratuitos, glossário metrológico.
  - **Casos de uso** — depoimentos de laboratórios piloto.
  - **Acreditação Cgcre** — guia explicando o suporte do sistema ao processo.
  - **Sobre nós** — equipe, missão.
  - **Contato / Demo** — agendamento de demo guiada (Calendly/integração).
  - **Login** e **Comece grátis** sempre visíveis no header.
- **Stack:** Next.js (SSR/SSG) hospedado em CDN, formulários integrados a CRM, analytics (consentimento LGPD).
- **SEO:** estrutura semântica para pesquisas como "software ISO 17025", "emissão certificado calibração balança", "RBC Inmetro software".
- **Conformidade LGPD:** banner de cookies (categorizado), política de privacidade explícita, DPO no rodapé, formulário de exercício de direitos do titular.

#### Auto-cadastro (signup) — fluxo unificado web
1. **Botão "Comece grátis"** → tela de signup.
2. **Escolha do método:**
   - E-mail + senha (com força mínima)
   - **Continuar com Google** (OAuth)
   - **Continuar com Microsoft** (OIDC)
   - **Continuar com Apple** (Sign in with Apple)
3. **Verificação de e-mail** (link mágico, expira em 30 min). SSO já entrega e-mail verificado pelo provider.
4. **Escolha entrar/criar organização:**
   - Se o domínio do e-mail (ex.: `@laboratorioxyz.com.br`) já existe em alguma organização, sugere "Solicitar acesso a [Organização]" (vai para fila do admin).
   - Caso contrário, **cria nova organização** e abre o wizard §7.14.
5. **Plano inicial:** trial Pro 14 dias automático; conversão via wizard §7.14 passo 10.
6. **Welcome email** com CTA para baixar o app Android e link do tour.

#### Convite a usuários existentes
- Admin envia convite por e-mail (§7.13).
- Convidado clica → escolhe método de login (e-mail/senha ou SSO) → entra direto na organização que o convidou (sem passar pelo wizard de criação).

#### Cadastro a partir do app Android (campo)
- **Não permitido criar organização** pelo app — apenas login com credenciais ativas.
- Justificativa: criação de tenant exige decisões (perfil regulatório, plano, dados fiscais) que não fazem sentido em campo.

---

## 8. Especificação do Certificado de Calibração (cláusula 7.8 ISO/IEC 17025)

> Conteúdo mínimo obrigatório, derivado de [`iso 17025/04-templates/certificado-calibracao.md`](./iso%2017025/04-templates/certificado-calibracao.md). Toda emissão validada contra esta lista.
>
> **3 templates de PDF** (Template A, B, C) — selecionados automaticamente pelo sistema com base no perfil regulatório da organização emissora (§6.5). O técnico **não escolhe** o template; ele é decidido por configuração e bloqueado na emissão.

### 8.1 Cabeçalho
- Número do certificado / ano (sequencial irrevogável)
- Página X de N
- Razão social, endereço, CNPJ do laboratório
- **Acreditação Cgcre nº CAL-XXXX** (quando aplicável e dentro do escopo)
- Local de realização (laboratório / endereço do cliente)

### 8.2 Cliente
- Razão social, endereço, CNPJ
- Solicitação / OS

### 8.3 Item calibrado
- Descrição, fabricante, modelo, número de série, TAG, identificação do cliente
- Faixa nominal, resolução/divisão, classe
- Estado na recepção (conforme / com observações)

### 8.4 Datas
- Recebimento, calibração, emissão

### 8.5 Método
- Procedimento técnico (PT-XXX, Rev. NN)
- Norma de referência
- Adições / desvios / exclusões (se houver)

### 8.6 Padrões utilizados (rastreabilidade)
- Para cada padrão: identificação, certificado vinculado, laboratório emissor (acreditado / INM), validade, rastreado a (SI via INM)
- Declaração: "*Os resultados são metrologicamente rastreáveis ao SI via [INM país]*"

### 8.7 Condições ambientais
- Temperatura, umidade, pressão, com unidades e tolerâncias

### 8.8 Resultados
- Tabela completa: ponto, leitura, valor convencional, erro, repetibilidade, excentricidade
- **Incerteza expandida U (k=2)**, fator de abrangência declarado
- Balanço de incerteza disponível como anexo

### 8.9 Resultados antes/após ajuste
- Se houve ajuste, ambos os conjuntos.

### 8.10 Declaração de conformidade (opcional)
- Apenas se cliente solicitou na OS, com regra de decisão acordada explícita.

### 8.11 Opiniões e interpretações (opcional)
- Identificadas como tal, emitidas por pessoal autorizado.

### 8.12 Observações
- "*Os resultados deste certificado referem-se exclusivamente ao item calibrado.*"
- "*Este certificado **não recomenda intervalo de calibração**, salvo solicitação contratual identificada.*"

### 8.13 Assinatura
- Signatário autorizado: nome, cargo, autorização, assinatura eletrônica
- Hash SHA-256 do documento
- QR code de verificação pública

### 8.14 Variantes do template por perfil regulatório

#### Template A — Laboratório acreditado RBC (Tipo A)
- **Cabeçalho:** logo do laboratório + **símbolo Cgcre** + texto "Acreditação Cgcre nº CAL-XXXX".
- **Seção de padrões:** coluna "Origem" preenchida com nº CAL do laboratório RBC ou identificação do INM.
- **Rodapé:** "*Os resultados são metrologicamente rastreáveis ao SI por meio do INM (Inmetro). Certificado emitido sob acreditação Cgcre nº CAL-XXXX, signatária dos acordos de reconhecimento mútuo ILAC MRA. Os resultados deste certificado referem-se exclusivamente ao item calibrado.*"
- **Numeração:** série acreditada (ex.: `CAL-1234/2026/00001`).
- **Caso item fora do escopo acreditado:** símbolo Cgcre **suprimido** automaticamente + aviso "Calibração realizada fora do escopo acreditado".

#### Template B — Organização com padrões RBC, sem ISO 17025 (Tipo B)
- **Cabeçalho:** logo da organização, **sem símbolo Cgcre/RBC**.
- **Seção de padrões:** coluna "Origem" mostra obrigatoriamente o nº CAL-XXXX do laboratório RBC que calibrou cada padrão.
- **Rodapé:** "*Os resultados são metrologicamente rastreáveis ao Sistema Internacional de Unidades (SI) por meio dos padrões utilizados, calibrados por laboratórios acreditados pela Cgcre/Inmetro (RBC). Esta organização não é acreditada Cgcre. Os resultados deste certificado referem-se exclusivamente ao item calibrado.*"
- **Numeração:** série interna da organização (ex.: `CC/2026/00001`).
- Sem campo de escopo/CMC.

#### Template C — Organização com padrões calibrados pelo Inmetro fora de RBC (Tipo C)
- **Cabeçalho:** logo da organização, **sem símbolo Cgcre/RBC**, sem qualquer alusão à acreditação.
- **Seção de padrões:** coluna "Origem" mostra "Inmetro" (ou outro INM identificado).
- **Rodapé:** "*Os resultados são metrologicamente rastreáveis ao Sistema Internacional de Unidades (SI) por meio dos padrões utilizados, calibrados pelo Inmetro. Esta organização não é acreditada Cgcre e este certificado não está sob escopo RBC. Os resultados deste certificado referem-se exclusivamente ao item calibrado.*"
- **Numeração:** série interna da organização (ex.: `CC/2026/00001`).
- Sem campo de escopo/CMC.
- Validador semântico bloqueia uso das siglas "RBC" e "Cgcre" em qualquer campo livre.

#### Elementos comuns aos 3 templates
- Página X de N, cabeçalho institucional, dados do cliente, item calibrado, datas, método, condições ambientais, resultados, incerteza expandida com k declarado, declaração de conformidade (opcional), observações, assinatura eletrônica, hash SHA-256, **QR code de verificação pública**.
- Geração em **PDF/A** imutável.

---

## 9. Regras de bloqueio (impossível sair errado)

| Situação | Bloqueio |
|----------|----------|
| Padrão vencido | Bloqueia início da OS |
| Padrão sem certificado anexado | Bloqueia aprovação final |
| Padrão fora da faixa do ensaio | Bloqueia o ensaio |
| Ambiente fora da faixa do procedimento | Bloqueia execução (ou abre NC) |
| Procedimento não vigente | Não selecionável na OS |
| Técnico sem competência para o tipo de instrumento | Bloqueia execução |
| Revisor = executor | Bloqueia revisão |
| Signatário sem competência ou autorização vencida | Bloqueia assinatura |
| Cálculo de U menor que CMC declarada | **Bloqueia emissão** — sinaliza CMC subdeclarada ou erro no balanço de incerteza; exige revisão do Gestor da Qualidade com ação corretiva registrada (recalcular balanço ou revisar CMC declarada) |
| Declaração de conformidade sem regra de decisão acordada | Bloqueia emissão |
| Cliente sem endereço cadastrado | Bloqueia cadastro de equipamento |
| Equipamento sem cliente | Cadastro impossível por arquitetura |
| Reemissão tentando alterar leitura bruta / padrão / ambiente (§7.10) | Bloqueada — exige nova OS |
| Reemissão sem dupla aprovação (signatário ≠ original + GQ) | Bloqueia emissão da nova versão |
| Plano excedido (ex.: limite de OS/mês no Starter) | Bloqueia criação de nova OS até upgrade ou início do próximo ciclo |
| Org Tipo B ou C usando padrão de fonte não permitida (ver §7.4) | Bloqueia seleção do padrão na OS |
| Org Tipo B ou C tentando inserir símbolo Cgcre/RBC | Impossível por arquitetura (campo não existe na UI) |
| Org Tipo C usando "RBC" ou "Cgcre" em campo livre | Bloqueio semântico antes da emissão |
| Org Tipo A com acreditação vencida | Bloqueia emissão com símbolo (permite sem) |
| Org Tipo A calibrando item fora do escopo acreditado | Símbolo Cgcre suprimido + aviso obrigatório ao signatário |
| Org Tipo A com U expandida menor que CMC declarada | **Bloqueia emissão do ponto** — indica CMC subdeclarada ou erro no balanço; exige revisão do Gestor da Qualidade antes de prosseguir (não emitir sem símbolo esconde inconsistência técnica) |
| Mudança de perfil regulatório sem dupla aprovação Admin | Bloqueia transição |

---

## 10. Modelo de dados (visão lógica)

> **Toda tabela transacional carrega `organization_id` (multitenant — §6.6).** Omitido na visualização abaixo por concisão.

```
users  (global; e-mail único; identity_providers: password|google|microsoft|apple|saml)
  └─ user_identity_providers (vínculos OAuth/SAML)
  └─ user_devices (dispositivos Android registrados)
  └─ user_mfa (TOTP, backup codes)

organizations  (regulatory_profile: A | B | C; cgcre_number; accreditation_valid_until)
  └─ organization_profile_history (mudanças de perfil com aprovações)
  └─ organization_subscriptions (plano, limites, ciclo)
  └─ organization_onboarding_steps (10 passos do wizard §7.14)
  └─ organization_branding (logo, cor, identidade do certificado)
  └─ organization_sso_config (SAML/SCIM enterprise)
  └─ memberships  (user_id × organization_id × roles[])
  └─ teams · team_memberships
  └─ competencies · authorizations · authorization_evidence
  └─ clients
       └─ client_addresses
       └─ client_contacts
       └─ equipments  ← obrigatoriamente vinculado a 1 client
            └─ equipment_history
            └─ equipment_attachments
  └─ standards (padrões e auxiliares; source_type: INM | RBC | ILAC_MRA | OUTRO)
       └─ standard_certificates (PDFs, validade, hash, emissor, nº CAL quando RBC)
       └─ standard_usage (uso por OS — para histórico e impacto de troca/renovação)
  └─ procedures · procedure_revisions
  └─ work_orders
       └─ work_order_environment
       └─ work_order_tests
       └─ work_order_evidence
  └─ calculations · uncertainty_budgets
  └─ decision_rules
  └─ reviews · approvals
  └─ certificates  (normative_package_version registrado — §16.5)
       └─ certificate_revisions  (motive_code: DADO_CADASTRAL | RECALCULO_INCERTEZA | ...; aprovações; hash novo + anterior)
  └─ scope_items · cmc_items
  └─ nonconforming_work · complaints · corrective_actions  (motive, severity, action plan, root cause)
  └─ impartiality_declarations  (assinadas anualmente por usuário)
  └─ risk_register  (riscos à imparcialidade e operação — cláusula 8.5)
  └─ quality_documents  (MQ, PG, PT, IT, FR — versionados e aprovados)
  └─ audits  (plano anual + ciclos com checklist + NC geradas)
  └─ management_reviews  (pauta padrão + ata + deliberações — cláusula 8.9)
  └─ quality_indicators  (snapshot mensal para tendência)
  └─ audit_logs  (append-only, hash chain)
  └─ email_outbox  (e-mails transacionais §17.7 com status de entrega)
  └─ notifications  (in-app + push + e-mail unificado)
  └─ sync_events  (Android ↔ Backend; idempotência por event_id)
```

---

## 11. Requisitos não-funcionais

### 11.1 Disponibilidade
- SLA backend: 99,5% mensal.
- App Android: 100% offline para execução.

### 11.2 Performance
- Wizard de calibração no Android: ação → resposta < 200 ms (offline).
- Geração de certificado PDF: < 5 s no servidor.
- Sincronização típica de uma OS: < 30 s em 4G.

### 11.3 Segurança
- TLS 1.3 obrigatório.
- Banco local Android criptografado (SQLCipher).
- Hash SHA-256 em anexos e certificados.
- RBAC + segregação de funções.
- **MFA obrigatório** para signatários e administradores; opcional para demais.
- Logs imutáveis com cadeia de hash.
- **Multitenancy isolada por Row Level Security** (PostgreSQL RLS) + middleware de tenant + testes de cross-tenant leak.
- **OAuth 2.0 / OIDC** para SSO social (Google, Microsoft, Apple).
- **SAML 2.0 + SCIM** para SSO corporativo Enterprise.
- Rate limiting por IP e por usuário; proteção contra brute force.
- Vault de segredos por organização.

### 11.4 Privacidade e LGPD
- **Dados pessoais minimizados** — coleta limitada ao necessário para execução da calibração e rastreabilidade humana.
- **Termos de confidencialidade e DPA** aceitos no onboarding; DPA customizável no plano Enterprise (§6.7.1).
- **DPO designado** e contato publicado no portal e no rodapé do site.
- **Armazenamento em território nacional** — dados hospedados em região brasileira (AWS sa-east-1 ou equivalente); DR e backups também em território nacional. **Sem transferência internacional no MVP.**
- **Matriz de tratamento** (anexo ao DPA, referência contratual):

| Classe de dado | Papel Aferê | Base legal (LGPD) | Retenção |
|----------------|-----------------|-------------------|----------|
| Usuários da plataforma (nome, e-mail, credenciais) | Controlador | Execução de contrato (art. 7 V) | Ativa + 5 anos pós-desligamento |
| Clientes finais do laboratório (cadastros, contatos) | Operador | Sob instrução do controlador (laboratório) | Conforme instrução do lab; mín. 5 anos para registros técnicos |
| Leituras, evidências, certificados | Operador | Obrigação legal do lab (art. 7 II) + Execução de contrato (art. 7 V) | Mín. 5 anos; configurável no plano (5/10 anos) |
| Audit logs (identidade do ator + ação) | Controlador | Legítimo interesse (art. 7 IX) + obrigação legal | Mín. 10 anos; PII pseudonimizável sem quebra de hash chain |
| Biometria Android (2º fator local) | **Não coletada** | — | Template permanece no dispositivo via Android Keystore; Aferê não recebe o template |

- **Retenção — hierarquia:** matriz acima é o piso normativo/contratual; configuração de plano só parametriza **acima** desse piso.
- **Direitos do titular (art. 18 LGPD):** fluxo self-service no perfil do usuário para acesso, retificação, portabilidade e eliminação — SLA ≤ 15 dias. Dados sob obrigação legal ou retenção contratual são preservados com justificativa documentada; PII do ator em audit logs é pseudonimizada (mapping table separada e deletável) **sem quebrar a cadeia de hashes**.
- **Consentimento segregado por finalidade:** comunicação operacional, cobrança, marketing e integração de mensageria (WhatsApp) com bases legais e trilhas de consentimento separadas.
- **Formato de portabilidade declarado:** export ZIP contendo CSVs + PDF/A originais + audit log em JSONL + JSON schema documentado. Publicado no site como argumento anti-lock-in.

### 11.5 Usabilidade
- Android: foco em operação com luvas, telas grandes, contraste alto, retorno tátil.
- Web: WCAG 2.1 AA.
- PT-BR como idioma primário.

### 11.6 Auditabilidade
- Toda ação relevante registrada em `audit_logs`.
- Exportação de trilha por OS, certificado, usuário ou período.

### 11.7 Internacionalização (Fases futuras)
- Modelo preparado para múltiplos países e múltiplos INMs.

### 11.8 Preparação para DCC
- Entidades e cálculos versionados, com possibilidade de exportação XML segundo padrão DCC.

---

## 12. Roadmap

### Fase 1 — MVP operacional (mês 1 a 6)
> "Uma calibração executada do início ao certificado pelo celular."

- **Site de vendas público** com auto-cadastro (§7.15)
- **Auto-cadastro com Google/Microsoft/Apple + e-mail/senha** (§7.1)
- **Wizard de Onboarding em 10 passos** (§7.14)
- **Multitenancy com isolamento por RLS** (§6.6)
- **3 perfis regulatórios A/B/C com 3 templates de PDF** (§6.5, §8.14)
- **Planos comerciais (Starter/Pro/Enterprise) com trial Pro 14d** (§6.7)
- Login, perfis, RBAC, MFA para signatários e admins
- Gestão básica de usuários, equipes e competências (§7.13)
- Cadastro Cliente + Endereços + Contatos
- Cadastro Equipamento (vinculado a cliente)
- Cadastro Padrões com bloqueios e validação de fonte por perfil
- Procedimentos versionados
- Ordem de Serviço
- Wizard de execução completo (passos 1 a 15)
- Engine de cálculo + incerteza (k=2)
- Revisão técnica (web)
- Assinatura e emissão (com `normative_package` versionado — §16.5)
- Certificado PDF/A com QR code
- Verificação pública por QR
- Trilha de auditoria com hash chain
- Sincronização offline com idempotência
- E-mails transacionais essenciais (verificação, convite, certificado emitido, vencimento)

### Fase 2 — Laboratório maduro (mês 7 a 12)
- Módulo Qualidade completo (NC, reclamação, ação corretiva, auditoria interna, análise crítica)
- Escopo e CMC avançados
- Regras de conformidade sofisticadas (banda de guarda configurável)
- Painel gerencial e indicadores
- Portal do cliente completo
- Reemissão controlada
- Treinamento e gestão de competência
- Cartas de controle / indicadores de estabilidade

### Fase 3 — Ecossistema (mês 13 a 18)
- Integração ERP / financeiro
- Integração com portal Cgcre (consulta de escopo)
- API REST aberta
- Importação em massa (CSV/Excel)
- Relatórios estatísticos avançados
- Exportação **DCC XML**
- Suporte a outros instrumentos (termômetros, manômetros, paquímetros)

---

## 13. Critérios de aceite do MVP

O MVP é considerado pronto para produção quando, simultaneamente:

1. ✅ Uma calibração de balança IPNA pode ser executada do início ao certificado **exclusivamente pelo celular**, offline.
2. ✅ O sistema **bloqueia** uso de padrão vencido, sem certificado, fora de faixa.
3. ✅ O certificado é emitido com **resultado, incerteza expandida e fator k declarado**.
4. ✅ A revisão técnica e a assinatura ficam **registradas com identidade, timestamp e dispositivo**.
5. ✅ O QR code do certificado **valida autenticidade publicamente**.
6. ✅ Todo evento crítico aparece na **trilha de auditoria imutável**.
7. ✅ A sincronização Android → backend é **idempotente e resiliente** a perda de rede.
8. ✅ O cadastro de equipamento exige obrigatoriamente vínculo com cliente e endereço.
9. ✅ Signatário sem competência para o tipo de instrumento **não consegue assinar**.
10. ✅ Certificado emitido por laboratório acreditado respeita **escopo e CMC**.
11. ✅ Auto-cadastro funciona com e-mail/senha **e** SSO (Google/Microsoft/Apple); MFA obrigatório para signatários e admins.
12. ✅ **Wizard de Onboarding (§7.14)** completável em ≤ 1 hora pelo Administrador inicial, com bloqueios duros para emitir o 1º certificado.
13. ✅ **Multitenancy isolada por RLS** verificada por testes automatizados de cross-tenant leak (zero vazamentos).
14. ✅ Numeração sequencial por organização sem colisão entre tenants.
15. ✅ Sistema reconhece os **3 perfis regulatórios** (Tipo A/B/C) e seleciona automaticamente o template de PDF correspondente; tentativa de uso indevido de selo Cgcre/RBC é bloqueada.
16. ✅ **Reemissão controlada (§17.8)** funciona com dupla aprovação, versionamento R1/R2, hash anterior preservado e notificação automática ao cliente.
17. ✅ Página pública de verificação por QR responde corretamente para certificado autêntico, reemitido e não localizado (§17.5.6) e **expõe apenas metadados mínimos** (sem dados de cliente final, sem PDF completo sem autenticação).
18. ✅ **Plano de Validação do Software Aferê** aprovado e executado: protocolo formal, casos-teste normativos (incluindo ≥10 cenários-referência EURAMET cg-18 rodados em CI para a engine de incerteza — release bloqueado se qualquer divergir além de ε declarado), rastreabilidade requisito→teste, registro de evidências e procedimento de revalidação após mudança relevante (ISO/IEC 17025 §7.11).
19. ✅ **Hardening de multitenancy e audit log**: pool de conexões fail-closed sem `tenant_id`; linter de PR rejeita SQL sem `organization_id`; fuzz cross-tenant semanal em CI; audit log em object storage WORM (object lock) com checkpoints assinados periodicamente.
20. ✅ **Modelo de sincronização offline documentado e testado**: event sourcing por OS, idempotência por `(device_id, client_event_id)`, optimistic locking por agregado, lock exclusivo por OS após início da assinatura, matriz de conflitos com política de merge/rejeição por tipo. Teste de caos: 1.000 OS geradas offline por ≥ 5 dispositivos com sync randomizado — zero perdas, zero duplicatas.
21. ✅ **Parecer jurídico formal** sobre assinatura eletrônica auditável (MP 2.200-2 §10 II) anexado ao dossiê; minuta de DPA e matriz controlador/operador (§11.4) revisadas por advogado LGPD.
22. ✅ **Owner de governança normativa** nomeado com RACI e orçamento antes do go-live (§16.4).

---

## 14. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Cálculo de incerteza incorreto | Alto (certificado inválido) | Média | Engine validada com cenários de referência EURAMET cg-18; testes automatizados; versionamento da engine no certificado |
| Sincronização perde dados de campo | Alto | Baixa | Fila persistente, idempotência, reconciliação manual de conflitos |
| Assinatura eletrônica questionada juridicamente | Médio | Média | Trilha de auditoria + hash + planejamento para ICP-Brasil em Fase 2 |
| Cliente exige certificado em formato proprietário | Baixo | Alta | Suporte a templates personalizados (Fase 2) |
| Auditoria Cgcre identifica gap | Alto | Média | Mapeamento explícito norma → módulo + checklist de implementação publicado |
| Competência de signatário expira sem aviso | Médio | Alta | Alertas proativos 30/15/7 dias antes; bloqueio automático no vencimento |
| Engine de cálculo evolui e quebra reemissão antiga | Alto | Baixa | Versão da engine gravada por certificado; reemissão usa engine original |
| LGPD em dados de cliente | Médio | Média | Minimização, retenção configurável, DPO, cláusulas no onboarding |
| Cross-tenant data leak (multitenancy) | Crítico | Baixa | RLS PostgreSQL + middleware de tenant + testes automatizados de isolamento + revisão de PRs sensíveis |
| Provider de SSO (Google/Microsoft) indisponível | Médio | Baixa | Fallback para e-mail+senha + cache de sessão; status page do provider monitorada |
| Reemissão usada para encobrir erro grave (fraude) | Alto | Baixa | Dupla aprovação + trilha imutável + lista controlada de motivos + bloqueio de mudança em leituras brutas |
| Conformidade comercial: cliente excede limite do plano e fica bloqueado em campo | Médio | Média | Alerta proativo 80%/90%/100% + grace period de 24h + opção de upgrade em 1 clique |
| Cobertura normativa desatualizada (norma muda e ninguém atualiza) | Alto | Média | Comitê normativo mensal (§16.4) com SLA contratual; release-norm trimestral |

---

## 15. Glossário

| Termo | Significado |
|-------|-------------|
| **CMC** | Capacidade de Medição e Calibração — melhor incerteza declarada no escopo de acreditação |
| **DCC** | Digital Calibration Certificate — formato XML do PTB/BIPM, Plano Inmetro 2024–2027 |
| **DOQ-CGCRE** | Documento Orientativo da Coordenação Geral de Acreditação |
| **EMA** | Erro Máximo Admissível |
| **GUM** | Guide to the Expression of Uncertainty in Measurement (ISO/IEC Guide 98-3) |
| **IPNA / NAWI** | Instrumento de Pesagem Não Automático / Non-Automatic Weighing Instrument |
| **INM** | Instituto Nacional de Metrologia (no Brasil, Inmetro) |
| **NIT-DICLA** | Norma Inmetro Técnica da Divisão de Acreditação de Laboratórios |
| **OS** | Ordem de Serviço |
| **RBAC** | Role-Based Access Control |
| **RBC** | Rede Brasileira de Calibração — laboratórios de calibração acreditados pela Cgcre/Inmetro |
| **Perfil regulatório (A/B/C)** | Configuração da organização emissora que define modelo de certificado, fontes de padrões aceitas e bloqueios — ver §6.5 |
| **Multitenant** | Arquitetura SaaS em que múltiplas organizações compartilham a mesma instância com isolamento lógico de dados |
| **RLS** | Row Level Security — mecanismo do PostgreSQL que filtra linhas por critério de tenant a cada consulta |
| **OAuth 2.0 / OIDC** | Padrão aberto de autorização e autenticação delegada (usado para login com Google, Microsoft, Apple) |
| **SAML 2.0** | Padrão de federação de identidade para SSO corporativo entre organização cliente e Aferê |
| **SCIM** | System for Cross-domain Identity Management — provisionamento automático de usuários a partir de IdP corporativo |
| **MFA** | Multi-Factor Authentication — exige fator adicional além de senha (TOTP, biometria) |
| **TOTP** | Time-based One-Time Password — código numérico gerado por app (Google/Microsoft Authenticator) |
| **SSO** | Single Sign-On — autenticação única que permite login com identidade já estabelecida (Google, IdP corporativo) |
| **PDF/A** | Subconjunto do PDF para arquivamento de longo prazo, sem dependências externas e com fontes embutidas |
| **LGPD** | Lei Geral de Proteção de Dados (Brasil, Lei 13.709/2018) |
| **DPA** | Data Processing Agreement — acordo contratual que define como o Aferê processa dados pessoais em nome da organização |
| **DPO** | Data Protection Officer — encarregado pelo tratamento de dados pessoais |
| **MRR / ARPU / CAC** | Monthly Recurring Revenue / Average Revenue per Account / Customer Acquisition Cost — métricas SaaS (§6.7.4) |
| **NPS** | Net Promoter Score — métrica de satisfação |
| **PLG** | Product-Led Growth — modelo em que o próprio produto (trial, auto-cadastro) é o motor de aquisição |
| **RTM / RTAC** | Regulamento Técnico Metrológico / Regulamento Técnico de Avaliação da Conformidade |
| **U** | Incerteza expandida |
| **k** | Fator de abrangência (tipicamente k=2 para ~95% de confiança) |

---

## 16. Governança normativa e conformidade contínua

> **Princípio:** o sistema **garante por arquitetura** que cada certificado emitido respeita o conjunto normativo aplicável **na data e versão registrados no próprio certificado**. Acompanhar evolução de normas é responsabilidade compartilhada entre o produto (motor de regras versionado) e a operação (processo de governança documentado abaixo).

### 16.1 O que o sistema garante por arquitetura

| Garantia | Mecanismo no produto |
|----------|----------------------|
| Conteúdo do certificado conforme **ISO/IEC 17025:2017 cláusula 7.8** | Template fixo + checklist obrigatório por campo (§8) |
| Modelo correto por perfil regulatório (Tipo A/B/C) | Seleção automática de template (§8.14), bloqueio de selo Cgcre/RBC indevido (§9) |
| Rastreabilidade metrológica (ILAC P10, NIT-DICLA-021) | Padrão sem cadeia documental válida bloqueia emissão (§7.4) |
| Avaliação de incerteza (ISO/IEC Guide 98-3 / GUM, ILAC P14, DOQ-CGCRE-008) | Engine de cálculo versionada + balanço documentado (§7.8) |
| Boa prática NAWI (EURAMET cg-18) | Procedimentos de excentricidade, repetibilidade, linearidade implementados no wizard (§7.7) |
| EMA conforme **Portaria Inmetro 157/2022** (IPNA) | Critérios por classe (I/II/III/IIII) embutidos como dados versionados |
| Pesos padrão conforme **Portaria Inmetro 289/2021** | Validação de classe E1/E2/F1/F2/M1/M2/M3 no cadastro do padrão |
| Regra de decisão (ILAC G8) | Acordo registrado na OS, decisão calculada e impressa |
| Uso do símbolo Cgcre (DOQ-CGCRE-028) | Bloqueio automático fora do escopo, fora de CMC, ou em perfis B/C |
| Controle de documentos (ISO 17025 §8.3) | Procedimentos versionados, documentos não-vigentes não selecionáveis |
| Trilha de auditoria (ISO 17025 §8.4) | `audit_logs` append-only com cadeia de hashes |
| Segregação de funções (executor ≠ revisor ≠ signatário) | RBAC + bloqueios (§5.3, §7.1) |

### 16.2 O que continua dependendo de operação humana correta

| Aspecto | Por quê |
|---------|---------|
| Competência **efetiva** do pessoal | O sistema valida autorização **registrada**, não a competência real |
| Imparcialidade **efetiva** | O sistema registra declarações de conflito, não julga |
| Validade real da acreditação Cgcre | O sistema usa a data informada; renovação é processo externo |
| Veracidade das **leituras digitadas** | O sistema valida coerência (resolução, faixa), não substitui o técnico |
| Manutenção de procedimentos atualizados | Elaboração e aprovação são feitas por humanos no módulo Procedimentos |
| Tratamento efetivo de não conformidades | O sistema documenta, a organização executa |
| Análise crítica pela direção (§8.9) | Pauta sustentada pelo painel gerencial; deliberação é humana |

> **Conclusão:** o sistema reduz drasticamente a chance de erro técnico no certificado e impossibilita várias classes de não conformidade — mas **acreditação Cgcre é resultado da operação como um todo**, não apenas do software.

### 16.3 Matriz de cobertura normativa por release (MVP)

| Norma / Portaria | Versão coberta no MVP | Status |
|------------------|----------------------|--------|
| ABNT NBR ISO/IEC 17025 | **2017** | ✅ Coberta |
| Portaria Inmetro 157/2022 (IPNA) | **vigente desde 02/01/2023** | ✅ Coberta |
| Portaria Inmetro 289/2021 (pesos padrão) | **2021** | ✅ Coberta |
| Portaria Inmetro 248/2008 + 350/2012 (pré-medidos) | Vigente | ⚠ Referência (fora do escopo direto do MVP) |
| DOQ-CGCRE-008 (incerteza) | Vigente | ✅ Coberta |
| DOQ-CGCRE-028 (símbolo Cgcre) | Vigente | ✅ Coberta |
| NIT-DICLA-021 / 030 / 038 | Vigente | ✅ Coberta |
| ILAC P10, P14, G8, G24 | Vigente | ✅ Coberta |
| EURAMET cg-18 (NAWI) | Edição vigente | ✅ Coberta |
| RTM de balanças automáticas | Por tipo | ⏳ Fase 3 |
| RTM de manômetros, termômetros, paquímetros | Por tipo | ⏳ Fase 3 |
| Especificação **DCC XML** (PTB/BIPM/Inmetro) | Plano Inmetro 2024–2027 | ⏳ Fase 3 |

### 16.4 Processo de governança normativa (responsabilidade do produto)

1. **Comitê Normativo** — composto por: gestor da qualidade do laboratório piloto, metrologista interno do produto, product manager. Reunião mensal.
2. **Watchlist normativa** — monitoração ativa de:
   - Portal Inmetro (DOU diário, área de Metrologia Legal e Cgcre)
   - Publicações ILAC (P-series, G-series)
   - Atualizações ABNT (consultas e novas edições)
   - Newsletters DOQ-CGCRE / NIT-DICLA
   - Plano Estratégico Inmetro (DCC, modernização)
3. **Pipeline de mudança normativa**
   - **Monitoração** (semanal) → registro em backlog normativo
   - **Análise de impacto** (Comitê) → identifica módulos afetados
   - **Planejamento** → entra em release específico de conformidade (`release-norm-YYYY-MM`)
   - **Implementação** → atualização de regras versionadas
   - **Validação** → testes contra cenários normativos + revisão por especialista externo
   - **Comunicação** → release notes técnicas + alerta no painel do gestor de cada organização
4. **SLA de conformidade**
   - Mudança normativa **publicada** → início de análise: **≤ 5 dias úteis**
   - **Mudança crítica** (afeta validade de certificados): plano de mitigação **≤ 15 dias úteis**, release **≤ 60 dias**
   - **Mudança evolutiva**: release no próximo ciclo trimestral

### 16.5 Versionamento das regras normativas (compliance immutability)

Cada certificado emitido grava no banco o **"normative package"** completo usado para sua emissão:

```
normative_package_v_2026.04 = {
  iso_17025_clause_7_8: "2017",
  rtm_ipna: "Portaria 157/2022 vigente desde 02/01/2023",
  rtm_pesos: "Portaria 289/2021",
  uncertainty_engine: "v3.2.1",
  decision_rule_lib: "ILAC G8 v2019",
  cgcre_symbol_rules: "DOQ-CGCRE-028 rev. vigente em 2026-04",
  template_version: "A | B | C - v1.0"
}
```

**Consequências:**
- **Reemissão** usa o package **original** do certificado (mesma versão de regras, mesmo template), garantindo equivalência.
- **Nova emissão** após mudança normativa usa o package vigente.
- Auditoria pode reproduzir, byte a byte, a emissão de qualquer certificado histórico.

### 16.6 Limitações declaradas no MVP

- **Escopo de instrumento:** apenas balanças não automáticas (IPNA). Outros instrumentos entram em Fase 3.
- **Assinatura:** eletrônica auditável (não ICP-Brasil) — ICP-Brasil entra em Fase 2.
- **Exportação DCC:** não no MVP — modelo de dados preparado, exportação em Fase 3.
- **Idiomas do certificado:** apenas PT-BR no MVP.
- **Atualização normativa:** processo definido, equipe a constituir junto com lançamento.

### 16.7 O que o sistema entrega e o que depende da operação

- **Conteúdo, layout e regras automatizadas de emissão:** o sistema aplica as normas e portarias listadas em §16.3 na versão vigente registrada no certificado. Os campos exigidos pela cláusula 7.8 da ISO/IEC 17025 e os bloqueios de §9 são garantidos por arquitetura.
- **Conformidade sistêmica ISO/IEC 17025 da organização:** o sistema **suporta** o atendimento à norma, mas a conformidade efetiva depende dos fatores humanos descritos em §16.2 (competência real, imparcialidade, validade da acreditação, veracidade das leituras, tratamento de NC). Nenhum software sozinho garante acreditação Cgcre.
- **Atualização normativa:** compromisso de SLA definido em §16.4; depende da governança normativa com owner nominal, RACI e orçamento em vigor antes do go-live.
- **Cobertura de instrumentos:** o MVP cobre apenas balanças não automáticas (NAWI/IPNA, Portaria 157/2022). Demais instrumentos seguem o roadmap (§12). A cobertura vigente é declarada explicitamente em §16.3 e no próprio certificado — sem promessa implícita.

> **Redação comercial controlada:** o site de vendas (§17.1), materiais comerciais, contratos e comunicação pública NÃO devem afirmar "100% conforme", "passa em qualquer auditoria", "conformidade garantida" nem "impossível errar". Claims permitidos:
> - *"Bloqueia as não conformidades listadas em §9 do PRD."*
> - *"Suporta a operação ISO/IEC 17025 com trilha, evidência e rastreabilidade por arquitetura."*
> - *"Impede violação das regras automatizadas de emissão declaradas."*
> - *"Reduz classes específicas de erro (padrão vencido, uso indevido de selo, omissão de incerteza, revisor = executor, etc.)."*

---

## 17. Wireframes textuais (site de vendas + wizard de onboarding)

> **Convenção:** os wireframes são representações **textuais e indicativas** — descrevem hierarquia, elementos e CTAs, não estilo visual final. Servem como base para o time de design produzir os layouts em ferramenta de UI (Figma/Penpot).

### 17.1 Site de vendas público (`afere.com.br`)

#### 17.1.1 Header (presente em todas as páginas)
```
┌────────────────────────────────────────────────────────────────────────┐
│ [LOGO Aferê]  Como funciona · Conformidade · Preços · Recursos ·   │
│                   Casos · Contato            [Entrar] [Comece grátis →]│
└────────────────────────────────────────────────────────────────────────┘
```
- Logo à esquerda, navegação centralizada, CTAs à direita.
- "Comece grátis" em botão primário (cor da marca); "Entrar" em link discreto.
- Sticky no scroll.

#### 17.1.2 Footer (presente em todas as páginas)
```
┌────────────────────────────────────────────────────────────────────────┐
│ Produto      Conformidade      Empresa       Legal                     │
│ Como funciona  ISO 17025       Sobre nós     Termos de uso             │
│ Preços         Cgcre/RBC       Carreiras     Política de privacidade   │
│ Recursos       Inmetro         Blog          DPA (LGPD)                │
│ Status         Auditoria       Contato       Cookies                   │
│                                                                        │
│ © Aferê · CNPJ XX.XXX.XXX/0001-XX · DPO: dpo@afere.com.br     │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.1.3 Home (`/`)
```
┌────────────────────────────────────────────────────────────────────────┐
│ [HEADER]                                                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   HERO                                                                 │
│   "Emita certificados de calibração que passam em qualquer auditoria"  │
│   Plataforma metrológica web + Android para laboratórios e empresas    │
│   acreditadas RBC, com padrões RBC ou padrões Inmetro.                 │
│                                                                        │
│   [Comece grátis — 14 dias]   [Ver demo de 2 minutos ▶]               │
│                                                                        │
│   ★★★★★  "Reduzimos retrabalho a zero" — Lab. Acme                    │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│   SOCIAL PROOF                                                         │
│   [Logo cliente 1] [Logo 2] [Logo 3] [Logo 4] [Logo 5] [Logo 6]       │
├────────────────────────────────────────────────────────────────────────┤
│   PROBLEMA → SOLUÇÃO                                                   │
│   Certificado errado custa caro. O Aferê impede por arquitetura.   │
│   ┌─────────────┬─────────────┬─────────────┐                          │
│   │ Padrão      │ Cálculo     │ Selo Cgcre  │                          │
│   │ vencido?    │ de incerteza│ usado fora  │                          │
│   │ Bloqueado.  │ automático. │ do escopo?  │                          │
│   │             │             │ Bloqueado.  │                          │
│   └─────────────┴─────────────┴─────────────┘                          │
├────────────────────────────────────────────────────────────────────────┤
│   3 PERFIS, 3 TEMPLATES                                                │
│   ┌─────────────┬─────────────┬─────────────┐                          │
│   │ TIPO A      │ TIPO B      │ TIPO C      │                          │
│   │ Acreditado  │ Padrões RBC │ Padrões     │                          │
│   │ RBC/17025   │ sem 17025   │ Inmetro     │                          │
│   │ [Ver mais]  │ [Ver mais]  │ [Ver mais]  │                          │
│   └─────────────┴─────────────┴─────────────┘                          │
├────────────────────────────────────────────────────────────────────────┤
│   COMO FUNCIONA (carrossel/animação 3 etapas)                          │
│   1. Cadastre cliente e equipamento                                    │
│   2. Execute no Android com wizard guiado                              │
│   3. Revise, assine e entregue o certificado com QR                    │
│   [Ver fluxo completo →]                                               │
├────────────────────────────────────────────────────────────────────────┤
│   CONFORMIDADE EM CADA EMISSÃO                                         │
│   ✓ ISO/IEC 17025:2017       ✓ Portaria Inmetro 157/2022 (IPNA)        │
│   ✓ Portaria 289/2021         ✓ DOQ-CGCRE-008 / 028                   │
│   ✓ ILAC P10/P14/G8           ✓ EURAMET cg-18                          │
│   [Ver matriz completa de conformidade →]                              │
├────────────────────────────────────────────────────────────────────────┤
│   DEPOIMENTO EM DESTAQUE                                               │
│   "Antes do Aferê tinha 12% de reemissão. Hoje, zero."            │
│   — João Silva, Gerente da Qualidade, Lab. Acme                       │
├────────────────────────────────────────────────────────────────────────┤
│   CTA FINAL                                                            │
│   Comece em 5 minutos. Trial Pro 14 dias. Sem cartão.                  │
│   [Criar conta com Google] [Criar conta com e-mail]                    │
├────────────────────────────────────────────────────────────────────────┤
│ [FOOTER]                                                               │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.1.4 Página de Preços (`/precos`)
```
┌────────────────────────────────────────────────────────────────────────┐
│ [HEADER]                                                               │
├────────────────────────────────────────────────────────────────────────┤
│   "Planos para cada estágio do seu laboratório"                        │
│   [ Mensal | Anual (-2 mês) ]   ← toggle                               │
├────────────────────────────────────────────────────────────────────────┤
│   ┌────────────────┬────────────────┬────────────────┐                 │
│   │   STARTER      │   PRO ★popular │   ENTERPRISE   │                 │
│   │   R$ 249/mês   │   R$ 749/mês   │   Sob consulta │                 │
│   │                │                │                │                 │
│   │ Para começar   │ Lab em operação│ Multi-org +    │                 │
│   │                │                │ SSO corporativo│                 │
│   │                │                │                │                 │
│   │ ✓ 3 usuários   │ ✓ 15 usuários  │ ✓ Ilimitado    │                 │
│   │ ✓ 80 OS/mês    │ ✓ OS ilimitada │ ✓ + tudo       │                 │
│   │ ✓ App Android  │ ✓ + Qualidade  │ ✓ SAML/SCIM    │                 │
│   │ ✓ 3 templates  │ ✓ + ERP        │ ✓ DCC XML      │                 │
│   │ ✓ Login Google │ ✓ + Painel     │ ✓ White-label  │                 │
│   │                │                │                │                 │
│   │ [Começar →]    │ [Começar →]    │ [Falar conosco]│                 │
│   └────────────────┴────────────────┴────────────────┘                 │
├────────────────────────────────────────────────────────────────────────┤
│   COMPARATIVO COMPLETO (tabela expansível)                             │
│   ▶ Ver todos os recursos lado a lado                                  │
├────────────────────────────────────────────────────────────────────────┤
│   ADD-ONS                                                              │
│   ▢ Pacote 50 GB · ▢ Usuário extra · ▢ White-label · ▢ ICP-Brasil     │
├────────────────────────────────────────────────────────────────────────┤
│   FAQ                                                                  │
│   ▷ Posso trocar de plano depois?                                      │
│   ▷ Como funciona o trial?                                             │
│   ▷ E se eu exceder o limite?                                          │
│   ▷ Como é o onboarding?                                               │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.1.5 Página Conformidade (`/conformidade`)
```
┌────────────────────────────────────────────────────────────────────────┐
│ [HEADER]                                                               │
├────────────────────────────────────────────────────────────────────────┤
│   "Conformidade não é promessa, é arquitetura"                         │
│   Como o Aferê garante ISO 17025 e portarias Inmetro a cada        │
│   certificado emitido.                                                 │
├────────────────────────────────────────────────────────────────────────┤
│   3 PERFIS REGULATÓRIOS                                                │
│   [Tabela comparativa Tipo A / B / C com diferenças visuais]           │
├────────────────────────────────────────────────────────────────────────┤
│   MATRIZ DE COBERTURA                                                  │
│   Norma                       │ Versão coberta          │ Status       │
│   ABNT NBR ISO/IEC 17025      │ 2017                    │ ✓            │
│   Portaria Inmetro 157/2022   │ vigente                 │ ✓            │
│   ... (lista §16.3)                                                    │
├────────────────────────────────────────────────────────────────────────┤
│   GOVERNANÇA NORMATIVA                                                 │
│   Comitê mensal · Watchlist Inmetro/ILAC · SLA ≤ 60d para mudanças     │
│   críticas                                                             │
├────────────────────────────────────────────────────────────────────────┤
│   PERGUNTAS COMUNS DE AUDITORES                                        │
│   ▷ Como vocês versionam as regras normativas?                         │
│   ▷ O que acontece com certificados antigos quando uma norma muda?     │
│   ▷ A trilha de auditoria é exportável?                                │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.1.6 Página Como funciona (`/como-funciona`)
```
SEÇÕES:
1. Vídeo principal (3 minutos) — fluxo completo
2. Cadastro de cliente e equipamento (animação)
3. App Android no campo (screenshots reais do wizard)
4. Cálculo de incerteza automático (animação)
5. Revisão e assinatura (workflow visual)
6. Certificado emitido + QR de verificação
7. CTA: [Comece grátis] / [Agendar demo]
```

#### 17.1.7 Demais páginas (estrutura sumária)

| Página | Conteúdo principal |
|--------|--------------------|
| `/recursos` | Blog + ebooks + checklist 17025 + glossário metrológico (lead magnets com formulário) |
| `/casos` | Card por cliente: foto, depoimento, 3 métricas |
| `/contato` | Form curto + Calendly embedado para demo |
| `/sobre` | Equipe, missão, diferenciais |
| `/blog/[slug]` | Posts SEO sobre 17025, RBC, calibração, incerteza |

### 17.2 Wizard de Onboarding (Web)

> Layout consistente em todos os passos: barra de progresso superior + sidebar com 10 itens + área principal + ações no rodapé.

#### 17.2.1 Layout-base
```
┌────────────────────────────────────────────────────────────────────────┐
│ [LOGO Aferê]                          Olá, João  · [Sair]          │
├──────────────────┬─────────────────────────────────────────────────────┤
│                  │  Passo 4 de 10 · ▰▰▰▱▱▱▱▱▱▱  40%                    │
│ ✓ 1 Identidade   ├─────────────────────────────────────────────────────┤
│ ✓ 2 Endereços    │                                                     │
│ ✓ 3 Branding     │  ÁREA PRINCIPAL DO PASSO ATUAL                      │
│ ▶ 4 Perfil       │                                                     │
│   5 Escopo/CMC   │                                                     │
│   6 Numeração    │                                                     │
│   7 Equipe       │                                                     │
│   8 1º padrão    │                                                     │
│   9 1º proced.   │                                                     │
│  10 Plano        │                                                     │
│                  │                                                     │
│ [Salvar e sair]  │                                                     │
│                  ├─────────────────────────────────────────────────────┤
│                  │  [← Voltar]    [Pular passo]    [Continuar →]       │
└──────────────────┴─────────────────────────────────────────────────────┘
```

#### 17.2.2 Passo 1 — Identidade da organização
```
Titulo: "Vamos conhecer sua organização"
Subtítulo: "Esses dados aparecem no cabeçalho do certificado."

[CNPJ: __.___.___/____-__]  ← validação + busca pública (preenche campos abaixo)
[Razão social: ________________________________]
[Nome fantasia: _______________________________]
[Segmento: ▼ Laboratório de calibração / Empresa industrial / Outro]
[Telefone: (__) _____-____]
[E-mail institucional: ____________@____________]

✓ Privacidade: usaremos esses dados apenas para emitir certificados
  e gerar a assinatura institucional. Ver Política de Privacidade.

[Continuar →]
```

#### 17.2.3 Passo 2 — Endereços
```
Titulo: "Onde vocês operam?"
Subtítulo: "Você pode adicionar mais endereços depois."

ENDEREÇO PRINCIPAL (obrigatório)
[CEP: _____-___] [Buscar] ← auto-preenche
[Logradouro: ________________] [Nº: ____] [Compl: ____]
[Bairro: __________] [Cidade: __________] [UF: __]
[Apelido: ex. "Sede"]

[+ Adicionar outro endereço]

[← Voltar]                                          [Continuar →]
```

#### 17.2.4 Passo 3 — Branding
```
Titulo: "Identidade visual do certificado"

LOGO  [Arrastar arquivo aqui ou clicar para enviar]  PNG/SVG, fundo
                                                     transparente, máx 1MB
                ┌────────────────┐
                │   PRÉVIA       │
                │  [logo aqui]   │
                └────────────────┘

COR PRIMÁRIA  [seletor de cor]  Hex: #1A4F8B

ASSINATURA INSTITUCIONAL (texto que aparece no rodapé)
[ Laboratório XYZ Ltda — CNPJ XX.XXX.XXX/0001-XX                        ]

PRÉVIA DO CABEÇALHO DO CERTIFICADO:
┌────────────────────────────────────────────────────────────┐
│ [LOGO]  Laboratório XYZ Ltda                               │
│         Rua A, 123 — São Paulo/SP — CNPJ XX.XXX.XXX/0001   │
└────────────────────────────────────────────────────────────┘

[← Voltar]                                          [Continuar →]
```

#### 17.2.5 Passo 4 — Perfil regulatório (decisão crítica)
```
Titulo: "Qual o perfil regulatório da sua organização?"
Subtítulo: "Essa escolha define o modelo de certificado e as regras de
            uso de selo Cgcre/RBC. Você pode mudar depois com aprovação
            de 2 administradores."

┌──────────────────┬──────────────────┬──────────────────┐
│ TIPO A           │ TIPO B           │ TIPO C           │
│                  │                  │                  │
│ Acreditado RBC   │ Sem 17025,       │ Padrões Inmetro  │
│ ISO/IEC 17025    │ padrões RBC      │ fora de RBC      │
│                  │                  │                  │
│ ✓ Selo Cgcre     │ ✗ Sem selo       │ ✗ Sem selo       │
│ ✓ Escopo/CMC     │ ✓ Rastreável RBC │ ✓ Rastreável INM │
│                  │                  │                  │
│ [○ Selecionar]   │ [○ Selecionar]   │ [○ Selecionar]   │
└──────────────────┴──────────────────┴──────────────────┘

[Compare em detalhe →] (abre modal com tabela §6.5)

▼ Selecionei TIPO A — me peça os dados de acreditação:
  [Nº CAL: CAL-_______] [Validade: __/__/____] [Anexar certificado Cgcre]

[← Voltar]                                          [Continuar →]
```

#### 17.2.6 Passo 5 — Escopo e CMC (somente Tipo A)
```
Titulo: "Cadastre seu escopo acreditado"
Subtítulo: "Pode pular agora e completar depois — mas o selo Cgcre só
            sai dentro do escopo cadastrado."

[+ Adicionar item de escopo]
┌─────────────────────────────────────────────────────────────────┐
│ Tipo: ▼ NAWI/IPNA  Faixa: 0-3 kg  Classe: III  CMC: U=±0,5 mg │
│                                                  [Editar][Excluir]│
└─────────────────────────────────────────────────────────────────┘

[Pular esta etapa]                                  [Continuar →]
```

#### 17.2.7 Passo 6 — Numeração e identidade do certificado
```
Titulo: "Como você quer numerar seus certificados?"

Padrão sugerido para o seu perfil (Tipo A): CAL-XXXX/YYYY/NNNNN
Exemplo: CAL-1234/2026/00001

[ Personalizar ▼ ]
Prefixo: [CAL-1234]  Separador: [/]  Ano: [☑ incluir]  Sequencial: [5 dígitos ▼]

PRÉVIA DO PRIMEIRO CERTIFICADO:
CAL-1234/2026/00001

[Ver prévia completa do PDF →] (abre modal com template aplicado)

[← Voltar]                                          [Continuar →]
```

#### 17.2.8 Passo 7 — Equipe inicial
```
Titulo: "Convide sua equipe"
Subtítulo: "Pode adicionar mais usuários depois."

[+ Adicionar usuário]
┌─────────────────────────────────────────────────────────┐
│ Nome:                E-mail:                Papel:      │
│ [Maria Souza____] [maria@___] [▼ Signatária]            │
│                                              [Excluir]  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ [Carlos Lima___] [carlos@__] [▼ Técnico]   [Excluir]    │
└─────────────────────────────────────────────────────────┘

ⓘ Cada convidado recebe um e-mail com link válido por 72h.
ⓘ Signatários precisam confirmar MFA no 1º login.

[Pular esta etapa]                                  [Enviar convites →]
```

#### 17.2.9 Passo 8 — 1º padrão
```
Titulo: "Cadastre seu primeiro padrão"
Subtítulo: "Sem pelo menos 1 padrão válido você não consegue emitir
            certificados."

[Tipo: ▼ Peso padrão / Termohigrômetro / Barômetro / ...]
[Identificação interna: PESO-001]
[Fabricante:______] [Modelo:______]
[Valor nominal: 1 kg] [Classe: ▼ E2 / F1 / F2 / M1 / ...]
[Incerteza declarada: ±____ mg]

CERTIFICADO DO PADRÃO (obrigatório)
[Anexar PDF: __________________________]
Fonte do certificado:
  ○ INM (Inmetro)
  ● RBC (laboratório acreditado Cgcre) — Nº CAL: [CAL-____]
  ○ ILAC MRA
[Data da calibração: __/__/____] [Vencimento: __/__/____]

ⓘ Seu perfil (Tipo B) só aceita padrões com fonte RBC. ✓ Validado.

[← Voltar]                                          [Continuar →]
```

#### 17.2.10 Passo 9 — 1º procedimento
```
Titulo: "Cadastre seu primeiro procedimento"
Subtítulo: "Comece com um template pronto e ajuste depois."

ESCOLHA UM TEMPLATE:
┌────────────────────────┬────────────────────────┬────────────────────────┐
│ IPNA classe III campo  │ IPNA bancada           │ Verificação interna    │
│ EURAMET cg-18          │ EURAMET cg-18          │ Procedimento simplif.  │
│ 5 ensaios padrão       │ 7 ensaios padrão       │ 3 ensaios              │
│ [Usar este]            │ [Usar este]            │ [Usar este]            │
└────────────────────────┴────────────────────────┴────────────────────────┘

[Ou criar do zero]    [Pular]

[← Voltar]                                          [Continuar →]
```

#### 17.2.11 Passo 10 — Plano e ativação
```
Titulo: "Você está usando Pro · Trial 14 dias"
Subtítulo: "Tudo desbloqueado até DD/MM/YYYY. Sem cartão agora."

PLANO ATUAL:                          [Comparar planos →]
┌────────────────────────────────────────────────┐
│ ★ PRO  R$ 749/mês (anual: R$ 624/mês)         │
│ 15 usuários · OS ilimitada · Qualidade · ERP   │
│ [Manter trial e converter depois]              │
│ [Adicionar cartão e ativar agora]              │
└────────────────────────────────────────────────┘

[ ☑ Li e aceito os Termos de Uso ]
[ ☑ Li e aceito o DPA (LGPD) ]

[← Voltar]                                          [Concluir →]

▼ Após concluir:
   1. Tour guiado pelo app web (3 min)
   2. Link para baixar o app Android
   3. CTA: "Crie sua primeira OS"
```

### 17.3 App Android — wireframes textuais

> **Princípios de design mobile do produto:**
> - **Alto contraste** e **fontes grandes** — uso com luvas, ambientes industriais, baixa iluminação.
> - **Botões alvo ≥ 56dp** — toque preciso mesmo com luvas.
> - **Indicador de sincronização sempre visível** — operação offline-first exige feedback constante.
> - **Modal de bloqueio é onipresente** — qualquer regra do §9 violada vira tela bloqueante explicativa.
> - **Confirmar > Digitar** — sempre que o sistema sabe o valor, mostra para o técnico apenas confirmar.
> - **Wizard impositivo** — sem menu lateral durante a execução; só `Voltar / Continuar`.

#### 17.3.1 Login e seleção de organização

```
┌──────────────────────────┐
│        [LOGO]            │
│      Aferê           │
│                          │
│  Bem-vindo de volta      │
│                          │
│  E-mail                  │
│  [_____________________] │
│                          │
│  Senha                   │
│  [_____________________] │
│                          │
│  [   👆 Biometria   ]    │
│                          │
│  [    Entrar       →]    │
│                          │
│  ──────  ou  ──────      │
│                          │
│  [G] Continuar com Google│
│  [⊞] Continuar com MS    │
│                          │
│  Esqueci a senha · Ajuda │
│                          │
│  ⚪ Modo offline ativo   │
└──────────────────────────┘
```

```
┌──────────────────────────┐
│ ← Selecionar organização │
├──────────────────────────┤
│                          │
│  Você participa de:      │
│                          │
│  ┌────────────────────┐  │
│  │ ⭐ Lab. Acme        │  │
│  │ Tipo A · 12 OS hoje│  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ Indústria XYZ      │  │
│  │ Tipo C · 3 OS hoje │  │
│  └────────────────────┘  │
│                          │
│  [+ Solicitar acesso]    │
│                          │
└──────────────────────────┘
```

#### 17.3.2 Home / Dashboard do técnico

```
┌──────────────────────────┐
│ Lab. Acme   👤 João  ⚙   │
│ ✓ Sincronizado 14:22     │
├──────────────────────────┤
│                          │
│  Olá, João               │
│  Hoje, 19/04             │
│                          │
│  ┌────────────────────┐  │
│  │ MINHAS OS          │  │
│  │  ▶ 3 atribuídas    │  │
│  │  ▶ 1 em andamento  │  │
│  │  ✓ 5 concluídas    │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ ⚠ ATENÇÃO          │  │
│  │ 2 padrões vencendo │  │
│  │ em 7 dias          │  │
│  └────────────────────┘  │
│                          │
│  [ + Iniciar nova OS ]   │
│                          │
├──────────────────────────┤
│ 🏠 Home  📋 OS  ⚖ Pad  ⋯ │
└──────────────────────────┘
```

#### 17.3.3 Lista de OS

```
┌──────────────────────────┐
│ ← OS                  🔍 │
├──────────────────────────┤
│ [Atribuídas|Em and.|Sync]│
├──────────────────────────┤
│                          │
│ ┌──────────────────────┐ │
│ │ OS-2026-00142        │ │
│ │ Lab. Acme            │ │
│ │ Balança Toledo 3kg   │ │
│ │ TAG: BAL-007         │ │
│ │ 📍 Cliente · Hoje    │ │
│ │            [Iniciar →]│ │
│ └──────────────────────┘ │
│                          │
│ ┌──────────────────────┐ │
│ │ OS-2026-00143        │ │
│ │ Padaria Pão Doce     │ │
│ │ Balança Filizola 15kg│ │
│ │ ⚠ Padrão vencendo    │ │
│ │            [Iniciar →]│ │
│ └──────────────────────┘ │
│                          │
│ ⏳ 1 OS aguardando sync  │
│                          │
└──────────────────────────┘
```

#### 17.3.4 Detalhe da OS / Pré-execução

```
┌──────────────────────────┐
│ ← OS-2026-00142          │
├──────────────────────────┤
│                          │
│ CLIENTE                  │
│ Lab. Acme                │
│ Rua A, 123 — São Paulo   │
│                          │
│ EQUIPAMENTO              │
│ Balança Toledo Prix 3    │
│ Série: 9087654           │
│ TAG: BAL-007             │
│ Max: 3 kg · d: 0,5 g     │
│ Classe: III              │
│                          │
│ PROCEDIMENTO             │
│ PT-005 rev.04            │
│ IPNA classe III campo    │
│                          │
│ PADRÕES NECESSÁRIOS      │
│ ✓ PESO-001 (1 kg, F1)    │
│ ✓ PESO-002 (2 kg, F1)    │
│ ✓ TH-003 (termohigro)    │
│                          │
│ REGRA DE DECISÃO         │
│ Não solicitada           │
│                          │
│ ────────────────────     │
│ [  Iniciar wizard  →]    │
└──────────────────────────┘
```

#### 17.3.5 Wizard de execução — 15 passos

> **Layout-base de cada passo:**
> ```
> ┌──────────────────────────┐
> │ ← Passo X/15           ⓘ │
> │ ▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱  20%      │
> ├──────────────────────────┤
> │ TÍTULO DO PASSO          │
> │ Subtítulo / instrução    │
> │                          │
> │ [conteúdo específico]    │
> │                          │
> ├──────────────────────────┤
> │ [Voltar]    [Continuar →]│
> └──────────────────────────┘
> ```

##### Passo 1 — Identificação da OS
```
┌──────────────────────────┐
│ ← Passo 1/15           ⓘ │
│ ▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱  7%      │
├──────────────────────────┤
│ Identificação            │
│                          │
│ OS: OS-2026-00142        │
│ Técnico: João Silva ✓    │
│                          │
│ 🔒 Confirme sua senha    │
│ [_____________________]  │
│                          │
│ ou [👆 Biometria]        │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 2 — Verificação do equipamento
```
┌──────────────────────────┐
│ ← Passo 2/15           ⓘ │
├──────────────────────────┤
│ Verifique o equipamento  │
│                          │
│ Toledo Prix 3            │
│ Série: 9087654           │
│ TAG: BAL-007             │
│                          │
│ 📷 Foto da placa         │
│ [   Tocar para tirar  ]  │
│                          │
│ Lacres íntegros?         │
│ ○ Sim   ○ Não (foto)     │
│                          │
│ Estado na recepção:      │
│ ● Conforme               │
│ ○ Com observações        │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 3 — Reserva e validação de padrões
```
┌──────────────────────────┐
│ ← Passo 3/15           ⓘ │
├──────────────────────────┤
│ Padrões da OS            │
│                          │
│ ✓ PESO-001 · 1 kg · F1   │
│   Cert: RBC CAL-1234     │
│   Vence: 12/08/2026 ✓    │
│                          │
│ ✓ PESO-002 · 2 kg · F1   │
│   Cert: RBC CAL-1234     │
│   Vence: 12/08/2026 ✓    │
│                          │
│ ✓ TH-003 · termohigr.    │
│   Cert: RBC CAL-9876     │
│   Vence: 30/06/2026 ✓    │
│                          │
│ Todos válidos para o     │
│ perfil Tipo A.           │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

> **Variante bloqueada (modal de §9):**
> ```
> ┌──────────────────────────┐
> │ 🚫 PADRÃO BLOQUEADO      │
> │                          │
> │ PESO-001 vence em 5 dias │
> │ — fora da política da    │
> │ organização (≥ 30 dias). │
> │                          │
> │ Não é possível avançar.  │
> │                          │
> │ [Trocar padrão]          │
> │ [Falar com qualidade]    │
> └──────────────────────────┘
> ```

##### Passo 4 — Condições ambientais
```
┌──────────────────────────┐
│ ← Passo 4/15           ⓘ │
├──────────────────────────┤
│ Ambiente                 │
│                          │
│ Faixa do procedimento:   │
│ Temp: 18°C – 25°C        │
│ Umid: 30% – 70%          │
│                          │
│ Lido em TH-003:          │
│ Temp: [22.4] °C  📷      │
│ Umid: [55.0] %   📷      │
│ Pres: [1013] hPa 📷      │
│                          │
│ ✓ Dentro da faixa        │
│                          │
│ [+ Foto do display TH]   │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 5 — Verificação inicial (zero)
```
┌──────────────────────────┐
│ ← Passo 5/15           ⓘ │
├──────────────────────────┤
│ Verificação inicial      │
│                          │
│ 1. Estabilizar a balança │
│ 2. Zerar                 │
│ 3. Aguardar 30s ⏱        │
│                          │
│ Indicação no zero:       │
│ [ 0,000 ] g              │
│                          │
│ ⏱ Cronômetro: 0:28 / 0:30│
│                          │
│ [ Capturar leitura ]     │
│                          │
├──────────────────────────┤
│ [Voltar]   [Continuar ✓→]│
└──────────────────────────┘
```

##### Passo 6 — Excentricidade
```
┌──────────────────────────┐
│ ← Passo 6/15           ⓘ │
├──────────────────────────┤
│ Excentricidade           │
│ Carga: 1 kg (PESO-001)   │
│                          │
│       [diagrama prato]   │
│       ┌──────────┐       │
│       │  ① Centro │       │
│       │ ②   ③   ④│       │
│       │ ⑤        │       │
│       └──────────┘       │
│                          │
│ ① Centro:  [1000.0] g ✓  │
│ ② Frente:  [_____] g     │
│ ③ Direita: [_____] g     │
│ ④ Trás:    [_____] g     │
│ ⑤ Esquerda:[_____] g     │
│                          │
│ Δ máx calculado: —       │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 7 — Repetibilidade
```
┌──────────────────────────┐
│ ← Passo 7/15           ⓘ │
├──────────────────────────┤
│ Repetibilidade           │
│ Carga: 2 kg (PESO-002)   │
│ 6 repetições             │
│                          │
│ Rep 1: [2000.1] g ✓      │
│ Rep 2: [2000.0] g ✓      │
│ Rep 3: [2000.1] g ✓      │
│ Rep 4: [_____] g         │
│ Rep 5: [_____] g         │
│ Rep 6: [_____] g         │
│                          │
│ ⏱ Aguarde 15s entre      │
│   pesagens               │
│                          │
│ Desv. padrão: 0,058 g    │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 8 — Linearidade (curva)
```
┌──────────────────────────┐
│ ← Passo 8/15           ⓘ │
├──────────────────────────┤
│ Linearidade — crescente  │
│                          │
│ Pontos sugeridos:        │
│ 10%, 25%, 50%, 75%, 100% │
│                          │
│ 0,3 kg → [300.1] g  ✓    │
│ 0,75kg → [750.0] g  ✓    │
│ 1,5 kg → [1500.0]g  ✓    │
│ 2,25kg → [____.__]g      │
│ 3,0 kg → [____.__]g      │
│                          │
│ Padrão sugerido:         │
│ PESO-001 + PESO-002      │
│ (combinação automática)  │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 9 — Pesagem mínima (se aplicável)
```
┌──────────────────────────┐
│ ← Passo 9/15           ⓘ │
├──────────────────────────┤
│ Pesagem mínima           │
│                          │
│ Critério: USP <41>       │
│ (2σ × 1000 ≤ 0,1% leit.) │
│                          │
│ σ medido: 0,058 g        │
│ Mínima calculada: 116 g  │
│                          │
│ ✓ Adequada para usos     │
│   acima de 116 g         │
│                          │
│ Não aplicável a esta OS? │
│ [Marcar como N/A]        │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 10 — Cálculo consolidado e incerteza
```
┌──────────────────────────┐
│ ← Passo 10/15          ⓘ │
├──────────────────────────┤
│ Cálculo + Incerteza      │
│                          │
│ Erro máx: +0,1 g         │
│ Repetib.: 0,058 g        │
│ Excentr.: 0,1 g          │
│                          │
│ U expandida (k=2):       │
│ ±0,15 g                  │
│                          │
│ Balanço de incerteza:    │
│ Padrão........ 0,02 g    │
│ Repetib....... 0,058 g   │
│ Excentr....... 0,058 g   │
│ Resolução..... 0,29 g    │
│ Deriva........ 0,01 g    │
│                          │
│ [Ver balanço completo →] │
│                          │
│ ✓ U > CMC (0,5 mg)       │
│ ✓ Selo Cgcre liberado    │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 11 — Regra de decisão (condicional)
```
┌──────────────────────────┐
│ ← Passo 11/15          ⓘ │
├──────────────────────────┤
│ Regra de decisão         │
│ (acordada na OS)         │
│                          │
│ Regra: Aceitação binária │
│ com banda de guarda 50%  │
│ Especificação: ±2 g      │
│                          │
│ Por ponto:               │
│ 0,3 kg → APROVADO ✓      │
│ 0,75kg → APROVADO ✓      │
│ 1,5 kg → APROVADO ✓      │
│ 2,25kg → APROVADO ✓      │
│ 3,0 kg → APROVADO ✓      │
│                          │
│ Resultado: APROVADO      │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 12 — Observações técnicas
```
┌──────────────────────────┐
│ ← Passo 12/15          ⓘ │
├──────────────────────────┤
│ Observações              │
│                          │
│ Houve ajuste durante     │
│ a calibração?            │
│ ○ Sim   ● Não            │
│                          │
│ Notas reutilizáveis:     │
│ ☐ Calibração no local    │
│ ☐ Balança em uso fiscal  │
│ ☐ Ambiente sob A/C       │
│                          │
│ Observação livre:        │
│ ┌──────────────────────┐ │
│ │                      │ │
│ │                      │ │
│ └──────────────────────┘ │
│                          │
├──────────────────────────┤
│ [Voltar]    [Continuar →]│
└──────────────────────────┘
```

##### Passo 13 — Pré-visualização do certificado
```
┌──────────────────────────┐
│ ← Passo 13/15          ⓘ │
├──────────────────────────┤
│ Prévia do certificado    │
│                          │
│ ┌──────────────────────┐ │
│ │ [LOGO] Lab. Acme     │ │
│ │ ⓒ Cgcre CAL-1234     │ │
│ │ ─────────────────    │ │
│ │ Cert: CAL-1234/      │ │
│ │       2026/00142     │ │
│ │                      │ │
│ │ Cliente: Lab. Acme   │ │
│ │ Item: Toledo Prix 3  │ │
│ │ Série: 9087654       │ │
│ │                      │ │
│ │ Resultados (...)     │ │
│ │ U = ±0,15 g (k=2)    │ │
│ │                      │ │
│ │ [QR código]          │ │
│ └──────────────────────┘ │
│                          │
│ [Ver PDF inteiro →]      │
│                          │
│ Algo errado?             │
│ [Voltar ao passo X]      │
├──────────────────────────┤
│ [Voltar]   [Tudo certo ✓]│
└──────────────────────────┘
```

##### Passo 14 — Assinatura do executor
```
┌──────────────────────────┐
│ ← Passo 14/15          ⓘ │
├──────────────────────────┤
│ Assinatura do executor   │
│                          │
│ Eu, João Silva, declaro  │
│ que executei esta        │
│ calibração conforme      │
│ procedimento PT-005 r.04 │
│ e os dados registrados   │
│ refletem a realidade.    │
│                          │
│ 🔒 Confirme sua senha    │
│ [_____________________]  │
│                          │
│ ou [👆 Biometria + senha]│
│                          │
│ ⓘ Após assinar, a OS vai │
│   para revisão técnica.  │
│                          │
├──────────────────────────┤
│ [Voltar]    [Assinar ✓]  │
└──────────────────────────┘
```

##### Passo 15 — Conclusão e sincronização
```
┌──────────────────────────┐
│ ✓ Execução concluída     │
├──────────────────────────┤
│                          │
│      ✓                   │
│   Tudo certo!            │
│                          │
│ OS-2026-00142            │
│ enviada para revisão.    │
│                          │
│ Status de sincronização: │
│ ⏳ Sincronizando... 80%  │
│                          │
│ Próximos passos:         │
│ → Revisor: Maria S.      │
│ → Signatário: Carlos L.  │
│                          │
│ Você será notificado     │
│ quando o certificado     │
│ for emitido.             │
│                          │
│ [Iniciar nova OS]        │
│ [Voltar para Home]       │
│                          │
└──────────────────────────┘
```

#### 17.3.6 Cadastro rápido de equipamento em campo

```
┌──────────────────────────┐
│ ← Novo equipamento       │
├──────────────────────────┤
│ Cliente: Lab. Acme       │
│ (vínculo obrigatório)    │
│                          │
│ 📷 Foto da placa         │
│ [   Tocar para tirar  ]  │
│                          │
│ Identificação automática │
│ via OCR (em beta):       │
│ Fabricante: Toledo ✓     │
│ Modelo: Prix 3 ✓         │
│ Série: 9087654 ✓         │
│ [Editar campos]          │
│                          │
│ TAG do cliente:          │
│ [BAL-007______________]  │
│                          │
│ Capacidade Max:          │
│ [3] kg                   │
│                          │
│ Divisão d:               │
│ [0.5] g                  │
│                          │
│ Classe: ▼ III            │
│                          │
│ [Salvar e voltar à OS]   │
└──────────────────────────┘
```

#### 17.3.7 Padrões disponíveis (consulta)

```
┌──────────────────────────┐
│ ← Padrões             🔍 │
├──────────────────────────┤
│ [Todos] [Pesos] [Ambient]│
├──────────────────────────┤
│                          │
│ ✓ PESO-001               │
│   1 kg · classe F1       │
│   RBC CAL-1234           │
│   Vence: 12/08/2026      │
│                          │
│ ✓ PESO-002               │
│   2 kg · classe F1       │
│   RBC CAL-1234           │
│   Vence: 12/08/2026      │
│                          │
│ ⚠ PESO-005               │
│   5 kg · classe M1       │
│   Vence em 5 dias        │
│   [Solicitar renovação]  │
│                          │
│ 🚫 PESO-010              │
│   10 kg · classe M1      │
│   VENCIDO em 02/04/2026  │
│   Bloqueado para uso     │
│                          │
└──────────────────────────┘
```

#### 17.3.8 Sincronização e fila pendente

```
┌──────────────────────────┐
│ ← Sincronização          │
├──────────────────────────┤
│                          │
│ Status: ⏳ Em progresso  │
│ Última sync: há 2 min    │
│                          │
│ ┌──────────────────────┐ │
│ │ FILA PENDENTE        │ │
│ │                      │ │
│ │ • OS-00142 (env. 80%)│ │
│ │ • OS-00143 (aguard.) │ │
│ │ • 4 fotos (aguard.)  │ │
│ │                      │ │
│ │ Total: 12,4 MB       │ │
│ └──────────────────────┘ │
│                          │
│ ⓘ Aguardando rede.       │
│   Continue trabalhando.  │
│                          │
│ [Forçar sincronização]   │
│ [Ver conflitos (0)]      │
│                          │
└──────────────────────────┘
```

#### 17.3.9 Configurações / Perfil do usuário

```
┌──────────────────────────┐
│ ← Configurações          │
├──────────────────────────┤
│                          │
│ João Silva               │
│ joao@lab-acme.com.br     │
│ Lab. Acme · Técnico      │
│                          │
│ ▷ Trocar organização     │
│ ▷ Minhas competências    │
│ ▷ Senha e biometria      │
│ ▷ MFA                    │
│ ▷ Dispositivos vinculados│
│ ▷ Sincronização          │
│ ▷ Cache local (180 MB)   │
│ ▷ Idioma · PT-BR         │
│ ▷ Modo escuro · ●        │
│ ▷ Sobre · Termos · LGPD  │
│                          │
│ [Sair]                   │
│                          │
└──────────────────────────┘
```

#### 17.3.10 Modal de bloqueio padrão (reusado em todas as regras de §9)

```
┌──────────────────────────┐
│                          │
│        🚫                │
│                          │
│  AÇÃO BLOQUEADA          │
│                          │
│  [Mensagem específica    │
│   da regra violada,      │
│   ex.: "Padrão vencido"] │
│                          │
│  Por quê:                │
│  [Explicação breve com   │
│   link para a norma      │
│   aplicável]             │
│                          │
│  O que fazer:            │
│  [Sugestão acionável]    │
│                          │
│  [Entendi, voltar]       │
│  [Falar com qualidade]   │
│                          │
└──────────────────────────┘
```

### 17.4 App Web back-office — wireframes textuais

> **Princípios de design web do produto:**
> - **Densidade de informação alta** — usuários power (gestor, signatário, revisor) operam o dia inteiro.
> - **Atalhos de teclado** — toda ação frequente tem hotkey (revisão, aprovação, busca global).
> - **Filtros persistentes** — listas lembram filtros aplicados por usuário.
> - **Acessibilidade WCAG 2.1 AA** — navegação por teclado, contraste mínimo, ARIA labels.
> - **Indicador de organização ativa** sempre visível (multi-tenant — usuário pode ter N orgs).

#### 17.4.1 Layout-base

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] Lab. Acme ▾    🔍 Buscar (Ctrl+K)         🔔 12  ⚙   👤 João Silva ▾       │
├──────────────┬─────────────────────────────────────────────────────────────────────┤
│              │                                                                     │
│ 📊 Dashboard │  ÁREA PRINCIPAL                                                     │
│ 📋 OS        │                                                                     │
│ 👥 Clientes  │                                                                     │
│ ⚖ Equipam.   │                                                                     │
│ 🔢 Padrões   │                                                                     │
│ 📐 Procedim. │                                                                     │
│ ✍ Assinatura │                                                                     │
│ ✓ Revisão    │                                                                     │
│              │                                                                     │
│ ─── Qualid.  │                                                                     │
│ ⚠ NC         │                                                                     │
│ 🗣 Reclamaç. │                                                                     │
│ 📝 Auditoria │                                                                     │
│ 📈 Indicad.  │                                                                     │
│              │                                                                     │
│ ─── Config   │                                                                     │
│ 🏢 Organiz.  │                                                                     │
│ 👥 Usuários  │                                                                     │
│ 🔐 Segurança │                                                                     │
│ 📜 Trilha    │                                                                     │
│              │                                                                     │
└──────────────┴─────────────────────────────────────────────────────────────────────┘
```

#### 17.4.2 Dashboard gerencial

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Dashboard · Lab. Acme · Hoje, 19/04/2026                                            │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ OS HOJE  │  │ EM REVI. │  │ A ASSIN. │  │ EMITIDOS │  │ NC ABERT.│             │
│  │   12     │  │    3     │  │    5     │  │   142    │  │    2     │             │
│  │ +20% sem │  │ −1 ontem │  │ ⚠ 2 atras│  │ mês      │  │ ⚠ ação   │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
│                                                                                    │
│  ┌────────────────────────────────┐ ┌────────────────────────────────┐             │
│  │ EMISSÕES POR SEMANA            │ │ TEMPO MÉDIO POR OS             │             │
│  │ [gráfico de barras 12 sem]     │ │ [linha 12 sem · meta 35min]    │             │
│  └────────────────────────────────┘ └────────────────────────────────┘             │
│                                                                                    │
│  ┌────────────────────────────────┐ ┌────────────────────────────────┐             │
│  │ ⚠ ATENÇÃO                      │ │ AGENDA DA SEMANA               │             │
│  │ • PESO-005 vence em 5 dias     │ │ Seg · 4 OS · João              │             │
│  │ • 2 competências expiram (30d) │ │ Ter · 3 OS · Maria             │             │
│  │ • Acreditação Cgcre vence 2027 │ │ Qua · 6 OS · João, Carlos      │             │
│  │ • 1 conflito de sync pendente  │ │ ...                            │             │
│  └────────────────────────────────┘ └────────────────────────────────┘             │
│                                                                                    │
│  CONFORMIDADE                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ % cert. sem reemissão (mês): 99,3% ✓  (meta 98%)                │               │
│  │ % padrões válidos: 100% ✓                                        │               │
│  │ Última auditoria interna: 12/03/2026 · 0 NC                      │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.3 Lista de Ordens de Serviço

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ OS · 247 itens                                              [+ Nova OS]            │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Status: [Todas ▾]  Cliente: [Todos ▾]  Técnico: [Todos ▾]  Período: [Mês ▾]        │
│ Procedimento: [Todos ▾]  Equipamento: [Todos ▾]  [Limpar filtros]                  │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Nº         │ Cliente         │ Equipamento     │ Status     │ Técnico  │ Atualiz.  │
│────────────│─────────────────│─────────────────│────────────│──────────│───────────│
│ OS-00142   │ Lab. Acme       │ Toledo Prix 3   │ ✍ Assinar  │ João S.  │ 14:22     │
│ OS-00141   │ Padaria Pão     │ Filizola 15kg   │ ✓ Revisar  │ Maria S. │ 13:50     │
│ OS-00140   │ Indústria XYZ   │ Marte 50kg      │ 🔄 Em exec.│ Carlos L.│ 11:30     │
│ OS-00139   │ Lab. Acme       │ Toledo XS 0,5kg │ ✓ Emitido  │ João S.  │ ontem     │
│ OS-00138   │ ...             │ ...             │ ✓ Emitido  │ ...      │ ontem     │
│ ...                                                                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ◀ 1 2 3 ... 25 ▶                                            Mostrando 1-20 de 247 │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.4 Detalhe / Revisão técnica de OS

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ ← OS-2026-00142 · Lab. Acme · Toledo Prix 3                  [Imprimir prévia]     │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Status: ✓ Aguardando revisão · Atribuído a: Maria S. · Executado por: João S.      │
│                                                                                    │
│ ┌────────────────────────┐  ┌──────────────────────────────────────────────────┐   │
│ │ LINHA DO TEMPO         │  │ DADOS DA EXECUÇÃO                                │   │
│ │ ─ Criada    12/04 09:01│  │ Procedimento: PT-005 rev.04                      │   │
│ │ ─ Aceita    12/04 09:15│  │ Padrões: PESO-001, PESO-002, TH-003 (todos OK)   │   │
│ │ ─ Em exec.  19/04 11:00│  │ Ambiente: 22,4 °C / 55% / 1013 hPa ✓             │   │
│ │ ─ Executada 19/04 14:22│  │ Pontos da curva: 5 (10%/25%/50%/75%/100%)        │   │
│ │ ▶ Revisão   ─          │  │ Repetibilidade: σ = 0,058 g                      │   │
│ │ ─ Assinat.  ─          │  │ Excentricidade Δmax: 0,1 g                       │   │
│ │ ─ Emitido   ─          │  │ U expandida (k=2): ±0,15 g                       │   │
│ └────────────────────────┘  │ Conformidade: APROVADO (banda guarda 50%)        │   │
│                             │ [Ver balanço de incerteza →]                     │   │
│                             │ [Ver evidências (12 fotos) →]                    │   │
│                             │ [Ver prévia do certificado →]                    │   │
│                             └──────────────────────────────────────────────────┘   │
│                                                                                    │
│ CHECKLIST DE REVISÃO                                                               │
│ ☑ Padrões válidos no momento da execução                                           │
│ ☑ Ambiente dentro da faixa do procedimento                                         │
│ ☑ Pontos da curva adequados ao uso pretendido                                      │
│ ☑ Cálculo de incerteza coerente                                                    │
│ ☐ Verificada coerência com histórico do equipamento                                │
│                                                                                    │
│ COMENTÁRIOS DE REVISÃO                                                             │
│ ┌────────────────────────────────────────────────────────────────────────────┐     │
│ │                                                                            │     │
│ └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                    │
│ [Devolver ao técnico]                                  [Aprovar revisão →]         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.5 Fila de assinatura

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Fila de assinatura · 5 pendentes                                                   │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Filtrar por tipo de instrumento: [Todos ▾]                                         │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Nº         │ Cliente      │ Equipamento     │ Aguardando há │ Pré-validações       │
│────────────│──────────────│─────────────────│───────────────│──────────────────────│
│ OS-00142   │ Lab. Acme    │ Toledo Prix 3   │ 18 min        │ ✓ ✓ ✓ ✓ Tudo OK     │
│ OS-00138   │ Padaria Pão  │ Filizola 15kg   │ 2h 12min      │ ✓ ✓ ✓ ✓ Tudo OK     │
│ OS-00135   │ Indústria XYZ│ Marte 50kg      │ 5h 40min ⚠    │ ⚠ U > CMC: revisar  │
│ ...                                                                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│ [Selecionar todos]   [Assinar selecionados em lote (com re-autenticação)]          │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.6 Tela de assinatura (modal de re-autenticação)

```
                  ┌────────────────────────────────────────┐
                  │ ASSINATURA DO CERTIFICADO              │
                  ├────────────────────────────────────────┤
                  │                                        │
                  │ OS-2026-00142                          │
                  │ Lab. Acme · Toledo Prix 3              │
                  │                                        │
                  │ [Prévia compacta do certificado]       │
                  │                                        │
                  │ Eu, Carlos Lima, Signatário Autorizado,│
                  │ confirmo que verifiquei o conteúdo e   │
                  │ autorizo a emissão deste certificado.  │
                  │                                        │
                  │ Hash do documento:                     │
                  │ a3f9...c12d                            │
                  │                                        │
                  │ 🔒 Confirme sua senha                  │
                  │ [_________________________]            │
                  │                                        │
                  │ Código TOTP (MFA)                      │
                  │ [______]                               │
                  │                                        │
                  │ [Cancelar]      [Assinar e emitir →]   │
                  └────────────────────────────────────────┘
```

#### 17.4.7 Lista de Clientes

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Clientes · 87 ativos                                          [+ Novo cliente]     │
├────────────────────────────────────────────────────────────────────────────────────┤
│ 🔍 Buscar por razão social, CNPJ, segmento                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Razão social         │ CNPJ            │ Equipam. │ Cert. mês │ Próx. venc. │ Stat.│
│──────────────────────│─────────────────│──────────│───────────│─────────────│──────│
│ Lab. Acme            │ 12.345.678/0001 │ 23       │ 15        │ 02/05/2026  │ ●    │
│ Padaria Pão Doce     │ 23.456.789/0001 │ 4        │ 2         │ 18/05/2026  │ ●    │
│ Indústria XYZ        │ 34.567.890/0001 │ 67       │ 8         │ 23/04/2026⚠ │ ●    │
│ ...                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.8 Detalhe do Cliente (abas)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ ← Lab. Acme · CNPJ 12.345.678/0001-XX                          [Editar] [Inativar] │
├────────────────────────────────────────────────────────────────────────────────────┤
│ [Dados] [Contatos] [Endereços] [Equipamentos (23)] [Certificados] [Anexos] [Hist.] │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  Razão social: Lab. Acme Análises Ltda.                                            │
│  Nome fantasia: Lab. Acme                                                          │
│  Inscrição estadual: 123.456.789.000                                               │
│  Segmento: Laboratório clínico                                                     │
│  Status: Ativo                                                                     │
│                                                                                    │
│  Responsável técnico: João das Neves (joao@lab-acme.com.br)                        │
│  Contrato vigente: até 31/12/2026 [Ver anexo]                                      │
│                                                                                    │
│  Condições especiais do local: Sala climatizada 21±2°C, restrição de acesso        │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.9 Lista global de Equipamentos

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Equipamentos · 312 ativos                                  [+ Novo equipamento]    │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Cliente: [Todos ▾]  Tipo: [Todos ▾]  Status: [Ativos ▾]  Vencimento: [Próx 30d ▾]  │
│ 🔍 Buscar por TAG, série, modelo                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Cód.    │ Cliente     │ TAG     │ Tipo·Modelo      │ Max·d·Cl │ Última│ Próx ⚠   │
│─────────│─────────────│─────────│──────────────────│──────────│───────│──────────│
│ EQ-0007 │ Lab. Acme   │ BAL-007 │ NAWI Toledo Prix3│ 3kg·0,5g·│18/04  │ 18/10/26 │
│         │             │         │                  │ III      │       │          │
│ EQ-0008 │ Indústria XY│ BL-X-22 │ NAWI Marte L50   │ 50kg·5g· │02/03  │ 02/05/26⚠│
│         │             │         │                  │ III      │       │          │
│ ...                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.10 Gestão de Padrões (com painel de vencimentos)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Padrões · 18 ativos · 2 vencendo em 30 dias                  [+ Novo padrão]       │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────────────┐     │
│ │ PAINEL DE VENCIMENTOS                                                      │     │
│ │ [gráfico de linha do tempo: hoje ──── 30d ──── 60d ──── 90d ──── 6m]      │     │
│ │   ▲ PESO-005 (5d)    ▲ TH-003 (45d)    ▲ PESO-010 (90d) ...               │     │
│ └────────────────────────────────────────────────────────────────────────────┘     │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Tipo: [Todos ▾]  Fonte: [Todas ▾]  Status: [Todos ▾]                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ID       │ Tipo     │ Valor·Cl │ Fonte    │ Cert.       │ Validade   │ Status     │
│──────────│──────────│──────────│──────────│─────────────│────────────│────────────│
│ PESO-001 │ Peso     │ 1kg · F1 │ RBC-1234 │ [PDF]       │ 12/08/2026 │ ✓ Válido   │
│ PESO-002 │ Peso     │ 2kg · F1 │ RBC-1234 │ [PDF]       │ 12/08/2026 │ ✓ Válido   │
│ PESO-005 │ Peso     │ 5kg · M1 │ RBC-1234 │ [PDF]       │ 24/04/2026 │ ⚠ 5 dias   │
│ PESO-010 │ Peso     │ 10kg· M1 │ RBC-1234 │ [PDF]       │ 02/04/2026 │ 🚫 Vencido │
│ TH-003   │ Termohigr│ —        │ RBC-9876 │ [PDF]       │ 30/06/2026 │ ✓ Válido   │
│ ...                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.11 Detalhe do Padrão

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ ← PESO-005 · Peso padrão 5 kg · classe M1                          [Editar][Hist.] │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ⚠ Este padrão vence em 5 dias. [Solicitar nova calibração]                         │
│                                                                                    │
│ Identificação: PESO-005                                                            │
│ Fabricante: Coelmatic · Modelo: M5K · Série: 9-22-115                              │
│ Valor nominal: 5,000 kg · Classe: M1 (Portaria 289/2021)                           │
│ Faixa de uso: cargas até 5 kg                                                      │
│ Incerteza declarada: ± 12 mg                                                       │
│ Fator de correção atual: +0,003 g                                                  │
│                                                                                    │
│ ─── HISTÓRICO DE CALIBRAÇÕES ───────────────────────────────────────────────       │
│                                                                                    │
│ Data       │ Lab.        │ Cert.       │ Fonte    │ U medida │ Validade           │
│────────────│─────────────│─────────────│──────────│──────────│────────────────────│
│ 24/04/2025 │ Lab Cal-1234│ 1234/25/088 │ RBC      │ ±12 mg   │ 24/04/2026 ⚠       │
│ 14/04/2024 │ Lab Cal-1234│ 1234/24/072 │ RBC      │ ±13 mg   │ 14/04/2025         │
│ 02/03/2023 │ Lab Cal-1234│ 1234/23/053 │ RBC      │ ±13 mg   │ 02/03/2024         │
│                                                                                    │
│ [+ Anexar nova calibração]                                                         │
│                                                                                    │
│ ─── USO RECENTE EM OS ───────────────────────────────────────────────              │
│ OS-00142 (19/04) · OS-00138 (18/04) · OS-00135 (17/04) · ...                       │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.12 Procedimentos (lista versionada)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Procedimentos · 14 vigentes                                  [+ Novo procedimento] │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Código  │ Título                          │ Tipo       │ Rev. │ Vigência    │ Stat.│
│─────────│─────────────────────────────────│────────────│──────│─────────────│──────│
│ PT-005  │ Calibração IPNA classe III campo│ NAWI III   │ 04   │ desde 03/24 │ ●    │
│ PT-006  │ Calibração IPNA bancada         │ NAWI       │ 02   │ desde 11/23 │ ●    │
│ PG-001  │ Controle de documentos          │ Gestão     │ 01   │ desde 01/24 │ ●    │
│ ...                                                                                │
│ PT-005  │ (rev. 03 obsoleta)              │ —          │ 03   │ até 03/24   │ ⊗    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.13 Módulo Qualidade — NC

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Não conformidades · 2 abertas · 7 fechadas (90d)                  [+ Abrir NC]     │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Status: [Abertas ▾]  Origem: [Todas ▾]  Severidade: [Todas ▾]                       │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Nº     │ Resumo                              │ Origem   │ Sever. │ Resp.    │ Idade│
│────────│─────────────────────────────────────│──────────│────────│──────────│──────│
│ NC-014 │ Padrão usado próximo ao venciment.. │ Auditoria│ Média  │ Maria S. │ 12d  │
│ NC-015 │ Cliente reportou divergência valor..│ Reclam.  │ Alta⚠  │ João S.  │ 3d   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.14 Trilha de auditoria

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Trilha de auditoria · imutável (append-only)                       [Exportar CSV]  │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Período: [Últimos 7 dias ▾]  Usuário: [Todos ▾]  Entidade: [Todas ▾]                │
│ Ação: [Todas ▾]  🔍 Buscar por ID                                                   │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Quando             │ Quem      │ Ação                  │ Entidade           │ Hash │
│────────────────────│───────────│───────────────────────│────────────────────│──────│
│ 19/04 14:22:45 UTC │ João S.   │ assinatura.executor   │ OS-2026-00142      │ a3f9.│
│ 19/04 14:22:42 UTC │ João S.   │ leitura.capturada     │ ...test_id 1245    │ b21c.│
│ 19/04 14:18:11 UTC │ João S.   │ ambiente.confirmado   │ OS-2026-00142      │ c876.│
│ 19/04 14:15:30 UTC │ Sistema   │ padrao.validado       │ PESO-001           │ d445.│
│ ...                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.15 Configurações da Organização

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Configurações · Lab. Acme                                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│ [Identidade] [Branding] [Perfil regulatório] [Numeração] [Plano] [Integrações]      │
│ [Segurança] [SSO/SAML] [Notificações] [LGPD/DPO]                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ PERFIL REGULATÓRIO ATUAL: TIPO A — Acreditado RBC                                  │
│ Cgcre Nº CAL-1234 · válido até 30/09/2027                                          │
│ Escopo: 3 itens cadastrados · CMC: 5 itens                                         │
│                                                                                    │
│ ⚠ Mudar perfil regulatório exige aprovação de 2 administradores e fica registrado  │
│   na trilha de auditoria. Certificados emitidos antes da mudança permanecem com o  │
│   perfil anterior.                                                                 │
│                                                                                    │
│ [Solicitar mudança de perfil] [Renovar acreditação] [Atualizar escopo]             │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### 17.4.16 Gestão de Usuários e Competências

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Usuários · 8 ativos · 1 convidado pendente                       [+ Convidar]      │
├────────────────────────────────────────────────────────────────────────────────────┤
│ [Lista] [Equipes] [Matriz de competências]                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│ Nome           │ Papel              │ Competências válidas       │ Último login   │
│────────────────│────────────────────│────────────────────────────│────────────────│
│ João Silva     │ Técnico            │ NAWI I, II, III · até 2027 │ hoje 14:22     │
│ Maria Souza    │ Revisor + Signatár.│ NAWI III · até 2026-09 ⚠   │ hoje 09:10     │
│ Carlos Lima    │ Signatário         │ NAWI I-IV · até 2027       │ ontem          │
│ Ana Costa      │ Gestor Qualidade   │ —                          │ hoje 08:00     │
│ ...                                                                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│ MATRIZ DE COMPETÊNCIAS                                                             │
│              │ NAWI I │ NAWI II │ NAWI III │ NAWI IV │ Termômetro │ Manômetro     │
│ João Silva   │   ✓    │   ✓     │    ✓     │   —     │     —      │     —         │
│ Maria Souza  │   —    │   —     │    ⚠ exp │   —     │     ✓      │     —         │
│ Carlos Lima  │   ✓    │   ✓     │    ✓     │   ✓     │     ✓      │     ✓         │
│ ...                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 17.5 Portal do Cliente Final — wireframes textuais

> **Princípios:**
> - **Foco no consumo do certificado** — não há criação/edição.
> - **Verificação pública por QR sem login** — qualquer terceiro (auditor, fiscal) confere autenticidade.
> - **Notificação proativa** — vencimento programático informa o cliente sobre seus equipamentos.

#### 17.5.1 Login do Cliente

```
┌──────────────────────────────────────────────────────┐
│              [LOGO Lab. Acme]                        │
│                                                      │
│  Portal de Certificados                              │
│                                                      │
│  E-mail: [_______________________]                   │
│  Senha:  [_______________________]                   │
│                                                      │
│  [        Entrar         →]                          │
│                                                      │
│  [G] Continuar com Google                            │
│  [⊞] Continuar com Microsoft                         │
│                                                      │
│  Esqueci a senha · Primeiro acesso                   │
│                                                      │
│  ──────────────────────────────                      │
│                                                      │
│  Apenas verificar autenticidade?                     │
│  [Verificar certificado por QR/código →]             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### 17.5.2 Dashboard do Cliente

```
┌────────────────────────────────────────────────────────────────────────┐
│ [LOGO Lab. Acme]    Olá, João das Neves (Lab. Acme)    🔔  ⚙  Sair    │
├────────────────────────────────────────────────────────────────────────┤
│ Meus equipamentos · Certificados · Vencimentos · Documentos · Suporte  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │ EQUIPAMENTOS         │  │ CERTIFICADOS         │                    │
│  │       23             │  │       142            │                    │
│  │ ativos               │  │ emitidos             │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
│                                                                        │
│  ⚠ ATENÇÃO                                                             │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │ 3 equipamentos com calibração vencendo em 30 dias          │        │
│  │ • BAL-007 Toledo Prix 3 — vence 18/05/2026                 │        │
│  │ • BAL-012 Filizola 15 kg — vence 24/05/2026                │        │
│  │ • BAL-015 Marte 50 kg — vence 28/05/2026                   │        │
│  │ [Solicitar nova calibração]                                │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                        │
│  CERTIFICADOS RECENTES                                                 │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │ CAL-1234/2026/00142 · Toledo Prix 3 · 19/04 · APROVADO     │        │
│  │                                              [Baixar PDF]  │        │
│  │ CAL-1234/2026/00141 · Filizola 15 kg · 18/04 · APROVADO    │        │
│  │                                              [Baixar PDF]  │        │
│  │ CAL-1234/2026/00140 · Marte 50 kg · 17/04 · APROVADO       │        │
│  │                                              [Baixar PDF]  │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.5.3 Lista de Equipamentos do Cliente

```
┌────────────────────────────────────────────────────────────────────────┐
│ ← Meus equipamentos · 23 ativos                                        │
├────────────────────────────────────────────────────────────────────────┤
│ 🔍 Buscar por TAG ou modelo                                             │
├────────────────────────────────────────────────────────────────────────┤
│ TAG     │ Equipamento          │ Local        │ Última cal. │ Próx. ⚠  │
│─────────│──────────────────────│──────────────│─────────────│──────────│
│ BAL-007 │ Toledo Prix 3        │ Sala 12      │ 18/04/2026  │ 18/10/26 │
│ BAL-008 │ Filizola 15 kg       │ Almoxarifado │ 12/03/2026  │ 12/09/26 │
│ BAL-012 │ Filizola 15 kg       │ Setor C      │ 24/02/2026  │ 24/05/26 │
│ ...                                                                    │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.5.4 Detalhe do Equipamento (visão do cliente)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ← BAL-007 · Toledo Prix 3                                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Fabricante: Toledo · Modelo: Prix 3 · Série: 9087654                   │
│ Capacidade Max: 3 kg · Divisão: 0,5 g · Classe: III                    │
│ Local: Sala 12 — São Paulo                                             │
│                                                                        │
│ HISTÓRICO DE CERTIFICADOS                                              │
│                                                                        │
│ Data       │ Certificado            │ Resultado │ U (k=2) │ Ação       │
│────────────│────────────────────────│───────────│─────────│────────────│
│ 19/04/2026 │ CAL-1234/2026/00142    │ APROVADO  │ ±0,15 g │ [PDF][QR]  │
│ 18/10/2025 │ CAL-1234/2025/00321    │ APROVADO  │ ±0,15 g │ [PDF][QR]  │
│ 22/04/2025 │ CAL-1234/2025/00102    │ APROVADO  │ ±0,16 g │ [PDF][QR]  │
│ ...                                                                    │
│                                                                        │
│ [+ Solicitar nova calibração]                                          │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.5.5 Visualizador de certificado (logado)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ← CAL-1234/2026/00142 · Toledo Prix 3                                  │
├────────────────────────────────────────────────────────────────────────┤
│ Status: ✓ Válido · Hash: a3f9c12d... · Assinatura verificada           │
│                                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │                                                                  │   │
│ │            [PRÉVIA INTEGRAL DO PDF — visualizador]               │   │
│ │                                                                  │   │
│ │                                                                  │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│ [Baixar PDF]   [Compartilhar link público]   [Imprimir]                │
│                                                                        │
│ ─── COMO VERIFICAR ESTE CERTIFICADO ─────────────────────────          │
│ • Aponte a câmera para o QR code da última página                      │
│ • Ou acesse: verifica.afere.com.br/c/a3f9c12d                      │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.5.6 Página pública de verificação por QR (sem login)

> **Princípio de minimização de dados.** A página pública confirma apenas a **autenticidade** do certificado e expõe metadados mínimos. Dados do cliente final (razão social, item calibrado, série), resultado técnico, signatário e PDF completo **não são públicos** — ficam disponíveis somente sob autenticação do cliente do laboratório no Portal (§17.5) ou para o próprio emissor no back-office (§17.4).

```
┌────────────────────────────────────────────────────────────────────────┐
│ [LOGO Aferê]                Verificação de Certificado              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Código do certificado:                                                │
│  [_____________________________]   [Verificar]                         │
│                                                                        │
│  ───────────────────────────────────────────────────                   │
│                                                                        │
│           ✓ CERTIFICADO AUTÊNTICO                                      │
│                                                                        │
│  Número:        CAL-1234/2026/00142                                    │
│  Emissor:       Lab. Acme Análises Ltda.                               │
│  Acreditação:   Cgcre nº CAL-1234 (válida)                             │
│  Data emissão:  19/04/2026                                             │
│  Status:        Vigente                                                │
│                                                                        │
│  [Acessar detalhes completos] → exige autenticação do cliente do lab   │
│                                                                        │
│  ───────────────────────────────────────────────────                   │
│  Quer também emitir certificados como o Lab. Acme?                     │
│  [Conheça o Aferê →]                                               │
└────────────────────────────────────────────────────────────────────────┘
```

> **Controles técnicos obrigatórios:**
> - **Rate limit por IP e por código** — anti-enumeração de hashes/códigos.
> - **URL do PDF original é assinada** (signed URL) com TTL curto; exige token de acesso emitido pelo lab para o cliente do certificado.
> - **Campos NÃO expostos publicamente:** razão social do cliente final, item, número de série, data de calibração, resultado, hash técnico completo, nome do signatário.
> - **Threat model documentado** antes do GA: anti-enumeração, CORS restrito, proteção contra side-channel por status HTTP, logs de tentativas de verificação.

> **Variante: certificado revogado/reemitido**
> ```
>           ⚠ ATENÇÃO
>           Este certificado foi REEMITIDO em 22/04/2026.
>           Versão atual: CAL-1234/2026/00142-R1
>           [Ver versão atual]
> ```

> **Variante: hash não encontrado**
> ```
>           🚫 NÃO LOCALIZADO
>           Nenhum certificado corresponde a este código.
>           Confira o QR ou contate o emissor.
> ```

### 17.6 Componentes reutilizáveis (web)

> **Princípio:** todo padrão visual abaixo é centralizado no design system `afere-ds`. Times não criam variantes locais.

#### 17.6.1 Modal de bloqueio (versão web do §17.3.10)

```
                ┌──────────────────────────────────────────────┐
                │ 🚫  AÇÃO BLOQUEADA                       [×] │
                ├──────────────────────────────────────────────┤
                │                                              │
                │  Padrão PESO-005 vence em 5 dias.            │
                │  A política da organização exige ≥ 30 dias   │
                │  de margem para iniciar nova OS.             │
                │                                              │
                │  POR QUÊ                                     │
                │  ISO/IEC 17025 cláusula 6.4 — equipamentos   │
                │  de medição devem ter rastreabilidade        │
                │  vigente. [Ver documentação ↗]               │
                │                                              │
                │  O QUE FAZER                                 │
                │  • Solicitar nova calibração do padrão       │
                │  • Substituir por outro padrão equivalente   │
                │  • Ajustar política da organização (Admin)   │
                │                                              │
                │  [Falar com Qualidade]   [Entendi, voltar]   │
                └──────────────────────────────────────────────┘
```

#### 17.6.2 Toast de notificação (4 variantes)

```
   ┌─────────────────────────────────────┐
   │ ✓ Certificado emitido com sucesso  │  ← sucesso (verde, 4s auto-dismiss)
   │   CAL-1234/2026/00142   [Ver][×]   │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │ ⚠ Padrão TH-003 vence em 7 dias    │  ← alerta (âmbar, 6s)
   │                          [Ver][×]   │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │ 🚫 Falha ao sincronizar — sem rede │  ← erro (vermelho, persiste)
   │   Tente novamente em alguns minutos │
   │                       [Tentar][×]   │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │ ⓘ Nova versão do procedimento PT-005│ ← info (azul, 5s)
   │                          [Ver][×]   │
   └─────────────────────────────────────┘
```

#### 17.6.3 Drawer de detalhes (slide-in lateral à direita)

```
┌──────────────────────────────────────┬──────────────────────────────┐
│                                      │ ← Detalhes               [×] │
│  Lista atrás (semi-bloqueada,        │                              │
│  scrim 40%)                          │ OS-2026-00142                │
│                                      │ ─────────────────────        │
│                                      │ Cliente: Lab. Acme           │
│                                      │ Equipamento: Toledo Prix 3   │
│                                      │ ...                          │
│                                      │                              │
│                                      │ [Ações]                      │
│                                      │ ─────────────────            │
│                                      │ [Abrir tela completa →]      │
└──────────────────────────────────────┴──────────────────────────────┘
```

#### 17.6.4 Estrutura padrão de tabela filtrável

```
┌────────────────────────────────────────────────────────────────┐
│ [Título]  N itens    [Filtros ativos: A·B·C  Limpar]  [+ Novo] │
├────────────────────────────────────────────────────────────────┤
│ 🔍 Busca         Coluna A: [▾]  Coluna B: [▾]  Período: [▾]    │
├─────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Sel.[☐]│ Coluna 1▾│ Coluna 2 │ Coluna 3▾│ Coluna 4 │ Ações    │
├─────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│  [☐]    │   ...    │   ...    │   ...    │   ...    │ ⋮        │
│  [☐]    │   ...    │   ...    │   ...    │   ...    │ ⋮        │
├─────────┴──────────┴──────────┴──────────┴──────────┴──────────┤
│ [Ações em lote ▾]    Página 1 de 13    ◀ 1 2 3 ... 13 ▶  20/p │
└────────────────────────────────────────────────────────────────┘
```

#### 17.6.5 Empty state (sem dados)

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                          📋                                    │
│                                                                │
│              Nenhuma OS criada ainda                           │
│                                                                │
│   Comece registrando uma nova ordem de serviço.                │
│   Ela vai guiar o técnico pelo fluxo de calibração.            │
│                                                                │
│              [+ Criar primeira OS]                             │
│                                                                │
│              [Ver tutorial ↗]                                  │
└────────────────────────────────────────────────────────────────┘
```

#### 17.6.6 Confirm dialog (ações destrutivas / sensíveis)

```
        ┌──────────────────────────────────────────────┐
        │ Tem certeza?                                 │
        ├──────────────────────────────────────────────┤
        │                                              │
        │  Você está prestes a INATIVAR o cliente      │
        │  "Lab. Acme". Os 23 equipamentos vinculados  │
        │  ficarão indisponíveis para nova OS, mas o   │
        │  histórico permanece consultável.            │
        │                                              │
        │  Digite o nome do cliente para confirmar:    │
        │  [_________________________________]         │
        │                                              │
        │  [Cancelar]            [Inativar cliente]    │
        └──────────────────────────────────────────────┘
```

#### 17.6.7 Loading / skeleton

```
┌────────────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░         │
├────────────────────────────────────────────────────────────────┤
│ ░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░         │
│ ░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░         │
│ ░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░░  ░░░░░░░░░         │
└────────────────────────────────────────────────────────────────┘
```

### 17.7 E-mails transacionais

> **Princípios:**
> - Mesmo template-base com cabeçalho da organização (logo + cor) + rodapé com endereço, DPO, link de descadastro (apenas para mensagens não transacionais).
> - **CTA único** por e-mail.
> - Versão **texto puro** sempre presente (acessibilidade + entregabilidade).
> - Idioma: PT-BR (Fase 2: EN).
> - Assunto curto, sem emoji excessivo, sem palavras de spam.

#### 17.7.1 Verificação de e-mail (signup)

```
Assunto: Confirme seu e-mail no Aferê
─────────────────────────────────────────────────────────────

[LOGO Aferê]

Olá!

Você (ou alguém) criou uma conta no Aferê com este e-mail.
Para concluir, confirme seu endereço:

      [ Confirmar e-mail ]   ← botão

Ou copie este link:
https://app.afere.com.br/verify?token=...

O link expira em 30 minutos.

Se não foi você, ignore este e-mail — nenhuma conta será criada.

—
Aferê · CNPJ XX.XXX.XXX/0001-XX
DPO: dpo@afere.com.br
```

#### 17.7.2 Convite de usuário (organização)

```
Assunto: Maria, você foi convidada para o Aferê do Lab. Acme
─────────────────────────────────────────────────────────────

[LOGO Lab. Acme]

Olá, Maria,

Carlos Lima (Administrador do Lab. Acme) convidou você para
participar do Aferê como **Signatária Autorizada**.

      [ Aceitar convite ]

O convite expira em 72 horas. Você poderá entrar com seu Google,
Microsoft ou criar uma senha.

Sobre o Aferê: plataforma metrológica para emissão de
certificados de calibração conforme ISO/IEC 17025.

—
Lab. Acme · contato@lab-acme.com.br
```

#### 17.7.3 Reset de senha

```
Assunto: Redefinir sua senha — Aferê
─────────────────────────────────────────────────────────────

Recebemos um pedido para redefinir sua senha.

      [ Redefinir senha ]

Link expira em 1 hora. Se você não solicitou, ignore.
Sua senha continua válida até que seja efetivamente alterada.
```

#### 17.7.4 Certificado emitido (cliente)

```
Assunto: Certificado CAL-1234/2026/00142 disponível
─────────────────────────────────────────────────────────────

[LOGO Lab. Acme]

Olá, João,

O certificado de calibração do equipamento BAL-007 (Toledo Prix 3)
está disponível para download.

  Número: CAL-1234/2026/00142
  Item: Toledo Prix 3 · Série 9087654
  Data: 19/04/2026
  Resultado: APROVADO
  Acreditação: Cgcre nº CAL-1234

      [ Baixar certificado (PDF) ]

Verificação pública:
https://verifica.afere.com.br/c/a3f9c12d

Histórico completo no Portal do Cliente:
https://portal.lab-acme.com.br/equipamentos/BAL-007

—
Lab. Acme · contato@lab-acme.com.br
```

#### 17.7.5 Alerta de vencimento (cliente — 30/15/7 dias)

```
Assunto: Calibração de BAL-007 vence em 30 dias
─────────────────────────────────────────────────────────────

[LOGO Lab. Acme]

Olá, João,

A calibração do equipamento abaixo se aproxima do vencimento
programado pela sua política interna:

  • BAL-007 · Toledo Prix 3 · Sala 12
    Vencimento programado: 18/05/2026 (em 30 dias)

      [ Solicitar nova calibração ]

Lembramos que o certificado de calibração não tem validade
automática — a periodicidade é definida por sua organização.

—
Lab. Acme · contato@lab-acme.com.br
```

#### 17.7.6 Alerta interno (gestor — padrão vencendo)

```
Assunto: ⚠ Padrão PESO-005 vence em 7 dias
─────────────────────────────────────────────────────────────

Atenção, Ana,

O padrão abaixo está com calibração vencendo:

  • PESO-005 · 5 kg · classe M1
    Validade: 24/04/2026 (em 7 dias)
    Última calibração: 24/04/2025 · RBC CAL-1234

Sem renovação até essa data, o padrão será automaticamente
bloqueado para uso em novas OS.

      [ Ver padrão ]   [ Solicitar renovação ]

—
Aferê · Sistema de notificações
```

#### 17.7.7 NC aberta (responsável)

```
Assunto: NC-015 atribuída a você — severidade Alta
─────────────────────────────────────────────────────────────

João,

Uma não conformidade foi atribuída a você:

  NC-015 · Cliente reportou divergência de valor
  Origem: Reclamação · Severidade: Alta
  Prazo de resposta: 48h úteis

      [ Abrir NC ]

—
Aferê · Módulo Qualidade
```

#### 17.7.8 Reemissão de certificado (cliente)

```
Assunto: Certificado CAL-1234/2026/00142 foi reemitido
─────────────────────────────────────────────────────────────

[LOGO Lab. Acme]

Olá, João,

O certificado abaixo foi reemitido em 22/04/2026 com a versão R1:

  Versão atual: CAL-1234/2026/00142-R1
  Versão anterior: CAL-1234/2026/00142 (substituída)
  Motivo: Correção de dado cadastral do cliente
  Data da reemissão: 22/04/2026

      [ Baixar certificado atualizado ]

Por transparência e conformidade ISO 17025 (§7.8.8), a versão
anterior continua acessível no histórico, marcada como
"substituída".

—
Lab. Acme · contato@lab-acme.com.br
```

#### 17.7.9 Trial expirando

```
Assunto: Seu trial Pro acaba em 3 dias
─────────────────────────────────────────────────────────────

Olá, Carlos,

Seu trial Pro do Aferê termina em 3 dias (22/04/2026).
Continue com tudo o que está usando:

  ✓ 8 usuários ativos
  ✓ 47 OS executadas
  ✓ 12 certificados emitidos
  ✓ Módulo Qualidade ativo

      [ Escolher plano ]

Sem ação, a organização entra em modo somente leitura por 7 dias
e depois em congelamento (dados preservados por 90 dias).

—
Aferê · Sucesso do Cliente
```

### 17.8 Fluxo de reemissão controlada (web) — ISO 17025 §7.8.8

> **Princípio:** **a reemissão é evento controlado, auditável e versionado.** Nunca se "edita" um certificado emitido — gera-se uma nova versão (R1, R2, ...) que substitui formalmente a anterior, com motivo registrado, dupla aprovação e notificação automática ao cliente.

#### 17.8.1 Quem pode reemitir
- **Iniciar pedido:** Signatário Autorizado, Gestor da Qualidade.
- **Aprovar reemissão:** Signatário Autorizado **diferente** do que assinou a versão anterior **+** Gestor da Qualidade (dupla aprovação obrigatória).
- **Casos de exceção** (organização Tipo A com signatário único): aprovação por Diretor da Qualidade registrado no sistema.

#### 17.8.2 Motivos válidos para reemissão (lista controlada)
- `DADO_CADASTRAL` — correção de dado do cliente, equipamento, endereço (não afeta resultado).
- `ERRO_TIPOGRAFICO` — texto/observação errada (não afeta resultado).
- `RECALCULO_INCERTEZA` — atualização do balanço de incerteza (afeta resultado).
- `MUDANCA_REGRA_DECISAO` — mudança contratual da regra (afeta conformidade declarada).
- `RETIRADA_DECLARACAO_CONFORMIDADE` — cliente solicitou retirada.
- `ANEXO_FALTANTE` — adição de evidência exigida.
- `OUTRO` — texto livre obrigatório com justificativa técnica.

> **Bloqueio:** mudanças que afetam **leituras brutas, padrões usados ou condições ambientais reais** **NÃO** podem ser reemitidas — exigem **nova OS**, com nova execução em campo.

#### 17.8.3 Wizard de reemissão (5 passos)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ← Reemissão de CAL-1234/2026/00142                                     │
│ ▰▰▱▱▱  Passo 2 de 5                                                    │
├────────────────────────────────────────────────────────────────────────┤
│ ① Motivo  ② Alteração  ③ Comparativo  ④ Aprovações  ⑤ Emissão          │
└────────────────────────────────────────────────────────────────────────┘
```

##### Passo 1 — Motivo

```
┌────────────────────────────────────────────────────────────────────────┐
│ Motivo da reemissão                                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ○ DADO_CADASTRAL — correção de dado do cliente/equipamento            │
│  ○ ERRO_TIPOGRAFICO — texto/observação errada                          │
│  ○ RECALCULO_INCERTEZA — atualização do balanço (afeta resultado)      │
│  ○ MUDANCA_REGRA_DECISAO — mudança contratual                          │
│  ○ RETIRADA_DECLARACAO_CONFORMIDADE                                    │
│  ○ ANEXO_FALTANTE                                                      │
│  ○ OUTRO (justifique)                                                  │
│                                                                        │
│  Justificativa técnica (obrigatória)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ⓘ Mudanças em leituras brutas, padrões ou ambiente exigem NOVA OS,    │
│    não reemissão. [Saiba por quê ↗]                                    │
│                                                                        │
│                                          [Cancelar]   [Continuar →]    │
└────────────────────────────────────────────────────────────────────────┘
```

##### Passo 2 — Alteração proposta

```
┌────────────────────────────────────────────────────────────────────────┐
│ O que muda                                                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Edite apenas os campos permitidos pelo motivo selecionado.            │
│                                                                        │
│  Cliente · Razão social                                                │
│  De: "Lab. Acme Ltda."                                                 │
│  Para: [Lab. Acme Análises Ltda.____________________________]          │
│                                                                        │
│  Cliente · CNPJ                                                        │
│  De: "12.345.678/0001-XX"                                              │
│  Para: [12.345.678/0001-XX] (não alterado)                             │
│                                                                        │
│  Demais campos: somente leitura.                                       │
│                                                                        │
│                                       [← Voltar]   [Continuar →]       │
└────────────────────────────────────────────────────────────────────────┘
```

##### Passo 3 — Comparativo lado a lado

```
┌────────────────────────────────────────────────────────────────────────┐
│ Compare                                                                │
├──────────────────────────────────────┬─────────────────────────────────┤
│ VERSÃO ATUAL · ...00142              │ NOVA VERSÃO · ...00142-R1       │
├──────────────────────────────────────┼─────────────────────────────────┤
│ [Prévia do PDF original]             │ [Prévia do PDF reemitido]       │
│                                      │                                 │
│ Cliente: Lab. Acme Ltda.             │ Cliente: Lab. Acme Análises Ltda│
│ ...                                  │ ...                             │
│                                      │                                 │
└──────────────────────────────────────┴─────────────────────────────────┘
                                       [← Voltar]   [Solicitar aprov. →]
```

##### Passo 4 — Aprovações (dupla)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Aprovações                                                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Aprovador 1 (Signatário diferente do original)                        │
│  ⏳ Aguardando: Maria Souza (notificada em 22/04 09:01)                │
│                                                                        │
│  Aprovador 2 (Gestor da Qualidade)                                     │
│  ⏳ Aguardando: Ana Costa (notificada em 22/04 09:01)                  │
│                                                                        │
│  Você pode acompanhar aqui ou aguardar notificação por e-mail quando   │
│  ambas as aprovações forem concluídas.                                 │
│                                                                        │
│  [Cancelar pedido]                                                     │
└────────────────────────────────────────────────────────────────────────┘
```

##### Passo 5 — Emissão e versionamento

```
┌────────────────────────────────────────────────────────────────────────┐
│ ✓ Reemissão concluída                                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Versão atual: CAL-1234/2026/00142-R1                                  │
│  Versão anterior: CAL-1234/2026/00142 (marcada como substituída)       │
│  Hash novo: f2a8...991e                                                │
│  Hash anterior preservado: a3f9...c12d                                 │
│                                                                        │
│  Notificação automática enviada para:                                  │
│  • Cliente (e-mail principal): joao@lab-acme.com.br                    │
│  • Cliente (CC): qualidade@lab-acme.com.br                             │
│                                                                        │
│  Página pública de verificação atualiza imediatamente:                 │
│  https://verifica.afere.com.br/c/a3f9c12d → mostra aviso de        │
│  reemissão e link para R1                                              │
│                                                                        │
│  [Ver certificado R1]   [Voltar à OS]                                  │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.8.4 Visão de versões no detalhe do certificado

```
┌────────────────────────────────────────────────────────────────────────┐
│ Versões deste certificado                                              │
├────────────────────────────────────────────────────────────────────────┤
│ Versão │ Data        │ Motivo            │ Por           │ Status      │
│────────│─────────────│───────────────────│───────────────│─────────────│
│ R1     │ 22/04/2026  │ DADO_CADASTRAL    │ Maria + Ana   │ ✓ Vigente   │
│ —      │ 19/04/2026  │ original          │ Carlos        │ Substituída │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.8.5 Regras de imutabilidade
- O PDF anterior **nunca é apagado**; permanece acessível com marca-d'água "SUBSTITUÍDA POR R1".
- Hash original preservado e ainda válido na verificação pública (aponta para R1 atual).
- Trilha de auditoria registra: pedido, aprovações, hash antigo, hash novo, motivo, justificativa, notificação enviada.
- Reemissão de reemissão segue mesma regra (R2 substitui R1, R3 substitui R2, ...).

### 17.9 Módulo Qualidade completo

> Sustenta as cláusulas **4** (requisitos gerais), **7.9** (reclamações), **7.10** (trabalho não conforme), **8.5** (riscos e oportunidades), **8.7** (ações corretivas), **8.8** (auditoria interna) e **8.9** (análise crítica pela direção) da ISO/IEC 17025:2017.

#### 17.9.1 Hub do módulo Qualidade

```
┌────────────────────────────────────────────────────────────────────────┐
│ Qualidade · Lab. Acme                                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ NC ABERTAS   │  │ AÇÕES VENC.  │  │ AUDITORIA    │                  │
│  │     2        │  │     1 ⚠      │  │  PROG: 4     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ RECLAMAÇÕES  │  │ RISCOS ATIVOS│  │ ANÁLISE CRÍT.│                  │
│  │     1        │  │     7        │  │ próx: 30/06  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                        │
│  ÁREAS                                                                 │
│  ▷ Não conformidades (NC) e ações corretivas                           │
│  ▷ Reclamações (clientes externos)                                     │
│  ▷ Trabalho não conforme (interno)                                     │
│  ▷ Auditoria interna (plano, programa, execução)                       │
│  ▷ Análise crítica pela direção                                        │
│  ▷ Imparcialidade e gestão de riscos                                   │
│  ▷ Documentos da qualidade (manual, PG, PT, IT, FR)                    │
│  ▷ Indicadores de qualidade                                            │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.2 Auditoria interna — plano anual

```
┌────────────────────────────────────────────────────────────────────────┐
│ Auditoria Interna 2026 · Programa anual                                │
├────────────────────────────────────────────────────────────────────────┤
│ Auditor líder: Ana Costa · Frequência: 2x/ano (mín. ISO 17025 §8.8)    │
├────────────────────────────────────────────────────────────────────────┤
│ Ciclo │ Janela     │ Áreas auditadas             │ Status              │
│───────│────────────│─────────────────────────────│─────────────────────│
│ 1     │ Mar/2026   │ §6.4 Equip · §7.6 Incerteza │ ✓ Concluída · 2 NC  │
│ 2     │ Set/2026   │ §6.2 Pessoal · §7.8 Cert.   │ Planejada           │
└────────────────────────────────────────────────────────────────────────┘
[+ Novo ciclo]   [Ver checklist padrão (§iso 17025/03-checklists)]
```

#### 17.9.3 Auditoria interna — execução de ciclo

```
┌────────────────────────────────────────────────────────────────────────┐
│ Auditoria 2026/Ciclo 1 · §6.4 Equipamentos / §7.6 Incerteza            │
├────────────────────────────────────────────────────────────────────────┤
│ Auditor: Ana Costa · Auditados: Carlos, Maria · Datas: 10–12/03/2026   │
├────────────────────────────────────────────────────────────────────────┤
│ CHECKLIST APLICADO (derivado do template /iso 17025/03-checklists)     │
│                                                                        │
│ § 6.4 — Equipamentos                                                   │
│  ☑ Inventário atualizado · Evidência: relatório PadInv-202603 [PDF]    │
│  ☑ Calibração rastreável                                                │
│  ☐ Etiqueta de status visível       → NC-014 aberta                    │
│  ☑ Programa de manutenção                                              │
│                                                                        │
│ § 7.6 — Incerteza                                                      │
│  ☑ Avaliação por método                                                 │
│  ☐ Balanço documentado p/ todos     → NC-013 aberta                    │
│  ☑ Coerência com CMC                                                   │
│                                                                        │
│ NC GERADAS                                                             │
│  • NC-013 · Severidade Média · Resp. Carlos · Prazo 30 dias            │
│  • NC-014 · Severidade Baixa · Resp. Maria · Prazo 60 dias             │
│                                                                        │
│ [Gerar relatório final]   [Encerrar ciclo]                             │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.4 Não conformidade — tratamento e ação corretiva

```
┌────────────────────────────────────────────────────────────────────────┐
│ NC-013 · Balanço de incerteza não documentado                          │
├────────────────────────────────────────────────────────────────────────┤
│ Origem: Auditoria 2026/Ciclo 1 · Severidade: Média                     │
│ Aberta em: 12/03/2026 · Responsável: Carlos · Prazo: 11/04/2026        │
├────────────────────────────────────────────────────────────────────────┤
│ DESCRIÇÃO                                                              │
│ 3 procedimentos de calibração (PT-005, PT-006, PT-008) não possuem     │
│ balanço de incerteza completo conforme DOQ-CGCRE-008.                  │
│                                                                        │
│ AÇÃO IMEDIATA (cláusula 7.10)                                          │
│ ☑ Suspender uso dos PT-005/006/008 até balanço completo                │
│ Evidência: comunicado interno [link]                                   │
│                                                                        │
│ ANÁLISE DE CAUSA RAIZ                                                  │
│ Método: 5 Por Quês                                                     │
│ Causa: ausência de revisão obrigatória do balanço durante elaboração   │
│ de procedimentos.                                                      │
│                                                                        │
│ AÇÃO CORRETIVA (cláusula 8.7)                                          │
│ Ação: incluir checagem obrigatória de balanço no fluxo de aprovação    │
│ de procedimentos. Resp: Ana Costa · Prazo: 11/04                       │
│                                                                        │
│ VERIFICAÇÃO DE EFICÁCIA                                                │
│ Critério: 100% dos procedimentos vigentes com balanço documentado.     │
│ A medir em: 60 dias após implementação.                                │
│                                                                        │
│ STATUS: 🟡 Em tratamento     [Atualizar]   [Anexar evidência]          │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.5 Reclamação de cliente (cláusula 7.9)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Reclamação RECL-007 · Lab. Acme                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Recebida em: 17/04/2026 · Canal: e-mail · Resp.: João S.               │
│ Severidade: Alta · Prazo de resposta: 48h úteis                        │
├────────────────────────────────────────────────────────────────────────┤
│ RELATO DO CLIENTE                                                      │
│ "Recebemos certificado da balança BAL-007 com TAG errado (BAL-070)."   │
│                                                                        │
│ AÇÕES                                                                  │
│ ☑ Acuso de recebimento enviado em 17/04 14:22                          │
│ ☑ NC-015 aberta vinculando esta reclamação                             │
│ ☐ Iniciar fluxo de reemissão (motivo DADO_CADASTRAL)                   │
│ ☐ Resposta formal ao cliente                                           │
│                                                                        │
│ [Iniciar reemissão →]   [Registrar resposta]   [Fechar reclamação]     │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.6 Imparcialidade e gestão de riscos (cláusulas 4.1 + 8.5)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Imparcialidade e Riscos                                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  DECLARAÇÕES DE CONFLITO DE INTERESSE                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ João Silva · 12/01/2026 · Sem conflito declarado [PDF]           │  │
│  │ Maria Souza · 12/01/2026 · Conflito relatado: cliente ABC [PDF]  │  │
│  │ ...                                                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  [+ Solicitar nova rodada de declarações]                              │
│                                                                        │
│  MATRIZ DE RISCOS À IMPARCIALIDADE / OPERAÇÃO                          │
│  Risco                       │ Prob │ Imp  │ Resp.  │ Status           │
│──────────────────────────────│──────│──────│────────│──────────────────│
│  Pressão comercial sobre     │ Méd  │ Alta │ Direção│ Monitorado       │
│  resultado                   │      │      │        │                  │
│  Padrões emprestados de      │ Bx   │ Alt  │ Carlos │ Mitigado: termo  │
│  fornecedor                  │      │      │        │ específico       │
│  ...                                                                   │
│                                                                        │
│  [+ Novo risco]   [Exportar para análise crítica]                      │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.7 Análise crítica pela direção (cláusula 8.9)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Análise Crítica · Próxima reunião: 30/06/2026                          │
├────────────────────────────────────────────────────────────────────────┤
│ Pauta padrão (sustentada pelos dados do sistema)                       │
│                                                                        │
│ ☑ Mudanças nas necessidades do cliente                                 │
│ ☑ Atendimento de objetivos                                             │
│ ☑ Adequação de políticas e procedimentos                               │
│ ☑ Status das ações de análises críticas anteriores                     │
│ ☑ Resultado de auditorias internas e externas                          │
│ ☑ Ações corretivas                                                     │
│ ☑ Avaliações por organismos externos                                   │
│ ☑ Volume e tipo de trabalho                                            │
│ ☑ Reclamações                                                          │
│ ☑ Eficácia das melhorias implementadas                                 │
│ ☑ Adequação de recursos                                                │
│ ☑ Resultados da identificação de riscos                                │
│ ☑ Resultados de garantia da validade                                   │
│ ☑ Outros fatores relevantes                                            │
│                                                                        │
│ ENTRADAS AUTOMÁTICAS (do sistema)                                      │
│ • 142 certificados emitidos no período · 0 reemissões por erro técnico │
│ • 2 NC abertas · 7 fechadas · taxa de reincidência: 0%                 │
│ • 1 reclamação · resolvida em < 24h                                    │
│ • Auditoria 2026/Ciclo 1: 2 NC, ambas em tratamento                    │
│ • Indicador de tempo médio por OS: 32min (meta 35min) ✓                │
│ • [Ver dossiê completo →]                                              │
│                                                                        │
│ ATA E DELIBERAÇÕES                                                     │
│ [Iniciar nova ata]   [Ver atas anteriores (5)]                         │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.8 Documentos da qualidade

```
┌────────────────────────────────────────────────────────────────────────┐
│ Documentos · 24 vigentes                                  [+ Novo doc] │
├────────────────────────────────────────────────────────────────────────┤
│ Tipo: [Todos ▾]  Status: [Vigentes ▾]  🔍                               │
├────────────────────────────────────────────────────────────────────────┤
│ Código  │ Título                              │ Tipo  │ Rev. │ Vigênc. │
│─────────│─────────────────────────────────────│───────│──────│─────────│
│ MQ-001  │ Manual da Qualidade                 │ Manual│ 03   │ 01/2026 │
│ PG-001  │ Controle de documentos              │ Gestão│ 01   │ 01/2024 │
│ PG-002  │ Controle de registros               │ Gestão│ 02   │ 06/2025 │
│ PG-003  │ Imparcialidade                      │ Gestão│ 01   │ 01/2024 │
│ PG-004  │ Reclamações                         │ Gestão│ 01   │ 01/2024 │
│ PG-005  │ Trabalho não conforme               │ Gestão│ 02   │ 09/2025 │
│ PG-006  │ Auditoria interna                   │ Gestão│ 01   │ 01/2024 │
│ PG-007  │ Análise crítica                     │ Gestão│ 01   │ 01/2024 │
│ PT-005  │ Calibração IPNA campo classe III    │ Técn. │ 04   │ 03/2024 │
│ ...                                                                    │
│ FR-001  │ Registro de calibração              │ Form. │ 03   │ 03/2024 │
│ ...                                                                    │
└────────────────────────────────────────────────────────────────────────┘
```

#### 17.9.9 Indicadores da qualidade

```
┌────────────────────────────────────────────────────────────────────────┐
│ Indicadores · 12 últimos meses                                         │
├────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────┐  ┌────────────────────────────┐         │
│ │ % CERT. SEM REEMISSÃO      │  │ TAXA DE NC POR ÁREA         │         │
│ │ [linha 12 meses · meta 98%]│  │ [barras horizontais]        │         │
│ │ atual: 99,3% ✓             │  │ Equipamentos: 3 / Pessoal: 2│         │
│ └────────────────────────────┘  └────────────────────────────┘         │
│ ┌────────────────────────────┐  ┌────────────────────────────┐         │
│ │ TEMPO MÉDIO POR OS         │  │ % AÇÕES CORRETIVAS NO PRAZO │         │
│ │ atual: 32min (meta ≤ 35)   │  │ atual: 87,5% (meta ≥ 90%) ⚠ │         │
│ └────────────────────────────┘  └────────────────────────────┘         │
│ ┌────────────────────────────┐  ┌────────────────────────────┐         │
│ │ EFICÁCIA AÇÕES CORRETIVAS  │  │ % SATISFAÇÃO CLIENTE        │         │
│ │ atual: 100%                │  │ atual: NPS 71               │         │
│ └────────────────────────────┘  └────────────────────────────┘         │
│                                                                        │
│ [Exportar dossiê para análise crítica]                                 │
└────────────────────────────────────────────────────────────────────────┘
```

### 17.10 Itens fora deste apêndice (próxima iteração)

- Versões mobile dos e-mails (responsividade) e fluxos in-app de notificação push.
- Wireframe do **fluxo de transferência de equipamento entre clientes** (com trilha de auditoria).
- Wireframe do **fluxo de mudança de perfil regulatório** com dupla aprovação (§6.5).
- Wireframe do **gerenciador de escopo e CMC** (Tipo A) com importação CSV.
- Wireframe do **gerenciador de DCC XML** (Fase 3).

---

## 18. Referências internas do repositório

- [`ideia.md`](./ideia.md) — base funcional original
- [`iso 17025/02-requisitos/`](./iso%2017025/02-requisitos) — requisitos por cláusula (4 a 8)
- [`iso 17025/03-checklists/checklist-implementacao.md`](./iso%2017025/03-checklists/checklist-implementacao.md) — gap analysis
- [`iso 17025/04-templates/certificado-calibracao.md`](./iso%2017025/04-templates/certificado-calibracao.md) — template normativo
- [`iso 17025/04-templates/incerteza-medicao.md`](./iso%2017025/04-templates/incerteza-medicao.md) — modelo de balanço
- [`iso 17025/04-templates/procedimento-calibracao.md`](./iso%2017025/04-templates/procedimento-calibracao.md) — modelo de PT
- [`normas e portarias inmetro/portarias/portaria-157-2022.md`](./normas%20e%20portarias%20inmetro/portarias/portaria-157-2022.md) — RTM IPNA
- [`normas e portarias inmetro/portarias/portaria-289-2021.md`](./normas%20e%20portarias%20inmetro/portarias/portaria-289-2021.md) — RTM pesos padrão
- [`normas e portarias inmetro/rtm/rtms-por-instrumento.md`](./normas%20e%20portarias%20inmetro/rtm/rtms-por-instrumento.md) — índice de RTMs por instrumento

---

**Fim do PRD v1.7.**
