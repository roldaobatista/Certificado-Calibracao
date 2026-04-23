# 0086 - Analise metrologica inicial sobre dados brutos da OS

## Contexto

A spec `0085-full-metrology-software-master-plan.md` abriu a primeira trilha critica: persistir dados brutos estruturados de repetitividade, excentricidade, linearidade, ambiente e evidencias na OS.

Com isso resolvido, o proximo passo seguro nao e "inventar" a incerteza expandida final sem fechar toda a engine NAWI/IPNA. O passo correto e usar o bruto persistido para:

- calcular estatisticas basicas reais de ensaio;
- detectar inconsistencias estruturais de captura;
- alimentar revisao, fila de assinatura e previa com sinais metrologicos de verdade;
- fail-close quando o bruto estiver incoerente para sustentar emissao.

## Objetivo

Adicionar em `@afere/engine-uncertainty` uma API de analise inicial dos dados brutos de ensaio, cobrindo:

- repetitividade;
- excentricidade;
- linearidade;
- completude minima da captura;
- coerencia de unidade entre os ensaios.

## Escopo

- criar modulo novo em `packages/engine-uncertainty` para analisar os dados brutos persistidos da OS;
- calcular media e desvio padrao amostral por serie de repetitividade;
- calcular delta maximo de excentricidade a partir do ponto central;
- calcular erro por ponto de linearidade usando referencia corrigida pelo erro convencional quando informado;
- detectar unidades mistas, ausencia de centro em excentricidade e ausencia de ensaios minimos;
- produzir resumo textual reutilizavel por `apps/api`;
- integrar a analise na revisao tecnica persistida, na previa persistida e na fila de assinatura.

## Fora de escopo

- calcular a incerteza expandida final completa;
- aplicar ainda Welch-Satterthwaite, piso `0,41 * d`, empuxo do ar, deriva ou conveccao;
- substituir definitivamente os campos-resumo atuais do certificado.

## Regras

- a analise nao pode inventar `U` final nem declarar rastreabilidade matematica que ainda nao foi implementada;
- inconsistencias estruturais viram `blockers` ou `warnings`, nao silencios;
- ausencia total de bruto estruturado nao deve quebrar leitura historica, mas deve degradar a prontidao do fluxo;
- unidades mistas entre ensaios falham fechado para revisao/assinatura.

## Criterios de aceite

- `@afere/engine-uncertainty` exporta uma funcao de analise de bruto;
- o modulo retorna estatisticas de repetitividade, excentricidade e linearidade quando houver dados suficientes;
- o modulo retorna `warnings` e `blockers` consistentes para captura incompleta ou incoerente;
- a revisao tecnica persistida exibe sinais derivados do bruto;
- a fila de assinatura considera incoerencias do bruto como pendencia operacional;
- existem testes do modulo novo e cobertura de integracao no backend.

## Evidencia

- `pnpm exec tsx --test packages/engine-uncertainty/src/raw-measurement-analysis.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/api typecheck`
- `pnpm --filter @afere/web typecheck`
