---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Contrato UI — Contas a Receber

> Linguagem do usuário, não jargão. Termos visíveis listados aqui.

## Telas

### TR-01 — Lista de cobranças

- Filtros: status (aberto/pago/atrasado), cliente, vencimento, valor
- Colunas: cliente, descrição (origem OS/contrato), valor, vencimento, status, ações
- Ação rápida: "Cobrar agora" (envia link WhatsApp/email), "Marcar como pago", "Cancelar"
- Indicador visual: vencido = vermelho; vence hoje = laranja; futuro = neutro; pago = verde

### TR-02 — Nova cobrança manual

- Campos: cliente (busca), descrição livre, valor, vencimento, meio (boleto/PIX)
- Opcional: parcelar em N vezes
- Regras automáticas: juros/multa/desconto pré-configurados (mostrar resumo)
- Botão: "Emitir e enviar" / "Salvar rascunho"

### TR-03 — Detalhe da cobrança

- Cabeçalho: cliente, valor original, valor atualizado, status
- Linha do tempo: emitida → enviada → vista → paga
- Comprovante de pagamento anexado (quando baixa manual)
- Histórico de comunicação (régua — Wave B)
- Botões: 2ª via, cancelar, baixar manualmente, anexar comprovante

### TR-04 — Painel de inadimplência (Wave B)

- Aging: 0-30 / 31-60 / 61-90 / > 90
- Top 10 devedores
- Régua: clientes em cada etapa (lembrete / aviso / alerta)

## Mensagens visíveis (PT-BR sem jargão)

| Contexto | Mensagem |
|---|---|
| Sucesso emissão | "Cobrança enviada para o cliente." |
| Erro gateway | "Não conseguimos emitir agora. Tente novamente em alguns minutos." |
| Webhook chegando | "Pagamento confirmado — cobrança baixada automaticamente." |
| Vencido | "Vencida há {N} dias. Valor com juros e multa: R$ X." |
| Cancelamento | "Tem certeza? Esta ação não pode ser desfeita." |

## Acessibilidade

- WCAG AA: cores não são o único sinal de status (ícone + texto).
- Atalhos teclado: `N` nova cobrança, `/` busca.

## Estados de erro

- Cliente sem CPF/CNPJ válido → bloqueia emissão com mensagem clara.
- Gateway fora → modo degradado: salva rascunho + alerta.
- Sem internet (mobile) → fila offline (Wave B).

## Non-goals UI

- Editor visual de régua complexa (Wave B básico; V2 avançado).
- Multi-moeda.

## Referências

- `docs/dominios/financeiro/README.md`
- `docs/comum/design-system.md` [INFERÊNCIA — verificar se existe]
