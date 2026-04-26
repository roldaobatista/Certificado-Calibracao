---
id: R5
version: 1
status: active
owner: regulator
rto: 4h
rpo: "0"
dispatcher: regulator + product-governance
executor: backend-api
---

# R5 — Revogação de certificado emitido

## Trigger

Executar quando um certificado já emitido precisar ser invalidado antes do vencimento natural:

- erro metrológico grave detectado após emissão (valor errado, unidade trocada, incerteza subestimada);
- não-conformidade crítica aberta contra a emissão (ex.: segregação de funções violada, signatário sem competência);
- determinação de órgão regulador ou decisão judicial;
- solicitação formal do cliente com motivo técnico justificado;
- fraude ou falsificação detectada no certificado original.

## Impacto

O certificado revogado perde validade imediata. O QR público e o portal do cliente devem refletir o status de revogação. A entidade que recebeu o certificado original precisa ser notificada. Reemissão só é permitida após análise do motivo e, quando aplicável, nova calibração. A trilha de audit deve registrar a revogação com justificativa, decisão e identidade do responsável.

## Papéis

- Dispatcher: `regulator` e `product-governance`.
- Executor: `backend-api`.
- Apoio: `metrology-auditor` para revisão técnica do motivo; `legal-counsel` se houver exposição de dados pessoais ou notificação regulatória; `db-schema` para validação de trilha imutável.
- Comunicação: `product-governance` coordena notificação ao cliente e, se necessário, ao órgão regulador.

## Passos

1. Congelar qualquer reemissão vinculada ao certificado até decisão formal.
2. Documentar o motivo da revogação em `compliance/incidents/<YYYY-MM-DD>-emission-revocation-<certificate-id>.md`.
3. Coletar aprovação escrita de duas pessoas distintas: uma técnica (`metrology-auditor` ou signatário substituto) e uma de governança (`regulator` ou `product-governance`).
4. Registrar evento de revogação no audit trail com: ID do certificado, motivo, timestamp, identidade dos aprovadores, hash do certificado original.
5. Atualizar o status do certificado no banco para `revoked`, mantendo todos os metadados originais inalterados.
6. Atualizar o endpoint público de verificação (QR) para retornar status `revoked` com data e motivo resumido.
7. Notificar o cliente por canal oficial (email registrado no contrato ou portal) com evidência de recebimento.
8. Se o motivo envolver erro metrológico, abrir não-conformidade no módulo de qualidade e vincular à revogação.
9. Se o motivo envolver violação de segurança ou LGPD, acionar `R6 — Security Incident` em paralelo.
10. Descongelar reemissão apenas após correção da causa raiz e nova aprovação.

## Validação

1. Consultar o QR público do certificado revogado e confirmar status `revoked`.
2. Verificar que o audit trail contém o evento de revogação com hash consistente.
3. Rodar `pnpm check:all`.
4. Rodar `pnpm test:tenancy` se a revogação tocou paths de emissão ou audit.
5. Confirmar que certificados históricos não-revogados permanecem com status válido.
6. Emitir certificado dogfood em staging e verificar que o workflow de revogação funciona end-to-end.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r5-emission-revocation-<certificate-id>/`:

- `summary.md` com motivo, aprovadores, decisão de revogação e notificações;
- cópia do certificado original (se não contiver dados pessoais sensíveis) ou seu hash;
- logs do evento de revogação no audit trail;
- comprovante de notificação ao cliente;
- parecer técnico de `metrology-auditor` quando aplicável;
- referência à não-conformidade ou incidente de segurança vinculado.

## Drill

- Frequência: semestral.
- Ambiente: staging.
- Cenário: emitir certificado dogfood, executar revogação com motivo técnico simulado, validar QR, audit trail e notificação.
- Critério de sucesso: RTO de 4h respeitado, QR refletindo status em menos de 5 minutos após revogação, audit trail verificável.

## Revisão

Revisar após incidente real, alteração no fluxo de emissão, mudança na legislação regulatória ou após drill. Mudança substantiva exige ADR.
