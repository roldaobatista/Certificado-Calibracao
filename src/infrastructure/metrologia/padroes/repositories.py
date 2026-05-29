"""Adapters Django dos repositorios M5 padroes (P5 — ADR-0072).

Implementa os Protocols de `src.domain.metrologia.padroes.repository` sobre
Django ORM + raw SQL. Use cases (src/application/metrologia/padroes/*) recebem
estes adapters via DI e ignoram Django (ADR-0007 spec-as-source).

Defesa em profundidade multi-tenant: leituras filtram `tenant_id` EXPLICITO
(alem da RLS) — sessao sem contexto retorna None (paralelo M4 SEG-CAL-02).

INV-PAD-006 (decisao C-10): `atualizar_com_lock` NUNCA toca incertezas/validade/
proximo_recal (o trigger PG bloquearia). A unica via que atualiza esses campos
e `aplicar_recal_aprovado`, que envolve o UPDATE em
`SET LOCAL app.padrao_recal_em_curso = '1'` — o GUC que o trigger libera.
"""

from __future__ import annotations

import json as _json
from datetime import datetime
from uuid import UUID

from django.db import connection

from src.domain.metrologia.padroes.entities import (
    AnaliseCartaControleSnapshot,
    IntercomparacaoPTSnapshot,
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
    VerificacaoIntermediariaSnapshot,
    VinculoAuxiliarSnapshot,
)
from src.domain.metrologia.value_objects import IncertezaExpandida
from src.infrastructure.metrologia.padroes import mappers
from src.infrastructure.metrologia.padroes.models import (
    AnaliseCartaControle,
    IntercomparacaoPT,
    PadraoMetrologico,
    RecalExternoPadrao,
    VerificacaoIntermediaria,
    VinculoAuxiliar,
)
from src.infrastructure.multitenant.context import active_tenant_context


def _incertezas_json(incertezas: tuple[IncertezaExpandida, ...]) -> str:
    return _json.dumps(mappers.incertezas_para_json(incertezas))


class DjangoPadraoRepository:
    """Raiz do agregado — CAS optimistic via `revision`."""

    def obter_por_id(self, padrao_id: UUID) -> PadraoMetrologicoSnapshot | None:
        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        obj = PadraoMetrologico.objects.filter(id=padrao_id, tenant_id=tenant_id).first()
        return mappers.model_para_snapshot(obj) if obj is not None else None

    def existe_numero_serie(self, tenant_id: UUID, numero_serie: str) -> bool:
        return PadraoMetrologico.objects.filter(
            tenant_id=tenant_id, numero_serie=numero_serie
        ).exists()

    def salvar_novo(self, snapshot: PadraoMetrologicoSnapshot) -> None:
        PadraoMetrologico.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            numero_serie=snapshot.numero_serie,
            fabricante=snapshot.fabricante,
            modelo=snapshot.modelo,
            subtipo=snapshot.subtipo.value,
            grandezas=mappers.grandezas_para_json(snapshot.grandezas),
            faixas=mappers.faixas_para_json(snapshot.faixas),
            incertezas_certificado=mappers.incertezas_para_json(
                snapshot.incertezas_certificado
            ),
            vinculacao=snapshot.vinculacao.value,
            classe=snapshot.classe.value,
            cert_externo_storage_key=snapshot.cert_externo_storage_key,
            validade_certificado_rastreabilidade=snapshot.validade_certificado_rastreabilidade,
            proximo_recal=snapshot.proximo_recal,
            intervalo_recal_meses=snapshot.intervalo_recal_meses,
            intervalo_vi_meses=snapshot.intervalo_vi_meses,
            criterio_intervalo=snapshot.criterio_intervalo,
            estado=snapshot.estado.value,
            revision=snapshot.revision,
            rastreabilidade_origem_revogada=snapshot.rastreabilidade_origem_revogada,
            vigencia_inicio=snapshot.vigencia_inicio,
            correlation_id=snapshot.correlation_id,
            descricao=snapshot.descricao,
            localizacao_lab=snapshot.localizacao_lab,
            revogado_em=snapshot.revogado_em,
            motivo_revogacao=snapshot.motivo_revogacao,
        )

    def atualizar_com_lock(
        self, snapshot: PadraoMetrologicoSnapshot, revision_anterior: int
    ) -> bool:
        """CAS sem tocar incertezas/validade/proximo_recal (INV-PAD-006)."""
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE padrao_metrologico
                SET estado = %s,
                    revision = revision + 1,
                    rastreabilidade_origem_revogada = %s,
                    revogado_em = %s,
                    motivo_revogacao = %s
                WHERE id = %s AND revision = %s
                """,
                [
                    snapshot.estado.value,
                    snapshot.rastreabilidade_origem_revogada,
                    snapshot.revogado_em,
                    snapshot.motivo_revogacao,
                    str(snapshot.id),
                    revision_anterior,
                ],
            )
            return bool(cur.rowcount == 1)

    def aplicar_recal_aprovado(
        self, snapshot: PadraoMetrologicoSnapshot, revision_anterior: int
    ) -> bool:
        """CAS + GUC: unica via que atualiza incertezas/validade/proximo_recal.

        `SET LOCAL app.padrao_recal_em_curso = '1'` libera o trigger
        `padrao_incertezas_so_via_recal` (INV-PAD-006). SET LOCAL vive ate o
        COMMIT do atomic do caller.
        """
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.padrao_recal_em_curso = '1'")
            cur.execute(
                """
                UPDATE padrao_metrologico
                SET estado = %s,
                    revision = revision + 1,
                    incertezas_certificado = %s::jsonb,
                    validade_certificado_rastreabilidade = %s,
                    proximo_recal = %s
                WHERE id = %s AND revision = %s
                """,
                [
                    snapshot.estado.value,
                    _incertezas_json(snapshot.incertezas_certificado),
                    snapshot.validade_certificado_rastreabilidade,
                    snapshot.proximo_recal,
                    str(snapshot.id),
                    revision_anterior,
                ],
            )
            return bool(cur.rowcount == 1)


class DjangoRecalExternoRepository:
    def salvar_novo(self, snapshot: RecalExternoPadraoSnapshot) -> None:
        RecalExternoPadrao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            padrao_id=snapshot.padrao_id,
            enviado_em=snapshot.enviado_em,
            lab_externo=snapshot.lab_externo,
            responsavel_envio_id_hash=snapshot.responsavel_envio_id_hash,
            status=snapshot.status.value,
            numero_protocolo_lab_externo=snapshot.numero_protocolo_lab_externo,
            retornado_em=snapshot.retornado_em,
            cert_externo_novo_storage_key=snapshot.cert_externo_novo_storage_key,
            incertezas_novas=mappers.incertezas_para_json(snapshot.incertezas_novas),
            validade_nova=snapshot.validade_nova,
            valor_convencional_novo=snapshot.valor_convencional_novo,
            aprovado_rt_em=snapshot.aprovado_rt_em,
            aprovado_rt_id_hash=snapshot.aprovado_rt_id_hash,
        )

    def obter_por_id(self, recal_id: UUID) -> RecalExternoPadraoSnapshot | None:
        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        obj = RecalExternoPadrao.objects.filter(
            id=recal_id, tenant_id=tenant_id
        ).first()
        return self._to_snapshot(obj) if obj is not None else None

    def ultimo_do_padrao(
        self, padrao_id: UUID
    ) -> RecalExternoPadraoSnapshot | None:
        obj = (
            RecalExternoPadrao.objects.filter(padrao_id=padrao_id)
            .order_by("-enviado_em")
            .first()
        )
        return self._to_snapshot(obj) if obj is not None else None

    def atualizar_retorno_e_aprovacao(
        self, snapshot: RecalExternoPadraoSnapshot
    ) -> None:
        """UPDATE controlado (retorno/aprovacao). Trigger WORM barra o resto."""
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE recal_externo_padrao
                SET status = %s,
                    retornado_em = %s,
                    cert_externo_novo_storage_key = %s,
                    incertezas_novas = %s::jsonb,
                    validade_nova = %s,
                    valor_convencional_novo = %s,
                    aprovado_rt_em = %s,
                    aprovado_rt_id_hash = %s
                WHERE id = %s
                """,
                [
                    snapshot.status.value,
                    snapshot.retornado_em,
                    snapshot.cert_externo_novo_storage_key,
                    _incertezas_json(snapshot.incertezas_novas),
                    snapshot.validade_nova,
                    snapshot.valor_convencional_novo,
                    snapshot.aprovado_rt_em,
                    snapshot.aprovado_rt_id_hash,
                    str(snapshot.id),
                ],
            )

    @staticmethod
    def _to_snapshot(obj: RecalExternoPadrao) -> RecalExternoPadraoSnapshot:
        from src.domain.metrologia.padroes.enums import StatusRecal

        return RecalExternoPadraoSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            padrao_id=obj.padrao_id,
            enviado_em=obj.enviado_em,
            lab_externo=obj.lab_externo,
            responsavel_envio_id_hash=obj.responsavel_envio_id_hash,
            status=StatusRecal(obj.status),
            numero_protocolo_lab_externo=obj.numero_protocolo_lab_externo,
            retornado_em=obj.retornado_em,
            cert_externo_novo_storage_key=obj.cert_externo_novo_storage_key,
            incertezas_novas=mappers.incertezas_de_json(obj.incertezas_novas),
            validade_nova=obj.validade_nova,
            valor_convencional_novo=obj.valor_convencional_novo,
            aprovado_rt_em=obj.aprovado_rt_em,
            aprovado_rt_id_hash=obj.aprovado_rt_id_hash,
        )


class DjangoVerificacaoIntermediariaRepository:
    def salvar_nova(self, snapshot: VerificacaoIntermediariaSnapshot) -> None:
        VerificacaoIntermediaria.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            padrao_id=snapshot.padrao_id,
            data_vi=snapshot.data_vi,
            executor_id_hash=snapshot.executor_id_hash,
            metodo_canonicalizado=snapshot.metodo_canonicalizado,
            metodo_hash=snapshot.metodo_hash,
            resultado=snapshot.resultado.value,
            desvio_observado=snapshot.desvio_observado,
            acao_corretiva_canonicalizada=snapshot.acao_corretiva_canonicalizada,
            acao_corretiva_hash=snapshot.acao_corretiva_hash,
        )

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[VerificacaoIntermediariaSnapshot]:
        from src.domain.metrologia.padroes.enums import ResultadoVI

        objs = VerificacaoIntermediaria.objects.filter(padrao_id=padrao_id).order_by(
            "data_vi"
        )
        return [
            VerificacaoIntermediariaSnapshot(
                id=o.id,
                tenant_id=o.tenant_id,
                padrao_id=o.padrao_id,
                data_vi=o.data_vi,
                executor_id_hash=o.executor_id_hash,
                metodo_canonicalizado=o.metodo_canonicalizado,
                metodo_hash=o.metodo_hash,
                resultado=ResultadoVI(o.resultado),
                criado_em=o.criado_em,
                desvio_observado=o.desvio_observado,
                acao_corretiva_canonicalizada=o.acao_corretiva_canonicalizada,
                acao_corretiva_hash=o.acao_corretiva_hash,
            )
            for o in objs
        ]


class DjangoIntercomparacaoPTRepository:
    def salvar_nova(self, snapshot: IntercomparacaoPTSnapshot) -> None:
        IntercomparacaoPT.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            padrao_id=snapshot.padrao_id,
            lab_organizador=snapshot.lab_organizador,
            protocolo=snapshot.protocolo,
            data_inicio=snapshot.data_inicio,
            resultado=snapshot.resultado.value if snapshot.resultado else None,
            data_resultado=snapshot.data_resultado,
            zeta_score=snapshot.zeta_score,
            relatorio_pt_storage_key=snapshot.relatorio_pt_storage_key,
            nao_conformidade_id=snapshot.nao_conformidade_id,
        )

    def obter_por_id(self, pt_id: UUID) -> IntercomparacaoPTSnapshot | None:
        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        obj = IntercomparacaoPT.objects.filter(id=pt_id, tenant_id=tenant_id).first()
        return self._to_snapshot(obj) if obj is not None else None

    def atualizar_resultado(self, snapshot: IntercomparacaoPTSnapshot) -> None:
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE intercomparacao_pt
                SET resultado = %s,
                    data_resultado = %s,
                    zeta_score = %s,
                    relatorio_pt_storage_key = %s,
                    nao_conformidade_id = %s
                WHERE id = %s
                """,
                [
                    snapshot.resultado.value if snapshot.resultado else None,
                    snapshot.data_resultado,
                    snapshot.zeta_score,
                    snapshot.relatorio_pt_storage_key,
                    snapshot.nao_conformidade_id,
                    str(snapshot.id),
                ],
            )

    @staticmethod
    def _to_snapshot(obj: IntercomparacaoPT) -> IntercomparacaoPTSnapshot:
        from src.domain.metrologia.padroes.enums import ResultadoPT

        return IntercomparacaoPTSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            padrao_id=obj.padrao_id,
            lab_organizador=obj.lab_organizador,
            protocolo=obj.protocolo,
            data_inicio=obj.data_inicio,
            resultado=ResultadoPT(obj.resultado) if obj.resultado else None,
            data_resultado=obj.data_resultado,
            zeta_score=obj.zeta_score,
            relatorio_pt_storage_key=obj.relatorio_pt_storage_key,
            nao_conformidade_id=obj.nao_conformidade_id,
        )


class DjangoAnaliseCartaControleRepository:
    def salvar_nova(self, snapshot: AnaliseCartaControleSnapshot) -> None:
        AnaliseCartaControle.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            padrao_id=snapshot.padrao_id,
            regra_violada=snapshot.regra_violada.value,
            pontos_referenciados_ids=[str(p) for p in snapshot.pontos_referenciados_ids],
            linha_central=snapshot.linha_central,
            ucl=snapshot.ucl,
            lcl=snapshot.lcl,
            sigma=snapshot.sigma,
            n_pontos=snapshot.n_pontos,
            janela_meses=snapshot.janela_meses,
            versao_motor_shewhart=snapshot.versao_motor_shewhart,
            decisao_rt=snapshot.decisao_rt.value,
            justificativa_canonicalizada=snapshot.justificativa_canonicalizada,
            justificativa_hash=snapshot.justificativa_hash,
            assinatura_a3_rt_id=snapshot.assinatura_a3_rt_id,
        )

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[AnaliseCartaControleSnapshot]:
        from src.domain.metrologia.padroes.enums import (
            DecisaoRTCarta,
            RegraWesternElectric,
        )

        objs = AnaliseCartaControle.objects.filter(padrao_id=padrao_id).order_by(
            "-criado_em"
        )
        return [
            AnaliseCartaControleSnapshot(
                id=o.id,
                tenant_id=o.tenant_id,
                padrao_id=o.padrao_id,
                regra_violada=RegraWesternElectric(o.regra_violada),
                pontos_referenciados_ids=tuple(
                    UUID(str(p)) for p in o.pontos_referenciados_ids
                ),
                linha_central=o.linha_central,
                ucl=o.ucl,
                lcl=o.lcl,
                sigma=o.sigma,
                n_pontos=o.n_pontos,
                janela_meses=o.janela_meses,
                versao_motor_shewhart=o.versao_motor_shewhart,
                decisao_rt=DecisaoRTCarta(o.decisao_rt),
                justificativa_canonicalizada=o.justificativa_canonicalizada,
                justificativa_hash=o.justificativa_hash,
                criado_em=o.criado_em,
                assinatura_a3_rt_id=o.assinatura_a3_rt_id,
            )
            for o in objs
        ]


class DjangoVinculoAuxiliarRepository:
    def salvar_novo(self, snapshot: VinculoAuxiliarSnapshot) -> None:
        VinculoAuxiliar.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            padrao_principal_id=snapshot.padrao_principal_id,
            padrao_auxiliar_id=snapshot.padrao_auxiliar_id,
            grandeza_influencia={"simbolo": snapshot.grandeza_influencia.value},
            vigencia_inicio=snapshot.vigencia_inicio,
            revogado_em=snapshot.revogado_em,
        )

    @staticmethod
    def _to_snapshot(o: VinculoAuxiliar) -> VinculoAuxiliarSnapshot:
        from src.domain.metrologia.value_objects import Grandeza

        return VinculoAuxiliarSnapshot(
            id=o.id,
            tenant_id=o.tenant_id,
            padrao_principal_id=o.padrao_principal_id,
            padrao_auxiliar_id=o.padrao_auxiliar_id,
            grandeza_influencia=Grandeza.from_string(
                str(o.grandeza_influencia.get("simbolo", o.grandeza_influencia))
            ),
            vigencia_inicio=o.vigencia_inicio,
            revogado_em=o.revogado_em,
        )

    def obter_por_id(self, vinculo_id: UUID) -> VinculoAuxiliarSnapshot | None:
        obj = VinculoAuxiliar.objects.filter(id=vinculo_id).first()
        return self._to_snapshot(obj) if obj is not None else None

    def listar_auxiliares_vigentes_de(
        self, padrao_principal_id: UUID
    ) -> list[VinculoAuxiliarSnapshot]:
        objs = VinculoAuxiliar.objects.filter(
            padrao_principal_id=padrao_principal_id, revogado_em__isnull=True
        )
        return [self._to_snapshot(o) for o in objs]

    def listar_vigentes_por_auxiliar(
        self, padrao_auxiliar_id: UUID
    ) -> list[VinculoAuxiliarSnapshot]:
        objs = VinculoAuxiliar.objects.filter(
            padrao_auxiliar_id=padrao_auxiliar_id, revogado_em__isnull=True
        )
        return [self._to_snapshot(o) for o in objs]

    def revogar(self, vinculo_id: UUID, revogado_em: datetime) -> bool:
        atualizadas = VinculoAuxiliar.objects.filter(
            id=vinculo_id, revogado_em__isnull=True
        ).update(revogado_em=revogado_em)
        return atualizadas == 1
