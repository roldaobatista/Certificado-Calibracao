---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/lgpd-rat.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/dominios/comercial/modulos/clientes/prd.md
---

# Catálogo de finalidades LGPD (Aferê)

> **Pra quê:** centralizar as bases legais aceitas pelo produto. Toda decisão de autorização (`AuthorizationProvider.can(..., purpose=...)`) e todo registro de aceite (Cliente, futuros módulos) consulta este catálogo.
>
> **Quem mantém:** Roldão decide o que entra/sai (após parecer do subagente `advogado-saas-regulado` em cada mudança). Inclusão de finalidade nova exige PR + revisão.
>
> **Validado pelo:** subagente advogado-saas-regulado em 2026-05-18 (parecer em `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-001-advogado.md`).

---

## Catálogo inicial (4 entradas — MVP-1)

| Código | Base legal | Quando usar | Coleta consentimento extra? |
|---|---|---|---|
| `execucao_contrato` | LGPD Art. 7º V | Cadastro/atendimento de cliente, OS, agendamento, financeiro do contrato comercial | Não — base autoexecutável |
| `obrigacao_legal` | LGPD Art. 7º II | NF-e, certificado ISO 17025, RAT trabalhista, retenção fiscal | Não |
| `interesse_legitimo` | LGPD Art. 7º IX | Anti-fraude, dedup, métricas internas anonimizadas | Não — exige LIA (`docs/conformidade/comum/lia-template.md` quando for usado) |
| `consentimento` | LGPD Art. 7º I | Marketing/lembretes WhatsApp (RAT-06 opt-in), comunicação não-contratual | **SIM** — opt-in explícito, separado do aceite de cadastro (vedação de bundle Art. 8º §4º) |

---

## Como usar no código

### Em `AuthorizationProvider.can()`

```python
provider.can(
    usuario_id=u.id,
    action="cliente.criar",
    resource={"tipo_pessoa": "PF"},
    tenant_id=t.id,
    purpose="execucao_contrato",  # ← string deste catálogo
)
```

A porta grava o `purpose` em `authz_decisions.purpose` (INV-AUTHZ-002). Auditoria ANPD: "quais cadastros foram feitos com base 'consentimento' em 2027?" responde com `SELECT ... WHERE purpose = 'consentimento'`.

### No aceite do cliente (`Cliente.aceite_lgpd_finalidade` — implementação opcional)

Por hora, o catálogo só vive aqui em texto. Quando Wave B (LGPD portal/DPO) precisar tabela formal, esta lista vira seed da tabela `lgpd_finalidades`.

---

## Não-finalidades (rejeitadas explicitamente)

- ~~`marketing_geral`~~ — dilui base; usar `consentimento` específico (RAT-06 WhatsApp).
- ~~`outros`~~ — sem propósito específico viola Art. 6º I (finalidade).
- ~~`pesquisa_interna`~~ — anonimizar dados (Art. 12 §1º) e reclassificar como `interesse_legitimo` se realmente preciso.

---

## Histórico

| Data | Mudança |
|------|---------|
| 2026-05-18 | Criação. 4 finalidades iniciais validadas pelo advogado. |
