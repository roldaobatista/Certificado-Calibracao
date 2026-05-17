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
  - docs/adr/0007-camada-dominio-gerador-spec.md
---

# Modelo de domínio — Módulo Engenharia Técnica

> Entidades específicas. Transversais (Tenant, Usuario, Cliente, OS, Orcamento, Equipamento) ficam em `docs/comum/modelo-de-dominio.md`.

---

## Entidades

### ProjetoTecnico
- **Atributos obrigatórios:** `id`, `tenant_id`, `codigo`, `titulo`, `descricao`, `cliente_id` (FK comum), `status` (rascunho|em_aprovacao|aprovado|obsoleto), `revisao_corrente_id`, `criado_em`, `criado_por`.
- **Atributos opcionais:** `tags`, `categoria` (automação|pesagem|calibração|manutenção|outro), `equipamento_id_principal`.
- **Invariantes:** `INV-TENANT-001`; constraint `UNIQUE (tenant_id, codigo)` (código único por tenant).
- **Ciclo de vida:** criado em rascunho → submetido → aprovado → pode virar obsoleto (não deletado).

### Revisao
- **Atributos:** `id`, `projeto_tecnico_id`, `letra` (A, B, C…), `status` (rascunho|em_aprovacao|aprovada|rejeitada|obsoleta), `motivo_revisao`, `criada_em`, `criada_por`, `aprovada_em`, `aprovador_id`, `assinatura_id` (FK pra registro de assinatura).
- **Imutabilidade:** revisão aprovada é IMUTÁVEL (`INV-001` — trilha WORM). Edição cria revisão nova.

### Desenho
- **Atributos:** `id`, `revisao_id`, `tipo` (desenho|diagrama_eletrico|esquema_ligacao|outro), `titulo`, `arquivo_original_id` (FK Anexo), `arquivo_pdf_id` (FK Anexo opcional), `pagina_referencia`.

### Anexo
- **Atributos:** `id`, `revisao_id`, `nome_original`, `mime_type`, `tamanho_bytes`, `hash_sha256`, `storage_path` (Backblaze B2), `kms_key_id`, `enviado_em`, `enviado_por`, `categoria` (desenho|diagrama|esquema|memorial|calculo|datasheet|outro).
- **Invariantes:** hash imutável; soft-delete apenas (marca obsoleto).

### BOM (LinhaBOM)
- **Atributos:** `id`, `revisao_id`, `posicao`, `componente_id` (FK BibliotecaComponente, nullable se ad-hoc), `descricao_ad_hoc`, `quantidade`, `unidade`, `referencia_desenho` (página/balão), `observacao`.
- **Invariantes:** posição única por revisão.

### BibliotecaComponente
- **Atributos:** `id`, `tenant_id`, `fabricante`, `modelo`, `descricao`, `categoria`, `datasheet_anexo_id`, `preco_referencial`, `unidade_padrao`, `criado_em`, `status` (ativo|deprecado).
- **Invariantes:** combinação (fabricante, modelo) única por tenant; validação anti-duplicidade.

### MemorialDescritivo
- **Atributos:** `id`, `revisao_id`, `escopo`, `premissas`, `solucoes`, `normas_aplicaveis` (lista), `consideracoes_finais`, `gerado_pdf_anexo_id`.
- **Imutável após aprovação da revisão.**

### EspecificacaoTecnica
- **Atributos:** `id`, `revisao_id`, `chave` (capacidade|classe|IP|tensao|faixa…), `valor`, `unidade`, `tolerancia`.

### CalculoTecnico
- **Atributos:** `id`, `revisao_id`, `titulo`, `valores_chave` (JSON: ex {carga_max: 5000, fator_seguranca: 2.5}), `planilha_anexo_id`, `metodo`, `norma_referencia`.

### AprovacaoTecnica
- **Atributos:** `id`, `revisao_id`, `aprovador_id`, `decidida_em`, `decisao` (aprovada|rejeitada), `comentario`, `tipo_assinatura` (interna|icp_brasil), `assinatura_payload` (JSON com nome, CREA, IP, hash), `bpm_pendencia_id` (nullable — se passou por BPM).
- **Imutável.**

### RelacaoProjetoEntidade
- **Atributos:** `id`, `revisao_id`, `entidade_tipo` (os|orcamento|equipamento|contrato|projeto_gestao), `entidade_id`, `papel` (projeto_origem|projeto_referencia), `criado_em`.
- **Permite rastreabilidade bidirecional.**

### HistoricoAlteracao
- **Atributos:** `id`, `entidade_tipo` (projeto|revisao|bom|memorial|...), `entidade_id`, `usuario_id`, `timestamp`, `acao` (criar|editar|aprovar|rejeitar|marcar_obsoleto), `diff_json`, `motivo`.

---

## Agregados

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| ProjetoTecnico | ProjetoTecnico, Revisao, Desenho, Anexo, BOM, MemorialDescritivo, EspecificacaoTecnica, CalculoTecnico | tenant isolation; revisão aprovada imutável |
| BibliotecaComponente | BibliotecaComponente | dedup por fabricante+modelo; tenant isolation |
| AprovacaoTecnica | AprovacaoTecnica | imutável; rastreável a CREA do aprovador |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| `Especificacao` | `{chave, valor, unidade, tolerancia}` | Sim |
| `AssinaturaTecnica` | `{aprovador_nome, crea, data, ip, hash_revisao, tipo}` | Sim |
| `LetraRevisao` | "A", "B", "C", ... (sequencial alfabético) | Sim |

---

## Eventos de domínio (publicados)

| Evento | Quando dispara | Payload | Quem consome |
|---|---|---|---|
| `Engenharia.ProjetoCriado` | novo projeto técnico | `{projeto_id, codigo, cliente_id}` | CRM |
| `Engenharia.RevisaoSubmetida` | revisão vai para aprovação | `{revisao_id, projeto_id, aprovador_id}` | BPM (cria pendência), notificações |
| `Engenharia.RevisaoAprovada` | aprovação concedida | `{revisao_id, projeto_id, aprovador_id, decidida_em}` | OS, Orçamentos, Estoque (BOM), CRM |
| `Engenharia.RevisaoRejeitada` | aprovação negada | `{revisao_id, comentario}` | autor (notificação) |
| `Engenharia.RevisaoMarcadaObsoleta` | retirada de uso | `{revisao_id, motivo}` | OS, Estoque (alerta) |
| `Engenharia.ComponenteCadastrado` | novo item na biblioteca | `{componente_id, fabricante, modelo}` | analytics |
| `Engenharia.BOMAtualizada` | linhas de BOM mudaram em revisão | `{revisao_id, diff}` | Orçamentos, Estoque |

---

## Comandos

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `criarProjeto` | UI | usuário tem permissão; código único | ProjetoTecnico criado + revisão A em rascunho |
| `criarRevisao` | UI | projeto existe; revisão anterior aprovada ou rejeitada | nova Revisao em rascunho com próxima letra |
| `submeterRevisao` | UI | revisão em rascunho; conteúdo mínimo válido | status `em_aprovacao` + evento `RevisaoSubmetida` |
| `aprovarRevisao` | UI / BPM callback | aprovador tem permissão e CREA registrado | AprovacaoTecnica imutável + status `aprovada` |
| `rejeitarRevisao` | UI / BPM callback | aprovador tem permissão | status `rejeitada` + evento |
| `marcarObsoleta` | UI | revisão aprovada | status `obsoleta` + evento |
| `cadastrarComponente` | UI | dedup OK | BibliotecaComponente criado |
| `vincularEntidade` | UI / API | revisão + entidade existem | RelacaoProjetoEntidade criada |
| `gerarMemorialPdf` | UI | memorial preenchido | Anexo PDF gerado |

---

## Schema físico

Ver `../schema-banco.md` (quando criado) — multi-tenant por ADR-0001+ADR-0002. Anexos no Backblaze B2 com chave KMS por tenant.

## Como este modelo evolui

- Entidade nova → verificar fronteira comum/módulo.
- Atributo novo → migration + bump CHANGELOG.
- Evento novo → atualizar consumidores + comunicar.
