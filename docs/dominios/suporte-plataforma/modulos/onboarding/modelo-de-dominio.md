---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/modelo-de-dominio.md
  - docs/comum/governanca-modelo-comum.md
---

# Modelo de domínio — Módulo Onboarding

> Entidades específicas do módulo de implantação. Tenant (entidade comum) referenciada, não duplicada.

---

## Entidades

### Implantacao

- **Atributos obrigatórios:** id, tenant_id (FK comum), responsavel_interno_id (FK usuário interno Aferê), status (enum), data_criacao, data_aceite (nullable).
- **Atributos opcionais:** observacoes, data_go_live_prevista.
- **Invariantes de agregado:** `INV-TENANT-001`; `INV-040` (status só avança em ordem definida).
- **Relacionamento com entidades comuns:** 1:1 com Tenant (sandbox + produção).
- **Ciclo de vida:** criada quando tenant nasce → status muda → imutável após "concluída" + termo assinado (reabertura exige nova OS de implantação).

### EtapaImplantacao

- **Atributos obrigatórios:** id, implantacao_id, ordem, nome, status (não_iniciada / em_andamento / pendente_cliente / concluída / pulada), data_conclusao (nullable).
- **Atributos opcionais:** observacoes, responsavel_etapa (pode diferir do responsável da implantação), anexos.
- **Invariantes:** `INV-041` (etapa pulada exige justificativa).
- **Ciclo de vida:** instanciada do template padrão na criação da implantação.

### ChecklistTemplate

- **Atributos obrigatórios:** id, nome, etapas_padrao (JSONB com ordem e nomes).
- **Ciclo de vida:** configurável globalmente (admin Aferê); versionado.

### ImportacaoInicial

- **Atributos obrigatórios:** id, implantacao_id, tipo (clientes / produtos / serviços / equipamentos / estoque), arquivo_path (Backblaze B2), status (validando / validado / executando / concluído / falhou), data, executor_id.
- **Atributos opcionais:** resumo (criados, duplicados, ignorados), hash_arquivo (idempotência).
- **Invariantes:** `INV-006` (idempotência por hash), `INV-TENANT-001`.

### InconsistenciaMigracao

- **Atributos obrigatórios:** id, importacao_id, linha_arquivo, campo, severidade (alerta / erro), descricao, status (aberta / resolvida / aceita).
- **Atributos opcionais:** dado_original, sugestao, justificativa_resolucao, resolvido_por, data_resolucao.
- **Invariantes:** `INV-042` (resolução exige justificativa auditável).

### TreinamentoRegistrado

- **Atributos obrigatórios:** id, implantacao_id, data, duracao_minutos, modulos_cobertos (array), participantes (array de pessoas do tenant).
- **Atributos opcionais:** anexos (slides, gravações), observacoes.

### ValidacaoAmbiente

- **Atributos obrigatórios:** id, implantacao_id, data, resultado (passou / falhou), checks_executados (JSONB com cada check + resultado).
- **Invariantes:** `SEC-001` (RLS), `SEC-KMS-*` (KMS configurado).

### TermoAceite

- **Atributos obrigatórios:** id, implantacao_id, data_geracao, pdf_path (Backblaze B2, WORM), data_assinatura (nullable), assinante_nome, assinante_documento.
- **Atributos opcionais:** assinatura_digital_blob (se A3), hash_pdf.
- **Invariantes:** `INV-043` (imutável após assinatura), `INV-001` (trilha WORM), retenção conforme `docs/conformidade/comum/retencao-matriz.md`.

### Sandbox

- **Atributos obrigatórios:** id, tenant_id, status (provisionando / ativo / promovido / arquivado), data_provisao.
- **Atributos opcionais:** data_promocao, snapshot_promovido_id.
- **Invariantes:** `INV-TENANT-001` (RLS isolado igual produção), ADR-0002.

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| Implantacao | EtapaImplantacao, ImportacaoInicial, InconsistenciaMigracao, TreinamentoRegistrado, ValidacaoAmbiente, TermoAceite | INV-040, INV-041, INV-042, INV-043, INV-TENANT-001 |
| Sandbox | (próprio) | INV-TENANT-001 |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| StatusImplantacao | enum: não_iniciada, em_andamento, pendente_cliente, concluída | Sim |
| SeveridadeInconsistencia | enum: alerta, erro | Sim |
| TipoImportacao | enum: clientes, produtos, serviços, equipamentos, estoque | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `Onboarding.ImplantacaoCriada` | nova implantação cadastrada | `{implantacao_id, tenant_id}` | configurações-sistema, billing, notificações |
| `Onboarding.EtapaConcluida` | etapa muda pra concluída | `{implantacao_id, etapa_id, ordem}` | notificações, métricas |
| `Onboarding.ImportacaoConcluida` | import finaliza | `{implantacao_id, tipo, resumo}` | clientes, produtos, estoque, equipamentos |
| `Onboarding.ValidacaoFalhou` | check automático negativo | `{implantacao_id, checks_falhos}` | notificações P1 |
| `Onboarding.TermoAssinado` | cliente assina | `{implantacao_id, data_assinatura}` | billing (libera produção), auditoria |
| `Onboarding.SandboxPromovido` | sandbox vira produção | `{tenant_id, snapshot_id}` | todos os módulos |

---

## Comandos (entradas)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `criarImplantacao` | UI/API | tenant existe | implantação criada + checklist instanciado |
| `executarImport` | UI | arquivo validado | import rodado + inconsistências geradas |
| `marcarEtapaConcluida` | UI | usuário tem permissão | status etapa = concluída + evento |
| `rodarValidacaoAmbiente` | UI | implantação em fase final | ValidacaoAmbiente persistida |
| `gerarTermo` | UI | validação passou | PDF gerado em WORM |
| `assinarTermo` | UI | termo gerado | data_assinatura + status implantação = concluída |
| `promoverSandbox` | UI | termo assinado + validação OK | snapshot copiado pro tenant produtivo |

---

## Schema físico

Ver `../schema-banco.md` quando criado pós ADR-0001.

## Como este modelo evolui

- Entidade nova → governanca-modelo-comum.md decide se vai pra comum ou módulo.
- Eventos novos → bump CHANGELOG + atualizar `integracoes-inter-modulos.md`.
