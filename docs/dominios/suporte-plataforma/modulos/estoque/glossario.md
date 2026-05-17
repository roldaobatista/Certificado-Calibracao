---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Glossário — Estoque multi-local

> Específico do módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Local de estoque | Posição física onde a peça está (central, veículo, com técnico, cliente) | "depósito" só | Container lógico de saldo | BIG-12 |
| Saldo | Quantidade de peça em um local específico em uma data | "estoque atual" cru | Número na tela de saldos | BIG-12 |
| Lote | Identificador de produção do fabricante (rastreabilidade) | "batch" cru | Subdivisão do saldo por origem | BIG-12 |
| Validade do lote | Data limite de uso | "expiry" | Filtro nas telas; bloqueia consumo após data | BIG-12 / JTBD-105 |
| Número de série (NS) | Identificador único de uma unidade física (selo INMETRO, padrão metrológico) | "tag" só | Item identificado individualmente | BIG-12 |
| Movimento | Evento de entrada/saída/transferência (append-only) | "lançamento" cru | Linha do kardex | BIG-12 |
| Kardex | Linha do tempo de movimentos de um item por local | "extrato" só | Tela de rastreabilidade | BIG-12 |
| Transferência 2-etapas | Saída do local A → trânsito → aceite do local B com foto | "transfer" cru | Movimento dividido em emissão e aceite | BIG-12 / JTBD-104 |
| Em trânsito | Saldo bloqueado entre etapa 1 (emissão) e etapa 2 (aceite) | "limbo" | Estado temporário do saldo | BIG-12 |
| Foto do lacre | Imagem obrigatória capturada no aceite de transferência (BIG-12 — selo INMETRO) | "anexo" cru | Evidência fotográfica do recebimento | BIG-12 |
| Inventário | Conferência física comparada ao saldo do sistema | "auditoria de estoque" | Tela de ajuste após contagem | BIG-12 |
| Reserva | Saldo alocado para OS específica, ainda não consumido | "pré-saída" | Saldo indisponível para outra OS | BIG-12 |
| Custo médio | Custo unitário recalculado a cada entrada (CMP) | "preço de custo" cru | Linha do kardex | [INFERÊNCIA] V2 |

---

## Como evolui

- Termo novo → checar conflito com glossário comum.
- Termo descontinuado → `@deprecated` + janela 3 meses.
