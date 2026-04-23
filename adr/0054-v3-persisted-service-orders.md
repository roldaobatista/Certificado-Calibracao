# ADR 0054 — Ordem de servico persistida para V3.1

## Status

Aceito

## Contexto

Depois de V2, usuarios, clientes, padroes, procedimentos e equipamentos ja existem no banco, mas a ordem de servico ainda e tratada apenas como leitura canonica baseada em cenarios. O roadmap foundation-first exige que `V3.1` abra o fluxo real da OS antes de resultados tecnicos, revisao e emissao oficiais.

## Decisao

Adotar uma camada persistida de ordem de servico para V3.1 com os seguintes pilares:

1. `packages/db/prisma/schema.prisma` passa a modelar `service_orders` com tenancy explicita e vinculos a cliente, equipamento, procedimento, padrao principal, tecnico executor e revisor atribuido.
2. A migracao V3.1 habilita RLS e policies na nova tabela, mantendo o mesmo padrao fail-closed das fatias anteriores.
3. O backend centraliza a persistencia em uma camada propria de emissao, separada dos cadastros V2, preservando `?scenario=` apenas como fallback canonico.
4. `GET /emission/service-order-review` reutiliza o contrato compartilhado atual e, sem `scenario`, monta o catalogo a partir das OS persistidas do tenant autenticado.
5. `POST /emission/service-order-review/manage` passa a abrir, editar e transicionar a OS real pelo ciclo basico da V3.1.
6. `apps/web` encaminha o cookie atual para a rota de OS e expoe formularios simples de abertura/manutencao sobre dados reais.

## Consequencias

### Positivas

- Fecha a principal lacuna entre os cadastros V2 e o fluxo operacional central.
- Reaproveita a tela e o contrato canonicos de OS sem criar uma segunda experiencia paralela.
- Prepara V3.2+ para usar OS reais como fonte dos resultados tecnicos, revisao e emissao.

### Limitacoes honestas

- V3.1 ainda nao persiste leituras metrologicas, anexos binarios, assinatura eletrônica nem audit trail critico append-only do fluxo regulado.
- O ciclo de OS cobre criacao, manutencao e status basicos; regras mais finas de revisao/assinatura continuam pertencendo a V3.3+.
- O front usa formularios server-driven simples, sem paginação server-side, autosave ou timeline expandida por eventos.
