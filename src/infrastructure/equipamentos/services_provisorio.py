"""Service de recebimento provisorio (T-EQP-053 / US-EQP-006 AC-EQP-006-6
/ INV-EQP-PROV-001 / P-EQP-R9 — Caminho A Roldao).

Cobre:
1. `criar_provisorio`: cria `RecebimentoProvisorio` + valida foto +
   calcula TTL D+7 + publica `equipamento.recebido_provisoriamente`.
2. `promover_provisorio`: cria `Equipamento` canonico + 1o
   `EquipamentoRecebimento` no mesmo bloco transacional + atualiza
   status do provisorio (`promovido` + UUID) + publica
   `equipamento.promovido_de_provisorio`. One-shot — trigger PG
   bloqueia re-promocao.

Defesa em camadas:
- Trigger PG `recebimento_provisorio_imutavel` (migration 0024):
  bloqueia mutacao em campos CORE pos-INSERT + bloqueia transicao
  saindo de status terminal.
- CHECK constraint Django `ck_provisorio_promovido_all_or_nothing`.
- Foto obrigatoria via service (defesa A; corretora RAT-EQP-FOTO).

Payload sanitizado (whitelist FECHADA):
RECEBIDO_PROVISORIO: provisorio_id, tag_provisoria,
    condicao_visual_chegada, foto_sha256, ttl_expira_em,
    data_recebimento.
PROMOVIDO: provisorio_id, equipamento_id, recebimento_id,
    tag_canonica, promovido_em.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.equipamentos.models import (
    CondicaoVisualChegada,
    Equipamento,
    EquipamentoRecebimento,
    EquipamentoStatus,
    RecebimentoProvisorio,
    RecebimentoProvisorioFoto,
    StatusFluxoLab,
    StatusRecebimentoProvisorio,
)
from src.infrastructure.equipamentos.services_foto_storage import (
    FotoInvalida,
    preparar_foto,
)
from src.infrastructure.equipamentos.validators import (
    LIMITE_LOCALIZACAO_FISICA,
    conter_pii_direta,
)

TTL_PROVISORIO_DIAS = 7
TAG_PROVISORIA_MIN_CHARS = 4
DESCRICAO_PROVISORIA_MIN_CHARS = 10


class ProvisorioInvalido(Exception):
    """Base de erros do service de provisorio."""


class TagProvisoriaInvalida(ProvisorioInvalido):
    """`tag_provisoria` <4 chars ou contem PII direta."""


class DescricaoEstimadaInvalida(ProvisorioInvalido):
    """`descricao_estimada` muito curta / com PII / >LIMITE."""


class FotoObrigatoriaProvisorio(ProvisorioInvalido):
    """Marco 2 + corretora: foto obrigatoria no provisorio."""


class CondicaoProvisorioInvalida(ProvisorioInvalido):
    """`condicao_visual_chegada` fora do enum."""


class ProvisorioJaPromovido(ProvisorioInvalido):
    """Promocao e one-shot — segunda tentativa retorna 409."""


class ProvisorioExpirado(ProvisorioInvalido):
    """Provisorio com `ttl_expira_em <= now()` OU status=expirado_descartado."""


class TagCanonicaInvalida(ProvisorioInvalido):
    """`tag_canonica` <4 chars / PII / duplicada (INV-049)."""


@dataclass(frozen=True)
class DadosCriarProvisorio:
    tag_provisoria: str
    descricao_estimada: str
    condicao_visual_chegada: str
    foto_bytes: bytes
    foto_mime_type: str


@dataclass(frozen=True)
class ResultadoCriarProvisorio:
    provisorio: RecebimentoProvisorio
    foto_sha256: str
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def criar_provisorio(
    *,
    tenant_id: UUID,
    recebido_por_id: UUID,
    dados: DadosCriarProvisorio,
    causation_id: UUID | None = None,
) -> ResultadoCriarProvisorio:
    """Cria `RecebimentoProvisorio` com foto + TTL D+7.

    Pre-condicoes (fail-fast):
    - tag_provisoria >=4 chars + anti-PII.
    - descricao_estimada 10..200 chars + anti-PII.
    - condicao em enum.
    - foto obrigatoria (Marco 2 dogfooding + corretora).
    """
    tag = (dados.tag_provisoria or "").strip()
    if len(tag) < TAG_PROVISORIA_MIN_CHARS:
        raise TagProvisoriaInvalida(
            f"tag_provisoria exige >={TAG_PROVISORIA_MIN_CHARS} chars "
            f"(atual={len(tag)})."
        )
    if conter_pii_direta(tag):
        raise TagProvisoriaInvalida(
            "tag_provisoria contem PII direta (CPF/CNPJ/e-mail/telefone/"
            "nomes proprios consecutivos)."
        )

    descricao = (dados.descricao_estimada or "").strip()
    if len(descricao) < DESCRICAO_PROVISORIA_MIN_CHARS:
        raise DescricaoEstimadaInvalida(
            f"descricao_estimada exige >={DESCRICAO_PROVISORIA_MIN_CHARS} "
            f"chars (atual={len(descricao)})."
        )
    if len(descricao) > LIMITE_LOCALIZACAO_FISICA:
        raise DescricaoEstimadaInvalida(
            f"descricao_estimada nao pode passar de "
            f"{LIMITE_LOCALIZACAO_FISICA} chars (atual={len(descricao)})."
        )
    if conter_pii_direta(descricao):
        raise DescricaoEstimadaInvalida(
            "descricao_estimada contem PII direta."
        )

    if dados.condicao_visual_chegada not in CondicaoVisualChegada.values:
        raise CondicaoProvisorioInvalida(
            f"condicao_visual_chegada '{dados.condicao_visual_chegada}' "
            "invalida."
        )

    if not dados.foto_bytes:
        raise FotoObrigatoriaProvisorio(
            "Foto obrigatoria no recebimento provisorio (Marco 2 + "
            "corretora RAT-EQP-FOTO)."
        )

    # Prepara foto ANTES do INSERT (mesmo padrao recebimento).
    try:
        preparada = preparar_foto(
            conteudo_bytes=dados.foto_bytes, mime_type=dados.foto_mime_type
        )
    except FotoInvalida:
        raise

    causation_id = causation_id or uuid4()
    ttl_expira_em = timezone.now() + timedelta(days=TTL_PROVISORIO_DIAS)

    with transaction.atomic():
        provisorio = RecebimentoProvisorio.objects.create(
            tenant_id=tenant_id,
            tag_provisoria=tag,
            descricao_estimada=descricao,
            condicao_visual_chegada=dados.condicao_visual_chegada,
            foto_storage_key=preparada.storage_key,
            foto_sha256=preparada.foto_sha256,
            recebido_por_id=recebido_por_id,
            ttl_expira_em=ttl_expira_em,
        )

        RecebimentoProvisorioFoto.objects.create(
            tenant_id=tenant_id,
            provisorio=provisorio,
            storage_key=preparada.storage_key,
            conteudo_bytes=preparada.bytes_limpos,
            mime_type=preparada.mime_type,
            tamanho_bytes=preparada.tamanho_bytes,
        )

        evento = publicar_evento(
            acao="equipamento.recebido_provisoriamente",
            tenant_id=tenant_id,
            usuario_id=recebido_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "provisorio_id": str(provisorio.id),
                "tag_provisoria": provisorio.tag_provisoria,
                "condicao_visual_chegada": provisorio.condicao_visual_chegada,
                "foto_sha256": provisorio.foto_sha256,
                "ttl_expira_em": provisorio.ttl_expira_em.isoformat(),
                "data_recebimento": provisorio.data_recebimento.isoformat(),
            },
            resource_summary=(
                f"provisorio:{provisorio.id}:recebido"
            ),
        )

    return ResultadoCriarProvisorio(
        provisorio=provisorio,
        foto_sha256=preparada.foto_sha256,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


@dataclass(frozen=True)
class DadosPromoverProvisorio:
    """Dados pra promover a `Equipamento` canonico (1o cadastro).

    `tag_canonica`, `numero_serie`, `fabricante`, `modelo`,
    `cliente_atual_id`, `perfil_tenant_snapshot` — mesmo schema do
    `services_equipamento.criar_equipamento`.
    """

    tag_canonica: str
    numero_serie: str
    fabricante: str
    modelo: str
    cliente_atual_id: UUID | None = None
    perfil_tenant_snapshot: dict | None = None
    snapshot_schema_version: str = "1.0.0"


@dataclass(frozen=True)
class ResultadoPromover:
    provisorio: RecebimentoProvisorio
    equipamento: Equipamento
    recebimento: EquipamentoRecebimento
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def promover_provisorio(
    *,
    tenant_id: UUID,
    provisorio: RecebimentoProvisorio,
    promovido_por_id: UUID,
    dados: DadosPromoverProvisorio,
    causation_id: UUID | None = None,
) -> ResultadoPromover:
    """Promove o provisorio a `Equipamento` canonico:
    1. Valida status `pendente_promocao` (one-shot via trigger PG).
    2. Cria `Equipamento` canonico via `services_equipamento.criar_equipamento`.
    3. Cria 1o `EquipamentoRecebimento` canonico (reusa
       `condicao_visual_chegada` + foto do provisorio).
    4. Atualiza provisorio.status -> promovido + equipamento_promovido_id +
       promovido_em.
    5. Publica `equipamento.promovido_de_provisorio`.
    """
    if provisorio.status == StatusRecebimentoProvisorio.PROMOVIDO.value:
        raise ProvisorioJaPromovido(
            "provisorio ja promovido — re-promocao bloqueada (one-shot)."
        )
    if provisorio.status == StatusRecebimentoProvisorio.EXPIRADO_DESCARTADO.value:
        raise ProvisorioExpirado(
            "provisorio em estado expirado_descartado — re-promocao "
            "bloqueada. Criar novo provisorio."
        )
    if provisorio.ttl_expira_em <= timezone.now():
        raise ProvisorioExpirado(
            "provisorio com TTL D+7 vencido — promocao bloqueada. "
            "Aguarde job marcar como expirado_descartado ou crie novo."
        )

    tag_canonica = (dados.tag_canonica or "").strip()
    if len(tag_canonica) < TAG_PROVISORIA_MIN_CHARS:
        raise TagCanonicaInvalida(
            f"tag_canonica exige >={TAG_PROVISORIA_MIN_CHARS} chars."
        )
    if conter_pii_direta(tag_canonica):
        raise TagCanonicaInvalida("tag_canonica contem PII direta.")

    causation_id = causation_id or uuid4()

    from src.infrastructure.equipamentos.services_equipamento import (
        DadosCriacaoEquipamento,
        TagDuplicada,
        criar_equipamento,
    )

    with transaction.atomic():
        # 1. Cria Equipamento canonico (reusa pipeline de criacao com
        #    INV-049 TAG unica + RLS + perfil_tenant_snapshot).
        try:
            equipamento = criar_equipamento(
                tenant_id=tenant_id,
                criado_por_id=promovido_por_id,
                dados=DadosCriacaoEquipamento(
                    tag=tag_canonica,
                    numero_serie=dados.numero_serie,
                    fabricante=dados.fabricante,
                    modelo=dados.modelo,
                    cliente_atual_id=dados.cliente_atual_id,
                    perfil_tenant_snapshot=dados.perfil_tenant_snapshot,
                    snapshot_schema_version=dados.snapshot_schema_version,
                ),
            )
        except TagDuplicada as exc:
            raise TagCanonicaInvalida(
                f"tag_canonica '{tag_canonica}' ja existe no tenant: {exc}"
            ) from exc

        # 2. Cria 1o EquipamentoRecebimento canonico (mesma foto +
        #    condicao do provisorio). Reusa foto_storage_key existente
        #    no provisorio — Wave A: criar novo asset; Marco 2 reaproveita.
        # Status inicial `recebido_pendente_inspecao` (default).
        recebimento_canonico = EquipamentoRecebimento.objects.create(
            tenant_id=tenant_id,
            equipamento=equipamento,
            condicao_visual_chegada=provisorio.condicao_visual_chegada,
            anomalias_observadas=(
                f"Promovido de provisorio {provisorio.id} "
                f"(tag provisoria: {provisorio.tag_provisoria})."
            )[:500],
            foto_storage_key=provisorio.foto_storage_key,
            foto_sha256=provisorio.foto_sha256,
            recebido_por_id=promovido_por_id,
        )

        # 3. Atualiza Equipamento.status -> em_calibracao_lab (matriz
        #    transicao_status_permitida valida).
        from django.db import IntegrityError, ProgrammingError

        try:
            Equipamento.objects.filter(id=equipamento.id).update(
                status=EquipamentoStatus.EM_CALIBRACAO_LAB.value
            )
        except (IntegrityError, ProgrammingError):
            pass

        # 4. Atualiza provisorio -> promovido (trigger PG valida que
        #    `status` muda apenas pendente -> promovido/expirado e que
        #    nenhum campo CORE muda).
        agora = timezone.now()
        RecebimentoProvisorio.objects.filter(id=provisorio.id).update(
            status=StatusRecebimentoProvisorio.PROMOVIDO.value,
            equipamento_promovido_id=equipamento.id,
            promovido_em=agora,
        )
        provisorio.refresh_from_db()
        equipamento.refresh_from_db()
        recebimento_canonico.refresh_from_db()

        evento = publicar_evento(
            acao="equipamento.promovido_de_provisorio",
            tenant_id=tenant_id,
            usuario_id=promovido_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "provisorio_id": str(provisorio.id),
                "equipamento_id": str(equipamento.id),
                "recebimento_id": str(recebimento_canonico.id),
                "tag_canonica": equipamento.tag,
                "promovido_em": agora.isoformat(),
            },
            resource_summary=(
                f"provisorio:{provisorio.id}:promovido:{equipamento.id}"
            ),
        )

    return ResultadoPromover(
        provisorio=provisorio,
        equipamento=equipamento,
        recebimento=recebimento_canonico,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


def calcular_taxa_provisorios_mensal(
    *, tenant_id: UUID
) -> dict:
    """T-EQP-057 / AC-EQP-006-9 — calcula taxa_provisorios_mensal:

    `pendentes_ativos / (recebimentos_canonicos_do_mes + provisorios_do_mes)`.

    Alerta P2 quando >5%. Retorna dict com numerador/denominador +
    flag `alerta_excedido`.
    """
    from datetime import UTC, datetime

    agora = datetime.now(UTC)
    inicio_mes = agora.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    pendentes = RecebimentoProvisorio.objects.filter(
        tenant_id=tenant_id,
        status=StatusRecebimentoProvisorio.PENDENTE_PROMOCAO.value,
        data_recebimento__gte=inicio_mes,
    ).count()
    promovidos_do_mes = RecebimentoProvisorio.objects.filter(
        tenant_id=tenant_id,
        status=StatusRecebimentoProvisorio.PROMOVIDO.value,
        promovido_em__gte=inicio_mes,
    ).count()
    recebimentos_canonicos_do_mes = EquipamentoRecebimento.objects.filter(
        tenant_id=tenant_id,
        data_recebimento__gte=inicio_mes,
    ).count()
    total_provisorios_do_mes = pendentes + promovidos_do_mes
    denominador = recebimentos_canonicos_do_mes + total_provisorios_do_mes
    taxa = pendentes / denominador if denominador else 0.0

    return {
        "tenant_id": str(tenant_id),
        "inicio_mes": inicio_mes.isoformat(),
        "pendentes_ativos": pendentes,
        "promovidos_no_mes": promovidos_do_mes,
        "recebimentos_canonicos_no_mes": recebimentos_canonicos_do_mes,
        "denominador": denominador,
        "taxa_provisorios_mensal": round(taxa, 4),
        "alerta_excedido": taxa > 0.05,
        "limiar_p2": 0.05,
    }


def marcar_provisorios_expirados(tenant_id: UUID) -> int:
    """T-EQP-056 — itera provisorios com TTL vencido e marca como
    `expirado_descartado` + publica `sistema.provisorio_expirado`.

    Retorna numero de provisorios marcados.
    """
    from src.infrastructure.multitenant.connection import run_as_system

    agora = timezone.now()
    pendentes_expirados = list(
        RecebimentoProvisorio.objects.filter(
            tenant_id=tenant_id,
            status=StatusRecebimentoProvisorio.PENDENTE_PROMOCAO.value,
            ttl_expira_em__lte=agora,
        ).only(
            "id", "tag_provisoria", "data_recebimento", "ttl_expira_em"
        )
    )

    contagem = 0
    for prov in pendentes_expirados:
        with transaction.atomic():
            RecebimentoProvisorio.objects.filter(id=prov.id).update(
                status=StatusRecebimentoProvisorio.EXPIRADO_DESCARTADO.value
            )
            contagem += 1

        # Publica evento sistema (modo_sistema).
        with run_as_system():
            publicar_evento(
                acao="sistema.provisorio_expirado",
                tenant_id=None,
                causation_id=uuid4(),
                payload={
                    "provisorio_id": str(prov.id),
                    "tenant_id_alvo": str(tenant_id),
                    "tag_provisoria": prov.tag_provisoria,
                    "data_recebimento": prov.data_recebimento.isoformat(),
                    "ttl_expira_em": prov.ttl_expira_em.isoformat(),
                    "expirado_em": agora.isoformat(),
                },
                resource_summary=f"provisorio:{prov.id}:expirado",
            )

    # Suprime warning de variavel nao usada (StatusFluxoLab importado
    # apenas pra clareza semantica do ciclo do laboratorio).
    _ = StatusFluxoLab
    return contagem
