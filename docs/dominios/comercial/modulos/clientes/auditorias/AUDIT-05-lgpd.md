---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 5-lgpd
auditor: advogado-saas-regulado
veredito: CONFORME COM RESSALVAS
---

# AUDIT-05 — LGPD / Jurídico / PII / Base legal

> Lente 5 de 10. Minuta consultiva — subagente IA sem OAB; juízo regulatório final de incidente exige advogado humano licenciado.

## VEREDITO

**CONFORME COM RESSALVAS** — arquitetura de privacidade sólida; ressalvas R1–R9 do parecer original foram implementadas no código (não só documentadas). Porém há um vazamento de salt que reabre o FAIL crítico de segurança e uma incoerência de retenção a consertar antes de replicar.

## O que está bom (manter)

- Aceite versionado imutável (VERSAO_VIGENTE + TEXTOS_HISTORICOS, lgpd.py:18-34); snapshot em aceite_lgpd_versao; texto cita tenant como controlador + art. 7º II/V.
- PF exige aceite; PJ exige só com PF associada (models.py:230-246).
- Hash PII salgado por tenant (services.py:27-40) — doc/nome/IP hasheados.
- motivo_observacao com enum + regex anti-PII server-side (mesclagem.py:39-67).
- Arquivo CSV transitório (read em memória, nunca persistido; só hash no audit).
- Declaração de procedência obrigatória (ClienteImportacaoDeclaracao).
- Soft-delete corretamente NÃO tratado como esquecimento (art. 16 II + ISO 8.4).

## Débitos

| ID | Descrição | Gravidade | Base legal | Arquivo:linha | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| D1 | salt da importação é `sha256("afere-salt:{tenant.id}")` — string derivável publicamente (qualquer um com tenant_id reconstrói). Degrada hash de CPF a quase-rainbow-table. Reabre o FAIL crítico que `hashear_pii_com_salt_tenant` resolveu. | ALTA | LGPD art. 6º VII + art. 46 | views.py:830-832 | NÃO | Segredo real no salt (KMS/SECRET_KEY, não tenant_id); HMAC com chave server-side. |
| D2 | Incoerência de retenção: aceite LGPD/bloqueio vivem no audit WORM, mas base legal (art. 16 II) pede vínculo ao ciclo do cliente (5a + ISO 25a), não ao ciclo curto do audit (2-5a, retencao-matriz.md:34). Conflito não resolvido. | MÉDIA | LGPD art. 16 II/III + art. 6º III | retencao-matriz.md:34; models.py:82-85 | NÃO a ambiguidade | Linha explícita na matriz: aceite/bloqueio = retenção do cadastro-pai; fechar draft→stable. |
| D3 | perdedor_nome_hash + perdedor_documento_hash no audit de mesclagem vão além do necessário (art. 6º III). Audit prova *que* houve mesclagem, não *quais* dados. | MÉDIA | LGPD art. 6º III | views.py:261-266 | NÃO | Remover os hashes; manter só perdedor_id (UUID já identifica). |
| D4 | Regex anti-PII de telefone/CPF não pega variações coladas a texto. Defesa em profundidade, não barreira. | BAIXA | LGPD art. 6º VI/III | mesclagem.py:33-36 | replicar com reforço | Aceitável como camada; documentar limitação. |
| D5 | `_hashear_doc`/`_hashear_pii` aceitam tenant_id=None "retrocompat" — hash sem tenant = cross-tenant correlacionável. | BAIXA | LGPD art. 6º VII; INV-TENANT | views.py:52-61 | NÃO o fallback | tenant_id obrigatório; remover ramo None. |

## Recomendação final

Pode replicar, mas conserte D1 antes — único ALTA, mesmo erro de fundo (salt previsível) que segurança já vetou; replicá-lo em equipamentos propaga a falha. D2/D3 na sequência (médios). D4/D5 higiene. Sem não-conformidade que impeça dogfooding-only. Gatilho humano: antes de tenant externo pago, texto do aceite + catálogo de motivos + cláusula DPA precisam de advogado humano licenciado.
