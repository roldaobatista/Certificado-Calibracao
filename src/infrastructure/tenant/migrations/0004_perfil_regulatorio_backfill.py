# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-004 (Sprint 1)
# AC-SAN-PERFIL-001-1b — 2º step do 3-step T1:
#   ADD NULL (0003) -> backfill (este) -> SET NOT NULL (0005).
# RunPython com SELECT FOR UPDATE + INSERT TenantPerfilHistorico.
# Balanças Solution (slug=balancas-solution) = "B" — perfil rastreavel nao-acreditado.
# Demais tenants existentes (testes, drills) = "D" por padrao conservador.
#
# Justificativa Balanças Solution = "B":
# - Roldão e identificado em docs/prd.md §2 linha 30 explicitamente como perfil B.
# - Balancas Solution opera dogfooding na atual janela; nao acreditada CGCRE; e nao
#   esta em trilha formal D->A; mas atende clientes regulados ocasionais (Roldao
#   confirmou na auditoria de 10 lentes 2026-05-27 + AskUserQuestion).
# - Justificativa ≥100 chars cumpre INV-TENANT-PERFIL-005.

from __future__ import annotations

from django.db import migrations


JUSTIFICATIVA_BALANCAS_SOLUTION = (
    "Balancas Solution e identificada explicitamente em docs/prd.md §2 linha 30 "
    "como perfil B (rastreavel nao-acreditado) — atende clientes regulados "
    "ocasionais. Roldao confirmou em AskUserQuestion da auditoria de 10 lentes "
    "2026-05-27. ADR-0067 aceita 2026-05-27. Provisionamento inicial sem documento "
    "CGCRE (perfil B nao exige acreditacao formal)."
)


JUSTIFICATIVA_PADRAO_TENANTS_RESIDUAIS = (
    "Tenant pre-saneamento sem perfil declarado explicitamente recebe D "
    "(comercial puro) por padrao conservador da migration 0004 — sem rituais ISO "
    "17025 ate confirmacao manual via aplicar_evento_cgcre direcao=CORRECAO_"
    "ADMINISTRATIVA. Aplica-se a tenants de teste/drill nao-canonicos."
)


def backfill_perfis(apps, schema_editor):
    """Itera tenants existentes com perfil_regulatorio NULL e atribui perfil + historico.

    NAO usa SECURITY DEFINER (essa funcao so existe na migration 0008 — esta migration
    e anterior). UPDATE direto e permitido aqui porque a trigger anti-mutacao tambem
    e criada apenas na migration 0008.

    NOTA tecnica: RunPython em Django 5.x roda DENTRO de transacao por default
    (atomic=True na declaracao da Migration). Nao usa select_for_update aqui
    porque (a) backfill e one-shot e (b) Django migrations ja serializam acesso
    via lock de migrations table; concorrencia entre migrations e impossivel.
    """
    Tenant = apps.get_model("tenant", "Tenant")
    # TenantPerfilHistorico ainda nao existe (criado na migration 0007) — armazenar
    # eventos de backfill em campo JSONB temporario do Tenant nao e opcao. Solucao:
    # rodar 0004 ANTES de 0007 cria janela de inconsistencia. Decisao do plan.md:
    # ordem das migrations e 0003 -> 0004 -> 0005 -> 0006 -> 0007. Significa que
    # historico de PROVISIONAMENTO_INICIAL desses tenants legados sera cravado na
    # migration 0007 (ou posterior) lendo perfil_regulatorio atual. Ver T-SAN-PERFIL-007.

    for tenant in Tenant.objects.filter(perfil_regulatorio__isnull=True):
        if tenant.slug == "balancas-solution":
            tenant.perfil_regulatorio = "B"
        else:
            # Heuristica conservadora — perfil D para tenants nao-canonicos.
            tenant.perfil_regulatorio = "D"
        tenant.save(update_fields=["perfil_regulatorio"])


def rollback_backfill(apps, schema_editor):
    """Rollback: zera perfis para NULL. Util apenas em dev — em prod, rollback
    desta migration exige 0005 nao ter rodado (CHECK constraint bloquearia)."""
    Tenant = apps.get_model("tenant", "Tenant")
    Tenant.objects.update(perfil_regulatorio=None)


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0003_perfil_regulatorio_add_nullable"),
    ]

    operations = [
        migrations.RunPython(
            backfill_perfis,
            reverse_code=rollback_backfill,
            elidable=False,
        ),
    ]
