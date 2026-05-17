---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Contrato UI — Frota

## Telas MVP-1

### T-FRT-01 — Lista de veículos
- Colunas: Foto, Placa, Modelo, Categoria, Responsável atual, Km, Status (Ativo/Manutenção/Inativo), Próx. revisão.
- Filtros: Categoria, Status, Responsável.
- Ações: Novo veículo, Exportar.

### T-FRT-02 — Cadastro/edição de veículo
- Seções: Identificação (placa, chassi, RENAVAM), Modelo/Marca/Ano, Categoria, Combustível, Aquisição (data/valor opcional), Documentos (CRLV, apólice).
- Validação placa: formato brasileiro (LLL-NNNN ou Mercosul) + dedup por tenant.

### T-FRT-03 — Painel do motorista UMC (CRÍTICO — INV-020)
- **Quem vê:** Motorista (próprio) + Gerente + Dono.
- **Topo da tela:** Status atual da jornada com semáforo:
  - VERDE: "Você pode dirigir mais Xh Ymin antes do próximo descanso."
  - AMARELO (T-5min até 5h30): "Pare em 5 min pra descansar 30 minutos. Regra de trânsito."
  - VERMELHO: "Você precisa parar AGORA. Continuar é violação da Lei 13.103. Avise o gerente."
- **Cronômetro grande** com tempo até próxima parada obrigatória.
- **Botões:** Iniciar direção, Registrar pausa (30 min descanso / refeição / espera), Encerrar jornada.
- **Histórico de hoje:** Linha do tempo com pausas + segmentos de direção.
- **Acessibilidade:** Tela legível em sol forte (contraste alto), botões grandes (uso em campo), funciona offline com sincronização (INV-016).

### T-FRT-04 — Agendamento de OS (lado do gerente — bloqueio INV-020)
- Ao escolher motorista + horário, painel lateral mostra:
  - "Esta OS adiciona Xh à jornada de [Nome]. Total previsto: Yh. **OK.**"
  - OU: "Esta OS faz [Nome] violar Lei 13.103: Z. Opções: 1) trocar motorista, 2) adiar pra dia seguinte, 3) dividir em 2 OS."
- Botão "Agendar mesmo assim" **NÃO EXISTE**. Bloqueio duro (INV-020).

### T-FRT-05 — Checklist pré-viagem
- Lista de itens; itens críticos marcados com escudo (ícone + cor).
- Itens default críticos: "Padrões com calibração vigente conferida", "Verificação intermediária dos padrões OK (INV-022)", "Certificados de padrão a bordo", "Pneus + freio + óleo + nível", "Documento do veículo (CRLV)", "CNH do motorista válida".
- Item crítico não-marcado → botão "Iniciar OS" bloqueado.

### T-FRT-06 — Comprovante de jornada (PDF exportável)
- Botão "Gerar comprovante" no painel do motorista.
- PDF/UA conforme (INV-016) — pro caso de fiscalização.

### T-FRT-07 — Manutenção (lista + cadastro)
- Lista de manutenções por veículo; lembrete visual de próx. revisão.

### T-FRT-08 — Abastecimento (cadastro rápido em campo)
- Form curto: km, litros, R$, foto da nota. Geolocalização opcional.

### T-FRT-09 — Caixa do técnico (OP3.2 — link com Financeiro)
- Solicitar adiantamento, registrar despesas, fechar e reconciliar.

## Mensagens (linguagem sem jargão)

| Erro | Mensagem na tela |
|---|---|
| INV-020 violation no agendamento | "Esta agenda viola a regra de trânsito do motorista profissional (Lei 13.103). Veja opções alternativas abaixo." |
| INV-020 alerta 5h25 | "Pare em 5 minutos pra um descanso de 30 minutos. Regra obrigatória de trânsito." |
| Atribuição inválida | "Esse colaborador não tem cadastro de motorista. Adicione o papel de motorista no perfil dele antes." |
| Checklist crítico não marcado | "Não dá pra iniciar a OS: o item [X] é obrigatório por regra de qualidade. Confirme antes de sair." |

## Acessibilidade

WCAG 2.1 AA (INV-016) — especialmente crítico no T-FRT-03 (uso em campo, sol, mãos ocupadas).
