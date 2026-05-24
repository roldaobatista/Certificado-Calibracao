"""Use case `coletar_aceite_atividade` — T-OS-063 (Fase 5).

Cobre AC-OS-004-7 (P-OS-A1 — consentimento art. 11 LGPD antes de aceite)
+ INV-OS-CONSBIO-001.

Fluxo:
1. Cria `ConsentimentoBiometriaTouch` (Padrao B imutavel) PRIMEIRO quando
   `biometria_payload_encrypted` presente — pre-requisito formal.
2. Cria `AceiteAtividade` (Padrao B imutavel) com FK 1:1 ao consentimento
   quando bio touch.
3. Texto canonicalizado via ADR-0029 + INV-DOC-CANON-001 (hash determinístico).

Use case puro.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.operacao.os.entities import (
    AceiteAtividadeSnapshot,
    ConsentimentoBiometriaTouchSnapshot,
)
from src.domain.operacao.os.regras import (
    canonicalizar_texto_probatorio,
    hash_texto_canonicalizado,
    valida_consentimento_biometria,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import EstadoAtividade


@dataclass(frozen=True, slots=True)
class ColetarAceiteInput:
    atividade_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    texto_aceite_bruto: str  # canonicalizado dentro do use case
    coletado_em: datetime
    correlation_id: UUID
    # Biometria opcional. Quando presente, ConsentimentoBiometriaTouch e
    # criado ANTES de AceiteAtividade (INV-OS-CONSBIO-001).
    biometria_payload_encrypted: bytes | None = None
    biometria_key_id: str = ""
    consentimento_texto_canonico_id: UUID | None = None  # NOT NULL se bio
    consentimento_texto_hash: str = ""
    consentimento_versao_politica: str = ""
    consentimento_concedido_em: datetime | None = None
    consentimento_tela_evidencia: bytes | None = None
    geo_lat: float | None = None
    geo_long: float | None = None
    geo_municipio_hash: str = ""


@dataclass(frozen=True, slots=True)
class ColetarAceiteResultado:
    aceite_id: UUID
    consentimento_id: UUID | None
    atividade_id: UUID
    correlation_id: UUID


class ErroColetarAceite(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def coletar_aceite_atividade(
    *,
    payload: ColetarAceiteInput,
    repository: OSRepository,
) -> ColetarAceiteResultado:
    """Cria ConsentimentoBiometriaTouch (quando bio touch) + AceiteAtividade."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroColetarAceite("AtividadeNaoEncontrada", 404)
    if atividade.estado != EstadoAtividade.EM_EXECUCAO:
        raise ErroColetarAceite(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; aceite so em EM_EXECUCAO",
        )

    # Aceite ja existe?
    existente = repository.get_aceite_por_atividade(payload.atividade_id)
    if existente is not None:
        raise ErroColetarAceite(
            "AceiteJaColetado",
            409,
            detalhe=f"aceite_id={existente.id}",
        )

    bio_presente = payload.biometria_payload_encrypted is not None

    # AC-OS-004-7: bio touch exige ConsentimentoBiometriaTouch ANTES.
    consentimento_id: UUID | None = None
    if bio_presente:
        if payload.consentimento_concedido_em is None:
            raise ErroColetarAceite(
                "ConsentimentoBiometriaAusente",
                412,
                detalhe="bio touch exige ConsentimentoBiometriaTouch (LGPD art. 11 II 'a')",
            )
        if not payload.consentimento_texto_hash or not payload.consentimento_versao_politica:
            raise ErroColetarAceite(
                "ConsentimentoIncompleto",
                412,
                detalhe="texto_hash + versao_politica obrigatorios",
            )
        if payload.consentimento_texto_canonico_id is None:
            raise ErroColetarAceite(
                "ConsentimentoIncompleto",
                412,
                detalhe="texto_canonico_id obrigatorio",
            )
        consentimento_id = uuid4()
        consent_snapshot = ConsentimentoBiometriaTouchSnapshot(
            id=consentimento_id,
            tenant_id=atividade.tenant_id,
            atividade_id=atividade.id,
            cliente_referencia_hash=payload.cliente_referencia_hash,
            cliente_key_id=payload.cliente_key_id,
            texto_canonico_id=payload.consentimento_texto_canonico_id,
            texto_hash=payload.consentimento_texto_hash,
            versao_politica=payload.consentimento_versao_politica,
            concedido_em=payload.consentimento_concedido_em,
            tela_renderizada_evidencia=payload.consentimento_tela_evidencia,
            criado_em=payload.coletado_em,
        )
        repository.salvar_consentimento(consent_snapshot)

    # AceiteAtividade.
    texto_canonico = canonicalizar_texto_probatorio(payload.texto_aceite_bruto)
    texto_hash = hash_texto_canonicalizado(payload.texto_aceite_bruto)
    aceite_snapshot = AceiteAtividadeSnapshot(
        id=uuid4(),
        tenant_id=atividade.tenant_id,
        atividade_id=atividade.id,
        consentimento_id=consentimento_id,
        cliente_referencia_hash=payload.cliente_referencia_hash,
        cliente_key_id=payload.cliente_key_id,
        texto_canonicalizado=texto_canonico,
        texto_hash=texto_hash,
        biometria_payload_encrypted=payload.biometria_payload_encrypted,
        biometria_key_id=payload.biometria_key_id,
        coletado_em=payload.coletado_em,
        geo_lat=payload.geo_lat,
        geo_long=payload.geo_long,
        geo_municipio_hash=payload.geo_municipio_hash,
        criado_em=payload.coletado_em,
    )
    # INV-OS-CONSBIO-001 — domain layer falha cedo se invariante violada.
    valida_consentimento_biometria(aceite_snapshot)
    salvo = repository.salvar_aceite(aceite_snapshot)

    return ColetarAceiteResultado(
        aceite_id=salvo.id,
        consentimento_id=consentimento_id,
        atividade_id=atividade.id,
        correlation_id=payload.correlation_id,
    )
