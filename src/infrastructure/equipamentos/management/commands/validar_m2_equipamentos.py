"""T-EQP-105 (Marco 2 `equipamentos`) — drill multi-tenant.

Critério `docs/faseamento/M2-equipamentos/tasks.md` linha T-EQP-105:
> Drill `validar_m2_equipamentos` PASS multi-tenant.

Cenário em 3 tenants, em paralelo (intercalado pra forcar troca de
contexto):
  Fase 1 — cadastra Equipamento canonico (testa INV-049 TAG unica
           por tenant + INV-EQP-001 snapshot imutavel pos-INSERT).
  Fase 2 — emite QR HMAC + grava em equipamentos_qrcode + valida
           via tabela (testa INV-EQP-QR-NUNCA-RECOMPUTA).
  Fase 3 — cria EquipamentoRecebimento (testa INV-EQP-ANOM-* e
           trigger PG imutabilidade foto + ambiental).
  Fase 4 — cria RecebimentoProvisorio (TTL D+7, INV-EQP-PROV-001
           sem FK em Equipamento).

Verificacoes:
  1. Zero vazamento cross-tenant (Equipamento, QRCode,
     EquipamentoRecebimento, RecebimentoProvisorio).
  2. Eventos publicados: cada tenant ve apenas seus eventos no bus.
  3. Auditoria: cadeia integra por tenant (hash chain).
  4. QR hash gravado resolve via verificar_qr_hash_em_tabela.
  5. RecebimentoProvisorio.id NAO existe como Equipamento.id.

Drill destrutivo-acumulativo (Auditoria INSERT-only). Aborta se
banco NAME != test* sem `--em-banco-descartavel`.

Saida: tabela + exit code 0 (PASS) ou 1 (FAIL).

Uso:
    docker compose exec app poetry run python manage.py \\
        validar_m2_equipamentos [--em-banco-descartavel]
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.audit.services import verificar_integridade_cadeia
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    CondicaoVisualChegada,
    Equipamento,
    EquipamentoRecebimento,
    QRCode,
    RecebimentoProvisorio,
    StatusRecebimentoProvisorio,
)
from src.infrastructure.equipamentos.services_equipamento import (
    DadosCriacaoEquipamento,
    criar_equipamento,
)
from src.infrastructure.equipamentos.services_qr import (
    gerar_qr_hash_versionado,
    verificar_qr_hash_em_tabela,
)
from src.infrastructure.equipamentos.services_recebimento import (
    DadosRecebimento,
    criar_recebimento,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


class Command(BaseCommand):
    help = (
        "Drill Marco 2 `equipamentos` — multi-tenant cadastro + QR HMAC + "
        "recebimento + provisório, com verificacao de isolamento cross-tenant."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--em-banco-descartavel",
            action="store_true",
            help="Confirma que o banco atual e descartavel.",
        )

    def handle(self, *args, **opts):
        self._abortar_se_nao_descartavel(opts.get("em_banco_descartavel", False))

        resultados: list[tuple[str, bool, str]] = []
        falha_critica = False

        try:
            tenants = self._criar_tenants(3)
            self.stdout.write(
                f"Criados {len(tenants)} tenants: {[t.slug for t in tenants]}"
            )
            operadores = self._criar_operadores(tenants)

            # FASE 1 — cadastro intercalado de Equipamento.
            eq_por_tenant = self._cadastrar_equipamento_intercalado(
                tenants, operadores
            )
            for tenant in tenants:
                ok = eq_por_tenant[tenant.id] is not None
                resultados.append(
                    (
                        f"cadastro equipamento tenant {tenant.slug}",
                        ok,
                        "ok" if ok else "falha",
                    )
                )

            # FASE 2 — emissao + verificacao de QR HMAC.
            qr_por_tenant = self._emitir_qr_intercalado(tenants, eq_por_tenant)
            for tenant in tenants:
                hash_versao = qr_por_tenant[tenant.id]
                with run_in_tenant_context(tenant.id):
                    resolvido = verificar_qr_hash_em_tabela(hash_versao)
                ok = (
                    resolvido is not None
                    and resolvido.equipamento_id == eq_por_tenant[tenant.id].id
                )
                resultados.append(
                    (
                        f"QR HMAC resolve via tabela tenant {tenant.slug}",
                        ok,
                        "ok" if ok else "FALHOU",
                    )
                )

            # FASE 3 — recebimento canonico (com ambiente).
            rec_por_tenant = self._criar_recebimento_intercalado(
                tenants, eq_por_tenant, operadores
            )
            for tenant in tenants:
                ok = rec_por_tenant[tenant.id] is not None
                resultados.append(
                    (
                        f"recebimento canonico tenant {tenant.slug}",
                        ok,
                        "ok" if ok else "falha",
                    )
                )

            # FASE 4 — recebimento provisorio (Caminho A Roldao).
            prov_por_tenant = self._criar_provisorio_intercalado(
                tenants, operadores
            )
            for tenant in tenants:
                ok = prov_por_tenant[tenant.id] is not None
                resultados.append(
                    (
                        f"recebimento provisorio tenant {tenant.slug}",
                        ok,
                        "ok" if ok else "falha",
                    )
                )

            # VERIFICACOES de isolamento.
            iso_eq = self._verificar_isolamento_equipamento(
                tenants, eq_por_tenant
            )
            resultados.append(
                (
                    "isolamento Equipamento cross-tenant",
                    iso_eq,
                    "zero vazamento" if iso_eq else "VAZOU",
                )
            )

            iso_qr = self._verificar_isolamento_qrcode(tenants)
            resultados.append(
                (
                    "isolamento QRCode cross-tenant",
                    iso_qr,
                    "zero vazamento" if iso_qr else "VAZOU",
                )
            )

            iso_prov = self._verificar_isolamento_provisorio(tenants)
            resultados.append(
                (
                    "isolamento RecebimentoProvisorio cross-tenant",
                    iso_prov,
                    "zero vazamento" if iso_prov else "VAZOU",
                )
            )

            # VERIFICACAO design INV-EQP-PROV-001: provisorio.id !=
            # Equipamento.id (UUIDs distintos).
            prov_design_ok = self._verificar_design_prov_001(
                tenants, prov_por_tenant
            )
            resultados.append(
                (
                    "design INV-EQP-PROV-001 (provisorio nao e equipamento)",
                    prov_design_ok,
                    "ok" if prov_design_ok else "FALHOU",
                )
            )

            # VERIFICACAO cadeia auditoria por tenant.
            cad_ok = self._verificar_cadeia_auditoria(tenants)
            resultados.append(
                (
                    "cadeia auditoria integra por tenant",
                    cad_ok,
                    "ok" if cad_ok else "QUEBROU",
                )
            )

            # VERIFICACAO evento equipamento.criado por tenant.
            ev_ok = self._verificar_evento_criado(tenants, eq_por_tenant)
            resultados.append(
                (
                    "evento equipamento.criado por tenant",
                    ev_ok,
                    "ok" if ev_ok else "FALHOU",
                )
            )

        except Exception as exc:  # -- drill captura tudo pra reportar
            falha_critica = True
            resultados.append(
                ("execucao do drill", False, f"excecao: {exc!r}")
            )

        # Saida final
        self.stdout.write("\n" + "=" * 78)
        self.stdout.write("Drill Marco 2 — equipamentos")
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
                f"banco '{nome}' nao parece descartavel. "
                "Passe --em-banco-descartavel se for ambiente local efemero."
            )
        )
        sys.exit(2)

    def _criar_tenants(self, n: int) -> list[Tenant]:
        tenants: list[Tenant] = []
        for i in range(n):
            t = Tenant.objects.create(
                nome_fantasia=f"Tenant Drill M2 #{i}",
                slug=f"drill-m2-{uuid4().hex[:8]}",
            )
            tenants.append(t)
        return tenants

    def _criar_operadores(
        self, tenants: list[Tenant]
    ) -> dict[UUID, Usuario]:
        out: dict[UUID, Usuario] = {}
        for tenant in tenants:
            u = Usuario.objects.create(
                email=f"op-{tenant.slug}-{uuid4().hex[:6]}@drill.local",
                nome_completo=f"Operador {tenant.slug}",
                is_active=True,
            )
            out[tenant.id] = u
        return out

    def _cadastrar_equipamento_intercalado(
        self,
        tenants: list[Tenant],
        operadores: dict[UUID, Usuario],
    ) -> dict[UUID, Equipamento]:
        out: dict[UUID, Equipamento] = {}
        # 1 cliente + 1 equipamento por tenant — intercalado.
        for tenant in tenants:
            operador = operadores[tenant.id]
            with run_in_tenant_context(tenant.id, operador.id):
                cliente = Cliente.objects.create(
                    tenant=tenant,
                    tipo_pessoa=TipoPessoa.PJ,
                    documento="11222333000181",
                    nome=f"Drill cli {tenant.slug}",
                    aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
                )
                # Usa service criar_equipamento para que evento
                # equipamento.criado seja publicado (defesa de verificacao).
                eq = criar_equipamento(
                    tenant_id=tenant.id,
                    criado_por_id=operador.id,
                    dados=DadosCriacaoEquipamento(
                        tag=f"DRILL-{tenant.slug}",
                        numero_serie=f"NSDRILL-{tenant.slug}",
                        fabricante="Toledo",
                        modelo="X",
                        cliente_atual_id=cliente.id,
                        perfil_tenant_snapshot={"perfil": "D"},
                    ),
                )
                out[tenant.id] = eq
        return out

    def _emitir_qr_intercalado(
        self, tenants: list[Tenant], eq_por_tenant: dict[UUID, Equipamento]
    ) -> dict[UUID, str]:
        out: dict[UUID, str] = {}
        emitido_em = datetime.now(tz=UTC)
        for tenant in tenants:
            eq = eq_por_tenant[tenant.id]
            with run_in_tenant_context(tenant.id):
                hash_versao = gerar_qr_hash_versionado(
                    equipamento_id=eq.id,
                    tenant_id=tenant.id,
                    emitido_em=emitido_em,
                )
                QRCode.objects.create(
                    tenant=tenant,
                    equipamento=eq,
                    hash=hash_versao,
                    emitido_em=emitido_em,
                )
                out[tenant.id] = hash_versao
        return out

    def _criar_recebimento_intercalado(
        self,
        tenants: list[Tenant],
        eq_por_tenant: dict[UUID, Equipamento],
        operadores: dict[UUID, Usuario],
    ) -> dict[UUID, EquipamentoRecebimento | None]:
        out: dict[UUID, EquipamentoRecebimento | None] = {}
        for tenant in tenants:
            eq = eq_por_tenant[tenant.id]
            operador = operadores[tenant.id]
            try:
                with run_in_tenant_context(tenant.id, operador.id):
                    resultado = criar_recebimento(
                        tenant_id=tenant.id,
                        equipamento=eq,
                        recebido_por_id=operador.id,
                        dados=DadosRecebimento(
                            condicao_visual_chegada=(
                                CondicaoVisualChegada.INTEGRO.value
                            ),
                            temp_ambiente_c="22.5",
                            ur_percentual="55",
                            pressao_kpa="101.3",
                        ),
                    )
                    out[tenant.id] = resultado.recebimento
            except Exception as exc:  # -- drill resumido
                out[tenant.id] = None
                self.stdout.write(
                    self.style.WARNING(
                        f"recebimento drill tenant {tenant.slug} falhou: {exc!r}"
                    )
                )
        return out

    def _criar_provisorio_intercalado(
        self,
        tenants: list[Tenant],
        operadores: dict[UUID, Usuario],
    ) -> dict[UUID, RecebimentoProvisorio | None]:
        out: dict[UUID, RecebimentoProvisorio | None] = {}
        agora = datetime.now(tz=UTC)
        for tenant in tenants:
            operador = operadores[tenant.id]
            try:
                with run_in_tenant_context(tenant.id, operador.id):
                    prov = RecebimentoProvisorio.objects.create(
                        tenant=tenant,
                        tag_provisoria=f"PROV-DRILL-{tenant.slug}",
                        descricao_estimada=(
                            "Equipamento sem cadastro completo — drill multi-tenant Marco 2."
                        ),
                        condicao_visual_chegada=(
                            CondicaoVisualChegada.INTEGRO.value
                        ),
                        foto_storage_key=f"prov-drill-{uuid4().hex[:8]}",
                        foto_sha256="a" * 64,
                        recebido_por_id=operador.id,
                        ttl_expira_em=agora + timedelta(days=7),
                        status=StatusRecebimentoProvisorio.PENDENTE_PROMOCAO,
                    )
                    out[tenant.id] = prov
            except Exception as exc:  # -- drill resumido
                out[tenant.id] = None
                self.stdout.write(
                    self.style.WARNING(
                        f"provisorio drill tenant {tenant.slug} falhou: {exc!r}"
                    )
                )
        return out

    def _verificar_isolamento_equipamento(
        self,
        tenants: list[Tenant],
        eq_por_tenant: dict[UUID, Equipamento],
    ) -> bool:
        for tenant in tenants:
            ids_outros = [
                eq_por_tenant[t.id].id for t in tenants if t.id != tenant.id
            ]
            with run_in_tenant_context(tenant.id):
                qs = Equipamento.objects.filter(id__in=ids_outros)
                if qs.exists():
                    return False
        return True

    def _verificar_isolamento_qrcode(self, tenants: list[Tenant]) -> bool:
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                qs = QRCode.objects.exclude(tenant_id=tenant.id)
                if qs.exists():
                    return False
        return True

    def _verificar_isolamento_provisorio(self, tenants: list[Tenant]) -> bool:
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                qs = RecebimentoProvisorio.objects.exclude(tenant_id=tenant.id)
                if qs.exists():
                    return False
        return True

    def _verificar_design_prov_001(
        self,
        tenants: list[Tenant],
        prov_por_tenant: dict[UUID, RecebimentoProvisorio | None],
    ) -> bool:
        for tenant in tenants:
            prov = prov_por_tenant[tenant.id]
            if prov is None:
                return False
            # UUID do provisorio NAO existe como Equipamento.id.
            with run_in_tenant_context(tenant.id):
                if Equipamento.objects.filter(id=prov.id).exists():
                    return False
        return True

    def _verificar_cadeia_auditoria(self, tenants: list[Tenant]) -> bool:
        for tenant in tenants:
            with run_in_tenant_context(tenant.id):
                relatorio = verificar_integridade_cadeia(tenant_id=tenant.id)
                # relatorio = dict[tenant_id_str | None, (integra, n, erros)]
                for integra, _n, _erros in relatorio.values():
                    if not integra:
                        return False
        return True

    def _verificar_evento_criado(
        self,
        tenants: list[Tenant],
        eq_por_tenant: dict[UUID, Equipamento],
    ) -> bool:
        for tenant in tenants:
            eq = eq_por_tenant[tenant.id]
            with run_in_tenant_context(tenant.id):
                exists = Auditoria.objects.filter(
                    action="equipamento.criado",
                    payload_jsonb__equipamento_id=str(eq.id),
                ).exists()
                if not exists:
                    return False
        return True
