---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — tratamento de erro

> **Pra quê:** categorizar erros + handling padrão em todas as camadas. Sem isso, "erro genérico Python" sobe pra UI e Roldão vê stack trace.

---

## Taxonomia (5 categorias)

| Categoria | Exemplo | Tratamento |
|-----------|---------|------------|
| **ValidationError** | CPF inválido, campo obrigatório vazio | Retorna 400 + mensagem PT-BR no campo |
| **PermissionError** | Usuário X tentou ação que requer papel Y | Retorna 403 + audit log + alerta SEV-3 se padrão repete |
| **DomainError** | Regra de negócio violada (e.g., emitir certificado sem signatário) | Retorna 422 + mensagem PT-BR explicando |
| **InfrastructureError** | Banco indisponível, lib externa caiu | Retry com backoff (ver `retry.md`) + alerta SEV-2 |
| **ProgrammingError** | Bug no nosso código (None onde não devia) | Sentry + log + retorna 500 genérico ao usuário + alerta SEV-1 |

---

## Princípios

1. **Mensagens em PT-BR** pra usuário final — nunca expor stack trace, código de erro técnico, ou caminho de arquivo.
2. **Logs detalhados em stderr** (ver `log.md`) com `tenant_id`, `user_id_hash`, `request_id`.
3. **Errors propagam estruturados** — usar exceções tipadas, não `Exception` genérico.
4. **Hooks fail-safe** — handler de erro nunca pode levantar erro novo.
5. **Nada de `except: pass`** — bloqueado por hook `anti-mascaramento`.

---

## Exemplo (quando código existir)

```python
class CertificadoError(DomainError):
    """Erro de domínio: certificado."""

class CertificadoSemSignatarioError(CertificadoError):
    """Tentou emitir sem signatário válido."""

# views/certificate.py
@api_view(['POST'])
def emitir_certificado(request):
    try:
        cert = use_case.emit(request.data, tenant=request.tenant)
    except CertificadoSemSignatarioError as e:
        return Response({"erro": str(e), "campo": "signatario"}, status=422)
    except DomainError as e:
        return Response({"erro": str(e)}, status=422)
    except ValidationError as e:
        return Response(e.message_dict, status=400)
    except InfrastructureError:
        # retry no Celery
        return Response({"erro": "Indisponibilidade temporária. Tentamos novamente em segundos."}, status=503)
    # ProgrammingError vaza pra Sentry + middleware genérico
    return Response(serialize(cert), status=201)
```

---

## Hooks relacionados

- `anti-mascaramento.sh` — bloqueia `assert True`, `pass` em handler, skip sem motivo
- Auditor Qualidade — verifica em pre-commit

---

## Referências

- `log.md` (estrutura do log)
- `retry.md` (política de retry pra Infrastructure)
- `auditor-qualidade-prompt.md`
- `REGRAS-INEGOCIAVEIS.md` TST-001..003
