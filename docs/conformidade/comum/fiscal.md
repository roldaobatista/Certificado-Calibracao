---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Conformidade fiscal — NFS-e municipal + NFe estadual

> **Pra quê:** mapear obrigações fiscais que o Aferê precisa atender quando módulo Financeiro entra em produção. Sem isso, "implementar NFS-e" vira "saber que tem que fazer, sem critério".

---

## 1. Matriz município × padrão (NFS-e)

| Município / região | Padrão | Cobertura via PlugNotas/Focus | Atenção |
|---------------------|--------|---------------------------------|---------|
| ABRASF (~70% dos municípios BR) | Nacional/ABRASF | ✅ ambos | Padrão mais estável |
| São Paulo (capital) | Próprio | ✅ ambos | Maior volume; mudanças frequentes |
| Rio de Janeiro | Próprio | ✅ ambos | Manutenções longas |
| Belo Horizonte | Próprio | ✅ ambos | |
| Curitiba | Próprio | ✅ ambos | |
| Salvador | Próprio | ✅ ambos | |
| Manaus | Próprio | ✅ ambos | |
| Vitória | FP2 exclusivo (regional) | ⚠️ verificar | Validar cobertura BaaS antes de aceitar tenant da região |
| **Padrão nacional novo (cutover 09/2026)** | **CONFAZ 95/22** | ⏳ ambos prometem cobrir | Janela competitiva (Dor #10) |

Consultar lista atualizada de municípios suportados por BaaS em `comum/integracoes-externas/plugnotas.md`.

---

## 2. NFe estadual

Quando entrar (V2): padrão único nacional, mais simples que NFS-e. Mesma estratégia via BaaS.

Calibração não tipicamente emite NFe — emite NFS-e (serviço). Mas se tenant também vender produtos físicos (peças, equipamentos), NFe entra.

---

## 3. Tipos de operação fiscal

| Operação | Obrigatoriedade |
|----------|-----------------|
| Emitir NFS-e por serviço | sim |
| Cancelar NFS-e (< 24h) | sim |
| Emitir CC-e (correção eletrônica > 24h) | sim |
| Modo contingência (SEFAZ fora) | sim — ver `fiscal-contingencia.md` |
| Inutilização de numeração | sim (numeração saltou) |
| Apuração mensal ISS | indireto (tenant decide com contador) |
| SPED Fiscal | indireto |

---

## 4. Atenções regulatórias específicas

### ISS (Imposto sobre Serviços)
- Alíquota varia por município (2-5%)
- Lei Complementar 116/2003 + atualizações
- Substituição tributária em alguns casos

### Retenções
- INSS (5% retido pra serviço prestado a pessoa jurídica em alguns casos)
- IRRF (1,5% pra serviços profissionais > R$ 666,68)
- CSLL/PIS/COFINS (1% + 0.65% + 3% em alguns regimes)
- Códigos de serviço LC 116/2003 — calibração tem código próprio (consultar)

### Regimes
- **Simples Nacional** — alíquota unificada (mais comum em ICP Aferê)
- **Lucro Presumido** — apuração mensal/trimestral
- **Lucro Real** — mais complexo (não-aplicável a tenant típico Aferê)

Aferê **não calcula imposto** — exibe campos pra tenant preencher conforme orientação do contador dele.

---

## 5. Auditoria fiscal

Tenant pode ser auditado pela Receita / Fisco municipal. Aferê fornece:
- Lista de NFS-e emitidas + canceladas + corrigidas
- XML original de cada NFS-e (preservado WORM 5 anos)
- Audit log de cada emissão
- Export em formato padrão SPED (V2)

Acesso "auditor read-only" (papel RBAC) — ver `auth-rbac.md`.

---

## 6. Auditor interno do Aferê

Auditor Segurança verifica:
- Endpoint de emissão sem MFA → FAIL
- NF-e emitida sem registro em audit log → FAIL
- XML não preservado em WORM → FAIL
- Cancelamento sem registro de razão → CONCERN

Auditor Produto verifica:
- AC "emite NFS-e em município X" cumprido antes do release

---

## 7. Pendências

- [ ] Criar `fiscal-contingencia.md` ✅ (este lote)
- [ ] Mapeamento de código de serviço LC 116 pra calibração
- [ ] UI de configuração de regime + alíquota por tenant
- [ ] Export SPED (V2)
- [ ] Smoke test cutover NFS-e 09/2026

---

## 8. Referências

- ADR-0008 (fiscal pluggable)
- `comum/integracoes-externas/plugnotas.md`
- `comum/integracoes-externas/focus-nfe.md`
- `comum/integracoes-externas/sefaz-municipios.md`
- `fiscal-contingencia.md`
- `retencao-matriz.md`
- Lei Complementar 116/2003
- Convênio CONFAZ 95/22
