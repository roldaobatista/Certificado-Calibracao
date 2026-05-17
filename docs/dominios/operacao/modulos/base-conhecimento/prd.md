---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# PRD — Módulo Base de Conhecimento

## 1. O que este módulo é

Repositório vivo do saber técnico da empresa: artigos, procedimentos operacionais, manuais internos, soluções de problemas comuns, FAQ, base por equipamento/marca/modelo, vídeos de treinamento e anexos técnicos. Aparece como sugestão dentro de Chamados e OS, evitando que técnico experiente seja o único ponto de conhecimento.

## 2. Por que este módulo existe

Conhecimento técnico hoje vive na cabeça de poucos. Quando técnico sai, fica doente ou está atendendo outro cliente, atendente/técnico júnior repete erro já resolvido. Módulo transforma cada solução em ativo reutilizável, com controle de versão e aprovação técnica.

## 3. Personas

Ver `personas.md` deste módulo + `../personas.md` (P-OP-01 técnico, P-OP-03 atendente) + `docs/comum/personas.md`.

## 4. Escopo

- CRUD de artigo (técnico, procedimento, manual, FAQ, solução-problema)
- Categorização por equipamento, marca, modelo, tipo de serviço, norma técnica
- Anexos (PDF, imagem, vídeo) e links externos
- Busca inteligente (full-text + filtros por categoria/equipamento)
- Sugestão automática de artigos dentro de Chamado (por equipamento+sintoma)
- Sugestão automática de artigos dentro de OS (por equipamento+tipo serviço)
- Controle de versão (histórico, comparar versões, rollback)
- Aprovação técnica obrigatória pra publicar (workflow rascunho→revisão→publicado)
- Comentários e sugestões de melhoria por leitor (técnico/atendente)
- Marcação "útil/não útil" pra ranquear
- Integração com Treinamentos (artigo pode ser leitura obrigatória de trilha)
- Vídeos hospedados internamente ou linkados (YouTube privado/Vimeo)
- Audit log (quem criou, quem aprovou, quem editou)

## 5. Non-goals

- Geração automática de artigo por IA sem revisão humana (técnico sempre revisa)
- Publicação pra cliente externo (módulo é interno; portal cliente fica em Atendimento)
- Wiki colaborativa estilo Confluence/Notion (edição sempre passa por aprovação)
- Tradução automática multi-idioma (MVP-2)
- Pagamento por artigo / monetização externa (fora de escopo)

## 6. User Stories

- **US-BCN-001:** técnico cria rascunho de artigo a partir de solução aplicada em OS
- **US-BCN-002:** responsável técnico revisa e aprova artigo, marcando versão publicada
- **US-BCN-003:** atendente vê sugestão automática de artigo ao abrir chamado por equipamento X
- **US-BCN-004:** técnico vê sugestão automática de artigo dentro da OS
- **US-BCN-005:** usuário busca por sintoma e recebe lista ranqueada por utilidade
- **US-BCN-006:** sistema mostra histórico de versões do artigo e permite comparar
- **US-BCN-007:** leitor deixa comentário sugerindo melhoria; vira tarefa de revisão
- **US-BCN-008:** leitor marca artigo como "útil/não útil" pra alimentar ranking
- **US-BCN-009:** responsável marca artigo como leitura obrigatória de trilha de treinamento
- **US-BCN-010:** sistema sinaliza artigo desatualizado (sem revisão > 12 meses)

## 7. Métricas

Ver `metricas.md`. Primárias: % chamados/OS com artigo sugerido aceito, tempo médio de resolução com vs sem artigo, cobertura por equipamento.

## 8. NFR

- Busca devolve resultados em < 800ms p95
- WCAG AA (INV-016)
- Vídeos servidos via CDN (sem bloquear app)
- Anexos > 50MB rejeitados (config tenant)

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo `US-BCN-NNN`. Mudança em fluxo de aprovação exige ADR.
