---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Segurança do Trabalho

> Termos específicos deste módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem (norma/spec) |
|---|---|---|---|---|
| EPI | Equipamento de Proteção Individual com CA emitido pelo MTE | "equipamento de segurança" | item entregue ao colaborador com termo assinado | NR-06 |
| CA | Certificado de Aprovação do EPI emitido pelo MTE | "número de aprovação" | número obrigatório no cadastro do EPI | NR-06 |
| ASO | Atestado de Saúde Ocupacional emitido por médico do trabalho | "atestado médico", "exame admissional" | colaborador apto/inapto para função, com validade | NR-07 / PCMSO |
| NR-10 | Norma Regulamentadora 10 — serviços em instalações elétricas | "treinamento elétrico" | técnico autorizado a trabalho com eletricidade | NR-10 / MTE |
| NR-12 | Norma Regulamentadora 12 — segurança em máquinas e equipamentos | "treinamento máquinas" | técnico autorizado a operar / regular máquina | NR-12 / MTE |
| NR-35 | Norma Regulamentadora 35 — trabalho em altura (>2m) | "treinamento altura" | técnico autorizado a trabalho em altura | NR-35 / MTE |
| NR-33 | Norma Regulamentadora 33 — espaço confinado | — | técnico autorizado a entrar em espaço confinado | NR-33 / MTE |
| PT | Permissão de Trabalho — autorização formal para serviço de risco em janela definida | "ordem de serviço de risco" | documento válido por turno; assinado emitente + executante | NR-33 / NR-35 |
| APR | Análise Preliminar de Risco — identificação de perigos antes da execução | "AST" (Análise de Segurança da Tarefa) | template preenchido + assinado antes de iniciar OS de risco | boa prática SST |
| Checklist de segurança | Lista de verificação obrigatória pré-OS | "checklist do técnico" | bloqueia execução da OS se não preenchido | módulo SST |
| Quase-acidente | Evento que poderia ter causado lesão / dano, mas não causou | "near-miss", "incidente sem dano" | registro obrigatório para análise preventiva | boa prática SST |
| Acidente de trabalho | Evento com lesão / dano material durante a jornada | — | gera registro interno + (V2) CAT eletrônica eSocial | Lei 8.213/91 art. 19 |
| Termo de entrega de EPI | Documento assinado pelo colaborador ao receber EPI | "recibo de EPI" | prova jurídica de entrega; imutável após assinatura | NR-06 item 6.6.1 |
| PCMSO | Programa de Controle Médico de Saúde Ocupacional | — | documento técnico armazenado como PDF; não gerado pelo módulo | NR-07 |
| PGR | Programa de Gerenciamento de Riscos | — | documento técnico armazenado como PDF; não gerado pelo módulo | NR-01 |
| Validade do CA | Data limite do Certificado de Aprovação do MTE | — | após essa data, EPI não pode ser entregue | NR-06 |
| Função | Cargo / atividade do colaborador (define ASO e treinamentos exigidos) | "papel" (esse é RBAC) | função registrada determina quais NRs aplicam | CBO + tenant |

---

## Como esta lista evolui

- Termo novo → adicionar + validar não-duplicação com glossário comum.
- Termo regulado tem origem obrigatória (NR-*, Lei 8.213/91 etc).
