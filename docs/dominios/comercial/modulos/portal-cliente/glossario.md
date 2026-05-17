---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/comum/glossario-roldao.md
---

# Glossário do módulo Portal do Cliente

> Termos específicos. Transversais ficam em `docs/comum/glossario-roldao.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Portal do Cliente | Área externa onde o cliente final do tenant acessa seus próprios dados | "Área do cliente externo", "Self-service" | A "minha conta" do cliente final | US-POR-001 |
| Cliente externo | Pessoa/empresa cliente do tenant (ex: cliente da Balanças Solution) — NÃO confundir com tenant | "Usuário externo" | Quem comprou serviço do nosso cliente | PRD |
| Tenant | Empresa que contrata o Aferê (ex: Balanças Solution) | "Cliente do Aferê" pode ambiguidade | A empresa que paga pelo Aferê | AGENTS.md / ADR-0002 |
| Login mágico | Link enviado por e-mail/WhatsApp que loga sem senha | "Magic link sem traduzir" | Link pra entrar sem digitar senha | US-POR-001 |
| Aprovação eletrônica | Aprovação de orçamento via clique + registro de IP/data/identidade | "Assinatura digital" (não é) | Cliente apertou "aprovar" e ficou registrado quem/quando/de onde | US-POR-005 |
| 2ª via | Cópia de boleto/Pix de fatura ainda em aberto | "Reemissão fiscal" (não é) | Quando o cliente precisa de outro boleto pra pagar | US-POR-006 |
| Visível ao cliente | Flag em anexo/documento que define se aparece no Portal | "Público" sozinho (ambíguo) | Marca de "esse arquivo o cliente externo pode ver" | US-POR-003, US-POR-008 |
| Timeline de status | Sequência cronológica de mudanças de estado de uma OS | "Status log" | A "linha do tempo" da OS pro cliente acompanhar | US-POR-007 |
| Thread (mensagem) | Conversa contínua vinculada a uma OS/orçamento/fatura | "Chat" | Linha de mensagens pra registrar comunicação | US-POR-009 |
| Opt-in | Consentimento explícito do cliente para receber comunicação por canal X | "Aceite" | Quando o cliente diz "sim, pode mandar pelo WhatsApp" | US-POR-010 (LGPD) |
| Opt-out | Cliente pediu para parar de receber comunicação | "Descadastro" | Quando o cliente pediu pra não receber mais | LGPD |
| Link mágico | Ver "Login mágico" — mesma coisa | — | — | — |
| Solicitação de mudança cadastral | Pedido do cliente para alterar dado sensível que precisa de aprovação interna | "Editar perfil" cego (não é) | Cliente pediu pra mudar CNPJ → atendente precisa aprovar | US-POR-011 |
| Validador externo (certificado) | Site/QR Code da entidade reguladora (INMETRO/RBC) que confere autenticidade do certificado | — | Link/QR que prova "esse certificado é de verdade" | US-POR-008 |
| Selo ANULADO | Marca visual em documento que perdeu validade | "Cancelado" sozinho (ambíguo) | Documento não vale mais, mas histórico preservado | US-POR-008 |
| Webhook (notificação ao tenant) | Disparo HTTP do portal pra integração interna do tenant | — | Sistema do tenant "fica sabendo" de algo do portal | US-POR-010 (futuro) |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo deprecado → `@deprecated` + janela 3 meses.
- Mudança definição → bump CHANGELOG.

## Convenções

- Termos em PT-BR. Quando técnico-original (opt-in, opt-out, thread, webhook) for inevitável, sempre traduzir na coluna "Se vir na tela/log".
- "Cliente" sozinho é ambíguo — sempre qualificar: "cliente externo" (do tenant) vs "tenant" (cliente do Aferê).
