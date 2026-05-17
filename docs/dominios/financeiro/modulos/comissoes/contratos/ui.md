---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Contrato UI — Comissões

## Telas

### TC-01 — Minha comissão (app vendedor/técnico)

- Cabeçalho: mês atual + seletor de período
- Cards: "Prevista" (calculado, aguardando cliente pagar) + "Devida" (pode receber) + "Paga"
- Lista detalhada: OS, cliente, valor da OS, % aplicado, valor da comissão, status, data
- Filtro por status (toggle)
- Acessível ofline (cache último fechamento)

### TC-02 — Detalhe da comissão

- Cabeçalho: OS + cliente + data execução
- Cálculo transparente: "Sua comissão = R$ {base} × {%} = R$ {valor}"
- Linha do tempo: OS concluída → título emitido → cliente pagou → comissão liberada → paga
- Botão "Contestar" (abre formulário com motivo + anexo)

### TC-03 — Painel financeiro (admin)

- Lista de comissões devidas no período
- Total devido por beneficiário
- Botão "Fechar mês e gerar lote"
- Exportar pra contas a pagar / folha (V2)

### TC-04 — Cadastro de regras

- Lista de beneficiários + % vigente
- Editar: nova vigência (não altera o passado)
- Alerta visível: "Esta alteração só vale pra OSs concluídas a partir de {data}. Comissões anteriores não mudam."

### TC-05 — Contestações (admin)

- Lista aberta
- Visão lado a lado: cálculo do sistema vs reclamação do beneficiário
- Botões: "Manter cálculo" / "Ajustar com correção" (gera evento auditável)

## Mensagens visíveis

| Contexto | Mensagem |
|---|---|
| Comissão prevista | "Aguardando cliente pagar para liberar." |
| Comissão devida | "Pronta para receber no próximo fechamento." |
| Comissão estornada | "Cliente cancelou esta OS após você ter recebido. R$ {x} estornado." |
| Mudança de regra | "Atenção: esta mudança só vale do dia X em diante." |

## Acessibilidade

- App offline-first (técnico em campo sem 4G)
- Cores + ícone + texto pra status (WCAG AA)

## Non-goals UI

- Configurador visual de fórmulas complexas (Wave B/V2)
- Gamificação / metas com ranking (Wave B)

## Referências

- BIG-09 / JTBD-072 / JTBD-078
