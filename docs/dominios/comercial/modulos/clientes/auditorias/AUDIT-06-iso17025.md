---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 6-iso17025
auditor: consultor-rbc-iso17025
veredito: SUSTENTA COM RESSALVAS
---

# AUDIT-06 — ISO 17025 / Metrologia / Rastreabilidade / Confidencialidade

> Lente 6 de 10. Parecer consultivo — subagente IA sem credencial CGCRE; auditoria CGCRE real exige consultor RBC humano credenciado.

## VEREDITO

**SUSTENTA COM RESSALVAS** — com 1 débito regulatório que CONTAMINA calibração se replicado (D-01, mesclagem sem âncora de identidade). Confidencialidade (cl. 4.2) e imutabilidade (cl. 8.4) sólidas. O problema é rastreabilidade de identidade do cliente no tempo — exatamente o que um certificado emitido vai precisar 25 anos depois.

## O que está bom (manter)

- `id` UUID estável e `editable=False` (models.py:49) — identificador nunca muda; base correta cl. 8.4.
- Proibição de hard-delete + soft-delete auditável (deletado_em, all_objects).
- `on_delete=models.PROTECT` em todas as FKs de Cliente.
- Trilha de auditoria atende formato CGCRE (INSERT-only + trigger PG + hash chain + advisory lock + verificar_integridade_cadeia).
- Confidencialidade cl. 4.2: AcessoDadosCliente loga quem viu o quê com finalidade enumerada; PII nunca crua; segregação por papel.
- Matriz de retenção reconcilia Receita × ISO 25a × LGPD.

## Débitos

| ID | Descrição | Gravidade | Cláusula | Arquivo | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| D-01 | Mesclagem não grava âncora de identidade canônica. Soft-delete do perdedor + evento, mas o perdedor não recebe FK `cliente_canonico_id` pro vencedor. Certificado emitido pro cliente-perdedor fica apontando UUID soft-deleted sem caminho navegável até o cadastro vivo. Rastreabilidade depende de reconstruir do audit — frágil. | CRÍTICA / REGULATÓRIO | cl. 8.4, 7.8.2, NIT-DICLA-030 | mesclar_clientes.py:100; models.py:173 | SIM — contamina calibração | Campo `cliente_canonico_id` (FK, imutável) preenchido no soft-delete; resolução de identidade encadeada; drill cert pré-merge resolve cliente pós-merge. |
| D-02 | Evento cliente.mesclado (sustenta rastreabilidade 25a) vive em tabela de retenção 2-5a. Conflito de prazos. | ALTA | cl. 8.4 | retencao-matriz.md:34; US-CLI-005.md:28 | SIM | Eventos que afetam rastreabilidade ISO → faixa 25a/WORM. |
| D-03 | `documento` (CPF/CNPJ) mutável via aplicar_sobrescritas na mesclagem. Cliente que assinou cert deixa de ser identificável pelo documento do cert. | MÉDIA | cl. 7.8.2, NIT-DICLA-021 | mesclar_clientes.py:95; models.py:60 | SIM | Certificado deve snapshotar {cliente_id,nome,documento} na emissão. Cravar INV antes do módulo certificados. |
| D-04 | EventoTimeline descrito como append-only no modelo-de-dominio mas não implementado nem com trigger. | MÉDIA | cl. 8.4 | modelo-de-dominio.md:34-36 | SIM (lacuna) | Quando implementar, reusar padrão Auditoria (INSERT-only + trigger + retenção 25a). |

## Recomendação final

Não replicar antes de fechar D-01. Equipamento também será mesclável e referenciado por certificado 25a; a retencao-matriz já promete `cliente_id_original_hash` pro equipamento, mas o Cliente não tem o equivalente — incoerência. Ordem: (1) implementar D-01 (campo + preenchimento + resolução encadeada + drill) bloqueante M2; (2) D-02 reclassificar retenção do evento; (3) cravar INV de snapshot de identidade no cert (D-03); (4) D-04 guarda futura. Gatilho: 1ª auditoria CGCRE real exige consultor RBC humano credenciado (R$ 5-15k/engajamento).
