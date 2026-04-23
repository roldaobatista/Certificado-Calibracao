# ADR 0056 — Fechamento da V4 no portal, QR público e reemissão controlada

## Status

Aceito

## Contexto

As leituras canônicas do portal e do QR já existiam, mas ainda eram majoritariamente demonstrativas. A V4 precisava abrir acesso externo real sem romper o fail-closed regulatório nem enfraquecer a trilha crítica construída na V3.

## Decisão

Adotar o fechamento conjunto de `V4.1` a `V4.4` sobre a mesma base persistida da emissão:

1. `certificate_publications` passa a ser a fonte de verdade para publicações públicas e autenticadas do certificado, incluindo supersessão, hash anterior, token público e notificação.
2. `emission_audit_events` passa a persistir `metadata` JSON para sustentar a hash-chain dos eventos de reemissão sem depender de reconstrução heurística.
3. O portal autenticado reutiliza a sessão HTTP-only do backend, mas restringe a leitura real a usuários `external_client` vinculados ao e-mail do cliente.
4. `?scenario=` permanece apenas como fallback demonstrativo; sem ele, as rotas V4 respondem sobre dados reais do tenant autenticado.
5. A verificação pública passa a distinguir `token_mismatch`, `certificate_not_found`, `invalid_audit_trail` e `missing_reissue_evidence`, preservando fail-closed.
6. O canal mobile/offline permanece como extensão operacional controlada na V4: contratos, outbox Android e fila humana precisam continuar verdes, mas sem reabrir o núcleo persistido do fluxo central.

## Consequências

### Positivas

- Fecha o primeiro caminho externo real do produto: cliente autenticado, viewer autenticado, QR público e reemissão rastreável.
- Elimina a dependência de payloads estáticos nas páginas centrais do portal quando há sessão válida.
- Torna verificável o histórico de reemissão sem perder o certificado anterior nem quebrar a autenticidade pública.

### Limitações honestas

- O canal mobile/offline continua sustentado por contratos, lógica Android e fila humana canônica; a ingestão persistida server-side do sync não foi expandida nesta fatia.
- O viewer autenticado continua expondo resumo autenticado do certificado; distribuição binária integral e sharing transacional seguem evoluções posteriores.
- A verificação pública depende de `certificate` + `token` e não substitui controles humanos em casos-limite regulatórios.
