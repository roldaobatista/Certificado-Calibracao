---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 2-seguranca
auditor: auditor-seguranca
veredito: SÓLIDO COM RESSALVAS
---

# AUDIT-02 — Segurança / Multi-tenant / RLS / Vazamento cross-tenant

> Lente 2 de 10. Régua: REGRAS-INEGOCIAVEIS.md (SEC-*, INV-TENANT-*, SEC-TENANT-*).

## VEREDITO

**SÓLIDO COM RESSALVAS** — base multi-tenant genuinamente forte (RLS + FORCE + NOBYPASSRLS reais, tenant_id server-side, trigger anti-mutation, hash PII salgado conserta o FAIL anterior de verdade). Mas há débitos reais que NÃO devem ser replicados cegamente.

## O que está bom (manter)

- tenant_id server-side via `UsuarioPerfilTenant` (middleware.py:77,113-136); header só seleciona dentro da lista permitida. Não forjável.
- RLS na MESMA migration (0002_rls_policies.py): ENABLE + FORCE + policies SELECT/INSERT/UPDATE/DELETE. INSERT amarrado a active_tenant_id.
- fail-loud sem fallback permissivo (`require_tenant_ctx()` RAISE EXCEPTION se contexto vazio).
- Connection patcher 3 camadas (RESET app.* no checkout do pool).
- Dedup cross-tenant safe via queryset filtrado, nunca via IntegrityError. UNIQUE parcial inclui tenant_id. Sem oracle.
- Hash PII salgado por tenant real (`afere-pii-salt:{tenant}:{valor}`).
- Trigger anti-mutation em auditoria e acessos_dados_cliente.
- CSV formula injection: lstrip antes de detectar gatilho; limite 2 MiB + linhas.

## Débitos

| ID | Descrição | Gravidade | Arquivo:linha | INV/SEC | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| SEG-D1 | Hash chain de auditoria não é cross-tenant-safe: `registrar_auditoria` pega `Auditoria.objects.order_by("-timestamp").first()` — sob RLS, "anterior" é filtrado pela lista de tenants do request. Tenant B encadeia ignorando linhas de A; verificador (sem RLS) recalcula contra ordem global e quebra. Frágil por design. | ALTA | services.py:134-136,157-176 | INV-TENANT-001 vs hash chain | NÃO — corrigir antes do M2 | Cadeia por tenant OU gravar em `run_as_system()` (cadeia global). Gravador e verificador no MESMO escopo. |
| SEG-D2 | Advisory lock emitido fora da seção crítica (mesmo achado D-01 da Lente 1). | MÉDIA | repositories.py:210-216 vs 217-354 | concorrência (lost-update PII) | NÃO | Mover lock pra dentro do atomic que envolve todo o bulk_upsert. |
| SEG-D3 | `_RE_CNPJ_AUDIT` com IGNORECASE+[A-Z0-9] casa quase qualquer alfanumérico de 14 chars; regex de telefone frouxa. Redação demais / falsa sensação se virar regra primária. | BAIXA | services.py:48-52 | SEC-LOG (defesa secundária) | CUIDADO | Denylist de chaves como defesa primária; regex secundária; testar com CNPJ ADR-0017. |
| SEG-D4 | `ADMIN_PATH_PREFIX="/admin/"` faz bypass total do TenantMiddleware; comentário sugere intenção de acesso cross-tenant via Admin sem trilha reforçada. | MÉDIA | middleware.py:48-50,67 | INV-TENANT-001 / isolamento-multi-tenant.md:111 | NÃO o bypass | Confirmar Admin roda como app_user (RLS ativa); suporte cross-tenant via support_user + trilha. Teste. |
| SEG-D5 | `get_by_id(incluir_deletados=False)` faz fallback pra all_objects; RLS ainda protege, mas amplia superfície e é padrão perigoso se copiado pra módulo sem RLS. | BAIXA | repositories.py:65-76 | INV-TENANT-001 (mitigado) | NÃO o fallback | Tornar incluir_deletados explícito; remover fallback. |

Secrets/KMS: sem chave hardcoded. SECRET_KEY via env sem default em base/prod. Senhas dev só em docker-compose/docs com sufixo explícito. SEC-001 não violado.

## Recomendação final

Não replicar o padrão antes de corrigir SEG-D1 e SEG-D2. SEG-D1 é o mais sério: a hash chain (pilar de imutabilidade ISO 17025/LGPD) é quebradiça por construção; o drill provavelmente passou por rodar single-tenant. Equipamentos terá ainda mais eventos — herdar multiplica. SEG-D2 vira corrupção de PII sob carga. SEG-D3/D5 podem ir pro backlog mas não copy-paste cego; SEG-D4 documentar política de acesso Admin/suporte antes do M2.
