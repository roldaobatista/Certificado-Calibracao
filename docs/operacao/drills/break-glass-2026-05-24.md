---
owner: roldao
revisado-em: 2026-05-24
status: stable
diataxis: reference
audiencia: auditor
tipo: drill-break-glass-criacao
relacionados:
  - docs/operacao/runbook.md
  - docs/faseamento/F-C1/spec.md
  - REGRAS-INEGOCIAVEIS.md
---

# Drill break-glass — 2026-05-24 (1ª execução em F-C1)

> **AC-FC1-006-5 + INV-ADMIN-003.** 1ª execução do `criar_admin_recovery`
> arquivada no escopo F-C1. Conta criada em ambiente dogfooding;
> credencial real **será rotacionada** antes do 1º deploy externo
> (Wave A — quando WebAuthn entrar).

## Contexto

- **Operador:** Roldão Batista (operação executada pelo agente Claude
  Code sob autorização explícita "voce faz tudo")
- **Ambiente:** dogfooding local (Docker Desktop Windows; container
  `afere-app`; banco `afere`)
- **Hora:** 2026-05-24

## Comando executado

```bash
docker compose exec -T app bash -c "printf 'CRIAR BREAK-GLASS admin-recovery@afere.local\ndrill-senha-14ch-x\ndrill-senha-14ch-x\n' | poetry run python manage.py criar_admin_recovery --email admin-recovery@afere.local --nome-completo 'Conta Recovery Roldão Batista'"
```

> **NOTA SOBRE SENHA:** `drill-senha-14ch-x` é placeholder de drill (14
> chars, sem complexidade real). Roldão **DEVE rotacionar** a senha
> desta conta antes de qualquer cenário onde ela possa ser usada de
> verdade. Rotação manual via Django admin (`/admin/usuario/usuario/`)
> ou via Django shell:
>
> ```python
> from src.infrastructure.usuario.models import Usuario
> u = Usuario.objects.get(email="admin-recovery@afere.local")
> u.set_password("<senha-real-complexa-com-entropia>")
> u.save()
> ```

## Resultado

- **Conta criada:** `admin-recovery@afere.local`, id
  `02ec172e-f491-4d17-8bf4-d7099b5e60af`.
- **Flags:** `is_break_glass=True`, `is_superuser=True`, `is_staff=True`,
  `mfa_obrigatorio=True`, `is_active=True`.
- **Evento na cadeia auditável imutável:** id
  `29cbd69d-ba27-4046-aa6b-292d3ccf3dd1`, ação
  `Admin.BreakGlass.CONTA_CRIADA`, `tenant_id=NULL` (cadeia sistema),
  `resource_summary=usuario=admin-recovery@afere.local`.
  Payload sanitizado contém `usuario_id`, `email`,
  `forcar_rotacao_senha=False`, `criado_via=manage.py criar_admin_recovery`.
  Hash chain válido (verificado via `verificar_integridade_cadeia()`).

## Validação dos GATEs

| GATE | Status pós-drill |
|---|---|
| Confirmação literal `CRIAR BREAK-GLASS <email>` exigida | ✅ aplicada (input 1) |
| Senha ≥14 chars validada | ✅ `drill-senha-14ch-x` tem 18 chars |
| Limite ≤2 contas `is_break_glass=True` | ✅ 1 conta agora (1ª da instalação) |
| Evento `Admin.BreakGlass.CONTA_CRIADA` na cadeia | ✅ id 29cbd69d-... |
| `is_superuser=True` + `is_staff=True` + `mfa_obrigatorio=True` | ✅ todos setados |

## Comportamento do middleware (não testado neste drill)

- AdminHardeningMiddleware camada 1 (MFA): com `is_break_glass=True` +
  device não-WebAuthn → 403 com motivo `break_glass_sem_u2f`
  (GATE-CYBER-BREAKGLASS-U2F-ENFORCE — INV-ADMIN-003 conserto P5).
- Camada 2 (IP allowlist): bypassada quando `is_break_glass=True`
  (qualquer IP loga; alerta crítico).
- Camadas 3 (rate-limit) e 4 (session-rebind): aplicadas normalmente.

**Cobertura de teste:** `tests/test_inv_admin_003_break_glass.py` cobre
o helper `_device_eh_webauthn` + invariantes do campo + gravação na
cadeia. 5/5 passed em 2026-05-24.

## Próximos passos obrigatórios

1. **Rotacionar senha** da conta `admin-recovery` antes de uso real
   (placeholder `drill-senha-14ch-x` está visível neste log público).
2. **Cadastrar U2F WebAuthn** quando Wave A integrar `django-otp-webauthn`
   (sem U2F, login fica bloqueado pelo middleware — comportamento
   intencional do GATE-CYBER-BREAKGLASS-U2F-ENFORCE).
3. **Drill mensal**: logar com a conta uma vez por mês quando o WebAuthn
   estiver ativo + arquivar `docs/operacao/drills/break-glass-drill-mensal-YYYY-MM.md`.

## Status do AC-FC1-006

| AC | Status |
|---|---|
| AC-FC1-006-1 (Usuario.is_break_glass field) | ✅ FECHADO (commit f43faaa) |
| AC-FC1-006-2 (middleware exige U2F WebAuthn) | ✅ FECHADO (commit 4957cf5) |
| AC-FC1-006-3 (comando criar_admin_recovery) | ✅ FECHADO (commit f43faaa) |
| AC-FC1-006-4 (runbook §11.bis) | ✅ FECHADO (commit f43faaa) |
| AC-FC1-006-5 (1ª execução em F-C1 arquivada) | ✅ FECHADO neste log |
