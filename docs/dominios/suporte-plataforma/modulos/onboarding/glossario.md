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

# Glossário do módulo Onboarding

> Termos específicos deste módulo. Termos transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Implantação | Processo formal de configurar tenant cliente do cadastro ao go-live | "instalação", "deploy do cliente" | "configuração inicial completa da empresa nova" | `novas funcionalidades.txt:1119` |
| Onboarding | Sinônimo de implantação no contexto deste módulo | — | mesmo que implantação | `novas funcionalidades.txt:1119` |
| Tenant | Empresa-cliente isolada no sistema multi-tenant | "cliente", "conta" (quando ambíguo) | "a empresa toda dela, separada das outras" | ADR-0002 |
| Sandbox | Ambiente de teste isolado por tenant antes da produção | "ambiente fake", "homologação" | "lugar pra testar sem quebrar nada" | `novas funcionalidades.txt:1136` |
| Go-live | Momento em que sandbox vira produção | "lançamento", "kickoff" (este último é diferente) | "dia em que o cliente passa a usar de verdade" | derivado |
| Wizard | Fluxo guiado de configuração em etapas sequenciais | "assistente" (ambíguo com IA) | "telas em sequência, uma de cada vez" | UX padrão |
| Checklist de implantação | Lista de etapas pré-definidas com status individual | "to-do list" | "lista do que falta pra concluir a implantação" | `novas funcionalidades.txt:1127-1128` |
| Etapa de implantação | Item individual no checklist (ex: "Importar clientes") | "task" | "uma das partes da implantação" | derivado |
| Responsável interno | Colaborador do Aferê atribuído à implantação | "PM" (sem contexto) | "quem cuida dessa implantação do nosso lado" | `novas funcionalidades.txt:1129` |
| Status da implantação | Estado agregado: não iniciada, em andamento, pendente cliente, concluída | — | "situação geral em que a implantação está" | `novas funcionalidades.txt:1130` |
| Termo de aceite | Documento assinado pelo cliente que marca fim da implantação | "contrato" (é diferente) | "papel que o cliente assina dizendo que tá tudo OK" | `novas funcionalidades.txt:1133` |
| Validação do ambiente | Checklist técnico automático antes de virar produção | — | "verificação de que tá tudo configurado certo" | `novas funcionalidades.txt:1132` |
| Migração de dados | Trazer dados do sistema antigo do cliente pro Aferê | "import" (subset) | "puxar tudo do programa antigo pro novo" | `novas funcionalidades.txt:1134` |
| Inconsistência de migração | Registro de erro/alerta encontrado durante import | "bug", "erro" (genéricos demais) | "linha do import que tem problema" | `novas funcionalidades.txt:1135` |
| Promoção pra produção | Ato de copiar configuração aprovada do sandbox pro tenant produtivo | "publish", "deploy" | "passar o que tá no teste pro de verdade" | derivado |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → marcar `@deprecated` + janela 3 meses.

## Convenções

- PT-BR.
- "Tenant" mantido em inglês (já no glossário comum) com tradução de campo.
