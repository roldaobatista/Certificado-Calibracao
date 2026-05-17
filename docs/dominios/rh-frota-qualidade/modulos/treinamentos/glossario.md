---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: treinamentos
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Treinamentos e Certificações Internas

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem (norma/spec) |
|---|---|---|---|---|
| Treinamento (do catálogo) | Item do catálogo com nome, categoria, carga horária e validade padrão | "curso", "capacitação" (genérico) | template; não é evento ocorrido | módulo treinamentos |
| Evento (turma) | Instância concreta de um treinamento (data, local, facilitador, participantes) | "agenda" | execução de uma turma | módulo treinamentos |
| Facilitador | Quem ministra o evento (interno ou externo) | "professor", "instrutor" (usar facilitador) | identificação obrigatória no certificado | módulo treinamentos |
| Prova / avaliação | Questionário com nota mínima | "exame" | base para emitir certificado | módulo treinamentos |
| Certificado de conclusão | PDF imutável emitido após aprovação | "diploma" | documenta competência | módulo treinamentos |
| Validade do certificado | Janela em que o certificado é considerado vigente | "vencimento" | após data, técnico fica inabilitado naquela trilha | módulo treinamentos |
| Trilha de capacitação | Conjunto obrigatório de treinamentos para função / equipamento / norma | "matriz de exigência" | bloqueia execução se incompleta | ISO 17025 cl. 6.2 |
| Matriz de competência | Visão consolidada colaboradores × habilidades com status | "skill matrix" | evidência auditável | ISO 17025 cl. 6.2 + ISO 9001 cap. 7.2 |
| Reciclagem | Repetição programada de treinamento antes do vencimento | "renovação" | evento que reseta validade | módulo treinamentos |
| Habilitação (do colaborador) | Status binário "apto / não apto" para atividade específica | "autorização" (autorização é signatário; ver INV-003) | resultado do cruzamento trilha × certificados válidos | módulo treinamentos |
| Categoria de treinamento | Segurança / Técnico / Normativo / Comportamental | — | classificação para relatórios | módulo treinamentos |
| Sub-categoria NR-* | NR-10 / NR-12 / NR-35 / NR-33 etc | — | dispara espelhamento em módulo `seguranca-trabalho` | NRs do MTE |
| ISO 17025 cl. 6.2 | Cláusula "Pessoal" da ISO/IEC 17025 — exige competência documentada | — | razão de ser deste módulo no contexto do produto | ISO/IEC 17025:2017 |
| Bypass de bloqueio | Liberação excepcional de técnico não-habilitado | — | gera registro auditável com justificativa + aprovador | módulo treinamentos + governança |
| Histórico de capacitação | Linha do tempo dos treinamentos do colaborador | "currículo interno" | export PDF disponível | módulo treinamentos |

---

## Como esta lista evolui

- Termo novo → adicionar + validar não-duplicação com glossário comum.
- Termo regulado tem origem obrigatória (ISO, NR-*).
