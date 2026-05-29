"""Porta `metrologia/padroes` consumida por M4 (calibracao) — D-PAD-5 / C-6.

Porta NOVA fail-CLOSED (ADR-0007 estilo `certificados/query_service.py` —
funcoes de modulo, sem estado). M4 chama `padrao_bloqueado_para_uso` ANTES de
gravar `PadraoUsado` (GATE-PAD-PORTA-M4). Padrao vencido/reprovado/suspenso
usado numa calibracao = risco E&O (corretora FURO) — esta barreira fecha o
vetor de sinistro.

`padrao_bloqueado_para_uso` retorna `(True, motivo)` se QUALQUER bloqueio:
- padrao inexistente / de outro tenant (RLS) / soft-deletado.
- estado != EM_USO (em recal, PT, baixado, sucateado — C-4).
- rastreabilidade da origem revogada (C-5 FURO-4).
- recal vencido (proximo_recal < hoje) / cert de rastreabilidade vencido.
- ultima VI REPROVADA (INV-CAL-VI-001).
- PT REJEITADO sem resolucao (INV-023).
- carta Shewhart violada SEM AnaliseCartaControle liberadora (perfil A —
  INV-PAD-010 + C-16 alerta/trend).
- QUALQUER excecao -> fail-CLOSED (nunca libera por engano).

C-15: adequacao faixa/grandeza<->ponto de calibracao NAO e decidida aqui — e
delegada EXPLICITAMENTE ao M4 (onde o ponto existe). Esta porta valida a SAUDE
do padrao; `snapshot_para_uso` expoe grandezas/faixas/incertezas pro M4 decidir.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.padroes import shewhart
from src.domain.metrologia.padroes.entities import PadraoUsadoSnapshot
from src.domain.metrologia.padroes.enums import (
    DecisaoRTCarta,
    EstadoPadrao,
    ResultadoPT,
    ResultadoVI,
)
from src.domain.metrologia.value_objects import Grandeza
from src.infrastructure.metrologia.padroes import mappers
from src.infrastructure.metrologia.padroes.models import (
    AnaliseCartaControle,
    IntercomparacaoPT,
    PadraoMetrologico,
    VerificacaoIntermediaria,
    VinculoAuxiliar,
)

_MIN_PONTOS_CARTA = 2


def padrao_bloqueado_para_uso(
    padrao_id: UUID,
    tenant_e_perfil_a: bool = False,
    hoje: _dt.date | None = None,
    _visitados: set[UUID] | None = None,
) -> tuple[bool, str]:
    """Retorna (bloqueado, motivo). Fail-CLOSED em qualquer erro.

    `tenant_e_perfil_a` (calculado pelo caller via predicate `tenant_perfil_e`)
    habilita o bloqueio por carta Shewhart (INV-PAD-008 — cartas exclusivas A).
    `hoje` injetavel pra teste deterministico.

    `_visitados` (interno) guarda os padroes ja avaliados nesta cadeia para
    evitar recursao infinita ao verificar auxiliares vinculados (INV-PAD-007).
    """
    try:
        hoje = hoje or _dt.date.today()
        visitados = _visitados or set()
        if padrao_id in visitados:
            # Ja avaliado nesta cadeia (vinculo auxiliar circular patologico):
            # nao re-bloqueia nem re-libera — quem chamou ja decide.
            return (False, "")
        visitados = visitados | {padrao_id}

        padrao = PadraoMetrologico.objects.filter(id=padrao_id).first()
        if padrao is None:
            return (True, "padrao inexistente ou de outro tenant (RLS)")
        if padrao.revogado_em is not None:
            return (True, "padrao revogado (soft-delete)")
        if padrao.estado != EstadoPadrao.EM_USO.value:
            return (True, f"padrao em estado {padrao.estado} (nao EM_USO)")
        if padrao.rastreabilidade_origem_revogada:
            return (True, "rastreabilidade da origem revogada (C-5)")
        if padrao.proximo_recal < hoje:
            return (True, f"recal vencido (proximo_recal={padrao.proximo_recal})")
        if padrao.validade_certificado_rastreabilidade < hoje:
            return (
                True,
                f"cert de rastreabilidade vencido "
                f"(validade={padrao.validade_certificado_rastreabilidade})",
            )

        # Ultima VI REPROVADA bloqueia (INV-CAL-VI-001).
        ultima_vi = (
            VerificacaoIntermediaria.objects.filter(padrao_id=padrao_id)
            .order_by("-data_vi")
            .first()
        )
        if ultima_vi is not None and ultima_vi.resultado == ResultadoVI.REPROVADO.value:
            return (True, "ultima verificacao intermediaria REPROVADA")

        # PT REJEITADO sem resolucao (INV-023).
        pt_rejeitada = (
            IntercomparacaoPT.objects.filter(
                padrao_id=padrao_id, resultado=ResultadoPT.REJEITADO.value
            )
            .order_by("-data_resultado")
            .first()
        )
        if pt_rejeitada is not None and pt_rejeitada.nao_conformidade_id is None:
            return (True, "intercomparacao/PT REJEITADA sem NC tratada")

        # Carta Shewhart (perfil A — INV-PAD-008 + INV-PAD-010 + C-16).
        if tenant_e_perfil_a:
            bloqueado_carta, motivo_carta = _bloqueado_por_carta(padrao_id)
            if bloqueado_carta:
                return (True, motivo_carta)

        # INV-PAD-007 (cl. 6.4.5): equipamento auxiliar vinculado vigente com
        # calibracao/rastreabilidade vencida (ou fora de EM_USO / VI reprovada)
        # contamina o balanco de incerteza do principal -> bloqueia o principal.
        bloqueado_aux, motivo_aux = _bloqueado_por_auxiliar(
            padrao_id, tenant_e_perfil_a, hoje, visitados
        )
        if bloqueado_aux:
            return (True, motivo_aux)

        return (False, "")
    except Exception as exc:
        # fail-CLOSED deliberado: qualquer erro inesperado bloqueia o uso do
        # padrao (nunca libera por engano — risco E&O).
        return (True, f"falha ao avaliar saude do padrao (fail-closed): {exc!r}")


def _bloqueado_por_auxiliar(
    padrao_principal_id: UUID,
    tenant_e_perfil_a: bool,
    hoje: _dt.date,
    visitados: set[UUID],
) -> tuple[bool, str]:
    """INV-PAD-007 (cl. 6.4.5): reavalia a saude dos auxiliares vigentes.

    Cada `VinculoAuxiliar` vigente (`revogado_em IS NULL` — ADR-0030) aponta um
    `PadraoMetrologico` auxiliar (subtipo AUXILIAR_* garantido na CRIACAO do
    vinculo, nao filtrado aqui) que entra na cadeia de incerteza do principal.
    Reusa `padrao_bloqueado_para_uso` recursivamente
    (mesmo conjunto de checagens: estado/recal/validade/VI/PT), propagando
    `visitados` para evitar ciclo. Auxiliar bloqueado -> principal bloqueado.
    """
    vinculos = VinculoAuxiliar.objects.filter(
        padrao_principal_id=padrao_principal_id, revogado_em__isnull=True
    )
    for v in vinculos:
        bloqueado_aux, motivo_aux = padrao_bloqueado_para_uso(
            v.padrao_auxiliar_id, tenant_e_perfil_a, hoje, visitados
        )
        if bloqueado_aux:
            return (
                True,
                f"auxiliar {v.padrao_auxiliar_id} bloqueado (INV-PAD-007 cl. 6.4.5): "
                f"{motivo_aux}",
            )
    return (False, "")


def _bloqueado_por_carta(padrao_id: UUID) -> tuple[bool, str]:
    """Read-model Shewhart (ADR-0070): re-calcula a serie de desvios das VIs.

    Se ha violacao Western Electric, exige uma AnaliseCartaControle WORM mais
    recente que a ultima VI E com decisao do RT que LIBERE o uso
    (ACEITO_COM_JUSTIFICATIVA). Caso contrario -> bloqueado (INV-PAD-010).
    """
    vis = list(
        VerificacaoIntermediaria.objects.filter(padrao_id=padrao_id).order_by("data_vi")
    )
    vis_com_desvio = [v for v in vis if v.desvio_observado is not None]
    serie = [Decimal(str(v.desvio_observado)) for v in vis_com_desvio]
    if len(serie) < _MIN_PONTOS_CARTA:
        return (False, "")

    limites = shewhart.calcular_limites(serie)
    violacoes = shewhart.detectar_violacoes(serie, limites)
    if not violacoes:
        return (False, "")

    ultima_analise = (
        AnaliseCartaControle.objects.filter(padrao_id=padrao_id)
        .order_by("-criado_em")
        .first()
    )
    if ultima_analise is None:
        return (
            True,
            "carta Shewhart com violacao sem AnaliseCartaControle (INV-PAD-010)",
        )
    # Guard de recencia (anti-stale): uma analise liberadora ANTIGA nao pode
    # cobrir uma VI nova que reativou a violacao. A decisao do RT precisa ser
    # pelo menos tao recente quanto o ultimo ponto da serie atual; senao,
    # exige nova analise (INV-PAD-010 — decisao deve cobrir o estado vigente).
    ultima_data_vi = vis_com_desvio[-1].data_vi
    if ultima_analise.criado_em < ultima_data_vi:
        return (
            True,
            "carta Shewhart: AnaliseCartaControle anterior a VI mais recente "
            "(decisao do RT defasada — exige nova analise, INV-PAD-010)",
        )
    if ultima_analise.decisao_rt != DecisaoRTCarta.ACEITO_COM_JUSTIFICATIVA.value:
        return (
            True,
            f"carta Shewhart: decisao do RT '{ultima_analise.decisao_rt}' "
            f"nao libera uso (INV-PAD-010)",
        )
    return (False, "")


def snapshot_para_uso(padrao_id: UUID) -> PadraoUsadoSnapshot | None:
    """Monta o PadraoUsadoSnapshot (VO imutavel consumido por M4 — D-PAD-5).

    Inclui leitura ambiental dos auxiliares vinculados vigentes (C-8). Retorna
    None se o padrao nao existe / RLS. NAO valida saude — o caller chama
    `padrao_bloqueado_para_uso` antes (GATE-PAD-PORTA-M4).
    """
    padrao = PadraoMetrologico.objects.filter(id=padrao_id).first()
    if padrao is None:
        return None
    leituras = _leituras_ambientais_auxiliares(padrao_id)
    return mappers.model_para_usado_snapshot(padrao, leituras)


def _leituras_ambientais_auxiliares(
    padrao_principal_id: UUID,
) -> tuple[tuple[Grandeza, Decimal], ...]:
    """Grandezas de influencia dos auxiliares vigentes (C-8).

    Marco 5: expoe a grandeza monitorada por cada auxiliar vigente. O VALOR da
    leitura ambiental no instante do uso e responsabilidade do M4 (medicao em
    campo) — aqui devolvemos 0 como placeholder estrutural ate o app-tecnico
    plugar a leitura (Wave A). Mantem o contrato do VO sem inventar dado.
    """
    vinculos = VinculoAuxiliar.objects.filter(
        padrao_principal_id=padrao_principal_id, revogado_em__isnull=True
    )
    return tuple(
        (Grandeza.from_string(str(v.grandeza_influencia.get("simbolo", v.grandeza_influencia))), Decimal("0"))
        for v in vinculos
        if isinstance(v.grandeza_influencia, dict) and "simbolo" in v.grandeza_influencia
    )


def buscar_disponivel_para_calibracao(
    tenant_id: UUID,
    tenant_e_perfil_a: bool = False,
    hoje: _dt.date | None = None,
) -> list[UUID]:
    """IDs dos padroes EM_USO do tenant que NAO estao bloqueados (saude OK).

    Conveniencia de UI/selecao — reusa `padrao_bloqueado_para_uso` por padrao
    (fail-closed). Listagens grandes podem virar query batch em Wave A.
    """
    candidatos = PadraoMetrologico.objects.filter(
        tenant_id=tenant_id,
        estado=EstadoPadrao.EM_USO.value,
        revogado_em__isnull=True,
    ).values_list("id", flat=True)
    disponiveis: list[UUID] = []
    for pid in candidatos:
        bloqueado, _motivo = padrao_bloqueado_para_uso(pid, tenant_e_perfil_a, hoje)
        if not bloqueado:
            disponiveis.append(pid)
    return disponiveis
