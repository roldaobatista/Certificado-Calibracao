# 0090 - Snapshot metrologico imutavel na ordem de servico

## Contexto

Os cadastros de `Equipment` e `Standard` agora aceitam perfis metrologicos canonicos. Isso resolve a modelagem da carteira, mas ainda nao fecha a rastreabilidade temporal da execucao, porque a OS continua dependendo de leitura ao vivo do cadastro ou de campos-resumo derivados.

Para sustentar a engine metrologica real e a auditoria tecnica, a OS precisa congelar o contexto metrologico relevante do instrumento e do padrao no momento da operacao.

## Objetivo

Persistir na `ServiceOrder` um snapshot estruturado de:

- perfil metrologico do equipamento;
- perfil metrologico do padrao principal.

O snapshot deve ser imutavel no sentido historico: mudancas futuras no cadastro nao podem reescrever silenciosamente o contexto de uma OS ja aberta.

## Regras

1. O snapshot e derivado automaticamente no `saveServiceOrder`.
2. O operador nao preenche esse snapshot manualmente.
3. Se o cadastro atual do item possuir perfil metrologico:
   - a OS salva esse perfil como snapshot.
4. Se o cadastro atual nao possuir perfil metrologico:
   - uma OS nova fica sem snapshot;
   - uma OS existente preserva o snapshot anterior quando a referencia continuar a mesma.
5. Se a OS trocar de equipamento ou padrao principal:
   - o snapshot deve acompanhar a nova referencia selecionada;
   - nao pode herdar snapshot do item anterior.

## Escopo desta fatia

- novas colunas JSONB em `service_orders`;
- leitura e escrita dos snapshots na persistencia em memoria e Prisma;
- exposicao dos snapshots e resumos no review persistido;
- exposicao dos resumos na previa persistida;
- testes cobrindo criacao, leitura e preservacao basica.

## Fora de escopo

- usar o snapshot para recalcular automaticamente o certificado;
- bloquear a OS por ausencia de snapshot;
- congelar tambem procedimento, ambiente alvo ou CMC nesta mesma fatia.

## Done when

- `ServiceOrder` persiste `equipmentMetrologySnapshot` e `standardMetrologySnapshot`;
- o review persistido exibe esses snapshots e seus resumos;
- a previa persistida mostra os resumos metrologicos congelados;
- testes comprovam que uma OS criada via `manage` herda os perfis do cadastro.
