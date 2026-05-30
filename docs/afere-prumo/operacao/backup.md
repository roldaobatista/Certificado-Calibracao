---
owner: <responsavel-backup>
ultima-conferencia: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 120
proposito: politica de backup com escopo, frequencia, retencao, restore e teste
---

<!-- proposito: politica de backup (o que e copiado, com que frequencia, onde mora, como restaurar) | renomear-para: docs/operacao/backup.md -->

# Política de Backup — <nome-do-projeto>

> **Backup** = cópia de segurança dos dados, guardada em outro lugar, para usar se o original for perdido ou corrompido. Esta política diz **o que** é copiado, **quando**, **por quanto tempo guardamos** e **quem** valida.

## 1. Escopo

O que entra no backup (e o que NÃO entra):

| Categoria | Inclui no backup? | Observação |
|---|---|---|
| Banco de dados de produção | sim | dump completo + WAL (write-ahead log, registro contínuo de mudanças) |
| Arquivos enviados pelo cliente (uploads) | sim | imagens, PDFs, anexos |
| Configurações da aplicação | sim | `.env` cifrado, configs de provedor |
| Segredos (chaves de API, certificados) | sim, em cofre separado | nunca no mesmo bucket dos dados |
| Logs de aplicação | sim, com retenção curta | úteis para auditoria pós-incidente |
| Caches reconstruíveis (Redis, CDN) | não | regerar a partir da fonte |
| Diretório `node_modules` / artefatos de build | não | regerar a partir do código |

Exemplo preenchido: `banco-producao-postgres-15` — dump diário via `pg_dump` + WAL contínuo via `pgbackrest`.

## 2. Frequência

| Categoria | Frequência | Tipo |
|---|---|---|
| Banco de produção | diário | full + WAL contínuo |
| Arquivos de cliente | diário | incremental |
| Configs e segredos | a cada mudança | versionado em cofre |
| Snapshot semanal consolidado | semanal | full de tudo |
| Snapshot mensal arquivado | mensal | full, congelado |

## 3. Retenção (quanto tempo guardamos)

| Tipo | Retenção | Justificativa |
|---|---|---|
| Diário | 30 dias | recuperação rápida de erro recente |
| Semanal | 12 semanas | cobrir trimestre |
| Mensal | 12 meses | conformidade contratual |
| Anual | 5 anos | obrigação fiscal (NF-e, Lei 8.846/94) |

## 4. Localização — regra 3-2-1

Manter sempre:
- **3** cópias dos dados (1 original + 2 backups)
- em **2** mídias diferentes (ex: disco do servidor + storage de objetos S3)
- com **1** cópia offsite (em região geográfica diferente, fora do datacenter principal)

Exemplo preenchido:
- Cópia 1 (original): banco em `<provedor-cloud>` região `sa-east-1`.
- Cópia 2 (online): bucket `s3://backup-<projeto>-sa-east-1` (mesma região, mídia diferente).
- Cópia 3 (offsite): bucket `s3://backup-<projeto>-us-east-1` (região diferente, replicação cross-region ativa).

## 5. Criptografia

- **Em trânsito** (durante a cópia): TLS 1.2+ obrigatório entre origem e destino.
- **Em repouso** (guardado no destino): AES-256, chaves gerenciadas em KMS dedicado.
- Chaves de criptografia têm rotação anual (ver `docs/seguranca/rotacao-credenciais.md`).
- Backup NUNCA gravado em texto claro, nem em ambiente de homologação.

## 6. Teste de restore

> Backup que nunca foi restaurado não é backup, é esperança.

- **Frequência mínima:** mensal.
- **Executor:** plantonista do mês (ver `on-call.md`).
- **Procedimento:** runbook `docs/operacao/runbooks/restaurar-backup.md` (instanciar via `runbook.template.md`).
- **Aceite:** restore termina em < RTO definido (ver `disaster-recovery.md`), dados validados por checksum + 3 queries de sanidade.
- **Registro:** linha em `docs/operacao/historico-restore.md` com data, executor, tempo gasto, resultado.
- **Aprendizado obrigatório:** todo teste de restore gera um registro de lição — o que correu mal, o que foi mais lento que o esperado, qual passo do runbook faltou. Se o restore falhou ou estourou o RTO, abrir post-mortem leve (`post-mortem.template.md`). Mesmo no sucesso, anotar 1 melhoria na coluna "lição" do `historico-restore.md`. Backup testado sem aprender nada é teste desperdiçado.

## 7. Monitoramento

- Alerta CRÍTICO se último backup diário falhar ou não concluir em 6h.
- Alerta ALTO se replicação cross-region atrasar mais de 2h.
- Alerta MÉDIO se uso de storage do bucket de backup crescer >20% mês-a-mês (possível vazamento de retenção).
- Canal de alerta: `#alertas-ops` + paging do plantonista (ver `on-call.md`).

## 8. Responsáveis

| Papel | Quem | O que faz |
|---|---|---|
| Dono do processo | <nome-do-DPO-ou-tech-lead> | aprova mudanças na política, revisa anualmente |
| Executor | plantonista da semana | acompanha alertas, executa restore de teste mensal |
| Auditor | <nome-do-auditor-interno> | verifica trimestralmente se a política está sendo seguida |

## 9. Histórico de revisões

| Data | Revisor | Mudança |
|---|---|---|
| 2026-05-28 | <nome> | criação inicial |
