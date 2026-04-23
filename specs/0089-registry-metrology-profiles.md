# 0089 - Perfis metrologicos canonicos para cadastros de padroes e equipamentos

## Contexto

A onda anterior passou a persistir leituras brutas de ensaio e a derivar sinais de repetitividade, excentricidade e linearidade. O passo seguinte do plano mestre exige que o cadastro-base do sistema deixe de depender apenas de labels textuais para representar instrumento e padrao.

Hoje o registro operacional ainda usa principalmente campos resumidos como `capacityClassLabel`, `classLabel`, `uncertaintyLabel` e `correctionFactorLabel`. Esses campos continuam uteis para leitura humana e para o layout documental, mas nao sao suficientes para alimentar a engine metrologica real descrita em `specs/0085-full-metrology-software-master-plan.md`.

## Objetivo

Adicionar perfis metrologicos estruturados e versionaveis aos cadastros persistidos de:

- `Standard`
- `Equipment`

Esses perfis devem coexistir com os labels atuais, sem quebrar o back-office V2/V3 ja em uso.

## Escopo

### 1. Padrao (`Standard`)

O cadastro do padrao passa a aceitar um `metrologyProfile` canonico contendo, no minimo:

- `quantityKind`
- `measurementUnit`
- `traceabilitySource`
- `certificateIssuer`
- `expandedUncertaintyValue`
- `coverageFactorK`

Campos complementares permitidos:

- `conventionalMassErrorValue`
- `degreesOfFreedom`
- `densityKgPerM3`
- `driftLimitValue`

### 2. Equipamento (`Equipment`)

O cadastro do equipamento passa a aceitar um `metrologyProfile` canonico contendo, no minimo:

- `instrumentKind`
- `measurementUnit`
- `maximumCapacityValue`
- `readabilityValue`
- `verificationScaleIntervalValue`

Campos complementares permitidos:

- `normativeClass`
- `minimumCapacityValue`
- `minimumLoadValue`
- `effectiveRangeMinValue`
- `effectiveRangeMaxValue`

## Regras de implementacao

1. A adicao deve ser **aditiva**:
   - nao remover labels atuais;
   - nao mudar a semantica dos catalogos existentes;
   - nao bloquear emissao legada apenas por ausencia do novo perfil.

2. Se qualquer campo do perfil metrologico for enviado no `manage`, o payload final deve ser validado contra o schema canonico correspondente.

3. Se nenhum campo do perfil for enviado:
   - o registro continua valido;
   - o sistema deve expor que o perfil metrologico ainda esta pendente.

4. Os novos dados devem ser persistidos em banco como JSON estruturado em coluna dedicada, preservando compatibilidade com a modelagem atual e preparando a futura normalizacao por entidades filhas.

5. O catalogo persistido deve expor no detalhe:
   - o objeto `metrologyProfile` quando existente;
   - um `metrologySummaryLabel` pronto para UI.

## Fora de escopo nesta fatia

- substituir labels humanos por derivacao automatica a partir do perfil;
- usar o perfil metrologico para recalcular a engine final do certificado;
- criar tabelas filhas normalizadas para componentes de incerteza;
- bloquear workflow operacional por perfil metrologico ausente.

## Done when

- `Standard` e `Equipment` persistem `metrologyProfile` estruturado;
- rotas `manage` validam o perfil quando informado;
- catalogos persistidos retornam `metrologyProfile` e `metrologySummaryLabel` no detalhe;
- telas web permitem informar e visualizar o perfil canonico;
- existe teste cobrindo persistencia e leitura dos novos campos.
