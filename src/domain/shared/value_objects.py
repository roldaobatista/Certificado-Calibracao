"""Value objects compartilhados (puros, sem Django).

Wave A · Marco 1 (clientes) acrescenta CPF + CNPJ.
Onda 2 saneamento (2026-05-23) acrescenta:
  - JanelaVigencia (ADR-0030 — vigência temporal canônica)
  - ReferenciaPIIAnonimizavel (ADR-0032 — FK cross-módulo anonimizável)
  - Telefone (E.164 + DDD-BR)
  - UF brasileira (enum fechado IBGE)
  - PaisISO3166 (alpha-2)
  - Dinheiro (centavos + moeda ISO 4217; default BRL)

CNPJ aceita formato alfanumerico [A-Z0-9]{12}[0-9]{2} desde ja (IN RFB 2.229/2024
— vigencia jul/2026). Algoritmo DV = Modulo 11 com pesos 2-9, valor do caractere
= ord(c) - 48 (retrocompativel com CNPJ numerico antigo). Ver ADR-0017.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_CNPJ_FORMATO_RE = re.compile(r"^[A-Z0-9]{12}[0-9]{2}$")
_CPF_FORMATO_RE = re.compile(r"^[0-9]{11}$")


@dataclass(frozen=True)
class Email:
    """Email validado no boundary; armazenado lowercase.

    ValueError eh levantado eagerly — INV-VALIDACAO-001 (a definir): boundary
    rejeita formato invalido antes de chegar no dominio.
    """

    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Email invalido: {self.value!r}")
        # frozen=True forca contornar com object.__setattr__
        object.__setattr__(self, "value", self.value.lower())

    def __str__(self) -> str:
        return self.value


def _so_alfanum(raw: str) -> str:
    """Remove pontuacao comum (., -, /, espaco) e UPPER. Nao filtra letras."""
    return re.sub(r"[\s./\-]", "", raw).upper()


def _valor_caractere_cnpj(c: str) -> int:
    """Mapeia char (digito ou letra) pra valor numerico (algoritmo Serpro).

    '0'..'9' -> 0..9
    'A'..'Z' -> 17..42 (ord(c) - 48)
    """
    return ord(c) - 48


def _dv_modulo11(numeros: list[int], pesos: list[int]) -> int:
    """Modulo 11 generico — usado por CPF e CNPJ."""
    soma = sum(n * p for n, p in zip(numeros, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


@dataclass(frozen=True)
class CNPJ:
    """CNPJ aceitando formato alfanumerico (IN RFB 2.229/2024 — ADR-0017).

    Validacao:
    1. Apos limpar pontuacao, bate ^[A-Z0-9]{12}[0-9]{2}$
    2. Os 2 ultimos digitos (DV1, DV2) sao validos por Modulo 11.

    Algoritmo oficial Serpro:
    - Mapear cada char pra ord(c) - 48
    - DV1 sobre os 12 primeiros chars com pesos [5,4,3,2,9,8,7,6,5,4,3,2]
    - DV2 sobre os 13 primeiros (incluindo DV1) com pesos [6,5,...,2,9,8,...,2]

    Armazenado normalizado (sem pontuacao, UPPER).

    INV-024: dedup entra na camada de banco (UNIQUE(tenant_id, documento)).
    INV-036: idem.
    """

    value: str

    _PESOS_DV1: ClassVar[list[int]] = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    _PESOS_DV2: ClassVar[list[int]] = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def __post_init__(self) -> None:
        limpo = _so_alfanum(self.value)
        if not _CNPJ_FORMATO_RE.match(limpo):
            raise ValueError(
                f"CNPJ formato invalido: {self.value!r} -> {limpo!r} "
                f"(esperado 12 alfanumericos + 2 digitos verificadores). "
                f"Documento estrangeiro (passaporte/RNE) sera suportado em V2 — "
                f"nao use CPF/CNPJ de terceiro como workaround."
            )

        # Rejeita sequencias "trivial" (todos iguais) que passam no DV mas
        # nao sao CNPJ reais — pratica padrao Receita.
        if len(set(limpo)) == 1:
            raise ValueError(f"CNPJ invalido (sequencia trivial): {limpo!r}")

        nums = [_valor_caractere_cnpj(c) for c in limpo]
        dv1_calc = _dv_modulo11(nums[:12], CNPJ._PESOS_DV1)
        dv2_calc = _dv_modulo11(nums[:13], CNPJ._PESOS_DV2)
        if nums[12] != dv1_calc or nums[13] != dv2_calc:
            raise ValueError(
                f"CNPJ DV invalido: {limpo!r} "
                f"(DV1 esperado {dv1_calc}, achou {nums[12]}; "
                f"DV2 esperado {dv2_calc}, achou {nums[13]})"
            )

        object.__setattr__(self, "value", limpo)

    def __str__(self) -> str:
        return self.value

    def formatado(self) -> str:
        """Representacao XX.XXX.XXX/XXXX-XX (ou letras nas 12 primeiras posicoes)."""
        v = self.value
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:14]}"

    @property
    def e_alfanumerico(self) -> bool:
        """True se contem alguma letra (CNPJ pos IN RFB 2.229/2024)."""
        return any(c.isalpha() for c in self.value[:12])


@dataclass(frozen=True)
class CPF:
    """CPF numerico padrao Receita Federal (11 digitos + DV).

    Algoritmo: Modulo 11 com pesos decrescentes (10..2 pro DV1, 11..2 pro DV2).
    Armazenado so com numeros.
    """

    value: str

    def __post_init__(self) -> None:
        limpo = re.sub(r"\D", "", self.value)
        if not _CPF_FORMATO_RE.match(limpo):
            raise ValueError(
                f"CPF formato invalido: {self.value!r} (esperado 11 digitos). "
                f"Documento estrangeiro (passaporte/RNE) sera suportado em V2 — "
                f"nao use CPF de terceiro como workaround."
            )
        if len(set(limpo)) == 1:
            raise ValueError(f"CPF invalido (sequencia trivial): {limpo!r}")

        nums = [int(c) for c in limpo]
        pesos_1 = list(range(10, 1, -1))  # [10,9,...,2]
        pesos_2 = list(range(11, 1, -1))  # [11,10,...,2]
        dv1 = _dv_modulo11(nums[:9], pesos_1)
        dv2 = _dv_modulo11(nums[:10], pesos_2)
        if nums[9] != dv1 or nums[10] != dv2:
            raise ValueError(
                f"CPF DV invalido: {limpo!r} "
                f"(DV1 esperado {dv1}, achou {nums[9]}; "
                f"DV2 esperado {dv2}, achou {nums[10]})"
            )

        object.__setattr__(self, "value", limpo)

    def __str__(self) -> str:
        return self.value

    def formatado(self) -> str:
        v = self.value
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"


# =====================================================================
# ADR-0030 — VIGENCIA TEMPORAL CANONICA
# =====================================================================


@dataclass(frozen=True)
class JanelaVigencia:
    """Janela temporal canonica de entidade regulatoria (ADR-0030).

    Convencao unica para vigencia + revogacao em RT, RTCompetencia,
    Certificado, Procedimento, Padrao, Plano, Tarifa.

    Invariantes (INV-VIG-001..004):
      - inicio <= fim (quando ambos presentes)
      - revogado_em exige motivo_revogacao com >=10 chars
      - revogado_em <= fim (nao revogar depois do fim natural)
      - todo timestamp UTC-aware (timezone obrigatoria)

    Uso:
      vigencia = JanelaVigencia(inicio=datetime(2026,1,1,tzinfo=UTC), fim=None)
      assert vigencia.vigente_em(datetime.now(UTC))
    """

    inicio: datetime
    fim: datetime | None = None
    revogado_em: datetime | None = None
    motivo_revogacao: str | None = None

    def __post_init__(self) -> None:
        # Timezone obrigatoria
        for nome, dt in (("inicio", self.inicio), ("fim", self.fim), ("revogado_em", self.revogado_em)):
            if dt is not None and dt.tzinfo is None:
                raise ValueError(
                    f"JanelaVigencia.{nome} exige timezone-aware datetime "
                    f"(use datetime.now(UTC) ou similar) — INV-VIG-004"
                )
        # INV-VIG-001
        if self.fim is not None and self.inicio > self.fim:
            raise ValueError(
                f"JanelaVigencia: inicio {self.inicio} > fim {self.fim} (INV-VIG-001)"
            )
        # INV-VIG-002
        if self.revogado_em is not None:
            motivo = self.motivo_revogacao or ""
            if len(motivo) < 10:
                raise ValueError(
                    f"JanelaVigencia.revogado_em exige motivo_revogacao com >=10 chars "
                    f"(achou {len(motivo)}) — INV-VIG-002"
                )
            # INV-VIG-003
            limite = self.fim if self.fim is not None else datetime.max.replace(tzinfo=UTC)
            if self.revogado_em > limite:
                raise ValueError(
                    f"JanelaVigencia: revogado_em {self.revogado_em} > fim {limite} (INV-VIG-003)"
                )

    def vigente_em(self, momento: datetime) -> bool:
        """True se a janela cobre o instante (UTC-aware)."""
        if momento.tzinfo is None:
            raise ValueError("vigente_em exige datetime tz-aware (INV-VIG-004)")
        if self.revogado_em is not None and momento >= self.revogado_em:
            return False
        if momento < self.inicio:
            return False
        if self.fim is not None and momento >= self.fim:
            return False
        return True

    def vigente_agora(self) -> bool:
        return self.vigente_em(datetime.now(UTC))


# =====================================================================
# ADR-0032 — REFERENCIA PII ANONIMIZAVEL (FK cross-modulo)
# =====================================================================


@dataclass(frozen=True)
class ReferenciaPIIAnonimizavel:
    """Par (uuid_atual_id, hash_original) para FK cross-modulo a entidade PII.

    Permite:
      - Query operacional: JOIN via uuid_atual_id (rapido)
      - Query auditoria: agrupar por hash_original (preservado pos-anonimizacao)
      - Reconciliacao Zona A/B/C (ADR-0021)

    uuid_atual_id == None significa entidade foi eliminada (Zona A — LGPD art. 18 VI).
    hash_original sempre presente (NOT NULL) — HMAC-tenant com key_id versionado.

    INV-ANON-001..004 — ver ADR-0032.
    """

    uuid_atual_id: UUID | None
    hash_original: str
    key_id: str  # versao da chave KMS (rotacao GATE-1 ciclo PII)

    def __post_init__(self) -> None:
        if not self.hash_original:
            raise ValueError("ReferenciaPIIAnonimizavel.hash_original NOT NULL — INV-ANON-001")
        if len(self.hash_original) < 32:
            raise ValueError(
                f"hash_original tamanho {len(self.hash_original)} < 32 — esperado HMAC hex"
            )
        if not self.key_id or not re.match(r"^v\d+$", self.key_id):
            raise ValueError(f"key_id formato invalido: {self.key_id!r} (esperado vN)")

    def eliminada(self) -> bool:
        """True se entidade original foi eliminada (Zona A)."""
        return self.uuid_atual_id is None


# =====================================================================
# TELEFONE (E.164 + DDD-BR)
# =====================================================================

_TELEFONE_E164_RE = re.compile(r"^\+\d{8,15}$")
# DDD-BR validos pos 2012 (ANATEL Plano de Numeracao)
_DDDS_BR_VALIDOS = frozenset({
    11, 12, 13, 14, 15, 16, 17, 18, 19,  # SP
    21, 22, 24,  # RJ
    27, 28,  # ES
    31, 32, 33, 34, 35, 37, 38,  # MG
    41, 42, 43, 44, 45, 46,  # PR
    47, 48, 49,  # SC
    51, 53, 54, 55,  # RS
    61,  # DF
    62, 64,  # GO
    63,  # TO
    65, 66,  # MT
    67,  # MS
    68,  # AC
    69,  # RO
    71, 73, 74, 75, 77,  # BA
    79,  # SE
    81, 87,  # PE
    82,  # AL
    83,  # PB
    84,  # RN
    85, 88,  # CE
    86, 89,  # PI
    91, 93, 94,  # PA
    92, 97,  # AM
    95,  # RR
    96,  # AP
    98, 99,  # MA
})


@dataclass(frozen=True)
class Telefone:
    """Telefone E.164 com validacao DDD-BR quando codigo pais = +55.

    Internacional aceito (>=8 e <=15 digitos pos +).
    Numeros BR: +55 + DDD (2 digitos) + numero (8 ou 9 digitos).
    Celular BR: numero comeca com 9 (pos 2012).
    """

    value: str

    def __post_init__(self) -> None:
        limpo = re.sub(r"[\s().\-]", "", self.value)
        if not limpo.startswith("+"):
            # Tentativa de auto-correcao: assume BR se 10-11 digitos
            so_digitos = re.sub(r"\D", "", limpo)
            if 10 <= len(so_digitos) <= 11:
                limpo = "+55" + so_digitos
            else:
                raise ValueError(
                    f"Telefone exige formato E.164 (+CCNNNN...): {self.value!r}"
                )
        if not _TELEFONE_E164_RE.match(limpo):
            raise ValueError(f"Telefone formato E.164 invalido: {limpo!r}")
        # Validacao especifica BR
        if limpo.startswith("+55"):
            resto = limpo[3:]
            if len(resto) not in (10, 11):
                raise ValueError(
                    f"Telefone BR (+55) exige DDD + 8/9 digitos: {limpo!r}"
                )
            try:
                ddd = int(resto[:2])
            except ValueError as e:
                raise ValueError(f"Telefone BR DDD invalido: {limpo!r}") from e
            if ddd not in _DDDS_BR_VALIDOS:
                raise ValueError(
                    f"Telefone BR DDD {ddd:02d} nao esta no plano ANATEL: {limpo!r}"
                )
        object.__setattr__(self, "value", limpo)

    def __str__(self) -> str:
        return self.value

    @property
    def is_brasileiro(self) -> bool:
        return self.value.startswith("+55")

    @property
    def is_celular_br(self) -> bool:
        """Celular BR pos 2012 — DDD + 9 digitos comecando em 9."""
        if not self.is_brasileiro:
            return False
        resto = self.value[3:]
        return len(resto) == 11 and resto[2] == "9"


# =====================================================================
# UF brasileira (IBGE) + Pais ISO 3166-1 alpha-2
# =====================================================================

_UFS_VALIDAS = frozenset({
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
})


@dataclass(frozen=True)
class UF:
    """Unidade Federativa do Brasil (IBGE — 27 UFs)."""

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        if v not in _UFS_VALIDAS:
            raise ValueError(f"UF invalida: {self.value!r} (esperado uma de {sorted(_UFS_VALIDAS)})")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value


_PAIS_ISO_RE = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True)
class PaisISO3166:
    """Pais codigo ISO 3166-1 alpha-2 (ex: BR, US, PT). Lista completa nao validada
    — apenas formato. ISO 3166-1 tem ~249 codigos; manter whitelist seria overhead.
    """

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        if not _PAIS_ISO_RE.match(v):
            raise ValueError(f"PaisISO3166 formato invalido: {self.value!r} (esperado 2 letras)")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value


# =====================================================================
# DINHEIRO (centavos + moeda ISO 4217)
# =====================================================================

_MOEDA_ISO_RE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class Dinheiro:
    """Dinheiro em CENTAVOS (int) + moeda ISO 4217 (default BRL).

    Centavos evita float arredondamento (sempre int).
    Aritmetica entre moedas diferentes rejeitada (ValueError).

    MVP-1: BRL only (decisao Onda 10). Multi-moeda em V2 — VO ja preparado.
    """

    centavos: int
    moeda: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.centavos, int):
            raise ValueError(f"Dinheiro.centavos deve ser int: {type(self.centavos).__name__}")
        m = self.moeda.strip().upper()
        if not _MOEDA_ISO_RE.match(m):
            raise ValueError(f"Dinheiro.moeda formato ISO 4217 invalido: {self.moeda!r}")
        object.__setattr__(self, "moeda", m)

    def __add__(self, outro: Dinheiro) -> Dinheiro:
        if not isinstance(outro, Dinheiro):
            return NotImplemented
        if self.moeda != outro.moeda:
            raise ValueError(f"Dinheiro: nao soma {self.moeda} com {outro.moeda}")
        return Dinheiro(self.centavos + outro.centavos, self.moeda)

    def __sub__(self, outro: Dinheiro) -> Dinheiro:
        if not isinstance(outro, Dinheiro):
            return NotImplemented
        if self.moeda != outro.moeda:
            raise ValueError(f"Dinheiro: nao subtrai {self.moeda} com {outro.moeda}")
        return Dinheiro(self.centavos - outro.centavos, self.moeda)

    def __mul__(self, fator: int) -> Dinheiro:
        if not isinstance(fator, int):
            raise ValueError("Dinheiro: multiplicacao so por inteiro (use Decimal pra fracoes)")
        return Dinheiro(self.centavos * fator, self.moeda)

    @property
    def reais(self) -> float:
        """Apenas para representacao — NUNCA usar em calculo."""
        return self.centavos / 100

    def __str__(self) -> str:
        sinal = "-" if self.centavos < 0 else ""
        abs_c = abs(self.centavos)
        return f"{self.moeda} {sinal}{abs_c // 100},{abs_c % 100:02d}"


# =====================================================================
# F-A-M3 (Onda 2 saneamento — 2026-05-22)
# TENANT LIFECYCLE ESTADO + transicoes validas
# =====================================================================


class TenantLifecycleEstado(Enum):
    """Estados do ciclo de vida de um Tenant (ADR-0015 — lifecycle tenant).

    7 estados terminais ou em-transito do tenant no SaaS. Maquina de estados
    explicita (decisao 2026-05-22 — F-A-M3): sem string-typing, sem campo
    livre. Transicoes invalidas viram excecao em runtime.

    Estados:
      - PROVISIONANDO: tenant criado, infra sendo montada (state machine
        7 etapas em ADR-0015). Nao loga ate ATIVO.
      - ATIVO: operando normalmente. Plano em dia.
      - SUSPENSO_INADIMPLENCIA: inadimplencia leve. Login ok, mutacoes
        bloqueadas; sessoes mantidas. (modo `read_only` em billing-saas.)
      - READONLY: leitura permitida (mutacoes bloqueadas) por motivo nao
        financeiro — ex: migracao em andamento, congelamento por auditoria.
      - BLOQUEADO: inadimplencia grave OU bloqueio administrativo. Sessoes
        encerradas, login bloqueado, features desligadas. (modo
        `bloqueado_total` em billing-saas.)
      - CANCELANDO: cliente cancelou; janela de retencao Receita 5a / ISO
        25a esta correndo. Acesso so para download de portabilidade.
      - EXTINTO: fim da janela de retencao; chave KMS revogada
        (crypto-shredding). Sem retorno.

    Transicoes validas (TRANSICOES_VALIDAS abaixo):
      PROVISIONANDO -> ATIVO | EXTINTO (falha no provisioning aborta)
      ATIVO -> SUSPENSO_INADIMPLENCIA | READONLY | BLOQUEADO | CANCELANDO
      SUSPENSO_INADIMPLENCIA -> ATIVO (pagou) | BLOQUEADO (escalou)
      READONLY -> ATIVO (motivo resolvido) | CANCELANDO
      BLOQUEADO -> ATIVO (pagou+regularizou) | CANCELANDO
      CANCELANDO -> EXTINTO (janela vencida)
      EXTINTO -> (terminal — nenhuma)
    """

    PROVISIONANDO = "provisionando"
    ATIVO = "ativo"
    SUSPENSO_INADIMPLENCIA = "suspenso_inadimplencia"
    READONLY = "readonly"
    BLOQUEADO = "bloqueado"
    CANCELANDO = "cancelando"
    EXTINTO = "extinto"

    def __str__(self) -> str:
        return self.value


# Mapa de transicoes validas — frozenset por estado-origem.
# Tentar transicionar com destino fora do set levanta TransicaoInvalida.
# Imutavel (frozenset) — alteracao exige ADR.
_TRANSICOES_VALIDAS: dict[TenantLifecycleEstado, frozenset[TenantLifecycleEstado]] = {
    TenantLifecycleEstado.PROVISIONANDO: frozenset({
        TenantLifecycleEstado.ATIVO,
        TenantLifecycleEstado.EXTINTO,
    }),
    TenantLifecycleEstado.ATIVO: frozenset({
        TenantLifecycleEstado.SUSPENSO_INADIMPLENCIA,
        TenantLifecycleEstado.READONLY,
        TenantLifecycleEstado.BLOQUEADO,
        TenantLifecycleEstado.CANCELANDO,
    }),
    TenantLifecycleEstado.SUSPENSO_INADIMPLENCIA: frozenset({
        TenantLifecycleEstado.ATIVO,
        TenantLifecycleEstado.BLOQUEADO,
    }),
    TenantLifecycleEstado.READONLY: frozenset({
        TenantLifecycleEstado.ATIVO,
        TenantLifecycleEstado.CANCELANDO,
    }),
    TenantLifecycleEstado.BLOQUEADO: frozenset({
        TenantLifecycleEstado.ATIVO,
        TenantLifecycleEstado.CANCELANDO,
    }),
    TenantLifecycleEstado.CANCELANDO: frozenset({
        TenantLifecycleEstado.EXTINTO,
    }),
    TenantLifecycleEstado.EXTINTO: frozenset(),  # terminal
}


class TransicaoInvalida(ValueError):
    """Tentativa de mover Tenant entre estados nao permitidos."""


def validar_transicao_tenant(
    origem: TenantLifecycleEstado, destino: TenantLifecycleEstado
) -> None:
    """Levanta TransicaoInvalida se (origem, destino) nao esta em
    _TRANSICOES_VALIDAS. Caller responsavel por usar este validador em todo
    update de Tenant.estado_lifecycle.

    Uso:
      validar_transicao_tenant(tenant.estado, TenantLifecycleEstado.BLOQUEADO)
      tenant.estado = TenantLifecycleEstado.BLOQUEADO
    """
    permitidos = _TRANSICOES_VALIDAS.get(origem, frozenset())
    if destino not in permitidos:
        raise TransicaoInvalida(
            f"TenantLifecycleEstado: transicao invalida {origem.value!r} -> "
            f"{destino.value!r}. Permitidos a partir de {origem.value!r}: "
            f"{sorted(p.value for p in permitidos)}."
        )


def transicoes_validas_de(
    origem: TenantLifecycleEstado,
) -> frozenset[TenantLifecycleEstado]:
    """Retorna o conjunto de estados-destino permitidos a partir de `origem`.

    Util para UI / testes / documentacao gerada.
    """
    return _TRANSICOES_VALIDAS.get(origem, frozenset())
