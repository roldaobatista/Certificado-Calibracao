---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Personas — Contas a Receber

Referência detalhada em `../../personas.md` e `docs/comum/personas.md`.

## P-FIN-01 — Responsável financeiro do tenant (primária)

**Quem é:** pessoa que opera cobrança diária. Em tenant pequeno pode ser o próprio dono.

**Jornada no módulo:**
1. Recebe notificação "OS concluída — gerar título?"
2. Confere valor, escolhe boleto ou PIX, emite
3. Cliente paga → vê baixa automática
4. Atrasou → régua dispara sozinha (Wave B); ele só intervém em casos extremos

**Frustrations:** "Tenho 200 boletos abertos e não sei quais cobrar primeiro" / "Cliente pagou mas não bateu — preciso conciliar OFX no Excel" / "Liguei pra cobrar e cliente já tinha pago — passei vergonha".

**Permissões:** emitir, baixar manualmente, configurar régua, ver tudo do tenant.

## P-FIN-02 — Dono

**Toca o módulo:** painel inadimplência > 30 dias (Wave B); decisão "perdoo este cliente fiel?" / "corto este?". Não opera cobrança diária.

**Permissões:** ver tudo; pode escalar/perdoar título.

## P-COM-02 — Vendedor

**Toca o módulo:** indireto — comissão dele depende de título recebido (gatilho OP4). Vê "Minha comissão" → lista de OSs com status pago/aberto.

**Permissões:** read-only nos próprios títulos relacionados.

## P-CLI — Cliente final do tenant

**Toca o módulo:** recebe link de pagamento (WhatsApp/email), paga, ganha comprovante. Pode acessar portal cliente (Wave B) e ver histórico.

**Frustrations:** "Boleto chegou sem identificar a OS" / "Paguei e tenant ligou cobrando" / "Não consigo segunda via".

**Permissões:** ver/baixar próprios títulos.

## Anti-personas

- Cobrador externo terceirizado pedindo acesso direto ao painel — não permitido (export controlado).
- Cliente final pedindo pra alterar valor — só tenant pode.
