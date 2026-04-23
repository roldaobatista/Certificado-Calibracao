# 0085 - Plano mestre para implementar o software metrologico completo

## Contexto

O repositório atual já cobre fundação técnica, cadastros persistidos, fluxo operacional mínimo, portal persistido, trilha crítica, governança regulatória e parte relevante do backlog V1-V5. Mesmo assim, ainda existe uma distância material entre o estado atual do software e a especificação técnico-metrológica completa do produto.

Os principais gaps remanescentes estão concentrados em:

- engine metrológica real para NAWI/IPNA, incluindo leituras brutas, ensaios e balanço de incerteza;
- modelagem estruturada de dados metrológicos de instrumento, padrão, procedimento e coleta;
- documento oficial com PDF/A validado externamente, evidências binárias e assinatura eletrônica operacional;
- canal Android offline-first real, com sync cliente-servidor materializado fora do modo canônico;
- fechamento regulatório e de validação do software no nível exigido para operação auditável.

Este plano organiza a implementação completa em ondas executáveis, preservando a lógica `foundation-first` do roadmap atual e evitando misturar fechamento do núcleo com adiantamentos cosméticos.

## Objetivo

Levar o produto do estado atual para um software operacional completo de calibração de balanças, com:

- coleta estruturada e persistida de dados brutos de ensaio;
- cálculo metrológico rastreável e validado;
- emissão controlada de certificado com publicação verificável;
- assinatura eletrônica operacional com trilha auditável;
- canal mobile offline-first real;
- dossiê de validação, governança regulatória e evidências de release consistentes com uso real.

## Princípios de execução

1. Não reabrir a fundação sem necessidade: aproveitar o que V1-V5 já consolidou.
2. Fechar primeiro os gaps de núcleo metrológico antes de expandir canal ou estética.
3. Separar claramente:
   - assinatura eletrônica auditável operacional;
   - assinatura qualificada ICP-Brasil;
   - conformidade PDF/A estrutural;
   - validação formal externa.
4. Tudo que afeta emissão oficial, cálculo, audit trail, sync e perfil regulatório segue fail-closed.
5. Toda onda termina com evidência arquivável e regressão automatizada.

## Escopo do "tudo"

Para este plano, "implementar tudo" significa fechar oito frentes:

1. Modelo de dados metrológico profundo.
2. Engine de cálculo e regra de decisão.
3. Fluxo web operacional ponta a ponta com dados brutos.
4. Certificado oficial, publicação, QR e reemissão.
5. Assinatura eletrônica operacional e trilha jurídica mínima.
6. Android offline-first real e sync materializado.
7. Qualidade, LGPD, governança e dossiê em cima de operação real.
8. Validação do software, piloto controlado e readiness de produção.

## Ondas de execução

### Onda 0 - Rebaseline executável (1-2 semanas)

**Objetivo:** travar o plano, evitar refação paralela e preparar o repositório para a segunda onda de implementação.

**Entregáveis:**

- consolidar esta spec como plano mestre;
- abrir épicos/subspecs derivados para cada frente crítica;
- congelar adiantamentos fora do caminho crítico enquanto o núcleo metrológico é fechado;
- definir baseline de testes e evidências por onda.

**Done when:**

- existe backlog priorizado, dependente e com owners claros;
- toda nova implementação relevante aponta para uma sub-spec derivada deste plano.

### Onda 1 - Modelo de dados metrológico profundo (3-4 semanas)

**Objetivo:** sair do modelo resumido atual e passar a persistir os dados que realmente sustentam cálculo, revisão e auditoria.

**Entregáveis:**

- estruturação explícita de `Max`, `d`, `e`, classe normativa, faixa efetiva e tipo de instrumento;
- modelagem de padrão com erro convencional, incerteza expandida, `k`, densidade, emissor, certificado, validade e origem;
- entidade de sessão de calibração e entidades filhas para:
  - leituras de repetitividade;
  - leituras de excentricidade;
  - pontos de linearidade;
  - histerese e testes complementares;
  - condições ambientais;
  - anexos/evidências;
- versionamento de alterações críticas sem sobrescrita destrutiva dos dados brutos;
- storage metadata para PDFs, anexos e hashes.

**Done when:**

- o banco permite reconstruir integralmente uma calibração sem depender de campos-resumo;
- auditor consegue diferenciar dado bruto, cálculo derivado, revisão e emissão.

### Onda 2 - Engine metrológica real (4-6 semanas)

**Objetivo:** implementar o núcleo matemático real do produto.

**Entregáveis:**

- cálculo de repetitividade, excentricidade e linearidade;
- cálculo de resolução, repetitividade, componentes de padrão e fatores ambientais;
- regra de substituição de `s(I)` por piso vinculado à resolução quando aplicável;
- composição de incerteza combinada e expandida;
- cálculo de graus de liberdade efetivos e fator `k`;
- regra de decisão parametrizável;
- classificador de EMA por classe conforme Portaria 157/2022;
- suíte de cenários-referência para validação da engine.

**Done when:**

- a engine opera sobre leituras reais persistidas;
- os resultados do certificado não são mais digitados manualmente como resumo;
- o release falha quando os cenários de referência divergem do epsilon aprovado.

### Onda 3 - Fluxo operacional web completo (4-6 semanas)

**Objetivo:** transformar o back-office em fluxo real de execução, revisão e emissão com base na nova modelagem.

**Entregáveis:**

- wizard real de OS e execução técnica;
- telas de coleta por ensaio com validação contextual;
- revisão técnica sobre dados brutos, não apenas sobre resumo;
- bloqueios automáticos por padrão, ambiente, competência, escopo/CMC e regra de decisão;
- auditoria de alteração campo a campo em leitura crítica;
- anexos binários reais ligados à OS.

**Done when:**

- um técnico consegue abrir OS, registrar ensaios, anexar evidências e submeter para revisão;
- um revisor consegue aprovar ou reprovar com base em dados persistidos completos.

### Onda 4 - Documento oficial, assinatura operacional e publicação (3-5 semanas)

**Objetivo:** fechar o documento emitido como artefato oficial do sistema.

**Entregáveis:**

- renderer oficial de certificado com layout por perfil A/B/C;
- integração do documento com resultados reais da engine e dados persistidos;
- anexação de rastreabilidade e evidências quando aplicável;
- assinatura eletrônica operacional auditável;
- publicação persistida com QR, hash, revisão e reemissão controlada;
- validação externa de PDF/A e tratamento fail-closed quando não aprovado.

**Done when:**

- o certificado oficial deixa de ser artefato canônico de regressão e passa a ser artefato operacional;
- QR e portal conseguem verificar certificados emitidos do fluxo real;
- reemissão preserva cadeia, hash anterior e rastreabilidade.

**Observação de escopo:**

- ICP-Brasil, PAdES qualificado e carimbo do tempo oficial devem ser tratados como sub-onda própria após a assinatura operacional estar estável.

### Onda 5 - Android offline-first real e sync materializado (6-10 semanas)

**Objetivo:** sair da modelagem TypeScript e entregar o canal mobile real.

**Entregáveis:**

- app Android Kotlin real;
- banco local protegido;
- outbox e sync cliente-servidor reais;
- replay protection, idempotência e fila humana conectados ao backend persistido;
- suporte a coleta offline de leituras e evidências;
- cobertura de conflitos críticos do fluxo de OS/certificado.

**Done when:**

- uma calibração pode começar offline, sincronizar depois e manter consistência com o backend;
- a matriz de conflitos deixa de ser apenas simulador e vira evidência de operação real.

### Onda 6 - Qualidade, validação formal e go-live controlado (4-6 semanas)

**Objetivo:** fechar o sistema como software auditável, não apenas funcional.

**Entregáveis:**

- dossiê formal de validação do software;
- rastreabilidade requisito -> teste -> evidência;
- runbooks de operação e incidentes com drills reais;
- fechamento de NCs e riscos abertos ligados ao núcleo metrológico;
- readiness de piloto controlado com critérios de entrada e saída;
- release-norm de go-live baseada em operação real.

**Done when:**

- existe piloto controlado com evidência arquivada;
- a plataforma pode ser apresentada como sistema operacional auditável, sem promessas acima do que realmente implementa.

## Trilhas transversais obrigatórias

Estas trilhas rodam em paralelo às ondas, mas não podem quebrar o caminho crítico:

### T1 - Segurança, tenancy e audit trail

- manter RLS, RBAC, MFA e hash-chain verdes a cada nova entidade crítica;
- impedir update destrutivo em leituras brutas e evidências;
- estender fuzz e testes de isolamento para novos módulos.

### T2 - Evidências binárias e storage

- padronizar upload, hash, retenção, versionamento e vínculo com OS/certificado;
- preparar WORM/imutabilidade onde o domínio exigir.

### T3 - Validação metrológica e regulatória

- cada incremento da engine precisa de cenário de referência e parecer de conformidade;
- cada incremento documental precisa de snapshot, manifesto e checklist de norma aplicável.

### T4 - UX operacional

- o frontend deve continuar simples para o operador, mesmo com aumento da profundidade metrológica;
- não expor complexidade matemática onde o operador só precisa registrar dado corretamente.

## Dependências críticas

1. Onda 1 é pré-requisito da Onda 2.
2. Onda 2 é pré-requisito da Onda 3.
3. Onda 3 é pré-requisito da Onda 4 e da Onda 5.
4. Onda 4 e Onda 5 alimentam a Onda 6.
5. ICP-Brasil e PAdES qualificado não devem bloquear a primeira entrega operacional do fluxo real; entram após assinatura operacional estabilizada.

## Principais riscos

- tentar implementar Android real antes de fechar engine e fluxo web;
- tentar qualificar juridicamente a assinatura antes de estabilizar o documento operacional;
- manter leituras brutas fora do banco e continuar dependente de resumos;
- tratar PDF determinístico de regressão como se fosse certificado PDF/A formal de produção;
- expandir Qualidade avançada sem fechar antes a base metrológica.

## Critérios executivos de sucesso

- existe uma OS real com dados brutos completos, revisão, assinatura e certificado publicado;
- a engine calcula o certificado a partir de leituras persistidas, sem digitação manual do resultado final;
- o certificado reflete corretamente o perfil A/B/C e as regras de escopo/CMC;
- o portal valida o certificado real via QR;
- o Android consegue operar offline e sincronizar sem perda ou duplicidade aceita;
- o dossiê de validação cobre software, engine, documento e sync.

## Sequência imediata recomendada

1. Abrir sub-spec de modelagem de dados metrológicos e leituras brutas.
2. Abrir sub-spec da engine metrológica real para NAWI/IPNA.
3. Abrir sub-spec do fluxo web de coleta e revisão sobre dados brutos.
4. Abrir sub-spec do certificado oficial operacional, separado do renderer canônico de regressão.
5. Somente depois abrir a sub-spec do app Android Kotlin real.

## Evidência esperada ao final deste plano

- `specs/0085-full-metrology-software-master-plan.md`
- novas sub-specs derivadas por frente crítica
- atualização do backlog executável com as ondas aprovadas
- dossiês por onda em `compliance/validation-dossier/releases/`
