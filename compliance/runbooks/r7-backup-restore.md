---
id: R7
version: 1
status: active
owner: db-schema
rto: 8h
rpo: "até o último backup validado"
dispatcher: product-governance
executor: db-schema + operador de infra
---

# R7 — Restauração de backup

## Trigger

Executar quando houver perda, corrupção ou indisponibilidade dos dados de produção:

- falha de storage primário ou database corruption;
- ransomware ou deleção acidental em ambiente de produção;
- falha de replicação com divergência irreversível;
- disaster recovery após incidente de segurança (acionar `R6` em paralelo se aplicável);
- necessidade de rollback após deploy com migração destrutiva falha.

## Impacto

Certificados, trilhas de audit, registros de qualidade e dados de clientes podem estar parcial ou totalmente perdidos. O RPO depende da última cópia íntegra validada. A emissão regulada deve permanecer congelada até a restauração completa e validação de integridade. Dados restaurados de backup anterior podem perder transações mais recentes, exigindo reconciliação manual.

## Papéis

- Dispatcher: `product-governance`.
- Executor: `db-schema` e operador de infra.
- Apoio: `backend-api` para validação de aplicação pós-restauração; `lgpd-security` para verificar que nenhum dado pessoal foi exposto durante o processo; `regulator` para aprovar retorno da emissão.
- Comunicação: `product-governance` coordena status com stakeholders e clientes afetados.

## Passos

1. Congelar emissão regulada e exibir banner operacional de manutenção no back-office.
2. Documentar o incidente em `compliance/incidents/<YYYY-MM-DD>-backup-restore-<slug>.md`.
3. Identificar o escopo exato do dano: quais tabelas, schemas, arquivos ou buckets foram afetados.
4. Selecionar o backup mais recente que passe na validação de integridade (hash do dump, checksum do storage).
5. Provisionar ambiente de restauração isolado (nunca restaurar diretamente sobre produção sem validação intermediária).
6. Restaurar o backup no ambiente isolado e executar `pnpm test:tenancy` e `pnpm check:all`.
7. Validar RLS: confirmar que políticas de tenant isolation estão ativas e corretas.
8. Validar hash-chain do audit log desde o início do backup restaurado até o último evento conhecido antes do incidente.
9. Reconciliar transações perdidas: identificar gap entre último backup e momento do incidente, documentar o que não foi recuperável.
10. Promover o ambiente validado para produção com switch controlado (blue/green ou failover DNS).
11. Reabilitar RLS e confirmar que o role `afere_app` está ativo com `FORCE RLS`.
12. Rodar smoke test de emissão dogfood em staging antes de remover o banner de produção.
13. Remover freeze de emissão apenas com aprovação do dispatcher.

## Validação

1. Rodar `pnpm check:all`.
2. Rodar `pnpm test:tenancy`.
3. Verificar que `pnpm audit-chain:verify` passa no estado restaurado.
4. Confirmar que `pnpm worm-check` não detecta drift em storage regulatório.
5. Validar QR de certificados históricos e emitir certificado dogfood novo.
6. Verificar que RLS está ativo em todas as tabelas multitenant.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r7-backup-restore-<slug>/`:

- `summary.md` com escopo, backup utilizado, RPO alcançado, transações perdidas e decisão de retorno;
- hash/verificação do backup restaurado;
- logs de validação (`pnpm check:all`, `pnpm test:tenancy`, `pnpm audit-chain:verify`);
- evidência de RLS ativa;
- relatório de reconciliação de gap;
- PR de correção da causa raiz.

## Drill

- Frequência: semestral.
- Ambiente: staging com backup isolado.
- Cenário: corromper intencionalmente uma tabela secundária de staging, restaurar do último backup, validar integridade e reconciliar gap.
- Critério de sucesso: RTO de 8h respeitado, RPO documentado, nenhuma perda de audit trail, RLS ativo após restauração.

## Revisão

Revisar após incidente real, alteração na estratégia de backup, troca de provider de infra, mudança no schema de banco ou após drill. Mudança substantiva exige ADR.
