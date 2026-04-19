# Ideia — App Android para Certificado de Calibração de Balanças

## 1. Descrição

Aplicativo Android para execução de calibração de balanças em campo e em laboratório, operando como **plataforma metrológica móvel** — e não como um simples gerador de PDF. O produto deve funcionar simultaneamente como **sistema metrológico**, **sistema da qualidade** e **sistema documental**, com base na ABNT NBR ISO/IEC 17025 e nos requisitos regulatórios do Inmetro/Cgcre.

## 2. Objetivo

- Executar calibrações em campo ou laboratório com operação offline.
- Registrar evidências técnicas e rastreabilidade metrológica.
- Calcular resultados e incerteza de medição.
- Aplicar regra de decisão quando cabível.
- Emitir certificado tecnicamente defensável.
- Manter trilha de auditoria completa.
- Sincronizar com backend, ERP ou laboratório central.

## 3. Base normativa

| Referência | Aplicação |
|------------|-----------|
| ABNT NBR ISO/IEC 17025:2017 | Competência, imparcialidade e operação consistente de laboratórios |
| Portaria Inmetro nº 157/2022 | RTM de instrumentos de pesagem não automáticos (IPNA) |
| Orientações Cgcre/Inmetro | Rastreabilidade, relato de resultados, declaração de conformidade, CMC |
| ILAC P10 / P14 | Política de rastreabilidade e incerteza em calibração |
| EURAMET cg-18 | Boa prática para calibração de NAWI (não obrigatória) |
| Plano Estratégico Inmetro 2024–2027 | Certificado de Calibração Digital (DCC) |

## 4. Premissas normativas do produto

1. Resultado bruto e incerteza **não podem ser omitidos** em certificado com declaração de conformidade.
2. Rastreabilidade metrológica dos padrões precisa ser controlada de ponta a ponta.
3. Certificado de calibração **não tem validade automática** — a periodicidade é definida pelo proprietário dentro do seu programa de calibração.
4. Recomendação de intervalo de recalibração não deve constar no certificado (salvo condição específica).
5. Para laboratório acreditado, o sistema deve respeitar **escopo, CMC e uso correto de referência à acreditação**.
6. Nenhum app, sozinho, garante ISO/IEC 17025 — a conformidade depende também de pessoal competente, procedimentos válidos, padrões rastreáveis e sistema de gestão efetivo.

## 5. Arquitetura do produto

### 5.1 Camadas funcionais

- **Metrológica:** cálculos, incerteza, CMC, regra de decisão.
- **Regulatória:** RTM/portarias, escopo, símbolo, uso legal.
- **Qualidade:** trilha de auditoria, competência, documentos, bloqueios.
- **Documental:** certificado robusto, verificável, reemitível e rastreável.

### 5.2 Componentes técnicos

- **App Android de campo** — execução, coleta de evidências, operação offline, assinatura local, sincronização.
- **Backend técnico** — autenticação, regras de negócio, cálculo consolidado, revisão, emissão, auditoria, APIs.
- **Portal web** — consulta de certificados, QR code, gestão administrativa, procedimentos, padrões, escopo/CMC, qualidade.

### 5.3 Estratégia de dados

- Banco local no Android criptografado.
- Fila de sincronização assíncrona.
- Backend como fonte oficial.
- Anexos armazenados com hash.
- Trilha de auditoria imutável.

## 6. Perfis de usuário

| Perfil | Responsabilidade |
|--------|------------------|
| Técnico executor | Realiza a calibração e registra evidências |
| Revisor técnico | Confere coerência técnica, cálculos e completude |
| Signatário autorizado | Aprova a emissão do certificado |
| Gestor da qualidade | Administra procedimentos, não conformidades e auditoria |
| Administrador | Gerencia usuários, perfis, integrações e parâmetros |
| Auditor somente leitura | Consulta trilhas, certificados, revisões e evidências |
| Cliente/portal | Consulta certificados e autenticidade |

## 7. Módulos obrigatórios

### 7.1 Autenticação, perfis e rastreabilidade humana
Login forte, autenticação offline com cache seguro, assinatura eletrônica por credencial, bloqueio por competência técnica. Técnico executa; revisor não pode revisar o próprio serviço; signatário só assina se os requisitos estiverem íntegros.

### 7.2 Cadastro de clientes e locais
Razão social/nome, CNPJ/CPF, contatos, endereço, unidades/filiais, local exato da balança, responsável pelo acompanhamento, condições especiais do local, histórico de serviços, anexos contratuais.

### 7.3 Instrumentos de pesagem
Código interno, tipo, fabricante, modelo, número de série, capacidade máxima, divisão, classe, tara, localização, uso pretendido, faixa efetiva, status regulatório, fotos da placa e lacres, aprovação de modelo quando aplicável. Histórico por instrumento com reparos, troca de célula/indicador e ocorrências.

### 7.4 Padrões e instrumentos auxiliares
Controle de pesos padrão, massas auxiliares, termohigrômetro, barômetro, inclinômetro e acessórios. Cada padrão com: ID, descrição, fabricante/modelo, faixa, valor nominal, incerteza, certificado vinculado, laboratório emissor, data da calibração, vencimento interno, fatores de correção, status. **Regras:** padrão vencido bloqueia uso; padrão fora da faixa bloqueia ensaio; padrão sem cadeia documental válida impede aprovação final.

### 7.5 Procedimentos e métodos
Cadastro versionado com código, revisão, vigência, escopo de aplicação, tipo de instrumento, sequência de ensaios, critérios de aceitação, fórmula de cálculo, orçamento de incerteza, regra de decisão, modelo de certificado. Versionamento completo com motivo e aprovação.

### 7.6 Ordem de serviço metrológica
Container operacional da calibração.

**Status:** aberta · em deslocamento · em execução · aguardando evidência · aguardando revisão · aguardando assinatura · concluída · cancelada · reemitida.

**Campos:** cliente, local, instrumento, técnico, padrões previstos, procedimento, data/hora, condições ambientais, observações, fotos, assinatura do acompanhante.

### 7.7 Execução guiada (wizard)
1. Conferir instrumento
2. Registrar ambiente
3. Validar padrões disponíveis
4. Confirmar procedimento
5. Lançar pontos de carga
6. Registrar leituras e repetições
7. Registrar excentricidade, linearidade, histerese etc.
8. Registrar ocorrências
9. Fechar coleta

Operação **offline**; impede "pular etapa crítica" sem justificativa.

### 7.8 Cálculos metrológicos
- Erro de indicação, correções, médias.
- Repetibilidade, histerese, excentricidade, linearidade.
- Erro máximo observado.
- Incerteza padrão e expandida, fator de abrangência.
- Orçamento por contribuições (padrões, ambiente, resolução, operador/método).
- Comparação com limites internos, especificação do cliente e critério regulatório.
- Comparação com CMC quando acreditado.

### 7.9 Declaração de conformidade
**Não pode ser um simples botão "aprovado".** Exige especificação/requisito de referência, regra de decisão, modo de aplicação, banda de proteção (quando usada), registro de quem definiu a regra e indicação de acordo com o cliente.

**Saídas possíveis:** conforme · não conforme · sem declaração · inconclusivo/não aplicável.

### 7.10 Emissão do certificado
Campos mínimos:
- Número único e revisão
- Identificação do laboratório, cliente e instrumento
- Local da calibração
- Datas de calibração e emissão
- Procedimento/método
- Padrões principais utilizados
- Condições ambientais relevantes
- Resultados, incerteza, fator k, unidade
- Regra de decisão (quando aplicável)
- Declaração de conformidade (quando aplicável)
- Observações/limitações
- Signatário
- QR code / código de verificação

> "Próxima calibração" **não deve** compor o núcleo técnico do certificado — fica no plano interno de gestão do cliente.

### 7.11 Documentos e evidências
Fotos, vídeos curtos, assinatura, laudos, certificados de padrões, croquis, prints de leitura. Cada arquivo com carimbo de data/hora, hash, versão e bloqueio de exclusão após conclusão.

### 7.12 Qualidade
Não conformidades, ações corretivas, desvios de procedimento, tentativas de uso de padrão vencido, registros de treinamento/competência, aprovação de templates, revisão de procedimentos, eventos auditáveis, painel de pendências.

### 7.13 Escopo acreditado e CMC
Cadastro do escopo, faixas acreditadas, CMC por serviço/faixa, checagem se o serviço está dentro/fora do escopo, definição de uso ou não da referência à acreditação, vínculo com consulta pública RBC/Cgcre.

### 7.14 Sincronização e integridade
Banco local criptografado, fila de sincronização, resolução de conflito, envio diferido de anexos, assinatura de payload, logs de sincronização, backup, modo somente leitura em inconsistência crítica.

### 7.15 Portal / verificação externa
QR code no certificado, validação pública por código, visualização do PDF emitido, status (original / reemitido / cancelado / substituído).

### 7.16 Preparação para DCC
Arquitetura preparada para Certificado de Calibração Digital (DCC), conforme Plano Estratégico Inmetro 2024–2027.

## 8. Telas do app

| # | Tela | Função principal |
|---|------|------------------|
| 1 | Login | Autenticação, biometria, seleção de unidade, modo offline |
| 2 | Dashboard | OS do dia, padrões vencendo, pendências de sync, revisões |
| 3 | Minhas OS | Lista, filtros, iniciar execução, indicador offline |
| 4 | Abertura da calibração | Cliente, instrumento, procedimento, checklist pré-execução |
| 5 | Identificação do instrumento | Dados cadastrais, fotos da placa, lacres e conjunto |
| 6 | Condições ambientais | Temperatura, umidade, pressão, instrumento auxiliar, hora |
| 7 | Seleção de padrões | Lista, status, validade, bloqueio automático se inválido |
| 8 | Lançamento dos ensaios | Carga, indicação, erro, repetição, observações |
| 9 | Ensaios complementares | Excentricidade, repetibilidade, linearidade, histerese, zero |
| 10 | Cálculo preliminar | Resumo, erros, incerteza provisória, pendências |
| 11 | Ocorrências e desvios | Falhas, lacres rompidos, impossibilidades |
| 12 | Evidências | Fotos, anexos, assinatura do acompanhante, áudio opcional |
| 13 | Revisão técnica | Conferência, divergências, aceite ou devolução |
| 14 | Assinatura e emissão | Signatário, resumo final, assinatura eletrônica |
| 15 | Certificado | Pré-visualização, compartilhar PDF, QR, histórico |
| 16 | Padrões | Cadastro, validade, uso recente, bloqueios |
| 17 | Procedimentos | Revisões, comparar versões, aprovar nova revisão |
| 18 | Escopo / CMC | Faixas, serviços, CMC, status dentro/fora do escopo |
| 19 | Auditoria | Logs completos por OS ou certificado |
| 20 | Sincronização | Pendências, erros, reenvio, conflitos |

## 9. Fluxos operacionais

### 9.1 Fluxo A — calibração comum
`abrir OS` → `identificar balança` → `registrar ambiente` → `selecionar padrões` → `executar ensaios` → `calcular` → `revisar` → `assinar` → `emitir certificado` → `sincronizar`

### 9.2 Fluxo B — instrumento com problema
`abrir OS` → `identificar falha impeditiva` → `registrar evidências` → `emitir relatório de não execução ou execução parcial` → `bloquear certificado final`

### 9.3 Fluxo C — com declaração de conformidade
`executar ensaio` → `calcular resultado e incerteza` → `selecionar especificação` → `aplicar regra de decisão` → `gerar certificado com resultado + incerteza + declaração`

### 9.4 Fluxo D — serviço fora do escopo acreditado
`executar normalmente` → `sistema detecta fora do escopo` → `bloquear símbolo/referência RBC` → `emitir certificado sem menção à acreditação`

### 9.5 Fluxo E — calibração com ajuste
`coletar dados iniciais` → `registrar ajuste` → `coletar dados pós-ajuste` → `manter ambos os conjuntos` → `relatório configurável conforme política`

## 10. Regras de negócio

| ID | Regra |
|----|-------|
| RB-01 | Emissão bloqueada sem rastreabilidade (padrão vencido / sem certificado / fora da faixa) |
| RB-02 | Emissão bloqueada sem dados técnicos mínimos na OS |
| RB-03 | Procedimento obrigatório e versionado (código, revisão, vigência, aprovador) |
| RB-04 | Revisor técnico ≠ executor (salvo política formal com exceção registrada) |
| RB-05 | Signatário bloqueado se houver pendência técnica ou NC aberta |
| RB-06 | Regra de decisão obrigatória quando houver "conforme/não conforme" |
| RB-07 | Resultado e incerteza obrigatórios em certificado com declaração de conformidade |
| RB-08 | CMC respeitada: incerteza declarada ≥ CMC aplicável no escopo |
| RB-09 | Serviço fora do escopo → bloquear símbolo/referência RBC |
| RB-10 | Certificado sem "validade automática" — periodicidade é do proprietário |
| RB-11 | Retenção de registros técnicos (dados brutos, cálculos, revisão, anexos) |
| RB-12 | Trabalho não conforme bloqueia emissão até disposição formal |
| RB-13 | Controle de alteração com log (usuário, data/hora, antes/depois, motivo) |
| RB-14 | Hash documental em todo PDF e anexo crítico |
| RB-15 | QR code verificável contra backend oficial |
| RB-16 | Offline com reconciliação: "oficial" só após sincronização |
| RB-17 | Competência por usuário (habilitação por tipo de serviço/faixa) |
| RB-18 | Checagens intermediárias de padrões/equipamentos registradas |
| RB-19 | Métodos associados ao escopo acreditado |
| RB-20 | Arquitetura preparada para DCC (certificado digital estruturado) |

## 11. Histórias de usuário

- **HU-01** — Como técnico, quero executar a calibração offline para continuar trabalhando sem internet.
- **HU-02** — Como técnico, quero que o app me impeça de usar padrão vencido, para reduzir erro de campo.
- **HU-03** — Como revisor, quero ver dados brutos, cálculos e evidências para aprovar apenas serviços consistentes.
- **HU-04** — Como signatário, quero bloquear emissão quando faltar incerteza, evidência ou revisão.
- **HU-05** — Como gestor da qualidade, quero rastrear desvios e trabalhos não conformes para sustentar auditoria.
- **HU-06** — Como administrador, quero versionar procedimentos sem perder histórico.
- **HU-07** — Como cliente, quero validar o certificado por QR code para confirmar autenticidade.
- **HU-08** — Como laboratório acreditado, quero controlar escopo e CMC para evitar referência indevida à RBC.

## 12. Modelo mínimo de dados

```
users · roles · user_competencies
customers · customer_sites
instruments · instrument_photos
standards · standard_certificates
procedures · procedure_revisions
work_orders · work_order_environment · work_order_tests · work_order_evidence
calculations · decision_rules
reviews · approvals
certificates · certificate_revisions
audit_logs · nonconforming_work
scope_items · cmc_items
sync_events
```

## 13. Backlog por fase

### Fase 1 — MVP operacional
Login e perfis · cadastros básicos · controle de padrões · OS · execução guiada · cálculo · incerteza · revisão · assinatura · certificado PDF · QR/verificação · logs · sincronização offline.

### Fase 2 — Laboratório maduro
Módulo completo da qualidade · escopo e CMC avançados · regras de conformidade sofisticadas · painel gerencial · portal do cliente · reemissão controlada · auditoria avançada · treinamento/competência · indicadores de estabilidade.

### Fase 3 — Ecossistema
Integração ERP/financeiro · integração com portal · API externa · importação em massa · relatórios estatísticos · preparação para DCC/XML.

## 14. Critérios de aceite do MVP

O MVP só deve ser considerado pronto quando:

1. Uma calibração puder ser executada do início ao certificado pelo celular.
2. O sistema bloquear padrões vencidos.
3. O certificado sair com resultado, incerteza e fator k.
4. A revisão e a assinatura ficarem registradas.
5. O QR/code validar a autenticidade do certificado.
6. A operação funcionar offline e sincronizar depois.
7. O log mostrar quem alterou o quê.
8. A emissão com declaração de conformidade exigir regra de decisão.
9. O sistema distinguir serviço acreditado de serviço fora do escopo.
10. O certificado não depender de edição manual externa.

## 15. Decisões de produto recomendadas

- Android como app de campo, mas com **backend web obrigatório**.
- Cálculo no backend **e** no app, com reconciliação.
- PDFs gerados de forma padronizada no servidor.
- Modelo de permissões por função **e** por competência.
- Configuração de procedimento por revisão, não por código fixo.
- Todo evento relevante gerando trilha de auditoria.
- Certificado como saída do sistema, nunca documento editável manualmente.

## 16. Risco principal do projeto

O maior risco **não é técnico; é conceitual**: tentar transformar o app em "emissor rápido de certificado" em vez de "sistema metrológico com controle de qualidade e dados". Se isso acontecer, o produto até gera PDF, mas falha em auditoria, em revisão técnica e quando houver questionamento de resultado, incerteza, rastreabilidade ou conformidade.

## 17. Ordem de implementação recomendada

1. Modelo de dados
2. Regras de negócio
3. Workflow da OS
4. Motor de cálculo
5. Revisão / assinatura
6. Emissão do certificado
7. Portal / QR
8. Qualidade / escopo avançado

> Essa ordem reduz retrabalho e evita fazer um app "bonito" com base técnica fraca.

## 18. Próximos passos

- [ ] Validar PRD com stakeholders técnicos (metrologia + qualidade).
- [ ] Definir stack tecnológica (Android nativo vs. Kotlin Multiplatform / Flutter).
- [ ] Modelar banco de dados a partir das entidades listadas.
- [ ] Especificar motor de cálculo e orçamento de incerteza em documento separado.
- [ ] Desenhar wireframes das 20 telas.
- [ ] Definir padrão de numeração e template de certificado.
- [ ] Preparar plano de homologação contra ISO/IEC 17025.

## 19. Referências

- ABNT NBR ISO/IEC 17025:2017
- Portaria Inmetro nº 157/2022 — RTM de IPNA
- Orientações Cgcre/Inmetro (declaração de conformidade, incerteza, relato de resultados, escopo RBC)
- ILAC P10 — Política de Rastreabilidade Metrológica
- EURAMET cg-18 — Guideline on the Calibration of Non-Automatic Weighing Instruments
- Plano Estratégico Inmetro 2024–2027 (DCC)
