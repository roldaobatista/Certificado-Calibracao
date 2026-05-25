"""Regras de transicao de estado-maquina + validacao de INVs (T-OS-022).

Dominio puro — sem Django, sem PG. Use cases consomem.

Cobertura:
- INV-OS-ATIV-001: OS so transita CONCLUIDA quando TODAS atividades terminais.
- INV-OS-ATIV-002: cross-tenant proibido entre OS e AtividadeDaOS.
- INV-OS-ATIV-003: tipo da atividade em enum fechado.
- INV-OS-ATIV-005: executor designado e unico autorizado a iniciar/concluir.
- INV-OS-CONSBIO-001: AceiteAtividade com bio touch exige consentimento_id.
- INV-OS-FAT-001: faturamento = sum(atividades nao canceladas).
- INV-DOC-CANON-001: canonicalizacao texto probatorio (texto_hash determinístico).
- Tabela de transicoes OS e AtividadeDaOS (espelha §4 da spec M3).
"""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterable
from decimal import Decimal

from .entities import (
    AceiteAtividadeSnapshot,
    AtividadeSnapshot,
    OSSnapshot,
)
from .value_objects import EstadoAtividade, EstadoOS

# =============================================================
# Tabelas de transicao estado-maquina (espelha spec M3 §4)
# =============================================================

_TRANSICOES_OS: frozenset[tuple[EstadoOS, EstadoOS]] = frozenset(
    {
        (EstadoOS.RASCUNHO, EstadoOS.AGENDADA),
        (EstadoOS.AGENDADA, EstadoOS.EM_EXECUCAO),
        (EstadoOS.EM_EXECUCAO, EstadoOS.CONCLUIDA),
        (EstadoOS.CONCLUIDA, EstadoOS.FATURADA),
        (EstadoOS.FATURADA, EstadoOS.PAGA),
        # Cancelamento desde qualquer estado nao-terminal:
        (EstadoOS.RASCUNHO, EstadoOS.CANCELADA),
        (EstadoOS.AGENDADA, EstadoOS.CANCELADA),
        (EstadoOS.EM_EXECUCAO, EstadoOS.CANCELADA),
    }
)


_TRANSICOES_ATIVIDADE: frozenset[tuple[EstadoAtividade, EstadoAtividade]] = frozenset(
    {
        (EstadoAtividade.PENDENTE, EstadoAtividade.AGENDADA),
        (EstadoAtividade.AGENDADA, EstadoAtividade.EM_EXECUCAO),
        (EstadoAtividade.EM_EXECUCAO, EstadoAtividade.CONCLUIDA),
        (EstadoAtividade.EM_EXECUCAO, EstadoAtividade.NAO_CONFORME),
        (EstadoAtividade.NAO_CONFORME, EstadoAtividade.EM_EXECUCAO),  # resolverNC
        # Cancelamento desde qualquer estado nao-terminal:
        (EstadoAtividade.PENDENTE, EstadoAtividade.CANCELADA),
        (EstadoAtividade.AGENDADA, EstadoAtividade.CANCELADA),
        (EstadoAtividade.EM_EXECUCAO, EstadoAtividade.CANCELADA),
    }
)


def transicao_os_permitida(de: EstadoOS, para: EstadoOS) -> bool:
    """Verifica se transicao da OS eh valida (INV-027 + INV-OS-ATIV-001)."""
    if de == para:
        return True
    return (de, para) in _TRANSICOES_OS


def transicao_atividade_permitida(de: EstadoAtividade, para: EstadoAtividade) -> bool:
    """Verifica se transicao da AtividadeDaOS eh valida."""
    if de == para:
        return True
    return (de, para) in _TRANSICOES_ATIVIDADE


# =============================================================
# INVs computados a partir de snapshots
# =============================================================


def os_deve_transitar_concluida(atividades: Iterable[AtividadeSnapshot]) -> bool:
    """INV-OS-ATIV-001: OS conclui quando TODAS atividades em estado terminal.

    `terminal` = CONCLUIDA | NAO_CONFORME | CANCELADA (vide
    `EstadoAtividade.terminal`). OS sem atividades NAO conclui (retorna False).
    """
    atividades_list = list(atividades)
    if not atividades_list:
        return False
    return all(a.estado.terminal for a in atividades_list)


def calcular_tipo_predominante(atividades: Iterable[AtividadeSnapshot]) -> str:
    """Calcula `tipo_predominante` da OS na transicao -> CONCLUIDA.

    Regra de empate (PRD §6 + AC-OS-004-3): `calibracao` sempre vence
    (alimenta KPI ISO 17025). Considera apenas atividades nao canceladas.
    """
    relevantes = [
        a for a in atividades if a.estado != EstadoAtividade.CANCELADA
    ]
    if not relevantes:
        return ""

    # Calibracao sempre vence.
    for a in relevantes:
        if a.tipo.value == "calibracao":
            return "calibracao"

    # Senao, retorna o tipo da atividade com maior `sequencia` (heuristica
    # razoavel: ultima atividade executada na ordem). Pode evoluir.
    return max(relevantes, key=lambda a: a.sequencia).tipo.value


def calcular_valor_total_atualizado(atividades: Iterable[AtividadeSnapshot]) -> Decimal:
    """INV-OS-FAT-001 (ADR-0042): sum(valor) de atividades nao canceladas."""
    return sum(
        (a.valor_unitario_snapshot for a in atividades if a.estado != EstadoAtividade.CANCELADA),
        start=Decimal(0),
    )


def atividade_pode_ser_iniciada_por(
    atividade: AtividadeSnapshot, user_id: object
) -> bool:
    """INV-OS-ATIV-005: executor designado eh unico autorizado a iniciar."""
    if atividade.estado != EstadoAtividade.PENDENTE and atividade.estado != EstadoAtividade.AGENDADA:
        return False
    if atividade.tecnico_executor_id is None:
        return False
    return atividade.tecnico_executor_id == user_id


def atividade_pode_ser_concluida_por(
    atividade: AtividadeSnapshot, user_id: object
) -> bool:
    """INV-OS-ATIV-005: executor designado eh unico autorizado a concluir."""
    if atividade.estado != EstadoAtividade.EM_EXECUCAO:
        return False
    if atividade.tecnico_executor_id is None:
        return False
    return atividade.tecnico_executor_id == user_id


def valida_tenant_atividade_da_os(
    atividade: AtividadeSnapshot, os: OSSnapshot
) -> None:
    """INV-OS-ATIV-002: AtividadeDaOS herda tenant da OS pai. Cross-tenant proibido.

    Raise ValueError se viola.
    """
    if atividade.tenant_id != os.tenant_id:
        raise ValueError(
            f"INV-OS-ATIV-002: cross-tenant detectado — atividade.tenant_id={atividade.tenant_id} "
            f"!= os.tenant_id={os.tenant_id}"
        )
    if atividade.os_id != os.id:
        raise ValueError(
            f"INV-OS-ATIV-002: atividade.os_id={atividade.os_id} != os.id={os.id}"
        )


def valida_consentimento_biometria(aceite: AceiteAtividadeSnapshot) -> None:
    """INV-OS-CONSBIO-001 (P-OS-A1) + INV-OS-ACEITE-BIO-001 (SEG-M3-OS-02).

    (a) bio touch exige `consentimento_id NOT NULL`.
    (b) `biometria_key_id` precisa estar setado e seguir padrao
        `BIOMETRIA_KEY_<tenant_id>` (chave KMS dedicada por tenant —
        nao reusa chave geral de PII). Defesa em profundidade contra
        comprometimento cross-tenant da chave biometrica.

    Raise ValueError se algum item violado. Espelha trigger PG
    `aceite_atividade_consbio_check` em camada de dominio pra falhar cedo.

    Validacao de tamanho de trajetoria (≥8 pontos + bbox 30×20px) +
    watermark HMAC `HMAC(BIOMETRIA_KEY, tenant_id|atividade_id|aceito_em)`
    sao aplicadas no use case `coletar_aceite_atividade` ANTES do
    snapshot — exigem dados brutos (decifrados) que NAO chegam aqui.
    """
    if aceite.biometria_payload_encrypted is None:
        return  # sem biometria, nada a validar
    if aceite.consentimento_id is None:
        raise ValueError(
            "INV-OS-CONSBIO-001: AceiteAtividade com biometria exige consentimento_id NOT NULL "
            "(LGPD art. 11 II 'a' + Res. CD/ANPD 2/2022)."
        )
    # SEG-M3-OS-02: chave dedicada por tenant — formato canonico
    # `BIOMETRIA_KEY_<tenant_id>`. Vazio ou prefixo errado = bug de chamador.
    if not aceite.biometria_key_id or not aceite.biometria_key_id.startswith(
        "BIOMETRIA_KEY_"
    ):
        raise ValueError(
            "INV-OS-ACEITE-BIO-001: biometria_key_id deve seguir formato "
            "'BIOMETRIA_KEY_<tenant_id>' (chave KMS dedicada por tenant — "
            "LGPD art. 11 II 'g' + Lei 14.063/2020 art. 4o)."
        )


# =============================================================
# Canonicalizacao texto probatorio (ADR-0029 + INV-DOC-CANON-001)
# =============================================================

_MARCADOR_INICIO = "<<<CORPO INICIO>>>"
_MARCADOR_FIM = "<<<CORPO FIM>>>"


def canonicalizar_texto_probatorio(corpo: str) -> str:
    """ADR-0029: UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores.

    Retorna texto pronto pra hashing determinístico cross-platform.
    Aplica em ordem:
    1. NFC (composicao Unicode canonica)
    2. \\r\\n -> \\n (LF unico)
    3. Strip trailing whitespace por linha
    4. Strip leading/trailing global
    5. Envelope com marcadores
    """
    if not isinstance(corpo, str):
        raise TypeError("canonicalizar_texto_probatorio: corpo deve ser str.")

    canonico = unicodedata.normalize("NFC", corpo)
    canonico = canonico.replace("\r\n", "\n").replace("\r", "\n")
    canonico = "\n".join(line.rstrip() for line in canonico.split("\n"))
    canonico = canonico.strip()

    return f"{_MARCADOR_INICIO}\n{canonico}\n{_MARCADOR_FIM}"


def hash_texto_canonicalizado(corpo: str) -> str:
    """Retorna SHA-256 hex do texto pos-canonicalizacao (INV-DOC-CANON-001).

    Determinístico cross-platform: mesmo input -> mesmo hash em qualquer SO.
    """
    canonico = canonicalizar_texto_probatorio(corpo)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()
