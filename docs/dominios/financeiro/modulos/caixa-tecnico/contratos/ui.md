---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Contrato UI — Caixa do Técnico

## App técnico (mobile, offline-first)

### TCT-01 — Meu caixa

- Saldo destacado: "Você tem R$ X em adiantamento aberto. R$ Y em despesas pendentes."
- Botão grande "Lançar despesa" (1 toque)
- Botão "Solicitar adiantamento"
- Lista de despesas recentes (status visual)
- Banner "X despesas pra sincronizar" se offline pendente

### TCT-02 — Nova despesa (≤ 30s)

- Câmera abre primeiro — tira foto recibo
- Valor (teclado numérico grande)
- Categoria (botões grandes com ícone)
- OS (autocomplete; opcional)
- Descrição (opcional)
- "Salvar" (offline-ok; sincroniza depois)

### TCT-03 — Reembolso de km

- Origem + destino (com sugestão de OS)
- km (manual; V2: Google Maps API)
- Sistema mostra "Valor: X km × R$ Y = R$ Z" automático
- Foto opcional (placa + odômetro)

### TCT-04 — Solicitar adiantamento

- Valor + motivo (curto) + OS opcional
- Mostra alçada esperada ("Será aprovado por: {financeiro/dono}")
- Status acompanhável: solicitado → aprovado → entregue

### TCT-05 — Fechar prestação (≤ 5 min)

- Resumo: total adiantado / total despesas / saldo
- Lista filtrável das despesas
- Botão grande "Fechar prestação"
- Confirmação: "Você vai devolver R$ X" ou "Você vai receber R$ Y"

## App financeiro (web/mobile)

### TCT-06 — Validar despesas

- Lista pendente do tenant
- Swipe direita = validar; esquerda = rejeitar (com motivo de uma lista)
- Foto em zoom rápido
- Indicador anti-fraude: ícone se foto repetida ou valor 3σ acima

### TCT-07 — Aprovar adiantamentos

- Lista solicitações
- Aprovar/Rejeitar em 1 toque

### TCT-08 — Política de despesa

- Limites por categoria
- Alçada
- Tarifa km
- Toggle GPS obrigatório (com aviso LGPD)

## Mensagens visíveis

| Contexto | Mensagem |
|---|---|
| Sem foto | "Precisa anexar a foto do recibo para registrar." |
| Offline | "Sem sinal — vamos guardar e enviar quando voltar a conexão." |
| Foto duplicada | "Esta foto já foi usada em outra despesa. Tire uma nova." |
| Limite excedido | "Categoria {x} permite até R$ {y} por dia. Justifique." |
| Prestação fechada | "Prestação enviada. Saldo: você {recebe/devolve} R$ {x}." |

## Acessibilidade

- App mobile WCAG AA; botões grandes (campo, luvas, sol).
- Modo escuro pra leitura em ambiente escuro.
- Câmera com flash automático em recibo claro.

## Non-goals UI

- OCR (V2)
- Mapa de rota dirigida (V2 — integração Google Maps)
- Notificação push avançada (V2)

## Referências

- JTBD-062 (5 min)
- BIG-08
