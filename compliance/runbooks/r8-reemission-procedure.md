---
id: R8
version: 1
status: active
owner: regulator
rto: 2h
rpo: "0"
dispatcher: regulator
executor: backend-api
---

# R8 — Procedimento de reemissão controlada

## Trigger

Executar quando um certificado válido precise ser reemitido sem alterar o resultado metrológico original:

- certificado original perdido, danificado fisicamente ou não entregue ao cliente;
- erro de impressão ou formatação do documento (PDF/A) que não afete o conteúdo metrológico;
- reemissão após revogação controlada (quando a causa raiz foi corrigida e nova calibração não é necessária);
- determinação regulatória ou solicitação formal do cliente com motivo documentado;
- mudança de razão social ou endereço do laboratório que não altere o escopo acreditado.

## Impacto

A reemissão cria um novo documento com numeração/ID distinto, vinculado ao original através da trilha de audit. O certificado original permanece válido até a entrega do novo, salvo em casos de revogação. O cliente deve receber o novo documento por canal oficial. A trilha deve preservar a rastreabilidade completa entre original e reemissão.

## Papéis

- Dispatcher: `regulator`.
- Executor: `backend-api`.
- Apoio: `metrology-auditor` para confirmar que o resultado metrológico não foi alterado; `legal-counsel` se houver mudança contratual ou notificação obrigatória; `db-schema` para validação de trilha imutável.
- Comunicação: `product-governance` coordena entrega ao cliente.

## Passos

1. Verificar o certificado original no sistema: status (ativo, revogado, expirado), dados metrológicos e identidade do signatário original.
2. Documentar o motivo da reemissão em `compliance/incidents/<YYYY-MM-DD>-reemission-<original-id>.md`.
3. Confirmar que a causa do reemissão não altera o resultado metrológico (ex.: não é permitido reemitir com valores diferentes sem nova calibração).
4. Obter aprovação de `regulator` ou `metrology-auditor` para prosseguir.
5. Gerar novo certificado com ID distinto, mantendo o mesmo conteúdo metrológico do original.
6. Incluir no novo certificado uma cláusula de "reemissão" indicando o ID do documento original e o motivo.
7. Registrar evento de reemissão no audit trail com: ID original, ID novo, motivo, timestamp, aprovador.
8. Atualizar o portal do cliente para que ambos os certificados (original e reemissão) sejam consultáveis, com vínculo explícito.
9. Se o original estava revogado, atualizar o QR do original para referenciar a reemissão.
10. Entregar o novo certificado ao cliente por canal oficial com comprovante de recebimento.
11. Se o motivo for perda/dano do documento físico, registrar declaração do cliente quando exigido pela política interna.

## Validação

1. Consultar QR do certificado original e confirmar vínculo com a reemissão (se aplicável).
2. Consultar QR do novo certificado e confirmar que aponta para o original.
3. Verificar que o audit trail contém o evento de reemissão com hash consistente.
4. Comparar conteúdo metrológico do novo certificado com o original e confirmar identidade (exceto ID, data de emissão e cláusula de reemissão).
5. Rodar `pnpm check:all`.
6. Emitir certificado dogfood em staging e executar workflow de reemissão end-to-end.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r8-reemission-<original-id>/`:

- `summary.md` com motivo, aprovador, IDs dos certificados e decisão;
- cópia do certificado original e do novo (ou seus hashes);
- logs do evento de reemissão no audit trail;
- comprovante de entrega ao cliente;
- parecer de `metrology-auditor` confirmando inalteração do resultado metrológico;
- declaração do cliente quando aplicável.

## Drill

- Frequência: anual.
- Ambiente: staging.
- Cenário: emitir certificado dogfood, simular perda pelo cliente, executar reemissão controlada, validar vínculo no QR e no audit trail.
- Critério de sucesso: RTO de 2h respeitado, QR atualizado em menos de 5 minutos, conteúdo metrológico inalterado, trilha de audit verificável.

## Revisão

Revisar após reemissão real, alteração no fluxo de emissão, mudança na norma regulatória de reemissão (Inmetro/Cgcre) ou após drill. Mudança substantiva exige ADR.
