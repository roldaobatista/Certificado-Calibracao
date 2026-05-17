---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Personas — Base de Conhecimento

> Específicas deste módulo. Transversais ficam em `../personas.md` e `docs/comum/personas.md`.

---

## P-BCN-01 — Autor de Conteúdo Técnico

**Identidade:** técnico sênior/responsável técnico, 35-55 anos, vivência em campo e laboratório, conhece os equipamentos e clientes.

**Goals deste módulo:**
- Registrar solução que descobriu sem virar projeto paralelo
- Atualizar artigos quando equipamento muda firmware ou norma é revisada
- Ver suas contribuições reconhecidas (autoria visível)

**Frustrations:**
- Editor pesado que tira foco da prática
- Aprovação demora semanas e o artigo perde validade

**Jornada típica:**
1. Resolve problema na OS → clica "criar artigo a partir desta OS"
2. Sistema pré-preenche título, equipamento, sintoma, solução, fotos
3. Autor refina texto, marca categoria, envia pra aprovação
4. Recebe notificação de aprovado/rejeitado com comentário

**Devices:** web desktop principal, mobile leitura.
**Frequência:** semanal (publica) / diária (consulta).

---

## P-BCN-02 — Aprovador Técnico

**Identidade:** responsável técnico do laboratório/empresa, formação superior, assina certificados, responde por qualidade.

**Goals:**
- Garantir que conteúdo publicado está tecnicamente correto e não cria risco
- Manter base atualizada conforme normas vigentes (ISO 17025, NIT-DICLA, etc.)

**Frustrations:**
- Fila de aprovação invisível
- Não ver o que mudou entre versões

**Jornada típica:**
1. Recebe lista de artigos pendentes
2. Abre artigo, vê diff com versão anterior (se atualização)
3. Aprova / pede ajustes / rejeita com motivo
4. Periodicamente revisa artigos com > 12 meses sem revisão

**Devices:** web desktop.
**Frequência:** semanal.

---

## P-BCN-03 — Consumidor de Conteúdo (Atendente/Técnico Júnior)

**Identidade:** atendente helpdesk ou técnico júnior, busca solução agora pra não bloquear cliente.

**Goals:**
- Achar resposta sem precisar interromper colega sênior
- Confiar que o que está lá foi validado

**Frustrations:**
- Buscar e não achar nada relevante
- Achar artigo desatualizado sem aviso

**Jornada típica:**
1. Abre chamado/OS → vê painel lateral com artigos sugeridos
2. Se nenhum serve, busca por sintoma/equipamento
3. Aplica solução, marca artigo como útil/não útil
4. Deixa comentário sugerindo melhoria se algo faltou

**Devices:** web desktop + mobile (técnico em campo).
**Frequência:** diária.

---

## Convenções

Se persona aparecer em ≥2 módulos com mesma responsabilidade, promover pra `../personas.md`.
