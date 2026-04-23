# ADR 0063 — Onda metrológica assistida no fluxo de emissão

## Status

Aceito

## Contexto

O fluxo persistido de emissão já sustentava OS, revisão, assinatura e emissão sobre dados reais do tenant, mas ainda carecia de uma trilha metrológica intermediária entre captura bruta e decisão oficial. Isso deixava o sistema dependente de labels manuais, sem orçamento preliminar de incerteza, sem avaliação indicativa da Portaria 157 e sem registro explícito da divergência entre decisão assistida e decisão oficial.

As `specs/0085` a `0097` consolidam essa lacuna como uma única onda: capturar medições brutas, derivar contexto metrológico persistido, produzir análise e orçamento preliminar, calcular avaliação indicativa e endurecer o gate da decisão oficial antes da assinatura.

## Decisão

Adotar a onda metrológica assistida como camada persistida do fluxo de emissão:

1. Persistir captura bruta de medições, perfis metrológicos de equipamento/padrão e snapshots metrológicos por OS.
2. Derivar labels de execução e contexto técnico a partir da captura bruta sempre que o operador não informar rótulos manuais válidos.
3. Introduzir no `packages/engine-uncertainty` uma trilha assistiva com análise estruturada, EMA indicativa da Portaria 157, orçamento preliminar e regra decisória indicativa.
4. Expor essa assistência nos contratos, no review técnico, na prévia do certificado, na fila de assinatura e na trilha de auditoria.
5. Exigir decisão oficial explícita para aprovação e emissão, com justificativa obrigatória quando houver divergência da avaliação indicativa.
6. Atualizar a bateria canônica de certificados para refletir o novo checklist de captura bruta metrológica, preservando o caráter determinístico dos snapshots.

## Consequências

### Positivas

- O fluxo persistido passa a ter rastreabilidade entre dado bruto, contexto metrológico, avaliação assistida e decisão oficial.
- A decisão oficial fica mais auditável, porque o sistema registra alinhamento, divergência e justificativa de forma explícita.
- A UI e os contracts compartilhados deixam de depender de campos puramente demonstrativos para assistência decisória.
- Os snapshots canônicos passam a cobrir a presença do gate metrológico no certificado determinístico.

### Limitações honestas

- A decisão indicativa continua assistiva e não substitui o cálculo oficial final do certificado.
- A avaliação da Portaria 157 é indicativa e depende de dados completos/coerentes para não cair em estado parcial ou bloqueado.
- A trilha continua sem assinatura digital qualificada externa para a decisão/revisão.
- A conformidade PDF/A formal segue dependente de validação externa, apesar da bateria de snapshots estar sincronizada.
