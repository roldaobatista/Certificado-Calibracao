"""Migration 0019 — OS.equipamento nullable + indice parcial (ADR-0082 / D-OSME-2).

Fatia 1c da frente os-multi-equipamento.

Operacoes:
1. AlterField OS.equipamento: adiciona null=True (migration relaxante, reversivel).
   OS single-equip legada/avulsa mantem o valor; OS multi-equip grava NULL.
2. RemoveIndex os_tenant_equip_idx (indice denso, era (tenant, equipamento)).
3. AddIndex os_tenant_equip_idx PARCIAL condition=equipamento_id IS NOT NULL.
   Novo indice cobre apenas OS com equipamento na cabeca (single-equip legada/avulsa);
   OS multi-equip tem equipamento=NULL e nao paga custo de indice.

Reversivel: AlterField remove null=True; RemoveIndex/AddIndex restauram indice denso.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ordens_servico", "0018_os_multi_equipamento_rename_equipamento"),
    ]

    operations = [
        # 1. Relaxa NOT NULL de OS.equipamento (migration relaxante — nao destrutiva).
        migrations.AlterField(
            model_name="os",
            name="equipamento",
            field=models.ForeignKey(
                "equipamentos.Equipamento",
                on_delete=models.PROTECT,
                null=True,
                blank=True,
                related_name="ordens_servico",
                help_text=(
                    "INV-OS-EQP-001: equipamento BAIXADO/DESCARTADO bloqueia abertura. "
                    "NULL em OS multi-equipamento (ADR-0082 / D-OSME-2): cada atividade "
                    "tecnica carrega o SEU equipamento em AtividadeDaOS.equipamento_id. "
                    "OS single-equip legada/avulsa pode manter valor aqui."
                ),
            ),
        ),
        # 2. Remove indice denso antigo (tenant, equipamento) — incluia linhas NULL.
        migrations.RemoveIndex(
            model_name="os",
            name="os_tenant_equip_idx",
        ),
        # 3. Recria como indice PARCIAL: so linhas com equipamento NOT NULL.
        #    Django gera RemoveIndex + AddIndex quando o modelo tem condition;
        #    aqui forcamos a mesma sequencia manualmente para clareza.
        migrations.AddIndex(
            model_name="os",
            index=models.Index(
                fields=["tenant", "equipamento"],
                name="os_tenant_equip_idx",
                condition=models.Q(equipamento__isnull=False),
            ),
        ),
    ]
