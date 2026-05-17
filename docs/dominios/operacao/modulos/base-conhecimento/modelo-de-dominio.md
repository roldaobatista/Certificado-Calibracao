---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Modelo de domínio — Base de Conhecimento

## Entidades

### Artigo
- **Atributos obrigatórios:** id, tenant_id, titulo, tipo (tecnico|procedimento|manual|faq|solucao), corpo, status (rascunho|em_revisao|publicado|arquivado), autor_id, criado_em, atualizado_em
- **Atributos opcionais:** equipamento_id, marca, modelo, tipo_servico, normas_relacionadas[], tags[]
- **Invariantes:** INV-TENANT-001 (tenant_id sempre presente); só publica após `AprovacaoTecnica` válida; uma versão "corrente" por artigo
- **Ciclo:** rascunho → em_revisao → publicado → (re-edição cria nova versão) → arquivado

### VersaoArtigo
- **Atributos:** id, artigo_id, numero_versao, corpo_snapshot, publicado_em, aprovado_por_id, comentario_aprovacao
- **Invariantes:** imutável após publicada; numero_versao monotônico

### AprovacaoTecnica
- **Atributos:** id, artigo_id, versao_id, aprovador_id, decisao (aprovado|rejeitado|ajustes), comentario, decidido_em
- **Invariantes:** aprovador ≠ autor; registra audit log

### Anexo
- **Atributos:** id, artigo_id, tipo (pdf|imagem|video|link), url_storage, tamanho_bytes, mime, descricao
- **Invariantes:** tamanho ≤ limite_tenant; vírus-scan obrigatório

### SugestaoArtigo
- **Atributos:** id, origem_tipo (chamado|os), origem_id, artigo_id, score, exibida_em, clicado (bool), aplicado (bool)
- **Invariantes:** uma sugestão por (origem, artigo)

### Comentario
- **Atributos:** id, artigo_id, autor_id, corpo, tipo (sugestao_melhoria|duvida|errata), criado_em, resolvido (bool)

### Voto
- **Atributos:** id, artigo_id, usuario_id, util (bool), criado_em
- **Invariantes:** um voto por (artigo, usuario); pode ser alterado

### TrilhaLeitura (referência leve)
- Referência ao módulo Treinamentos. Artigo pode estar em N trilhas; trilha pertence ao módulo Treinamentos.

---

## Agregados

| Raiz | Inclui | Invariantes |
|---|---|---|
| Artigo | VersaoArtigo, AprovacaoTecnica, Anexo | controle de versão atômico; publicar = transição validada |
| Comentario | (próprio) | autor pertence ao tenant |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| Categoria | (equipamento_id?, marca?, modelo?, tipo_servico?, normas[]) | Sim |
| Score sugestão | número 0-1 derivado de similaridade | Sim |

---

## Eventos publicados

| Evento | Quando dispara | Payload | Consumidores |
|---|---|---|---|
| `BaseConhecimento.ArtigoPublicado` | aprovação resulta em publicado | {artigo_id, versao, categoria} | Chamados, OS, Treinamentos |
| `BaseConhecimento.ArtigoArquivado` | arquivamento | {artigo_id, motivo} | Chamados, OS |
| `BaseConhecimento.SugestaoExibida` | sugestão renderizada | {origem, artigo_id, score} | Métricas |
| `BaseConhecimento.SugestaoAplicada` | usuário marca como aplicada | {origem, artigo_id} | Métricas |

## Eventos consumidos

| Evento | Origem | Uso |
|---|---|---|
| `Chamados.ChamadoAberto` | módulo Chamados | calcular sugestões |
| `OS.OSCriada` | módulo OS | calcular sugestões |
| `Treinamentos.TrilhaAtualizada` | módulo Treinamentos | marcar artigos como leitura obrigatória |

---

## Comandos

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| criarRascunho | UI / API / OS | autor autenticado | artigo em rascunho |
| submeterRevisao | UI | rascunho válido | artigo em_revisao |
| aprovarArtigo | UI aprovador | aprovador ≠ autor | versão publicada + evento |
| rejeitarArtigo | UI aprovador | aprovador ≠ autor | volta a rascunho com comentário |
| arquivarArtigo | UI | artigo publicado | status arquivado + evento |
| votarUtilidade | UI/API | leitor autenticado | voto registrado |

---

## Schema físico

Ver `../schema-banco.md` quando criado. Tabela principal `bcn_artigo`, `bcn_versao`, `bcn_aprovacao`, `bcn_anexo`, `bcn_sugestao`, `bcn_comentario`, `bcn_voto`.

## Como evolui

Entidade nova → ADR. Tipo novo de artigo → não exige ADR (configuração de tenant).
