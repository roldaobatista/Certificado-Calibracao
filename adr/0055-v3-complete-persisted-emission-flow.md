# ADR 0055 — Fechamento da V3 completa no fluxo persistido de emissao

## Status

Aceito

## Contexto

Com V1 e V2 persistidos, a principal lacuna do nucleo operacional era a metade final do fluxo de emissao. A leitura canônica ja mostrava dry-run, previa, workflow de revisao, fila de assinatura e trilha de auditoria, mas ainda sem depender de OS reais do tenant.

## Decisao

Adotar o fechamento conjunto de `V3.2` a `V3.5` sobre a mesma base persistida de `service_orders`, evitando criar tabelas paralelas de transicao:

1. `service_orders` passa a concentrar os dados tecnicos essenciais da OS, o parecer da revisao, a atribuicao do signatario e os metadados da emissao oficial.
2. Eventos criticos de emissao passam a viver em `emission_audit_events`, com hash-chain append-only por OS.
3. O backend deriva dry-run, previa, workflow, fila e trilha a partir da OS persistida e do onboarding real do tenant, preservando `?scenario=` apenas como fallback.
4. A aprovacao tecnica e a emissao oficial ganham endpoints de escrita dedicados, ambos protegidos por sessao e guardrails de papel, MFA e prerequisitos de onboarding.
5. O front passa a tratar o `item` persistido como ancora de navegacao entre as paginas da V3, evitando regressao silenciosa para cenarios estaticos.

## Consequencias

### Positivas

- Fecha o primeiro caminho real de OS para certificado emitido dentro do escopo V3.
- Reaproveita contratos e telas canonicas ja existentes, reduzindo duplicacao entre modo demonstrativo e modo persistido.
- Torna auditavel quem revisou, quem assinou, quando a emissao ocorreu e qual hash documental foi produzido.

### Limitacoes honestas

- A emissao ainda produz hash e metadados de documento, nao um renderer PDF/A final com assinatura criptografica externa.
- O QR publico permanece preparado via token e host persistidos, mas a verificacao publica continua pertencendo a V4.
- O audit trail V3 cobre o nucleo critico da emissao; exportacao operacional, filtros avancados e evidencias binarias continuam evolucoes posteriores.
