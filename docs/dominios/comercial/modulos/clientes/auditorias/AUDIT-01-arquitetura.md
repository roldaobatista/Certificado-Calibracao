---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 1-arquitetura
auditor: tech-lead-saas-regulado
veredito: DÉBITO ESTRUTURAL
---

# AUDIT-01 — Arquitetura / Camadas / DDD Hexagonal (módulo `clientes`)

> Auditoria crítica do Marco 1 antes de replicar o padrão no Marco 2 (`equipamentos`). Lente 1 de 10.

## VEREDITO

**DÉBITO ESTRUTURAL** — separação de pastas existe e o boilerplate está correto, mas há bug crítico de runtime que anula a proteção de concorrência da importação + anemic domain real (a entidade Cliente não existe como objeto de domínio) + invariantes só em 1-2 das 3 camadas que a ADR-0007 exige.

## O que está bom (manter e replicar)

- Value Objects puros e bem-feitos (`value_objects.py`): CPF/CNPJ/Email imutáveis, validam DV no `__post_init__`, sem Django. CNPJ alfanumérico (ADR-0017) correto.
- Repository como Protocol real + DTO `ClienteSnapshot` imutável atravessando fronteira (`repository.py:43`). Adapter injetado por construtor. DI de verdade.
- Use cases não importam Django — consomem só o Protocol.
- EventBus Protocol presente (ADR-0007 §4); zero Django signals.
- Defesa em profundidade tenant consistente.

## Débitos

| ID | Descrição | Gravidade | Arquivo:linha | Replicar? | Conserto |
|---|---|---|---|---|---|
| D-01 | Advisory lock + SERIALIZABLE não protegem nada. `transaction.atomic()` fecha na linha 215 contendo só o `pg_advisory_xact_lock`; o lock (xact) é liberado ao sair do `with`. Trabalho real (217-354) roda FORA do atomic e sem lock. Retry de SerializationFailure quase nunca dispara. Declarado "resolvido 2026-05-18" — NÃO está. | CRÍTICO | repositories.py:210-215 vs 217-354 | NÃO | Bloco 217-354 inteiro dentro do mesmo `with transaction.atomic()` que adquire o lock. Drill com 2 importações concorrentes do mesmo tenant. |
| D-02 | Anemic domain — não existe entidade `Cliente` de domínio. Só `ClienteSnapshot` (DTO) e `models.Cliente` (Django). Regra de negócio vive em `Model.clean()`/use case/serializer, nunca num agregado. ADR-0007 §2/§3(b) manda agregado com `assert_invariant_NNN()`. | ALTO | domain/comercial/clientes/ (ausência de agregado.py) | NÃO | Criar `domain/.../cliente.py` com entidade + métodos de invariante. Equipamentos começa PELO agregado. |
| D-03 | Lógica LGPD triplicada. "PF exige aceite / PJ exige dispensa / origem válida" copiada em models.py:230-258, serializers.py:84-104, importar_clientes.py:333-378. Três caminhos pro mesmo dado. | ALTO | models.py:213 / serializers.py:65 / importar_clientes.py:325 | NÃO | Centralizar em método de domínio único chamado pelos 3 pontos. |
| D-04 | Invariantes não estão nas 3 camadas exigidas. INV-024/036 só têm banco (UNIQUE). Aceite LGPD só `clean()`/serializer. Camada de domínio inexiste pra todas. | ALTO | models.py:6-10 / invariantes.py | CUIDADO | Por INV: CHECK + assert no agregado + teste citando ID. |
| D-05 | Auditoria espalhada na view. perform_create/mesclar/bloquear montam payload + chamam `registrar_auditoria` direto na view. Não passa pelo EventBus. Hash de PII repetido por endpoint. | MÉDIO | views.py:154-187, 244-268, 422-442 | CUIDADO | Emitir DomainEvent no use case; handler de audit assina. |
| D-06 | `get_by_id` viola o próprio contrato: no except DoesNotExist faz fallback pra `all_objects` e retorna deletado mesmo com `incluir_deletados=False`. | MÉDIO | repositories.py:65-76 | NÃO | Adapter cumpre o contrato; chamador pede `incluir_deletados=True` explícito. |
| D-07 | Normalização/inferência de documento duplicada entre use case e VOs do domínio. | BAIXO | importar_clientes.py:122-134 | CUIDADO | Delegar aos VOs. |

## Recomendação final

Corrigir D-01 no `clientes` ANTES do `equipamentos` — bloqueante; é bug ativo de concorrência declarado como resolvido sem estar. D-02/D-03/D-04 são débito estrutural a NÃO replicar — a ADR-0007 foi aceita mas não cumprida (existe a estrutura de pastas, não o agregado). Decisão: (1) fix D-01; (2) extrair agregado `Cliente` com política LGPD única (molde correto); (3) equipamentos começa pelo agregado. Aprovação dos 3 auditores Família 5 não cobriu bug de concorrência nem aderência fina à ADR — reforça necessidade de drill cronometrado e pentest externo antes do 1º tenant pago.
