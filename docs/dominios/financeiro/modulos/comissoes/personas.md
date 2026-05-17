---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Personas — Comissões

## P-COM-02 — Vendedor (primária)

**Quem é:** 25-50 anos. Vende calibração + peça + contrato. Vive da comissão; sem visibilidade transparente, perde confiança no dono.

**Jornada:**
1. Fecha venda → vê comissão prevista no app já no momento
2. Cliente paga → vê comissão virar devida (notificação)
3. Fim do mês → confere demonstrativo
4. Se discordar → abre contestação com histórico granular (JTBD-078)

**Frustrations:**
- "Recebi menos que devia — não sei onde foi descontado"
- "Comissão veio 2 meses depois — esqueci de quais clientes era"
- "Dono mudou a regra retroativamente — perdi R$ 800"

**Permissões:** ver própria comissão completa; histórico próprio reconstruível.

## P-OP-01 — Técnico de campo

**Toca o módulo:** similar ao vendedor; comissão sobre OS que ele executou (algumas regras tenant dão comissão pra técnico, não só pra vendedor — discovery valida).

**Permissões:** ver própria comissão.

## P-FIN-01 — Financeiro do tenant

**Jornada:**
1. Configura regras (cadastra % por beneficiário)
2. No fim do mês: fecha lote de comissões devidas
3. Paga (lança como contas a pagar ou folha — V2)
4. Trata contestações

**Frustrations:** "Sumiu uma comissão na planilha — agora preciso reconciliar tudo".

**Permissões:** configurar regras, ver tudo, pagar.

## P-FIN-02 — Dono

**Toca o módulo:**
- Vê total devido no mês (painel)
- Decide adiantar pagamento pra reter vendedor estrela
- Aprova mudança de regra (V2 — gate)

**Permissões:** ver tudo + alterar regras + aprovação alto nível.

## Anti-personas

- Vendedor demitido pedindo recálculo retroativo após mudança de regra — bloqueado por invariante "regra não-retroativa".
- Gerente comercial pedindo alterar regra individual sem registro — bloqueado por audit obrigatório.
- Vendedor querendo ver comissão do colega — não permitido.

## Referências

- JTBD-072 (previsão), JTBD-078 (contestar histórico), JTBD-082 (gatilho recebimento)
- `docs/dominios/comercial/personas.md` P-COM-02
- `docs/dominios/operacao/personas.md` P-OP-01
