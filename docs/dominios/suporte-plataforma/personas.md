---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas do domínio Suporte-Plataforma

---

## P-SUP-01 — Almoxarife / responsável de estoque

**Quem é:** 25-50 anos. Cuida do estoque central (peças, equipamentos, padrões). Pode acumular com técnico/gerente em tenant pequeno.

**Goals:**
- Saber em < 30s onde está cada peça (central / veículo / com técnico)
- Receber transferência de peça com aceite + foto obrigatória (JTBD-104)
- Alertar sobre estoque mínimo (JTBD-107)
- Não permitir saída sem lançamento na OS (JTBD-099)

**Frustrations:**
- "Técnico levou a peça e sumiu" (sem rastreabilidade)
- Peça vencida usada em calibração → cliente fica bravo
- Inventário físico que demora 8h

**Permissões:** Almoxarife — estoque (entrada/saída/transferência/inventário) + ver consumo por OS.

---

## P-SUP-02 — Metrologista de bancada (escolhe padrão)

Persona já listada no domínio Operação (P-OP-02). Toca Suporte-Plataforma ao:
- Escolher padrão pra calibração (lista filtrada por classe + validade + escopo)
- Registrar verificação intermediária do padrão (INV-022)
- Receber alerta de padrão precisando recalibrar

Detalhes em `docs/dominios/operacao/personas.md` P-OP-02.

---

## P-SUP-03 — Comprador / responsável de compras (V2 — Wave C)

**Quem é:** Pessoa que cuida da relação com fornecedor. Em tenant pequeno acumula com dono.

**Goals:**
- Cotar peça com 3+ fornecedores em paralelo
- Histórico de preços do fornecedor (subiu ou desceu?)
- Aprovar pedido de compra
- Conciliar nota fiscal de entrada com pedido

**Frustrations:**
- "Fornecedor me dá preço A; entrega com preço B"
- "Esqueci de renovar contrato — fornecedor parou de entregar"

**Permissões:** Comprador — fornecedor (CRUD) + cotação + aprovação compra + ver custo unitário.

---

## P-SUP-04 — Técnico de campo (consumo de peça no campo)

Persona já listada no domínio Operação (P-OP-01). Toca Suporte-Plataforma ao:
- Solicitar peça pra OS
- Receber transferência de peça (com aceite — 2 etapas, foto)
- Consumir peça ao concluir OS
- Registrar peça que ficou com cliente (devolução cobrada)

Detalhes em `docs/dominios/operacao/personas.md` P-OP-01.

---

## P-SUP-05 — Auditor CGCRE (V2)

**Quem é:** Auditor da CGCRE que verifica rastreabilidade de padrão durante auditoria de acreditação RBC do tenant.

**Goals (no Aferê via tenant):**
- Ver lista de padrões + certificado + classe + última verificação intermediária
- Ver lista de calibrações que usaram cada padrão
- Verificar que padrões vencidos não emitiram certificado

**Permissões:** Auditor read-only com acesso temporário do tenant.

---

## P-SUP-06 — Fornecedor externo (V2 quando portal)

**Quem é:** Empresa que vende peça/equipamento/serviço pro tenant. Sem login no Aferê na janela atual; em V2 talvez portal de cotação.

**Permissões:** Sem acesso direto (V2).

---

## Anti-personas

- **Tenant que quer estoque infinito** sem rastreabilidade → ANTI-12 (rastreabilidade obrigatória)
- **Tenant que quer importar Excel direto sem aceite 2-etapas** → INV-026 dedup + audit

---

## Referências

- `docs/discovery/personas-detalhadas.md`
- `docs/discovery/jobs-to-be-done.md` (BIG-08, BIG-12)
- `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` (rastreabilidade padrão)
