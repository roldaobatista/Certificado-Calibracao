---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 10-manutenibilidade
auditor: general-purpose (lente clean-code/refactoring)
veredito: MANUTENÍVEL COM RESSALVAS
---

# AUDIT-10 — Manutenibilidade / Dívida técnica / Duplicação / Acoplamento

> Lente 10 de 10.

## VEREDITO

**MANUTENÍVEL COM RESSALVAS** — arquitetura de camadas (domain Protocol → application use case → infra adapter) sólida e correta, mas views.py é God-class de 1016 linhas com regra de negócio embutida, e o padrão de auditoria/hash está copiado em 7 lugares. Replicar views.py como está propaga débito estrutural por N módulos.

## O que está bom (manter e replicar)

- Separação domain/application/infra rigorosa — esqueleto exemplar, DEVE ser o molde.
- VOs CPF/CNPJ imutáveis, validação eager, algoritmo Serpro, sem framework.
- DTOs frozen=True atravessando fronteiras.
- Constantes/enums isolados.
- Comentários explicam o PORQUÊ não-óbvio.
- Idempotência bloquear/desbloquear com select_for_update.

## Débitos

| ID | Descrição | Gravidade | Arquivo:linha | Replicar? | Refactor |
|---|---|---|---|---|---|
| D1 | views.py God-class: 1016 linhas, 8 actions, regra de negócio na view (~130 linhas só em bloquear). | ALTA | views.py:299-451,639-960 | NÃO | Validação → use cases/serializers; action fina chama use case; quebrar por US. |
| D2 | Helper audit + hashing PII copiado 6x com a mesma forma. | ALTA | views.py:175-187,245-268,424-442,513-526,901-931 | NÃO | audit/event_helpers.py com registrar_evento_cliente() único. |
| D3 | Regra pf_aceite_origem→base legal duplicada e divergente: lgpd.py:85 (dict nunca usado) vs importar_clientes.py:482 (if/if). | ALTA | lgpd.py:85 / importar_clientes.py:482 | corrigir já | Fonte única no domain; excluir _base_legal_do_origem. |
| D4 | Validação LGPD PF/PJ triplicada (models.clean / serializers.validate / importar_clientes). | ALTA | models.py:230 / serializers.py:84 / importar_clientes.py:333 | NÃO | Política LGPD em função de domínio única chamada pelos 3 boundaries. |
| D5 | except Exception: pass engolindo erro de upload.close(). | MÉDIA | views.py:721-722,958-960 | NÃO | logging.warning ou contextlib.suppress documentado. |
| D6 | Bug anti-formula-injection: sanitizar_celula_csv faz lstrip pra detectar mas retorna "'"+valor com whitespace original. "  =cmd" vira "'  =cmd" — Excel ainda interpreta. | ALTA | csv_safety.py:35-36 | corrigir já (bug segurança) | Retornar "'"+sem_ws_ini; testar com célula com espaços. |
| D7 | predicates_authz/views importam infrastructure.tenant/audit direto (não via porta). | MÉDIA | views.py:43,162,547 | herda | Envelope de audit (D2) isola num ponto. |
| D8 | import dentro de função em ~todas as actions; alguns desnecessários. | MÉDIA | views.py (todas actions) | NÃO | Imports no topo onde não há ciclo. |
| D9 | Imports não usados (field, ResultadoImportacao, ClienteImportacaoInput). Código morto — ruff pegaria; gate não rodou? | BAIXA | importar_clientes.py:35,40 | NÃO | Limpar; rodar ruff+mypy no módulo. |
| D10 | Inconsistência interna entre US (create via serializer; bloquear manual na view; mesclar misto). Checagens `is None` impossíveis (código morto defensivo). | MÉDIA | views.py:117-119,796-801 | NÃO | Padronizar entrada por serializer dedicado; remover checagens impossíveis. |

## Recomendação final

O padrão de CAMADAS é bom o suficiente pra ser molde do equipamentos — replique. Mas a camada de view NÃO deve ser replicada: God-class + validação na view + envelope audit copiado 6x. Resolver antes do M2 (não documentar): D2 (helper de evento único), D3 e D6 (bugs reais), D4 (política LGPD única), ViewSet fino como padrão. D9 indica que o quality gate (ruff/mypy) não foi aplicado no diff final — rodar no módulo.
