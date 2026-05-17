---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Glossário — Base de Conhecimento

> Termos específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Artigo | Unidade de conteúdo publicada na base (técnico, FAQ, procedimento, solução) | "post", "página" | conteúdo aprovado e versionado | spec módulo |
| Rascunho | Artigo em edição, ainda não submetido a aprovação | "draft" (na UI: "rascunho") | só autor e revisor enxergam | spec módulo |
| Em revisão | Artigo submetido, aguardando aprovação técnica | "pending" | bloqueia novas edições do autor | spec módulo |
| Publicado | Artigo aprovado e visível pra consumidores | "ativo", "live" | versão corrente exibida | spec módulo |
| Aprovação técnica | Ato do responsável técnico que autoriza publicação | "review", "OK do chefe" | gera registro auditável | ISO 17025 4.3 (analogia controle docs) |
| Versão | Estado imutável do artigo após publicação | "revisão" (ambíguo com aprovação) | comparável e revertível | spec módulo |
| Sugestão de artigo | Artigo recomendado automaticamente em Chamado/OS por similaridade | "recomendação" | painel lateral contextual | spec módulo |
| Trilha de leitura | Conjunto ordenado de artigos atribuído a função/cargo via Treinamentos | "playlist" | integração módulo Treinamentos | spec módulo |
| Útil/Não útil | Marcação binária do leitor que alimenta ranqueamento | "like/dislike", "estrela" | métrica de qualidade | spec módulo |
| Artigo desatualizado | Artigo sem revisão há > 12 meses (parametrizável por tenant) | "vencido" (confunde com licenças) | flag amarela na UI | spec módulo |
| Procedimento operacional | Artigo do tipo passo-a-passo executável | "POP", "SOP" | template específico com numeração de passos | ISO 9001 |

## Convenções

- Termos em PT-BR. "Wiki" não é usado (sugere edição livre, que este módulo não permite).
- Origem regulada quando aplicável.
