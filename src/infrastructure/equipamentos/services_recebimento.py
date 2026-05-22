"""Service de recebimento de equipamento (T-EQP-047+048+050+058+059 /
US-EQP-006 AC-EQP-006-1+2+3b+10+11).

Orquestra:
1. Valida `condicao_visual_chegada` em enum.
2. Valida `anomalias_observadas` (INV-EQP-ANOM-001 — anti-PII, ≤500).
3. Se `condicao != integro`: exige `decisao_apos_anomalia` em enum +
   `justificativa_decisao` ≥30 + anti-PII (INV-EQP-ANOM-002).
4. Se `foto_bytes` presente: chama `services_foto_storage` (EXIF strip
   + sha256 + storage_key). Marco 2 dogfooding: foto opcional;
   Wave A: obrigatoria para perfil A.
5. Cria `EquipamentoRecebimento` em
   `status_fluxo_lab=recebido_pendente_inspecao`.
6. Atualiza `Equipamento.status` -> `em_calibracao_lab` (trigger PG
   `transicao_status_permitida` valida).
7. Publica `equipamento.recebido` (payload sanitizado com
   `foto_sha256` quando presente — P-EQP-S3 / AC-EQP-006-11).
8. Se `decisao_apos_anomalia=contatar_cliente_aguardando`: publica
   `equipamento.notificacao_cliente_aguardando` (consumer real Wave A
   `comunicacao-omnichannel`).

Service separado `transicionar_status_fluxo_lab` (T-EQP-050): muda
fase do `EquipamentoRecebimento.status_fluxo_lab`; trigger PG valida.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import IntegrityError, ProgrammingError, transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.equipamentos.models import (
    CondicaoVisualChegada,
    DecisaoAposAnomalia,
    Equipamento,
    EquipamentoRecebimento,
    EquipamentoStatus,
    StatusFluxoLab,
)
from src.infrastructure.equipamentos.services_foto_storage import (
    FotoInvalida,
    persistir_foto_preparada,
    preparar_foto,
)
from src.infrastructure.equipamentos.validators import (
    deve_emitir_alerta_ambiental_ausente,
    validar_anomalias_observadas,
    validar_condicoes_ambientais,
    validar_justificativa_decisao,
)


class RecebimentoInvalido(Exception):
    """Base de erros do service de recebimento."""


class CondicaoInvalida(RecebimentoInvalido):
    """`condicao_visual_chegada` fora do enum."""


class AnomaliaSemDecisao(RecebimentoInvalido):
    """`condicao != integro` exige `decisao_apos_anomalia`."""


class DecisaoInvalida(RecebimentoInvalido):
    """`decisao_apos_anomalia` fora do enum."""


class JustificativaInvalida(RecebimentoInvalido):
    """Justificativa <30 chars ou contem PII direta."""


class AnomaliasObservadasInvalidas(RecebimentoInvalido):
    """`anomalias_observadas` >500 chars ou contem PII direta."""


class TransicaoStatusFluxoLabInvalida(RecebimentoInvalido):
    """Transicao no `status_fluxo_lab` bloqueada pelo trigger PG."""


class CondicoesAmbientaisInvalidas(RecebimentoInvalido):
    """Faixa fora do razoavel ou justificativa ausente/PII (P-EQP-R3)."""


@dataclass(frozen=True)
class DadosRecebimento:
    condicao_visual_chegada: str
    anomalias_observadas: str = ""
    decisao_apos_anomalia: str = ""
    justificativa_decisao: str = ""
    foto_bytes: bytes | None = None
    foto_mime_type: str = ""
    # T-EQP-055 (P-EQP-R3 / AC-EQP-006-7b) — condicoes ambientais.
    # None = ausente; quando todos None exige `justificativa_ambiental_ausentes`.
    temp_ambiente_c: float | int | str | None = None
    ur_percentual: float | int | str | None = None
    pressao_kpa: float | int | str | None = None
    justificativa_ambiental_ausentes: str = ""


@dataclass(frozen=True)
class ResultadoRecebimento:
    recebimento: EquipamentoRecebimento
    foto_storage_key: str
    foto_sha256: str
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def criar_recebimento(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    recebido_por_id: UUID,
    dados: DadosRecebimento,
    causation_id: UUID | None = None,
) -> ResultadoRecebimento:
    """Cria 1 `EquipamentoRecebimento` + publica eventos.

    Pre-condicoes (fail-fast):
    - condicao em enum.
    - anomalias_observadas anti-PII (INV-EQP-ANOM-001).
    - condicao != integro -> decisao em enum + justificativa ≥30 + anti-PII.
    - foto (opcional Marco 2): mime + tamanho + EXIF strip + sha256.
    """
    if dados.condicao_visual_chegada not in CondicaoVisualChegada.values:
        raise CondicaoInvalida(
            f"condicao_visual_chegada '{dados.condicao_visual_chegada}' "
            "invalida."
        )

    try:
        validar_anomalias_observadas(dados.anomalias_observadas)
    except ValueError as exc:
        raise AnomaliasObservadasInvalidas(str(exc)) from exc

    # T-EQP-055 (P-EQP-R3) — condicoes ambientais.
    try:
        validar_condicoes_ambientais(
            temp_ambiente_c=dados.temp_ambiente_c,
            ur_percentual=dados.ur_percentual,
            pressao_kpa=dados.pressao_kpa,
            justificativa_ausentes=dados.justificativa_ambiental_ausentes,
        )
    except ValueError as exc:
        raise CondicoesAmbientaisInvalidas(str(exc)) from exc

    eh_integro = (
        dados.condicao_visual_chegada == CondicaoVisualChegada.INTEGRO.value
    )
    if not eh_integro:
        if not dados.decisao_apos_anomalia:
            raise AnomaliaSemDecisao(
                "AC-EQP-006-2 — condicao != integro exige "
                "`decisao_apos_anomalia`."
            )
        if dados.decisao_apos_anomalia not in DecisaoAposAnomalia.values:
            raise DecisaoInvalida(
                f"decisao_apos_anomalia '{dados.decisao_apos_anomalia}' "
                "invalida."
            )
        try:
            validar_justificativa_decisao(dados.justificativa_decisao)
        except ValueError as exc:
            raise JustificativaInvalida(str(exc)) from exc

    causation_id = causation_id or uuid4()

    # Foto: prepara ANTES do INSERT do recebimento — evita UPDATE
    # pos-INSERT bloqueado pelo trigger T-EQP-058.
    preparada = None
    foto_storage_key = ""
    foto_sha256 = ""
    if dados.foto_bytes is not None:
        try:
            preparada = preparar_foto(
                conteudo_bytes=dados.foto_bytes,
                mime_type=dados.foto_mime_type,
            )
        except FotoInvalida:
            raise
        foto_storage_key = preparada.storage_key
        foto_sha256 = preparada.foto_sha256

    def _normalizar(valor: float | int | str | None) -> Decimal | None:
        if valor is None:
            return None
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                return None
        # Conversao via str pra evitar imprecisao binaria do float
        # (Decimal(0.1) != Decimal('0.1')).
        return Decimal(str(valor))

    temp_normalizado = _normalizar(dados.temp_ambiente_c)
    ur_normalizado = _normalizar(dados.ur_percentual)
    pressao_normalizado = _normalizar(dados.pressao_kpa)
    justificativa_ambiental = (
        dados.justificativa_ambiental_ausentes or ""
    ).strip()

    with transaction.atomic():
        recebimento = EquipamentoRecebimento.objects.create(
            tenant_id=tenant_id,
            equipamento=equipamento,
            condicao_visual_chegada=dados.condicao_visual_chegada,
            anomalias_observadas=(dados.anomalias_observadas or "").strip(),
            decisao_apos_anomalia=dados.decisao_apos_anomalia,
            justificativa_decisao=(dados.justificativa_decisao or "").strip(),
            foto_storage_key=foto_storage_key,
            foto_sha256=foto_sha256,
            recebido_por_id=recebido_por_id,
            temp_ambiente_c=temp_normalizado,
            ur_percentual=ur_normalizado,
            pressao_kpa=pressao_normalizado,
            justificativa_condicoes_ambientais_ausentes=justificativa_ambiental,
        )

        # Persiste BLOB da foto na tabela 1:1 (apos INSERT do
        # recebimento — FK valida).
        if preparada is not None:
            persistir_foto_preparada(
                tenant_id=tenant_id,
                recebimento_id=recebimento.id,
                preparada=preparada,
            )

        # Atualiza Equipamento.status -> em_calibracao_lab (matriz
        # `transicao_status_permitida` migration 0002).
        try:
            Equipamento.objects.filter(id=equipamento.id).update(
                status=EquipamentoStatus.EM_CALIBRACAO_LAB.value
            )
        except (IntegrityError, ProgrammingError):
            # Se transicao bloqueada (ex: equipamento ja em sucata),
            # o recebimento ja foi gravado — mantemos o recebimento
            # como evidencia historica + status do equipamento intocado.
            # Wave A: politica explicita.
            pass

        # P-EQP-S3 / AC-EQP-006-11 — payload sanitizado inclui foto_sha256.
        # T-EQP-055 (P-EQP-R3) — bloco ambiental: valores numericos OK no
        # payload (sao medidas, nao PII). Justificativa NUNCA vaza (pode
        # ter rastros de texto livre).
        payload: dict[str, object] = {
            "tenant_id": str(tenant_id),
            "equipamento_id": str(equipamento.id),
            "recebimento_id": str(recebimento.id),
            "condicao_visual_chegada": recebimento.condicao_visual_chegada,
            "status_fluxo_lab": recebimento.status_fluxo_lab,
            "tem_foto": bool(foto_storage_key),
            "foto_sha256": foto_sha256,
            "data_recebimento": recebimento.data_recebimento.isoformat(),
            "ambiente": {
                "temp_ambiente_c": (
                    float(temp_normalizado) if temp_normalizado is not None else None
                ),
                "ur_percentual": (
                    float(ur_normalizado) if ur_normalizado is not None else None
                ),
                "pressao_kpa": (
                    float(pressao_normalizado) if pressao_normalizado is not None else None
                ),
                "tem_justificativa_ausentes": bool(justificativa_ambiental),
            },
        }
        if not eh_integro:
            payload["decisao_apos_anomalia"] = recebimento.decisao_apos_anomalia

        evento = publicar_evento(
            acao="equipamento.recebido",
            tenant_id=tenant_id,
            usuario_id=recebido_por_id,
            causation_id=causation_id,
            payload=payload,
            resource_summary=(
                f"equipamento:{equipamento.id}:recebido:{recebimento.id}"
            ),
        )

        # T-EQP-055 (P-EQP-R3 / AC-EQP-006-7b) — alerta P3 stub quando
        # recebimento gravado sem nenhuma medicao ambiental E sem
        # justificativa. Wave A: hard block conforme matriz
        # exigencia-por-grandeza.
        if deve_emitir_alerta_ambiental_ausente(
            temp_ambiente_c=temp_normalizado,
            ur_percentual=ur_normalizado,
            pressao_kpa=pressao_normalizado,
            justificativa_ausentes=justificativa_ambiental,
        ):
            publicar_evento(
                acao="equipamento.recebimento_sem_ambiente",
                tenant_id=tenant_id,
                usuario_id=recebido_por_id,
                causation_id=causation_id,
                payload={
                    "tenant_id": str(tenant_id),
                    "equipamento_id": str(equipamento.id),
                    "recebimento_id": str(recebimento.id),
                    "data_recebimento": recebimento.data_recebimento.isoformat(),
                },
                resource_summary=(
                    f"equipamento:{equipamento.id}:"
                    f"recebimento_sem_ambiente:{recebimento.id}"
                ),
            )

        # AC-EQP-006-2 — decisao=contatar_cliente_aguardando dispara
        # evento adicional para consumer NotificacaoClienteService
        # (stub Marco 2; consumer real Wave A `comunicacao-omnichannel`).
        if (
            recebimento.decisao_apos_anomalia
            == DecisaoAposAnomalia.CONTATAR_CLIENTE_AGUARDANDO.value
        ):
            publicar_evento(
                acao="equipamento.notificacao_cliente_aguardando",
                tenant_id=tenant_id,
                usuario_id=recebido_por_id,
                causation_id=causation_id,
                payload={
                    "tenant_id": str(tenant_id),
                    "equipamento_id": str(equipamento.id),
                    "recebimento_id": str(recebimento.id),
                    "condicao_visual_chegada": (
                        recebimento.condicao_visual_chegada
                    ),
                    "solicitado_em": recebimento.data_recebimento.isoformat(),
                },
                resource_summary=(
                    f"equipamento:{equipamento.id}:"
                    f"notificacao_aguardando:{recebimento.id}"
                ),
            )

    return ResultadoRecebimento(
        recebimento=recebimento,
        foto_storage_key=foto_storage_key,
        foto_sha256=foto_sha256,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


@dataclass(frozen=True)
class ResultadoTransicao:
    recebimento: EquipamentoRecebimento
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def transicionar_status_fluxo_lab(
    *,
    tenant_id: UUID,
    recebimento: EquipamentoRecebimento,
    status_alvo: str,
    transicionado_por_id: UUID,
    observacao: str = "",
    causation_id: UUID | None = None,
) -> ResultadoTransicao:
    """Transiciona `recebimento.status_fluxo_lab` para `status_alvo`.

    Pre-condicoes (fail-fast):
    - `status_alvo` em `StatusFluxoLab.values`.
    - Transicao permitida pela matriz no trigger PG
      `transicao_status_fluxo_lab_permitida`.
    """
    if status_alvo not in StatusFluxoLab.values:
        raise TransicaoStatusFluxoLabInvalida(
            f"status_alvo '{status_alvo}' fora do enum."
        )

    causation_id = causation_id or uuid4()
    status_origem = recebimento.status_fluxo_lab

    with transaction.atomic():
        try:
            EquipamentoRecebimento.objects.filter(id=recebimento.id).update(
                status_fluxo_lab=status_alvo
            )
        except (IntegrityError, ProgrammingError) as exc:
            raise TransicaoStatusFluxoLabInvalida(
                f"transicao {status_origem} -> {status_alvo} bloqueada: {exc}"
            ) from exc

        recebimento.refresh_from_db()
        if recebimento.status_fluxo_lab != status_alvo:
            raise TransicaoStatusFluxoLabInvalida(
                f"transicao {status_origem} -> {status_alvo} nao aplicada."
            )

        evento = publicar_evento(
            acao="equipamento.recebimento_transicionado",
            tenant_id=tenant_id,
            usuario_id=transicionado_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(recebimento.equipamento_id),
                "recebimento_id": str(recebimento.id),
                "status_origem": status_origem,
                "status_alvo": status_alvo,
                "transicionado_em": recebimento.data_recebimento.isoformat(),
                "tem_observacao": bool(observacao),
            },
            resource_summary=(
                f"equipamento:{recebimento.equipamento_id}:"
                f"recebimento_transicionado:{recebimento.id}:"
                f"{status_origem}_to_{status_alvo}"
            ),
        )

    return ResultadoTransicao(
        recebimento=recebimento,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
