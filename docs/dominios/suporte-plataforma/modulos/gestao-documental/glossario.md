---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Gestão Documental

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Documento | Arquivo binário + metadados gerenciado pelo módulo | "arquivo", "anexo" (genéricos) | unidade gerenciável da biblioteca | Interno |
| Versão | Iteração imutável de um documento (v1, v2, v3) | "revisão" (ambíguo) | quem alterou e quando | Interno |
| Documento vigente | Versão atualmente válida (única por documento) | "ativo", "em uso" | versão a ser citada | ISO 9001 4.2.3 |
| Documento obsoleto | Versão anterior arquivada, consultável mas não vigente | "antigo", "deletado" | versão histórica | ISO 9001 4.2.3 |
| Documento em revisão | Versão criada mas aguardando aprovação | "rascunho" | ainda não vale | Interno |
| Documento vencido | Documento com data de validade ultrapassada | "expirado" | precisa renovação | Interno |
| Modelo de documento | Template reutilizável com variáveis | "formulário" (ambíguo) | base pra gerar docs | Interno |
| ACL | Lista de controle de acesso por documento | "permissão" (ambíguo) | quem pode ler/escrever | RFC genérico |
| OCR | Reconhecimento óptico de caracteres (extrai texto de imagem) | — | indexação de PDFs digitalizados | Padrão indústria |
| Trilha de auditoria | Log imutável de toda ação sobre documento | "histórico" (ambíguo) | evidência regulatória | `INV-001` |
| Política de retenção | Regra de quanto tempo um tipo de doc é mantido | — | descarte controlado | LGPD art. 16 |
| Link de compartilhamento | URL temporária para acesso externo | "link público" (impreciso) | acesso com TTL e auditoria | Interno |
| Pasta virtual | Agrupamento lógico (não físico) por entidade | "diretório" | filtro de visualização | Interno |

---

## Como esta lista evolui

Termo novo → adicionar + verificar conflito com glossário comum. Mudança de definição → bump CHANGELOG.
