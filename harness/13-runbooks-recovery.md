# 13 — Runbooks de recuperação operacional

> **P0-9**: o desenho cobria **detecção e bloqueio** (gates 3, 4 em `05-guardrails.md`), mas não detalhava **restauração e resposta**. Este arquivo fecha esse gap.
>
> Cada runbook é versionado, treinado em *drill* periódico e arquivado em `compliance/runbooks/`.

## Convenções

- **RTO** (Recovery Time Objective): tempo-alvo para retomar operação.
- **RPO** (Recovery Point Objective): janela máxima de dados aceitável perder.
- **Dispatcher**: quem autoriza a execução.
- **Executor**: quem efetivamente roda os comandos.
- Todo runbook registra evidência em `compliance/runbooks/executions/<YYYY-MM-DD>-<slug>/`.

---

## Runbook R1 — Rotação de chave KMS comprometida

**Trigger**: alerta de chave exposta (commit vazado, acesso indevido ao KMS, SIEM aponta uso anômalo).

**Impacto**: toda assinatura de pacote normativo e de checkpoint de audit feita com a chave comprometida fica suspeita.

**Dispatcher**: `lgpd-security` + `product-governance`.
**Executor**: operador de infra com permissão KMS.

**RTO**: 4h. **RPO**: 0 (nenhum dado perdido; apenas re-assinatura).

### Passos

1. **Contenção** (minuto 0–15):
   - Revogar (`disable`, não `delete`) a chave comprometida no KMS.
   - Girar secrets em `apps/api` que referenciam a chave.
   - Pausar pipeline de assinatura de novos pacotes normativos.

2. **Nova chave** (minuto 15–60):
   - Gerar chave KMS nova (política least-privilege, multi-region, grant auditado).
   - Registrar criação em `compliance/legal-opinions/kms-rotation-<data>.md`.

3. **Re-assinatura de artefatos vigentes** (hora 1–3):
   - Re-assinar todos os `compliance/normative-packages/approved/` com a nova chave.
   - Atualizar `releases/manifest.yaml` com novas assinaturas (hash do conteúdo permanece; só a assinatura muda).
   - **Certificados históricos não são alterados** — sua assinatura original continua válida; apenas o processo de verificação agora aceita ambas as chaves até `delete` da antiga.

4. **Checkpoint do audit log** (hora 3–3.5):
   - Emitir novo checkpoint assinado com a nova chave.
   - Validar hash-chain contínua entre último checkpoint antigo e o novo.

5. **Validação** (hora 3.5–4):
   - Boot do `apps/api` carrega pacote, valida com nova chave.
   - Smoke test: emitir certificado dogfood e verificar QR.
   - Rodar `evals/regulatory/` completo.

6. **Post-mortem** (D+7):
   - Incidente documentado em `compliance/incidents/<slug>.md`.
   - Eventual comunicação a clientes (coordenada com jurídico).
   - ADR se o vetor de comprometimento exige mudança de política.

### Drill

- **Frequência**: trimestral.
- **Ambiente**: staging com KMS espelhado.
- **Critério de sucesso**: RTO respeitado; zero falso-positivo em verificação de certificado histórico.

---

## Runbook R2 — Hash-chain divergente no audit log

**Trigger**: job diário (`Gate 3` em `05-guardrails.md`) detecta hash inconsistente vs checkpoint assinado.

**Impacto**: trilha imutável sob suspeita; emissão freeze global até análise.

**Dispatcher**: `product-governance`.
**Executor**: `db-schema` + `lgpd-security`.

**RTO**: 8h. **RPO**: até o último checkpoint válido (tipicamente 24h).

### Passos

1. **Freeze global** (minuto 0):
   - Banner de "emissão temporariamente indisponível — auditoria em curso".
   - `apps/api` passa a recusar emissões novas (`503 AUDIT_INTEGRITY_CHECK`).
   - Sync do Android continua armazenando offline (não perde dado).

2. **Identificação do ponto de divergência** (minuto 0–60):
   - Binary search entre último checkpoint válido e checkpoint corrompido.
   - Isolar o intervalo com linhas suspeitas.

3. **Quarentena** (hora 1–2):
   - Copiar linhas do intervalo suspeito para `compliance/quarantine/<data>/`.
   - **Não deletar** nada do log original.

4. **Forense** (hora 2–6):
   - Análise: substituição maliciosa, *race condition* legítimo, bug de aplicação, falha de storage?
   - Envolve `lgpd-security` se houver suspeita de acesso indevido.
   - Se malicioso: abre incidente LGPD formal; aciona jurídico.

5. **Reconstrução** (hora 6–7.5):
   - Se bug: aplicar fix, replay dos eventos válidos, regerar chain a partir do último checkpoint válido.
   - Se malicioso: chain reconstruída preserva log original + anotação formal; nada é apagado.
   - Novo checkpoint emitido (R1 se precisar rotação de chave).

6. **Unfreeze** (hora 7.5–8):
   - Smoke test: emissão dogfood.
   - Verificação da nova cadeia pelo job de integridade.
   - Remoção do banner.

7. **Comunicação** (D+1 a D+7):
   - Cliente afetado: notificação obrigatória.
   - Anatel/órgãos reguladores: avaliação caso a caso com jurídico.

### Drill

- **Frequência**: semestral.
- **Cenário**: injetar corrupção em staging, medir tempo até detecção + reconstrução.

---

## Runbook R3 — Violação de WORM / object lock

**Trigger**: smoke test pós-deploy ou audit scan detecta bucket sem retenção imutável configurada.

**Impacto**: certificados e checkpoints do intervalo podem ter sido teoricamente modificados ou deletados.

**Dispatcher**: `product-governance`.
**Executor**: operador de infra + `db-schema`.

**RTO**: 2h. **RPO**: depende do último backup offline (tipicamente 24h).

### Passos

1. **Snapshot imediato** (minuto 0–10):
   - Listar todos os objetos do bucket afetado com hash.
   - Comparar com manifest assinado anterior.

2. **Freeze de releases** (minuto 0):
   - Pipeline de release pausada.
   - Novos uploads bloqueados até política restaurada.

3. **Restaurar política** (minuto 10–30):
   - Reaplicar `Object Lock` / `Bucket Lock` / `Immutable Blob` conforme provider.
   - IaC (Terraform) revisado para garantir drift não reintroduz.

4. **Auditar deltas** (minuto 30–90):
   - Para cada objeto divergente: verificar se foi realmente alterado/deletado.
   - Reconciliar com backup offline (S3 Glacier / Azure Archive / GCS Coldline).

5. **Restauração** (minuto 90–120):
   - Restaurar objetos ausentes do backup.
   - Assinar manifest novo consolidando estado restaurado.

6. **Validação** (minuto 120):
   - Re-verificar QR de amostra de certificados afetados.
   - Retomar releases.

7. **Post-mortem**: ADR obrigatória sobre a falha de configuração + adição de teste em IaC review.

### Drill

- **Frequência**: semestral.
- **Cenário**: provisionar bucket sem lock em staging; job deve detectar em < 10 min.

---

## Runbook R4 — Disaster recovery de normative package

**Trigger**: `apps/api` falha ao carregar pacote normativo por corrupção, assinatura inválida ou ausência do arquivo.

**Impacto**: emissão indisponível até recuperação.

**Dispatcher**: `regulator` + `product-governance`.
**Executor**: `backend-api`.

**RTO**: 1h. **RPO**: 0 (pacote é imutável e replicado).

### Passos

1. **Identificação** (minuto 0–5):
   - Logs de boot apontam `hash_mismatch` ou `signature_invalid`.
   - `apps/api` falha *fail-closed*: não emite.

2. **Recuperação do storage WORM primário** (minuto 5–20):
   - `compliance/normative-packages/approved/<version>/` em S3/GCS/Azure imutável.
   - Download + validação de hash vs `releases/manifest.yaml`.

3. **Fallback para backup secundário** (minuto 20–35):
   - Se primário corrompido: storage frio/offline (Glacier, tape, ou cópia fora da cloud primária).
   - Validação de assinatura KMS.

4. **Fallback final: recompilação a partir de drafts aprovados** (minuto 35–55):
   - Só se primário e secundário falharem.
   - Pipeline de assinatura executa novamente contra a última ADR aprovada.
   - `regulator` valida que o pacote recompilado é idêntico ao esperado.

5. **Validação e retomada** (minuto 55–60):
   - Boot do `apps/api` carrega pacote restaurado.
   - Emissão dogfood + verificação QR.
   - Alerta encerrado.

### Drill

- **Frequência**: semestral.
- **Cenário**: corromper propositalmente o pacote em staging; medir RTO.

---

## Governança dos runbooks

- **Versionamento**: cada runbook tem `version` no frontmatter; mudança exige ADR.
- **Drill calendar**: `compliance/runbooks/drill-schedule.yaml` lista próximas execuções.
- **Execução real**: sempre arquiva evidência em `compliance/runbooks/executions/`.
- **Revisão**: anual completa; após incidente real, revisão imediata do runbook aplicável.
- **Propriedade**: `product-governance` coordena; `lgpd-security` co-assina R1 e R2.

## Não-objetivos

- Runbooks **não** cobrem BCP/DR de infra genérica (rede, VPC, banco primário) — isso fica em `infra/runbooks/`.
- Runbooks **não** substituem *incident response* formal — orquestram a parte regulatória/metrológica específica.
