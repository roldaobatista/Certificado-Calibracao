# 0091 - Contexto da analise bruta derivado do snapshot metrologico da OS

## Contexto

Depois da fatia `0090`, a OS passa a congelar o perfil metrologico de equipamento e padrao principal. A analise bruta atual, porem, ainda interpreta linearidade e unidade apenas com base no payload bruto informado diretamente na captura.

Isso mantem uma dependencia manual desnecessaria em dois pontos:

- erro convencional digitado em cada ponto de linearidade;
- unidade esperada inferida apenas das leituras, sem confronto com o snapshot da OS.

## Objetivo

Permitir que a analise de bruto receba um contexto derivado do snapshot da OS para:

- usar `conventionalMassErrorValue` do padrao como default da linearidade quando o ponto nao informar esse valor;
- confrontar a unidade das leituras com a unidade esperada congelada na OS.

## Regras

1. O contexto e opcional.
2. Sem contexto, a analise atual continua funcionando sem regressao.
3. Se `defaultConventionalMassErrorValue` existir:
   - ele so entra quando o ponto de linearidade nao informar `conventionalMassErrorValue`.
4. Se `expectedMeasurementUnit` existir e divergir da unidade coletada:
   - a analise deve falhar fechada com blocker explicito.

## Escopo

- expandir a API da engine de analise bruta;
- aplicar o contexto nas leituras persistidas da OS;
- cobrir por teste unitario da engine e teste integrado do fluxo persistido.

## Fora de escopo

- balanco completo de incerteza;
- uso de densidade, deriva e graus de liberdade dentro desta mesma fatia.

## Done when

- a engine aceita contexto opcional;
- a analise persistida da OS usa o snapshot congelado para default de erro convencional e validacao de unidade;
- os testes demonstram o comportamento com e sem contexto.
