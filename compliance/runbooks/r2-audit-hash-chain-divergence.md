---
id: R2
version: 1
status: active
owner: lgpd-security
rto: 8h
rpo: "até o último checkpoint válido"
dispatcher: product-governance
executor: db-schema + lgpd-security
---

# R2 — Hash-chain divergente no audit log

## Trigger

Executar quando o verificador de hash-chain detectar divergência entre audit log e checkpoint assinado:

- job diário de integridade falha;
- `pnpm audit-chain:verify <arquivo.jsonl>` retorna divergência;
- checkpoint assinado não corresponde ao estado reconstruído;
- alerta de storage indica alteração inesperada em artefato de auditoria.

## Impacto

A trilha imutável fica sob suspeita. Emissão regulada deve congelar imediatamente até delimitar a divergência e provar integridade do intervalo afetado. Sync Android pode continuar offline, mas nenhuma emissão nova deve ser finalizada.

## Papéis

- Dispatcher: `product-governance`.
- Executor: `db-schema` e `lgpd-security`.
- Apoio: `backend-api` para freeze de emissão; `legal-counsel` se houver suspeita de acesso indevido ou incidente LGPD.
- Revisão técnica: `senior-reviewer` em correção de código crítico.

## Passos

1. Ativar freeze global de emissão com erro `503 AUDIT_INTEGRITY_CHECK`.
2. Exibir banner operacional de auditoria em curso no back-office.
3. Preservar sync Android offline sem publicar emissões.
4. Identificar último checkpoint válido e primeiro checkpoint divergente.
5. Executar busca binária no intervalo para localizar o primeiro evento divergente.
6. Copiar intervalo suspeito para `compliance/quarantine/<YYYY-MM-DD>-audit-hash-chain/`.
7. Não apagar, sobrescrever ou compactar o log original.
8. Classificar causa provável: adulteração, bug, race condition, falha de storage ou erro operacional.
9. Se houver suspeita maliciosa ou dado pessoal exposto, abrir incidente LGPD e acionar `legal-counsel`.
10. Corrigir código ou configuração causadora antes de reconstruir.
11. Reconstruir a cadeia a partir do último checkpoint válido, preservando o log original e anexando anotação formal.
12. Emitir novo checkpoint assinado.
13. Remover freeze somente após validação completa.

## Validação

1. Rodar `pnpm audit-chain:verify <audit-restaurado.jsonl>`.
2. Rodar `pnpm check:all`.
3. Rodar `pnpm test:tenancy` se a divergência tocar paths de tenancy, sync ou emissão.
4. Confirmar que novo checkpoint é verificável com chave vigente.
5. Emitir certificado dogfood em staging e verificar QR.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r2-audit-hash-chain-divergence/`:

- `summary.md` com janela afetada, causa, responsáveis e decisão de unfreeze;
- saída do verificador antes e depois;
- hashes dos checkpoints envolvidos;
- cópia do intervalo suspeito em quarentena, quando permitido sem dados pessoais sensíveis;
- PR de correção;
- parecer jurídico quando aplicável.

## Drill

- Frequência: semestral.
- Ambiente: staging.
- Cenário: injetar corrupção controlada em linha de audit log e medir detecção, freeze, quarentena, reconstrução e unfreeze.
- Critério de sucesso: RTO de 8h respeitado e nenhum evento apagado.

## Revisão

Revisar após qualquer divergência real, alteração em `packages/audit-log/**`, mudança de storage WORM ou troca de política de checkpoint. Mudança substantiva exige ADR.
