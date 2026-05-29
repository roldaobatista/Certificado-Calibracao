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
    RecalExternoPadrao,
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
    limite: int = 200,
) -> list[UUID]:
    """IDs dos padroes EM_USO do tenant que NAO estao bloqueados (saude OK).

    Conveniencia de UI/selecao — reusa `padrao_bloqueado_para_uso` por padrao
    (fail-closed). `limite` capa o numero de candidatos avaliados (default 200,
    teto F-C3) pra evitar payload/queries ilimitados; o caller pagina o restante.

    GATE-PAD-PERF-DISPONIVEIS (Wave A): o loop chama a porta por padrao (N+1
    bounded por `limite`). Otimizacao batch (pre-carregar VI/PT/vinculo/carta em
    dicts e decidir em memoria) fica rastreada; baseline congelado por teste
    assertNumQueries. Uso single-padrao pelo M4 (1 chamada) nao e afetado.
    """
    candidatos = PadraoMetrologico.objects.filter(
        tenant_id=tenant_id,
        estado=EstadoPadrao.EM_USO.value,
        revogado_em__isnull=True,
    ).values_list("id", flat=True)[:limite]
    disponiveis: list[UUID] = []
    for pid in candidatos:
        bloqueado, _motivo = padrao_bloqueado_para_uso(pid, tenant_e_perfil_a, hoje)
        if not bloqueado:
            disponiveis.append(pid)
    return disponiveis


def carta_controle_readmodel(padrao_id: UUID) -> dict[str, object] | None:
    """Read-model da carta Shewhart (US-PAD-008-1 / ADR-0070 — perfil A na borda).

    Recalcula on-demand a serie de desvios das VIs + limites (LC/UCL/LCL/zona
    de alerta +/-2 sigma) + violacoes Western Electric. NAO persiste (a DECISAO do RT e que vira
    `AnaliseCartaControle` WORM — INV-PAD-010). Retorna None se o padrao nao
    existe (RLS). O gate de perfil A e responsabilidade da view (INV-PAD-008).
    """
    padrao = PadraoMetrologico.objects.filter(id=padrao_id).first()
    if padrao is None:
        return None
    vis = list(
        VerificacaoIntermediaria.objects.filter(padrao_id=padrao_id).order_by("data_vi")
    )
    vis_com_desvio = [v for v in vis if v.desvio_observado is not None]
    pontos = [
        {
            "vi_id": str(v.id),
            "data_vi": v.data_vi.isoformat(),
            "desvio": str(v.desvio_observado),
        }
        for v in vis_com_desvio
    ]
    serie = [Decimal(str(v.desvio_observado)) for v in vis_com_desvio]
    if len(serie) < _MIN_PONTOS_CARTA:
        return {
            "padrao_id": str(padrao_id),
            "n_pontos": len(serie),
            "pontos": pontos,
            "limites": None,
            "violacoes": [],
            "motivo": "pontos insuficientes para carta de controle (< 2)",
        }
    limites = shewhart.calcular_limites(serie)
    violacoes = shewhart.detectar_violacoes(serie, limites)
    dois_sigma = Decimal("2") * limites.sigma
    return {
        "padrao_id": str(padrao_id),
        "n_pontos": len(serie),
        "linha_central": str(limites.linha_central),
        "ucl": str(limites.ucl),
        "lcl": str(limites.lcl),
        "sigma": str(limites.sigma),
        "zona_alerta_superior": str(limites.linha_central + dois_sigma),
        "zona_alerta_inferior": str(limites.linha_central - dois_sigma),
        "pontos": pontos,
        "violacoes": [v.regra.value for v in violacoes],
        "versao_motor_shewhart": shewhart.VERSAO_MOTOR_SHEWHART,
    }


def montar_dossie_cgcre(padrao_id: UUID) -> dict[str, object] | None:
    """Dossie CGCRE em JSON estruturado (US-PAD-006 — perfil A na borda).

    Exporta o cadastro + historico (recals/VIs/PTs/cartas) do padrao em dados
    estruturados (NAO PDF/A — non-goal Wave B). Sem PII crua: executores/RT vao
    como `*_id_hash` (HMAC-tenant). Retorna None se o padrao nao existe (RLS).
    O gate de perfil A e responsabilidade da view (US-PAD-006 supervisao CGCRE).
    """
    padrao_obj = PadraoMetrologico.objects.filter(id=padrao_id).first()
    if padrao_obj is None:
        return None
    snap = mappers.model_para_snapshot(padrao_obj)

    recais = [
        {
            "recal_id": str(r.id),
            "lab_externo": r.lab_externo,
            "status": r.status,
            "enviado_em": r.enviado_em.isoformat(),
            "retornado_em": r.retornado_em.isoformat() if r.retornado_em else None,
            "aprovado_rt_em": r.aprovado_rt_em.isoformat() if r.aprovado_rt_em else None,
            "responsavel_envio_id_hash": r.responsavel_envio_id_hash,
            "aprovado_rt_id_hash": r.aprovado_rt_id_hash,
        }
        for r in RecalExternoPadrao.objects.filter(padrao_id=padrao_id).order_by(
            "enviado_em"
        )
    ]
    vis = [
        {
            "vi_id": str(v.id),
            "data_vi": v.data_vi.isoformat(),
            "resultado": v.resultado,
            "desvio_observado": str(v.desvio_observado)
            if v.desvio_observado is not None
            else None,
            "executor_id_hash": v.executor_id_hash,
            "metodo_hash": v.metodo_hash,
        }
        for v in VerificacaoIntermediaria.objects.filter(padrao_id=padrao_id).order_by(
            "data_vi"
        )
    ]
    pts = [
        {
            "pt_id": str(p.id),
            "lab_organizador": p.lab_organizador,
            "protocolo": p.protocolo,
            "data_inicio": p.data_inicio.isoformat(),
            "resultado": p.resultado,
            "zeta_score": str(p.zeta_score) if p.zeta_score is not None else None,
        }
        for p in IntercomparacaoPT.objects.filter(padrao_id=padrao_id).order_by(
            "data_inicio"
        )
    ]
    cartas = [
        {
            "analise_id": str(a.id),
            "regra_violada": a.regra_violada,
            "decisao_rt": a.decisao_rt,
            "versao_motor_shewhart": a.versao_motor_shewhart,
            "criado_em": a.criado_em.isoformat(),
            "justificativa_hash": a.justificativa_hash,
        }
        for a in AnaliseCartaControle.objects.filter(padrao_id=padrao_id).order_by(
            "criado_em"
        )
    ]
    return {
        "padrao": {
            "id": str(snap.id),
            "numero_serie": snap.numero_serie,
            "fabricante": snap.fabricante,
            "modelo": snap.modelo,
            "subtipo": snap.subtipo.value,
            "classe": snap.classe.value,
            "vinculacao": snap.vinculacao.value,
            "grandezas": [g.value for g in snap.grandezas],
            "estado": snap.estado.value,
            "validade_certificado_rastreabilidade": (
                snap.validade_certificado_rastreabilidade.isoformat()
            ),
            "proximo_recal": snap.proximo_recal.isoformat(),
            "criterio_intervalo": snap.criterio_intervalo,
            "rastreabilidade_origem_revogada": snap.rastreabilidade_origem_revogada,
        },
        "recals_externos": recais,
        "verificacoes_intermediarias": vis,
        "intercomparacoes_pt": pts,
        "analises_carta_controle": cartas,
        "versao_dossie": "1.0",
    }
