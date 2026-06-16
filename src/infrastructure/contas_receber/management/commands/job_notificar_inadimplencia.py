"""Job: aviso de inadimplência D+30/D+45 perfil A (T-CR-044 / D-CR-9 — Caminho C).

Itera tenants **perfil A** (D-CR-9 — demais perfis usam o payload de evento, D-CR-22).
Para cada `Titulo` vencido em D+30/D+45, agrupado por cliente, envia e-mail ao cliente
final (**remetente = tenant** — Aferê opera o envio, não cobra) e publica
`contas_receber.inadimplencia_dura_atingida` (cliente como `cliente_referencia_hash`,
NUNCA o e-mail — minimização D-CR-19).

**Aviso ao admin do tenant** (parecer Caminho C) = o EVENTO `inadimplencia_dura_atingida`
com payload rico (canal canônico de comunicação interna — D-CR-9/D-CR-22; consumido pelo
painel/CRM do tenant), NÃO um e-mail redundante: `usuario_perfil_tenant` tem RLS
`upt_self_select` (cada usuário só vê os próprios vínculos), então um job de sistema não
lista admins por query — o evento é o canal correto.

Resiliente: falha de SMTP loga e NÃO derruba o job (credenciais ausentes em Wave A).
`--dry-run` não envia nem publica. **DISPARO com PF real aguarda GATE-LGPD-RAT-CONSOLIDACAO**
(texto do e-mail congelado). Backend de e-mail: locmem em test; SMTP via env em dev/prod.

Limitação Wave A (3b-2): idempotência por dia (dias_vencido == 30/45 exato). Prova de
envio persistida + re-disparo robusto + fail-closed de bloqueio = Fatia 3b-3.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db import transaction

from src.application.contas_receber.notificar_inadimplencia import (
    TituloVencidoInfo,
    marco_de_dias_vencido,
    montar_aviso,
)
from src.domain.contas_receber.grace import grace_period_por_perfil
from src.infrastructure.multitenant.jobs import processar_em_contexto_tenant

logger = logging.getLogger(__name__)

_PERFIL_NOTIFICAVEL = "A"


class Command(BaseCommand):
    help = "Aviso de inadimplencia D+30/D+45 perfil A (Caminho C). --dry-run nao envia."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Conta avisos sem enviar e-mail nem publicar evento.",
        )

    def handle(self, *args: Any, **opts: Any) -> None:
        dry = bool(opts.get("dry_run", False))
        resultados = processar_em_contexto_tenant(lambda t: self._por_tenant(t, dry=dry))
        total = sum(resultados.values())
        self.stdout.write(self.style.SUCCESS(f"avisos de inadimplencia: {total}"))

    def _por_tenant(self, tenant: Any, *, dry: bool) -> int:
        if tenant.perfil_regulatorio != _PERFIL_NOTIFICAVEL:
            return 0
        grace = grace_period_por_perfil(_PERFIL_NOTIFICAVEL)  # 45
        hoje = date.today()
        from src.infrastructure.contas_receber.models import Titulo as TituloModel

        grupos: dict[tuple[UUID, str], list[TituloVencidoInfo]] = defaultdict(list)
        hashes: dict[UUID, str] = {}
        qs = TituloModel.objects.filter(
            estado="vencido", cliente_atual_id__isnull=False
        ).only("id", "cliente_atual_id", "cliente_referencia_hash", "valor_original", "data_vencimento")
        for t in qs:
            cliente_id = t.cliente_atual_id
            if cliente_id is None:
                continue
            dias = (hoje - t.data_vencimento).days
            marco = marco_de_dias_vencido(dias)
            if marco is None:
                continue
            grupos[(cliente_id, marco)].append(
                TituloVencidoInfo(
                    titulo_id=t.id,
                    valor_centavos=t.valor_original,
                    data_vencimento=t.data_vencimento,
                    dias_vencido=dias,
                )
            )
            hashes[cliente_id] = t.cliente_referencia_hash
        if not grupos:
            return 0

        tenant_nome = tenant.nome_fantasia or "seu fornecedor"
        enviados = 0
        for (cliente_id, marco), titulos in grupos.items():
            aviso = montar_aviso(
                tenant_nome=tenant_nome,
                titulos=titulos,
                marco=marco,
                grace_perfil=grace,
                canal_regularizacao_url=getattr(settings, "CANAL_REGULARIZACAO_URL", ""),
            )
            if dry:
                enviados += 1
                continue
            cliente_email = self._email_cliente(cliente_id)
            if cliente_email:
                self._enviar(
                    assunto=aviso.assunto,
                    corpo=aviso.corpo,
                    para=[cliente_email],
                    tenant_nome=tenant_nome,
                )
            self._publicar_evento(
                tenant_id=tenant.id,
                cliente_referencia_hash=hashes[cliente_id],
                aviso=aviso,
            )
            enviados += 1
        return enviados

    @staticmethod
    def _email_cliente(cliente_id: UUID) -> str:
        from src.infrastructure.clientes.models import Cliente

        c = Cliente.objects.filter(id=cliente_id).only("email").first()
        return (c.email or "") if c is not None else ""

    def _enviar(self, *, assunto: str, corpo: str, para: list[str], tenant_nome: str) -> None:
        """Envia e-mail. Resiliente: falha de SMTP loga e NÃO derruba o job."""
        msg = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=f"{tenant_nome} <{settings.DEFAULT_FROM_EMAIL}>",
            to=para,
        )
        try:
            msg.send(fail_silently=False)
        except Exception:  # -- SMTP indisponível/credenciais ausentes não param o job
            logger.warning(
                "job_notificar_inadimplencia: falha ao enviar aviso (SMTP)", exc_info=True
            )

    @staticmethod
    def _publicar_evento(*, tenant_id: UUID, cliente_referencia_hash: str, aviso: Any) -> None:
        from src.infrastructure.audit.event_helpers import publicar_evento

        causation_id = UUID(str(aviso.titulos_payload[0]["titulo_id"]))
        with transaction.atomic():
            publicar_evento(
                acao="contas_receber.inadimplencia_dura_atingida",
                payload={
                    "cliente_referencia_hash": cliente_referencia_hash,
                    "marco": aviso.marco,
                    "titulos_vencidos": aviso.titulos_payload,
                    "data_bloqueio_prevista": aviso.data_bloqueio_prevista.isoformat(),
                    "canal_regularizacao_url": getattr(
                        settings, "CANAL_REGULARIZACAO_URL", ""
                    ),
                },
                causation_id=causation_id,
                tenant_id=tenant_id,
                resource_summary=f"inadimplencia {aviso.marco} cliente {cliente_referencia_hash[:12]}",
            )
