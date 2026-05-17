---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Personas — Frota

## Primárias

### P-FRT-01 — Motorista UMC (= P-RFQ-01 + Persona 9)
- **Goal:** Saber se posso pegar a próxima OS sem violar a lei + não dirigir mais que 5h30 sem parar.
- **Frustração hoje:** Gerente marca OS no susto, eu chego no cliente e não posso voltar pra base no mesmo dia. Fiscal pede caderneta de jornada — eu não tenho.
- **Cenário típico:** Saio às 6h, chego no cliente 8h, faço calibração, gerente quer marcar mais um cliente longe. App tem que avisar: "se você pegar essa OS, vai violar a lei — chame outro técnico ou agende pra amanhã".
- **Permissões:** Self-service da própria jornada + checklist pré-viagem + iniciar/encerrar OS + caixa do técnico.

### P-FRT-02 — Gerente operacional (atribui veículo + agenda)
- **Goal:** Atribuir veículo a OS sem violar jornada legal; ver alertas de manutenção vencida.
- **Frustração hoje:** Não sei a jornada do motorista; não sei se carro foi pra revisão; abasteço de surpresa.
- **Cenário típico:** Vai marcar OS — sistema mostra "Motorista João tem 3h45 de direção hoje. Esta OS adiciona 2h. Tudo OK." OU "Esta OS faz Motorista João violar Lei 13.103. Opções: trocar motorista, dividir OS, adiar."

### P-FRT-03 — Dono (aprova veículo + caixa)
- **Goal:** Ver custo total da frota mensalmente; aprovar adiantamento de caixa do técnico.
- **Frustração hoje:** Combustível + manutenção em planilha; quanto custa cada UMC? Não sei.
- **MVP-1 entrega:** Lista de custos por veículo + caixa do técnico. TCO completo = Wave C.

## Secundárias

### P-FRT-04 — Técnico de campo não-motorista
- **Goal:** Usar veículo de pool sem ser motorista profissional (categoria B).
- **Diferença:** Lei 13.103 NÃO se aplica (não é UMC + não é profissional). Só checklist pré-viagem básico.

### P-FRT-05 — Responsável pela qualidade (P-RFQ-02)
- **Goal:** Auditar que padrões metrológicos a bordo da UMC têm calibração vigente (INV-011) + verificação intermediária (INV-022).
- **Toque aqui:** Checklist pré-viagem inclui "padrões calibrados conferidos?" como item bloqueante.

### P-FRT-06 — Financeiro
- **Goal:** Reconciliar caixa do técnico + repassar pedágio/combustível ao cliente quando contrato prevê.
- **Toque aqui:** Lê abastecimento + caixa daqui (read-only).

## Anti-personas

- **Tenant que NÃO registra jornada** → INV-020 não-negociável. App bloqueia OS + gera alerta + grava NC interna.
- **Tenant que dirige UMC com motorista sem CNH/E** → bloqueio duro no cadastro.
- **Tenant que tenta usar veículo de pessoa física no nome do dono pra evitar registro** → fora do escopo MVP-1, sem hook (problema fiscal do tenant).

## Referências

- Persona 9 motorista UMC (`docs/discovery/personas-detalhadas.md`)
- BIG-08 / OP3.2 (`docs/discovery/`)
- INV-020 + CLT 235-C §9
