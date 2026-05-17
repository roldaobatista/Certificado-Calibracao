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

# Glossário do módulo App do Técnico

> Termos **específicos** deste módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| check-in | Registro de chegada ao cliente com timestamp + GPS | "ponto", "bater ponto", "marcar presença" | Técnico confirmou que chegou ao endereço | US-APP-003 |
| deslocamento | Período entre saída do ponto anterior e chegada ao cliente | "viagem curta", "trajeto" | Técnico está se movendo, custo de hora de carro contando | US-APP-002 |
| sync | Sincronização de dados offline com servidor | "subir dados", "atualizar" | App enviando ao servidor o que foi feito offline | ADR-0004 |
| fila de sync | Lista local de operações pendentes de envio | "buffer", "pendências" | Operações registradas offline aguardando conexão | ADR-0004 |
| conflito de sync | Mesmo dado alterado em base e no app simultaneamente | "merge conflict" | Sistema precisa decidir qual versão prevalece | US-APP-013 |
| transferência de estoque | Movimentação de peça entre veículos de técnicos | "passar peça", "empréstimo" | Estoque sai de um veículo e entra em outro | US-APP-005 |
| assinatura de aceite | Assinatura tátil do cliente confirmando serviço | "assinatura A3", "assinatura ICP" | Aceite contratual — NÃO tem valor regulatório ISO 17025 | US-APP-007 |
| prestação de contas | Acerto pós-viagem entre adiantamento e despesas | "fechamento viagem", "acerto caixinha" | Cálculo saldo a receber/devolver pelo técnico | US-APP-009 |
| veículo (estoque) | Conjunto de peças sob responsabilidade de um técnico | "maleta", "kit", "carro" | Saldo de peças que aquele técnico tem fisicamente | US-APP-004 |
| pin/biometria | Mecanismo de desbloqueio do app além da senha de sessão | "lock" | Defesa contra uso indevido em caso de furto | NFR |

---

## Como esta lista evolui

- Termo novo → verificar conflito com glossário comum (hook valida).
- Termo descontinuado → `@deprecated` + janela de migração 3 meses.
- Mudança de definição → CHANGELOG seção "Modificado".

## Convenções

- Termos em PT-BR. Termos técnicos inevitáveis em inglês (ex: "sync") com tradução de campo.
- Definição em 1 linha; se precisar mais, criar `docs/explicacoes/<termo>.md`.
