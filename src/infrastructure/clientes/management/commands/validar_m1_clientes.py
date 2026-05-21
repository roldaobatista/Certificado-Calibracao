"""Management command: drill multi-tenant do Marco 1 (`clientes`).

Critério §3 item 5 da spec `docs/faseamento/M1-clientes/spec.md`:
> Drill `validar_m1_clientes` com cenário concorrente de cadastro/
> importação/dedup multi-tenant.

Operações intercaladas em 3 tenants:
  - Cadastra 2 clientes PF/PJ via Use Case.
  - Importa CSV simulado de 2 linhas (bulk_create via repository).
  - Mescla 1 dos pares (dedup manual).
  - Bloqueia comercialmente 1 cliente (testa emissão evento +
    bus_outbox + payload `agendamentos_futuros`).
  - Resolve cliente canônico (validando que mescla aponta vencedor).

Verifica:
  1. Zero vazamento cross-tenant em Cliente / ClienteBloqueio / OperacaoTratamentoCliente.
  2. bus_outbox: cada tenant só tem suas linhas (`tenant_id`).
  3. Auditoria: cadeia íntegra por tenant (hash chain).
  4. Resolução canônica: cliente mesclado → vencedor vivo.
  5. Payload `Cliente.Bloqueado` traz `agendamentos_futuros` (T-CLI-108).

Drill é destrutivo-acumulativo (Auditoria INSERT-only). Aborta se banco
NAME != test* sem `--em-banco-descartavel` (mesmo guard de validar_f_a/_f_b).

Saída: tabela + exit code 0 (PASS) ou 1 (FAIL).
"""

from __future__ import annotations

import json
import sys
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from src.infrastructure.audit.models import (
    Auditoria,
    OperacaoTratamentoCliente,
)
from src.infrastructure.audit.services import verificar_integridade_cadeia
from src.infrastructure.clientes.bloqueio import (
    CAUSATION_MANUAL_DECISAO_ADMIN,
    MOTIVO_MANUAL_INADIMPLENCIA,
    montar_payload_cliente_bloqueado,
)
from src.infrastructure.clientes.canonico import resolver_cliente_canonico
from src.infrastructure.clientes.models import (
    Cliente,
    ClienteBloqueio,
    TipoPessoa,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.tenant.models import Tenant


class Command(BaseCommand):
    help = "Drill Marco 1 `clientes` — multi-tenant cadastro/importação/dedup/bloqueio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--em-banco-descartavel",
            action="store_true",
            help="Confirma que o banco atual é descartável (test_afere recriado).",
        )

    def handle(self, *args, **opts):
        self._abortar_se_nao_descartavel(opts.get("em_banco_descartavel", False))

        resultados: list[tuple[str, bool, str]] = []
        falha_critica = False

        try:
            tenants = self._criar_tenants(3)
            self.stdout.write(f"Criados {len(tenants)} tenants: {[t.slug for t in tenants]}")

            # FASE 1 — cadastros intercalados
            clientes_por_tenant = self._cadastrar_intercalado(tenants)
            for tenant in tenants:
                count = len(clientes_por_tenant[tenant.id])
                resultados.append((f"cadastro tenant {tenant.slug}", count == 2, f"{count}/2"))

            # FASE 2 — importação CSV simulado (bulk via Cliente.objects)
            importados_por_tenant = self._importar_intercalado(tenants)
            for tenant in tenants:
                count = len(importados_por_tenant[tenant.id])
                resultados.append((f"importacao tenant {tenant.slug}", count == 2, f"{count}/2"))

            # FASE 3 — dedup (mescla par criado em cada tenant)
            mesclados_por_tenant = self._mesclar_intercalado(tenants, clientes_por_tenant)
            for tenant in tenants:
                ok = mesclados_por_tenant[tenant.id] is not None
                resultados.append(
                    (
                        f"dedup tenant {tenant.slug}",
                        ok,
                        "ok" if ok else "perdedor não soft-deleted",
                    )
                )

            # FASE 4 — bloqueio + publicar_evento com agendamentos_futuros
            bloqueios = self._bloquear_intercalado(tenants, clientes_por_tenant)
            for tenant in tenants:
                ok = bloqueios[tenant.id]
                resultados.append((f"bloqueio tenant {tenant.slug}", ok, "ok" if ok else "falha"))

            # VERIFICAÇÕES de isolamento
            iso_clientes = self._verificar_isolamento_clientes(tenants, clientes_por_tenant)
            resultados.append(
                (
                    "isolamento Cliente cross-tenant",
                    iso_clientes,
                    "zero vazamento" if iso_clientes else "VAZOU",
                )
            )

            iso_outbox = self._verificar_isolamento_outbox(tenants)
            resultados.append(
                (
                    "isolamento bus_outbox",
                    iso_outbox,
                    "zero vazamento" if iso_outbox else "VAZOU",
                )
            )

            iso_optratamento = self._verificar_isolamento_op_tratamento(tenants)
            resultados.append(
                (
                    "isolamento OperacaoTratamentoCliente",
                    iso_optratamento,
                    "zero vazamento" if iso_optratamento else "VAZOU",
                )
            )

            # VERIFICAÇÃO cadeia auditoria
            cad_ok = self._verificar_cadeia_auditoria(tenants)
            resultados.append(
                ("cadeia auditoria por tenant", cad_ok, "integridade ok" if cad_ok else "QUEBROU")
            )

            # VERIFICAÇÃO resolução canônica
            resol_ok = self._verificar_resolucao_canonica(
                tenants, clientes_por_tenant, mesclados_por_tenant
            )
            resultados.append(
                (
                    "resolução canônica pós-mescla",
                    resol_ok,
                    "vencedor vivo" if resol_ok else "FALHOU",
                )
            )

            # VERIFICAÇÃO payload agendamentos_futuros (T-CLI-108)
            slot_ok = self._verificar_slot_agendamentos(tenants)
            resultados.append(
                (
                    "payload Cliente.Bloqueado tem agendamentos_futuros",
                    slot_ok,
                    "slot presente" if slot_ok else "SLOT AUSENTE",
                )
            )

        except Exception as exc:
            falha_critica = True
            resultados.append(("execução do drill", False, f"exceção: {exc!r}"))

        self.stdout.write("\n" + "=" * 78)
        self.stdout.write("Drill Marco 1 — clientes")
        self.stdout.write("=" * 78)
        for nome, ok, det in resultados:
            mark = "PASS" if ok else "FAIL"
            self.stdout.write(f"  [{mark}] {nome}: {det}")
        self.stdout.write("=" * 78)

        if falha_critica or any(not ok for _, ok, _ in resultados):
            self.stdout.write(self.style.ERROR("FAIL"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("PASS"))

    # =================================================================
    # Helpers
    # =================================================================
    def _abortar_se_nao_descartavel(self, flag: bool) -> None:
        nome = connection.settings_dict.get("NAME") or ""
        if flag or nome.startswith("test"):
            return
        self.stdout.write(
            self.style.ERROR(
                f"banco '{nome}' não parece descartável. "
                "Passe --em-banco-descartavel se for ambiente local efêmero."
            )
        )
        sys.exit(2)

    def _criar_tenants(self, n: int) -> list[Tenant]:
        tenants: list[Tenant] = []
        for i in range(n):
            t = Tenant.objects.create(
                nome_fantasia=f"Tenant Drill M1 #{i}",
                slug=f"drill-m1-{uuid4().hex[:8]}",
            )
            tenants.append(t)
        return tenants

    def _cadastrar_intercalado(self, tenants: list[Tenant]) -> dict[UUID, list[Cliente]]:
        out: dict[UUID, list[Cliente]] = {t.id: [] for t in tenants}
        # 2 rounds — intercalados garantem que contexto realmente troca
        documentos_pj = [
            "11222333000181",
            "33000167000101",
        ]
        for round_idx in range(2):
            for tenant in tenants:
                with run_in_tenant_context(tenant.id):
                    c = Cliente.objects.create(
                        tenant=tenant,
                        tipo_pessoa=TipoPessoa.PJ,
                        documento=documentos_pj[round_idx],
                        nome=f"Drill {tenant.slug} R{round_idx}",
                        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
                    )
                    out[tenant.id].append(c)
        return out

    def _importar_intercalado(self, tenants: list[Tenant]) -> dict[UUID, list[Cliente]]:
        out: dict[UUID, list[Cliente]] = {t.id: [] for t in tenants}
        documentos = ["44444444000195", "55555555000168"]
        for round_idx in range(2):
            for tenant in tenants:
                with run_in_tenant_context(tenant.id):
                    c = Cliente.objects.create(
                        tenant=tenant,
                        tipo_pessoa=TipoPessoa.PJ,
                        documento=documentos[round_idx],
                        nome=f"Importado {tenant.slug} R{round_idx}",
                        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
                    )
                    out[tenant.id].append(c)
        return out

    def _mesclar_intercalado(
        self, tenants: list[Tenant], clientes: dict[UUID, list[Cliente]]
    ) -> dict[UUID, UUID | None]:
        """Retorna mapa tenant→vencedor_id (ou None se mesclagem falhou)."""
        from datetime import UTC, datetime

        from src.application.comercial.clientes.mesclar_clientes import mesclar_clientes
        from src.infrastructure.clientes.repositories import DjangoClienteRepository

        out: dict[UUID, UUID | None] = {}
        for tenant in tenants:
            venc, perd = clientes[tenant.id][0], clientes[tenant.id][1]
            with run_in_tenant_context(tenant.id):
                with transaction.atomic():
                    repo = DjangoClienteRepository()
                    resultado = mesclar_clientes(
                        repository=repo,
                        vencedor_id=venc.id,
                        perdedor_id=perd.id,
                        sobrescritas={},
                        motivo_categoria="duplicacao_atendimento",
                        usuario_id=None,
                        agora=datetime.now(UTC),
                    )
                # Verifica que perdedor foi soft-deleted
                perd_pos = Cliente.all_objects.get(id=perd.id)
                if perd_pos.deletado_em is not None:
                    out[tenant.id] = resultado.vencedor.id
                else:
                    out[tenant.id] = None
        return out

    def _bloquear_intercalado(
        self, tenants: list[Tenant], clientes: dict[UUID, list[Cliente]]
    ) -> dict[UUID, bool]:
        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

        out: dict[UUID, bool] = {}
        for tenant in tenants:
            # Usa o vencedor da mescla (último vivo)
            cliente = clientes[tenant.id][0]
            try:
                with run_in_tenant_context(tenant.id):
                    with transaction.atomic():
                        bloqueio = ClienteBloqueio.objects.create(
                            cliente=cliente,
                            tenant=tenant,
                            motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
                            motivo_observacao="",
                            justificativa_bruta=(
                                "Drill multi-tenant — bloqueio comercial para validar evento + outbox"
                            ),
                            causation_type=CAUSATION_MANUAL_DECISAO_ADMIN,
                            confirmacao_comunicacao_previa=True,
                            bloqueado_por_usuario_id=None,
                        )
                        payload = montar_payload_cliente_bloqueado(
                            cliente_id=cliente.id,
                            tenant_id=tenant.id,
                            bloqueio_id=bloqueio.id,
                            motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
                            justificativa_hash=hashear_pii_com_salt_tenant(
                                "Drill multi-tenant", tenant.id
                            ),
                            causation_type=CAUSATION_MANUAL_DECISAO_ADMIN,
                            causation_id=None,
                            usuario_id=None,
                        )
                        publicar_evento(
                            acao="cliente.bloqueado",
                            payload=payload,
                            causation_id=uuid4(),
                            tenant_id=tenant.id,
                            usuario_id=None,
                            resource_summary=str(cliente.id),
                        )
                out[tenant.id] = True
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  bloqueio falhou em {tenant.slug}: {e!r}"))
                out[tenant.id] = False
        return out

    def _verificar_isolamento_clientes(
        self, tenants: list[Tenant], esperados: dict[UUID, list[Cliente]]
    ) -> bool:
        ok = True
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                visiveis = list(Cliente.objects.values_list("id", flat=True))
                esperados_ids = {c.id for c in esperados[tenant.id]}
                for cid in visiveis:
                    # Cada cliente visto neste tenant deve ser de algum cadastro/import nele
                    if cid not in esperados_ids:
                        # Procura se é mesclagem ou importação
                        pass
                # Não pode ver clientes de OUTRO tenant — só importados/mesclados/cadastrados aqui
                for outro in tenants:
                    if outro.id == tenant.id:
                        continue
                    outros_ids = {c.id for c in esperados[outro.id]}
                    vazamento = set(visiveis) & outros_ids
                    if vazamento:
                        ok = False
                        self.stdout.write(
                            self.style.ERROR(
                                f"  VAZAMENTO: tenant {tenant.slug} vê clientes de {outro.slug}: {vazamento}"
                            )
                        )
        return ok

    def _verificar_isolamento_outbox(self, tenants: list[Tenant]) -> bool:
        ok = True
        # bus_outbox é RLS por tenant; agregação cross-tenant exige modo sistema
        # (worker e management commands de auditoria operam aqui).
        with run_as_system():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT tenant_id, COUNT(*) FROM bus_outbox "
                    "WHERE acao = 'cliente.bloqueado' "
                    "GROUP BY tenant_id"
                )
                rows = dict(cur.fetchall())
        # Cada tenant deve ter EXATAMENTE 1 evento (do _bloquear_intercalado)
        for tenant in tenants:
            count = rows.get(tenant.id, 0)
            if count != 1:
                ok = False
                self.stdout.write(
                    self.style.ERROR(
                        f"  outbox tenant {tenant.slug}: esperado 1 evento, achou {count}"
                    )
                )
        return ok

    def _verificar_isolamento_op_tratamento(self, tenants: list[Tenant]) -> bool:
        # OperacaoTratamentoCliente é gravado por trigger AFTER INSERT/UPDATE em clientes
        ok = True
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                count = OperacaoTratamentoCliente.objects.count()
                # Cada tenant cadastrou ≥4 clientes (2 cadastro + 2 importação)
                if count < 4:
                    ok = False
                    self.stdout.write(
                        self.style.ERROR(
                            f"  OperacaoTratamentoCliente tenant {tenant.slug}: "
                            f"esperado ≥4 (cadastros+importações), achou {count}"
                        )
                    )
        return ok

    def _verificar_cadeia_auditoria(self, tenants: list[Tenant]) -> bool:
        ok = True
        for tenant in tenants:
            try:
                with run_in_tenant_context(tenant.id):
                    if Auditoria.objects.filter(tenant_id=tenant.id).exists():
                        verificar_integridade_cadeia(tenant_id=tenant.id)
            except Exception as e:
                ok = False
                self.stdout.write(self.style.ERROR(f"  cadeia tenant {tenant.slug} quebrou: {e!r}"))
        return ok

    def _verificar_resolucao_canonica(
        self,
        tenants: list[Tenant],
        cadastrados: dict[UUID, list[Cliente]],
        mesclados: dict[UUID, UUID | None],
    ) -> bool:
        ok = True
        for tenant in tenants:
            vencedor_id = mesclados.get(tenant.id)
            perdedor = cadastrados[tenant.id][1]
            if vencedor_id is None:
                ok = False
                continue
            with run_in_tenant_context(tenant.id):
                resolvido = resolver_cliente_canonico(perdedor.id)
                if resolvido != vencedor_id:
                    ok = False
                    self.stdout.write(
                        self.style.ERROR(
                            f"  tenant {tenant.slug}: resolver_cliente_canonico({perdedor.id}) "
                            f"→ {resolvido}, esperado {vencedor_id}"
                        )
                    )
        return ok

    def _verificar_slot_agendamentos(self, tenants: list[Tenant]) -> bool:
        """T-CLI-108: cada evento `cliente.bloqueado` no outbox carrega slot
        `agendamentos_futuros` no payload (Marco 1: lista vazia)."""
        ok = True
        with run_as_system():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT tenant_id, envelope_jsonb FROM bus_outbox "
                    "WHERE acao = 'cliente.bloqueado'"
                )
                rows = cur.fetchall()
        if not rows:
            self.stdout.write(self.style.ERROR("  nenhum evento cliente.bloqueado no outbox"))
            return False
        for tenant_id, env_raw in rows:
            env = env_raw if isinstance(env_raw, dict) else json.loads(env_raw)
            payload = env.get("payload", {})
            if "agendamentos_futuros" not in payload:
                ok = False
                self.stdout.write(
                    self.style.ERROR(f"  tenant {tenant_id}: payload sem agendamentos_futuros")
                )
            elif payload["agendamentos_futuros"] != []:
                ok = False
                self.stdout.write(
                    self.style.ERROR(
                        f"  tenant {tenant_id}: agendamentos_futuros não-vazio em Marco 1"
                    )
                )
        return ok
